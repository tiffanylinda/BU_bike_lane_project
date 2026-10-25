"""LaneMonitor: decide, one frame at a time, whether the bike lane is clear or blocked.

WHY ONE CLASS
-------------
Batch analysis, the replay demo (src/build_demo.py) and any future live mode all feed
detections through this same class, so they can never disagree about what counts as a
blockage. It never reads video: it takes the detections for one frame (rows of the
detections CSV) and returns any new events.

INPUTS
------
- A camera config dict (config/<camID>.yaml), using ``lane_polygon`` and ``blockage``.
- Per frame: the time in seconds and a list of detections, each a dict with at least
  ``cls`` (e.g. "car"), ``cx``, ``cy``, ``w``, ``h`` in full-frame pixels.

OUTPUTS
-------
``update()`` returns a list of new events (usually empty). Each event is a dict:
``{"event_id", "type": "possible" | "blocked" | "cleared", "t", "vehicle", "x", "y",
"stopped_for_s"}``; "cleared" also has ``"duration_s"`` and ``"reached_blocked"``, and
every event has ``"time"`` (ISO) when the caller passes a timestamp.

HOW IT WORKS (plain language)
-----------------------------
1. A vehicle is "in the lane" when the bottom-centre of its box (where its wheels touch
   the road) is inside a lane polygon (``lane_polygon`` or ``extra_lane_polygons``), or within ``lane_tolerance_px`` of it. The
   tolerance matters for our far-side lane: the polygon is only ~10 px tall there, so a
   parked car's wheels often land a few pixels outside it.
2. We follow each in-lane vehicle by POSITION (nearest box within ``merge_distance_px``),
   not by the tracker's id. Far away, the tracker often gives the same parked car a new
   id every few seconds; matching by position treats it as one vehicle.
3. A vehicle is "stopped" when it moved slower than ``stopped_max_speed_px_s`` over the
   last ``speed_window_s`` seconds.
4. If a stopped vehicle disappears (a bus or the Green Line passes in front of it), we
   keep it for ``merge_gap_s`` seconds instead of forgetting it. If it shows up again in
   the same place, the blockage simply continues. The price: when a car drives off
   without the detector seeing it move, the lane only reads clear after
   ``merge_gap_s + clear_after_s`` seconds.
5. Lane status: clear -> possible (a vehicle stopped ``possible_after_s``) -> blocked
   (stopped ``blocked_after_s``) -> clear (no stopped vehicle for ``clear_after_s``).
"""

import math
from collections import Counter


def point_in_polygon(x, y, polygon):
    """True if (x, y) is inside the polygon (a list of (x, y) points). Ray-casting rule."""
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        # Does a ray going right from (x, y) cross this edge?
        if (y1 > y) != (y2 > y):
            x_cross = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_cross:
                inside = not inside
    return inside


def distance_to_polygon_edge(x, y, polygon):
    """Shortest distance in pixels from (x, y) to the polygon's outline."""
    best = math.inf
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        length_sq = dx * dx + dy * dy
        # Project the point onto the edge, clamped to the segment's ends.
        s = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / length_sq))
        best = min(best, math.hypot(x - (x1 + s * dx), y - (y1 + s * dy)))
    return best


def in_lane(x, y, polygon, tolerance_px=0):
    """True if (x, y) is inside the lane polygon or within tolerance_px of its edge."""
    if point_in_polygon(x, y, polygon):
        return True
    return tolerance_px > 0 and distance_to_polygon_edge(x, y, polygon) <= tolerance_px


def lane_polygons(config):
    """All stretches of the bike lane for this camera, as a list of polygons.

    ``lane_polygon`` is the main stretch; ``extra_lane_polygons`` (optional) adds more
    stretches of the same lane, e.g. the block past an intersection. We keep them as
    separate polygons so the intersection in between is NOT lane: a car waiting at a red
    light there must not count as a blockage.
    """
    polygons = [config["lane_polygon"]] + list(config.get("extra_lane_polygons") or [])
    return [[tuple(point) for point in polygon] for polygon in polygons]


class LaneMonitor:
    """Frame-by-frame lane status. See the module docstring for the rules."""

    def __init__(self, config):
        blockage = config["blockage"]
        self.polygons = lane_polygons(config)
        self.vehicle_classes = set(blockage["vehicle_classes"])
        self.max_speed = blockage["stopped_max_speed_px_s"]
        self.speed_window_s = blockage.get("speed_window_s", 2.0)
        self.possible_after_s = blockage["possible_after_s"]
        self.blocked_after_s = blockage["blocked_after_s"]
        self.clear_after_s = blockage["clear_after_s"]
        self.merge_gap_s = blockage["merge_gap_s"]
        self.merge_distance_px = blockage["merge_distance_px"]
        self.tolerance_px = blockage.get("lane_tolerance_px", 0)

        self.status = "clear"
        self._vehicles = []  # vehicles currently being followed in the lane
        self._episode = None  # the current possible/blocked episode, if any
        self._next_event_id = 1
        self._last_stopped_t = None  # last time a stopped vehicle was seen

    # --- Step 1 and 2: which detections are in-lane vehicles, and who is who ----------
    def _in_lane_vehicles(self, detections):
        found = []
        for det in detections:
            if det["cls"] not in self.vehicle_classes:
                continue
            # Bottom-centre of the box = where the wheels touch the road.
            x = float(det["cx"])
            y = float(det["cy"]) + float(det["h"]) / 2
            if any(in_lane(x, y, polygon, self.tolerance_px) for polygon in self.polygons):
                found.append((x, y, det["cls"]))
        return found

    def _match(self, t, found):
        """Attach each in-lane detection to the nearest vehicle we already follow."""
        # Every (distance, vehicle, detection) pair close enough to be the same vehicle,
        # closest first, so each vehicle and each detection is used at most once.
        pairs = []
        for vi, vehicle in enumerate(self._vehicles):
            _, last_x, last_y = vehicle["points"][-1]
            for di, (x, y, _) in enumerate(found):
                distance = math.hypot(x - last_x, y - last_y)
                if distance <= self.merge_distance_px:
                    pairs.append((distance, vi, di))
        pairs.sort()

        used_vehicles, used_detections = set(), set()
        for _, vi, di in pairs:
            if vi in used_vehicles or di in used_detections:
                continue
            used_vehicles.add(vi)
            used_detections.add(di)
            self._observe(self._vehicles[vi], t, found[di])

        # Anything left over is a vehicle we have not seen before.
        for di, detection in enumerate(found):
            if di not in used_detections:
                vehicle = {"points": [], "classes": Counter(), "stopped_since": None, "last_seen": t}
                self._observe(vehicle, t, detection)
                self._vehicles.append(vehicle)

    def _observe(self, vehicle, t, detection):
        x, y, cls = detection
        vehicle["points"].append((t, x, y))
        vehicle["classes"][cls] += 1
        vehicle["last_seen"] = t
        # Only the last speed_window_s seconds matter for speed.
        vehicle["points"] = [p for p in vehicle["points"] if p[0] >= t - self.speed_window_s]

        # Step 3: stopped or moving? Needs at least half a window of history to judge.
        first_t, first_x, first_y = vehicle["points"][0]
        span = t - first_t
        if span < self.speed_window_s / 2:
            return
        speed = math.hypot(x - first_x, y - first_y) / span
        if speed < self.max_speed:
            if vehicle["stopped_since"] is None:
                vehicle["stopped_since"] = first_t  # it was already still across the window
        else:
            vehicle["stopped_since"] = None

    # --- Events -----------------------------------------------------------------------
    def _event(self, event_type, t, timestamp, vehicle, stopped_for):
        _, x, y = vehicle["points"][-1]
        event = {
            "event_id": self._episode["event_id"],
            "type": event_type,
            "t": round(t, 2),
            # The class seen most often: far away, a car flickers between "car" and "truck".
            "vehicle": vehicle["classes"].most_common(1)[0][0],
            "x": round(x, 1),
            "y": round(y, 1),
            "stopped_for_s": round(stopped_for, 1),
        }
        if timestamp is not None:
            event["time"] = timestamp
        return event

    def update(self, t, detections, timestamp=None):
        """Feed one frame (time in seconds + its detections). Returns a list of new events."""
        self._match(t, self._in_lane_vehicles(detections))

        # Step 4: forget vehicles not seen for merge_gap_s (they left, or we lost them).
        self._vehicles = [v for v in self._vehicles if t - v["last_seen"] <= self.merge_gap_s]

        events = []
        stopped = [v for v in self._vehicles if v["stopped_since"] is not None]

        if stopped:
            # When a stopped vehicle was last actually SEEN (hidden ones are still held).
            self._last_stopped_t = max(v["last_seen"] for v in stopped)
            # Keep following the episode's vehicle while it is still there; otherwise the
            # vehicle that has been stopped the longest.
            if self._episode and self._episode["vehicle"] in stopped:
                lead = self._episode["vehicle"]
            else:
                lead = min(stopped, key=lambda v: v["stopped_since"])
            # Measured up to when we last SAW it, so a hidden vehicle does not keep
            # adding stopped time while nobody can see it.
            stopped_for = lead["last_seen"] - lead["stopped_since"]

            if self.status == "clear" and stopped_for >= self.possible_after_s:
                self._episode = {
                    "event_id": self._next_event_id,
                    "vehicle": lead,
                    "start": lead["stopped_since"],
                    "reached_blocked": False,
                }
                self._next_event_id += 1
                self.status = "possible"
                events.append(self._event("possible", t, timestamp, lead, stopped_for))

            if self.status == "possible" and stopped_for >= self.blocked_after_s:
                self.status = "blocked"
                self._episode["reached_blocked"] = True
                events.append(self._event("blocked", t, timestamp, lead, stopped_for))

            if self._episode:
                self._episode["vehicle"] = lead

        elif self.status != "clear" and t - self._last_stopped_t >= self.clear_after_s:
            # Step 5: no stopped vehicle for clear_after_s -> the lane is clear again.
            episode = self._episode
            duration = self._last_stopped_t - episode["start"]
            event = self._event("cleared", t, timestamp, episode["vehicle"], duration)
            event["duration_s"] = round(duration, 1)
            event["reached_blocked"] = episode["reached_blocked"]
            events.append(event)
            self.status = "clear"
            self._episode = None

        return events


def run_on_dataframe(df, config):
    """Feed a whole detections CSV (as a pandas DataFrame) through a fresh LaneMonitor.

    Returns the list of events, with ``t`` in seconds from the first frame in the CSV.

    WHY we fill in empty frames: the CSV only has rows for frames where something was
    detected. When the parked car finally leaves, the frames after it may have no
    vehicles at all, so they are missing from the CSV. LaneMonitor still needs to "see"
    those empty frames to notice the lane is clear, so we rebuild the full list of
    processed frames from the frame numbers and feed empty ones too.
    """
    import pandas as pd  # only needed for batch runs, so imported here

    monitor = LaneMonitor(config)
    if df.empty:
        return []

    times = pd.to_datetime(df["time"], format="ISO8601")
    t0 = times.min()
    df = df.assign(t=(times - t0).dt.total_seconds())

    frames = sorted(df["frame"].unique())
    by_frame = {frame: group.to_dict("records") for frame, group in df.groupby("frame")}
    frame_times = df.groupby("frame")["t"].first()
    timestamps = df.groupby("frame")["time"].first()

    if len(frames) > 1:
        # The stride is the most common gap between processed frames; fps comes from the
        # first and last frame's times.
        step = int(pd.Series(frames).diff().dropna().mode().iloc[0])
        fps = (frames[-1] - frames[0]) / (frame_times[frames[-1]] - frame_times[frames[0]])
        all_frames = range(frames[0], frames[-1] + 1, step)
    else:
        fps, all_frames = None, frames

    events = []
    for frame in all_frames:
        t = frame_times[frame] if frame in frame_times.index else (frame - frames[0]) / fps
        timestamp = timestamps[frame] if frame in timestamps.index else None
        events.extend(monitor.update(float(t), by_frame.get(frame, []), timestamp))
    return events

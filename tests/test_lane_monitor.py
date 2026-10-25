"""Tests for LaneMonitor and the counting line, using small hand-made detections.

No video and no YOLO: each test builds the detections a real run would produce for a
simple scenario (a parked car, a car driving through, a train hiding the car...) and
checks the events LaneMonitor emits.
"""

import pandas as pd

from src.build_demo import clip_events
from src.count import count_crossings
from src.lane_monitor import LaneMonitor, in_lane, run_on_dataframe

# A thin far-side lane like ours: ~12 px tall, sloping across the frame.
CONFIG = {
    "lane_polygon": [[100, 400], [900, 360], [900, 372], [100, 412]],
    "counting_line": {"points": [[500, 340], [500, 420]], "side_a_name": "east", "side_b_name": "west"},
    "blockage": {
        "vehicle_classes": ["car", "truck", "bus"],
        "stopped_max_speed_px_s": 15,
        "speed_window_s": 2.0,
        "possible_after_s": 10,
        "blocked_after_s": 30,
        "clear_after_s": 5,
        "merge_gap_s": 20,
        "merge_distance_px": 40,
        "lane_tolerance_px": 8,
    },
}
FPS = 5  # we sample 5 frames per second


def car(x=500, bottom_y=386, cls="car"):
    """A 50x24 px car whose wheels (bottom-centre) are at (x, bottom_y)."""
    return {"cls": cls, "cx": x, "cy": bottom_y - 12, "w": 50, "h": 24}


def run(frames):
    """frames: list of detection lists, one per sampled frame. Returns all events."""
    monitor = LaneMonitor(CONFIG)
    events = []
    for i, detections in enumerate(frames):
        events += monitor.update(i / FPS, detections)
    return events


def seconds(n, detections):
    return [detections] * int(n * FPS)


def types(events):
    return [e["type"] for e in events]


def test_parked_car_goes_possible_blocked_cleared():
    events = run(seconds(45, [car()]) + seconds(30, []))
    assert types(events) == ["possible", "blocked", "cleared"]
    possible, blocked, cleared = events
    assert 9.5 <= possible["t"] <= 11
    assert 29.5 <= blocked["t"] <= 31
    assert cleared["reached_blocked"] is True
    assert 43 <= cleared["duration_s"] <= 46
    assert {e["event_id"] for e in events} == {1}


def test_short_stop_gives_no_events():
    assert run(seconds(8, [car()]) + seconds(30, [])) == []


def test_car_driving_through_gives_no_events():
    # 80 px/s along the lane: well above the 15 px/s "stopped" speed.
    frames = [[car(x=150 + 80 * i / FPS, bottom_y=405 - 4 * i / FPS)] for i in range(int(9 * FPS))]
    assert run(frames) == []


def test_occlusion_by_a_train_keeps_one_blockage():
    # Parked 25 s, hidden by a passing train for 12 s, visible again for 20 s, then leaves.
    frames = seconds(25, [car()]) + seconds(12, []) + seconds(20, [car(x=503)]) + seconds(30, [])
    events = run(frames)
    assert types(events) == ["possible", "blocked", "cleared"]


def test_class_flicker_and_jitter_is_one_vehicle():
    # Far away, YOLO flips between car and truck and the box jitters a few pixels.
    frames = [[car(x=500 + (i % 3), cls="car" if i % 4 else "truck")] for i in range(int(40 * FPS))]
    events = run(frames + seconds(30, []))
    assert types(events) == ["possible", "blocked", "cleared"]
    assert events[0]["vehicle"] == "car"  # the class seen most often


def test_wheels_just_outside_thin_polygon_count_with_tolerance():
    polygon = CONFIG["lane_polygon"]
    assert not in_lane(500, 393, polygon)  # 5 px below the lane's lower edge
    assert in_lane(500, 393, polygon, tolerance_px=8)
    assert not in_lane(500, 420, polygon, tolerance_px=8)  # the near lane is not our lane


def test_vehicle_outside_lane_is_ignored():
    assert run(seconds(45, [car(bottom_y=480)])) == []


def test_run_on_dataframe_fills_empty_frames_so_it_clears():
    # The CSV only has rows while the car is there; the empty frames after must still clear it.
    rows = []
    for i in range(int(40 * FPS)):
        frame = i * 12  # 60 fps video sampled at 5 fps
        time = pd.Timestamp("2026-10-24 12:00:00", tz="America/New_York") + pd.Timedelta(frame / 60, unit="s")
        rows.append({"frame": frame, "time": time.isoformat(), **car()})
    # One far-away pedestrian 50 s later, so the CSV runs on past the car leaving.
    frame = int(90 * 60)
    time = pd.Timestamp("2026-10-24 12:00:00", tz="America/New_York") + pd.Timedelta(90, unit="s")
    rows.append({"frame": frame, "time": time.isoformat(), "cls": "person", "cx": 50, "cy": 50, "w": 5, "h": 10})

    events = run_on_dataframe(pd.DataFrame(rows), CONFIG)
    assert types(events) == ["possible", "blocked", "cleared"]


def test_clip_window_carries_in_an_ongoing_blockage():
    events = run(seconds(45, [car()]) + seconds(30, []))
    clip = clip_events(events, start=35, end=80)
    assert clip[0]["t"] == 0 and clip[-1]["type"] == "cleared"
    assert "blocked" in types(clip)


def _track(uid, cls, points):
    return [{"uid": uid, "cls": cls, "cx": x, "cy": 380, "t": t} for t, x in points]


def test_bike_crossing_counts_once_even_when_wobbling():
    rows = _track("b1", "bicycle", [(0, 480), (1, 495), (2, 505), (3, 498), (4, 510), (5, 530)])
    crossings = count_crossings(rows, CONFIG)
    assert [c["mode"] for c in crossings] == ["bike"]


def test_rider_is_not_counted_as_pedestrian():
    rows = _track("b1", "bicycle", [(0, 480), (1, 520)]) + _track("p1", "person", [(0, 478), (1, 518)])
    rows.sort(key=lambda r: r["t"])
    assert [c["mode"] for c in count_crossings(rows, CONFIG)] == ["bike"]


def test_white_car_spot_is_in_cam_a_lane_but_the_intersection_is_not():
    import yaml

    from src.lane_monitor import lane_polygons

    with open("config/camA.yaml") as f:
        cam_a = yaml.safe_load(f)
    polygons = lane_polygons(cam_a)
    tolerance = cam_a["blockage"]["lane_tolerance_px"]

    def inside(x, y):
        return any(in_lane(x, y, p, tolerance) for p in polygons)

    assert inside(1043, 326)  # where the white car parks, past the intersection
    assert inside(600, 415)  # the original block
    assert not inside(950, 370)  # the crosswalk/intersection between the two blocks

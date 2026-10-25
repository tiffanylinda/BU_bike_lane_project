"""Count bikes and pedestrians crossing the counting line.

INPUTS:  a detections CSV (from src/detect.py) and its camera config (counting_line).
OUTPUTS: --output CSV with one row per counted object: time, t, uid, mode, direction.

    python -m src.count --detections data/detections/commave_camA_..._detections.csv \
        --config config/camA.yaml --output outputs/crossings.csv

A track is counted once, the first time its centre crosses the counting line. A person
crossing at almost the same time and place as a bicycle is its rider, not a pedestrian.

Note: on our far-side camera angle bikes are small and often missed, so treat these
counts as a rough lower bound (see the limitations section).
"""

import argparse
import math

# COCO class name -> the mode we report.
MODES = {"bicycle": "bike", "person": "pedestrian", "skateboard": "skateboard"}

# A person crossing within this many seconds and pixels of a bike crossing is its rider.
RIDER_MAX_SECONDS = 1.5
RIDER_MAX_PIXELS = 60


def side_of_line(x, y, line):
    """+1 or -1 for which side of the line (x, y) is on, 0 if exactly on it."""
    (x1, y1), (x2, y2) = line
    cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
    return (cross > 0) - (cross < 0)


def within_segment(x, y, line):
    """True if (x, y) projects onto the line segment (not past either end)."""
    (x1, y1), (x2, y2) = line
    dx, dy = x2 - x1, y2 - y1
    s = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    return 0 <= s <= 1


def count_crossings(rows, config):
    """Return one dict per counted crossing, sorted by time.

    ``rows`` is a list of detection dicts with uid, cls, cx, cy and t (seconds), sorted
    by time. Each uid is counted at most once (so a track wobbling on the line counts once).
    """
    line = config["counting_line"]["points"]
    names = {1: config["counting_line"]["side_a_name"], -1: config["counting_line"]["side_b_name"]}

    last_side = {}  # uid -> side it was on last time we saw it
    counted = set()
    crossings = []
    for row in rows:
        mode = MODES.get(row["cls"])
        uid = row["uid"]
        if mode is None or uid in counted:
            continue
        x, y = float(row["cx"]), float(row["cy"])
        side = side_of_line(x, y, line)
        previous = last_side.get(uid)
        if previous and side and side != previous and within_segment(x, y, line):
            counted.add(uid)
            crossings.append({"t": row["t"], "time": row.get("time"), "uid": uid, "mode": mode,
                              "direction": names[side], "x": x, "y": y})
        if side:
            last_side[uid] = side

    # Drop "pedestrians" that are really the riders of a bike crossing at the same moment.
    bikes = [c for c in crossings if c["mode"] == "bike"]

    def is_rider(person):
        return any(
            abs(person["t"] - bike["t"]) <= RIDER_MAX_SECONDS
            and math.hypot(person["x"] - bike["x"], person["y"] - bike["y"]) <= RIDER_MAX_PIXELS
            for bike in bikes
        )

    return [c for c in crossings if not (c["mode"] == "pedestrian" and is_rider(c))]


def main(argv=None):
    import pandas as pd
    import yaml

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--detections", required=True, help="A *_detections.csv from src/detect.py")
    parser.add_argument("--config", required=True, help="That camera's config/<camID>.yaml")
    parser.add_argument("--output", required=True, help="Where to write crossings.csv")
    args = parser.parse_args(argv)

    with open(args.config) as f:
        config = yaml.safe_load(f)
    df = pd.read_csv(args.detections)
    times = pd.to_datetime(df["time"], format="ISO8601")
    df = df.assign(t=(times - times.min()).dt.total_seconds()).sort_values("t")

    crossings = count_crossings(df.to_dict("records"), config)
    out = pd.DataFrame(crossings, columns=["time", "t", "uid", "mode", "direction"])
    out.to_csv(args.output, index=False)
    print(f"{len(out)} crossings -> {args.output}")
    print(out["mode"].value_counts().to_string() if len(out) else "(none)")


if __name__ == "__main__":
    main()

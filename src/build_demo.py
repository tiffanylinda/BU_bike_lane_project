"""Build the events.json that the replay demo and the rider web app play back.

INPUTS
  --detections  one video's *_detections.csv (from src/detect.py)
  --config      that camera's config/<camID>.yaml (lane polygon, blockage thresholds)
  --start/--end the demo clip's window, in seconds from the start of that video
                (default: the whole video)
  --video-src   the clip path the front end should load (written into the JSON)
OUTPUT
  --output      events.json in the shared format (Spec 4 in docs/KIRO_PROMPTS.md),
                default app/frontend/public/data/events.json

    python -m src.build_demo \
        --detections data/detections/commave_camA_2026-10-24_1200_detections.csv \
        --config config/camA.yaml --start 120 --end 185

The whole video goes through LaneMonitor (not just the clip window), so a car that
parked BEFORE the clip starts is still known to be blocking when the clip begins. If the
lane is already amber/red at --start, we add that state as an event at t=0.
"""

import argparse
import json

from src.count import count_crossings
from src.lane_monitor import run_on_dataframe

DEFAULT_OUTPUT = "app/frontend/public/data/events.json"


def clip_events(events, start, end):
    """Keep events inside [start, end] and make their times relative to the clip start."""
    before = [e for e in events if e["t"] < start]
    inside = [dict(e, t=round(e["t"] - start, 2)) for e in events if start <= e["t"] <= end]

    # The lane may already be amber/red when the clip starts: carry that state in at t=0.
    if before and before[-1]["type"] != "cleared" and not (inside and inside[0]["t"] == 0):
        carried = [dict(e, t=0.0) for e in before if e["event_id"] == before[-1]["event_id"]]
        inside = carried + inside
    return inside


def summarize(events, crossings):
    cleared = [e for e in events if e["type"] == "cleared" and e.get("reached_blocked")]
    return {
        "blockages": len({e["event_id"] for e in events if e["type"] == "blocked"}),
        "minutes_blocked": round(sum(e["duration_s"] for e in cleared) / 60, 2),
        "bikes": sum(1 for c in crossings if c["mode"] == "bike"),
    }


def main(argv=None):
    import pandas as pd
    import yaml

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--detections", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--start", type=float, default=0.0, help="Clip start, seconds into the video")
    parser.add_argument("--end", type=float, default=None, help="Clip end, seconds into the video")
    parser.add_argument("--video-src", default="media/demo_clip.mp4")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    with open(args.config) as f:
        config = yaml.safe_load(f)
    df = pd.read_csv(args.detections)
    times = pd.to_datetime(df["time"], format="ISO8601")
    df = df.assign(t=(times - times.min()).dt.total_seconds()).sort_values(["t", "frame"])
    end = args.end if args.end is not None else float(df["t"].max())

    events = run_on_dataframe(df.drop(columns="t"), config)
    clip = clip_events(events, args.start, end)

    crossings = [
        {"t": round(c["t"] - args.start, 2), "mode": c["mode"]}
        for c in count_crossings(df.to_dict("records"), config)
        if args.start <= c["t"] <= end
    ]

    clip_start_time = (times.min() + pd.Timedelta(args.start, unit="s")).isoformat()
    output = {
        "location": {key: config["location"][key] for key in ("name", "lat", "lon")},
        "clip_start_time": clip_start_time,
        "video": args.video_src,
        "events": [
            {k: e[k] for k in ("t", "type", "vehicle", "stopped_for_s", "duration_s", "event_id") if k in e}
            for e in clip
        ],
        "crossings": crossings,
        "summary": summarize(clip, crossings),
    }
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"{len(events)} events in the whole video, {len(clip)} in the clip -> {args.output}")
    for e in clip:
        print(f"  {e['t']:7.1f}s  {e['type']:<8} {e['vehicle']:<6} stopped {e['stopped_for_s']}s")
    print(f"summary: {output['summary']}")


if __name__ == "__main__":
    main()

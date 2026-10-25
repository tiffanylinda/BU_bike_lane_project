"""Turn detections CSVs into findings: blockages, time blocked, bikes affected.

INPUTS
  --detections  one or more *_detections.csv files (or a folder of them)
  --config-dir  where config/<camID>.yaml live (default config/)
OUTPUTS (in --output, default outputs/)
  insights.md                  a readable summary, one section per video/camera
  <video>_blockages.csv        one row per stop: start, end, duration, vehicle, reached_blocked

    python -m src.insights --detections data/detections --output outputs

Each video goes through the same LaneMonitor the app uses. Cameras are reported
separately and never added together (they film the same street).
"""

import argparse
from pathlib import Path


def episodes_from_events(events, video_end_t):
    """Pair each possible/blocked event with its "cleared" event -> one row per stop."""
    rows = {}
    for e in events:
        row = rows.setdefault(e["event_id"], {"event_id": e["event_id"], "vehicle": e["vehicle"],
                                             "x": e["x"], "y": e["y"], "reached_blocked": False})
        if e["type"] == "possible":
            row["start_t"] = e["t"] - e["stopped_for_s"]
        elif e["type"] == "blocked":
            row["reached_blocked"] = True
        elif e["type"] == "cleared":
            row["end_t"] = row["start_t"] + e["duration_s"]
    for row in rows.values():
        # Still stopped when the recording ended: it lasted at least until the end.
        row.setdefault("end_t", video_end_t)
        row["open_at_end"] = row["end_t"] == video_end_t
        row["duration_s"] = round(row["end_t"] - row["start_t"], 1)
    return list(rows.values())


def fmt_minutes(seconds):
    return f"{seconds / 60:.1f} min"


def analyse(csv_path, config_dir, output_dir):
    import pandas as pd
    import yaml

    from src.count import count_crossings
    from src.detect import load_camera_config, parse_video_name
    from src.lane_monitor import run_on_dataframe

    camera_id, start = parse_video_name(Path(str(csv_path).replace("_detections.csv", ".mp4")))
    config = load_camera_config(config_dir, camera_id)
    df = pd.read_csv(csv_path)
    if df.empty:
        return f"## {csv_path.name}\n\nNo detections.\n"

    times = pd.to_datetime(df["time"], format="ISO8601")
    t0 = times.min()
    df = df.assign(t=(times - t0).dt.total_seconds()).sort_values(["t", "frame"])
    recorded_s = float(df["t"].max())

    events = run_on_dataframe(df.drop(columns="t"), config)
    stops = pd.DataFrame(episodes_from_events(events, recorded_s))
    crossings = pd.DataFrame(count_crossings(df.to_dict("records"), config))

    video = csv_path.name.replace("_detections.csv", "")
    if len(stops):
        clock = lambda t: (t0 + pd.Timedelta(t, unit="s")).strftime("%H:%M:%S")  # noqa: E731
        stops["start"] = stops["start_t"].map(clock)
        stops["end"] = stops["end_t"].map(clock)
        stops[["event_id", "start", "end", "duration_s", "vehicle", "reached_blocked", "open_at_end", "x", "y"]].to_csv(
            output_dir / f"{video}_blockages.csv", index=False
        )

    blocked = stops[stops["reached_blocked"]] if len(stops) else stops
    blocked_s = float(blocked["duration_s"].sum()) if len(blocked) else 0.0
    bikes = crossings[crossings["mode"] == "bike"] if len(crossings) else crossings

    # Bikes that rode past while the lane was blocked: they had to merge into traffic.
    bikes_during = 0
    for _, stop in blocked.iterrows():
        bikes_during += int(((bikes["t"] >= stop["start_t"]) & (bikes["t"] <= stop["end_t"])).sum()) if len(bikes) else 0

    in_lane_vehicles = df[df["cls"].isin(config["blockage"]["vehicle_classes"])]
    lines = [
        f"## {video} (camera {camera_id})",
        "",
        f"- Recorded: {fmt_minutes(recorded_s)} starting {start:%Y-%m-%d %H:%M}",
        f"- **Blockages** (vehicle stopped in the bike lane {config['blockage']['blocked_after_s']} s or more): "
        f"**{len(blocked)}**, blocking the lane for **{fmt_minutes(blocked_s)}** "
        f"(**{100 * blocked_s / recorded_s:.0f}%** of the recording)",
    ]
    if len(blocked):
        longest = blocked.loc[blocked["duration_s"].idxmax()]
        lines += [
            f"- Longest: {fmt_minutes(longest['duration_s'])} ({longest['vehicle']}, from {longest['start']})"
            + (" — still there when the recording ended" if longest["open_at_end"] else ""),
            f"- Median blockage: {fmt_minutes(float(blocked['duration_s'].median()))}",
            f"- By vehicle: " + ", ".join(f"{k} {v}" for k, v in blocked["vehicle"].value_counts().items()),
        ]
    short = len(stops) - len(blocked)
    lines += [
        f"- Shorter stops ({config['blockage']['possible_after_s']}-{config['blockage']['blocked_after_s']} s, "
        f"e.g. pick-ups/drop-offs): {short}",
        f"- Bikes counted crossing the line: {len(bikes)}"
        + (f" ({len(bikes) / (recorded_s / 3600):.0f} per hour)" if recorded_s > 0 else ""),
        f"- Bikes that passed while the lane was blocked: {bikes_during}",
        "",
        "Detection health (how well the camera sees the far lane):",
        f"- Frames analysed: {df['frame'].nunique()}; vehicle detections: {len(in_lane_vehicles)}; "
        f"median vehicle confidence: {in_lane_vehicles['conf'].median():.2f}" if len(in_lane_vehicles) else "- No vehicles detected",
        f"- Detections by class: " + ", ".join(f"{k} {v}" for k, v in df["cls"].value_counts().items()),
        "",
    ]
    if len(blocked):
        lines += ["| # | start | end | duration | vehicle |", "|---|---|---|---|---|"]
        for _, s in blocked.sort_values("start_t").iterrows():
            lines.append(f"| {s['event_id']} | {s['start']} | {s['end']} | {fmt_minutes(s['duration_s'])} | {s['vehicle']} |")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--detections", nargs="+", required=True, help="CSV files or folders of them")
    parser.add_argument("--config-dir", default="config/")
    parser.add_argument("--output", default="outputs/")
    args = parser.parse_args(argv)

    csvs = []
    for item in map(Path, args.detections):
        csvs += sorted(item.glob("*_detections.csv")) if item.is_dir() else [item]
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    report = ["# Comm Ave bike lane: findings", ""]
    report += [analyse(csv, args.config_dir, output_dir) for csv in csvs]
    report += [
        "_Limitation: the bike lane is on the far side of the street, so small or hidden "
        "vehicles and bikes can be missed. Treat counts as lower bounds._",
    ]
    text = "\n".join(report)
    (output_dir / "insights.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()

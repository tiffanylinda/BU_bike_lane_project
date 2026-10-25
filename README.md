# Comm Ave Bike Lane Monitor

A BU hackathon project (Spark! / Hackachusetts). We filmed the Commonwealth Ave bike lane
between Essex St and Kenmore Square, detected vehicles stopped in the bike lane with
computer vision, and built a rider app that warns cyclists when the lane is blocked.

- **Rider web app** (`app/frontend/rider.html`): a mobile-first prototype of the rider app.
- **Replay demo** (`app/frontend/index.html`): a recorded clip plays next to a phone that
  shows lane status and alerts in sync, for presenting.
- **Detection pipeline** (`src/`): video → detections CSV → lane status events for the app.

> **Note:** this repository is a copy of our team's original Hackachusetts repository, made for
> the BU submission. The whole team contributed to the project, but because the files were
> copied over rather than forked, the commit history here doesn't show my teammates'
> contributions.

## Repository layout

```
app/frontend/   React + Vite front end: replay demo and rider web app (runs from static files)
app/backend/    optional FastAPI API with sample data (the front end does not need it)
src/            detection pipeline: detect.py, lane_monitor.py, count.py, build_demo.py
tools/          pick_points.py (draw the lane outline), export_frame.py
config/         per-camera settings: lane outline, counting line, thresholds, model
notebooks/      run_detection.ipynb: runs detection in Google Colab
tests/          pytest tests for the pipeline (synthetic data, no video needed)
docs/, .kiro/   project specs and the prompts used to build it
```

## Run the app

```bash
cd app/frontend
npm install
npm run dev
```

Open the URL Vite prints (e.g. http://localhost:5173) for the replay demo, or add
`/rider.html` for the rider web app. See [app/README.md](app/README.md) for building and
hosting on GitHub Pages.

## Run the pipeline

```
raw video --detect.py--> detections CSV --build_demo.py (LaneMonitor + counting)--> events.json --> app
```

1. **Detect** in Google Colab (free GPU): open `notebooks/run_detection.ipynb`, choose a
   T4 GPU runtime, set your Drive folders in Step 4, and run all cells. Videos must be named
   `commave_<camID>_YYYY-MM-DD_HHMM.mp4`; the camera id picks `config/<camID>.yaml`.
   Run the notebook's 3-minute quick check first and look at the `_annotated.mp4`: the yellow
   outline is the lane and the blue box is the area YOLO looks at.

2. **Build events** for a demo clip (on a laptop, no GPU needed):

   ```bash
   pip install -r requirements.txt
   python -m src.build_demo --detections <folder>/commave_camA_2026-10-24_1200_detections.csv \
       --config config/camA.yaml --start 120 --end 185
   ```

   This writes `app/frontend/public/data/events.json`. Put the same stretch of raw video in
   `app/frontend/public/media/demo_clip.mp4`.

3. **Test:** `python -m pytest tests app/backend/tests -q`

### How detection works

- `src/detect.py` runs YOLO (`yolov8s`) with ByteTrack tracking. It analyses 5 frames per
  second and only looks at an upscaled crop around the far-side lane, which makes small, distant
  vehicles visible to the model and keeps a 40-minute video to roughly 10 minutes on a Colab GPU.
- `src/lane_monitor.py` decides the lane status, one frame at a time: a vehicle whose wheels are
  in the lane outline and has stopped for 10 s is "possible", and for 30 s it is "blocked". It
  follows vehicles by position, and it remembers a stopped vehicle while a bus or train hides it.
- `src/count.py` counts bikes and pedestrians crossing the counting line.

All settings (lane outline, thresholds, crop, model) are in `config/camA.yaml` and
`config/camB.yaml`. To redraw a lane outline, run
`python tools/pick_points.py --video <clip>` and paste the printed points into the config.

## Privacy

Raw video and frames are never committed (`data/` and `*.mp4`/`*.mov` are gitignored).
Annotated videos blur faces and license plates.

## Limitations

The bike lane is on the far side of Comm Ave from our cameras, so vehicles and especially bikes
are small and often hidden by traffic and the Green Line. Counts are lower bounds, and a car
that leaves while hidden only reads as gone about 20 s later. A camera on the lane's side of the
street, or with a clearer view, would be far more reliable.

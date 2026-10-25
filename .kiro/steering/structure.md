# Project structure

bike-lane-project/
  config/camA.yaml, camB.yaml  per camera: lane outline(s), counting line, thresholds, crop, model
  config/camera.yaml          template for a new camera
  data/                       raw video, frames, detections, Telraam (gitignored, lives on Drive)
  src/detect.py               video -> detections CSV (+ optional annotated, blurred MP4)
  src/lane_monitor.py         LaneMonitor class: frame-by-frame lane status + events
  src/count.py                detections -> counting-line crossings (bike, pedestrian, ...)
  src/build_demo.py           detections CSV -> events.json for the app
  tools/pick_points.py        click on a frame to get line/polygon coordinates
  tools/export_frame.py       save a video's first frame as a PNG
  notebooks/run_detection.ipynb  Colab notebook that runs detection from Google Drive
  tests/                      pytest tests using small synthetic data
  app/                        "Comm Ave Lane Watch" app
    frontend/                 React + Vite: replay demo (index.html) + rider web app (rider.html)
    frontend/public/data/     events JSON the front end plays back (runs without the backend)
    backend/                  optional FastAPI + uvicorn API over sample CSVs in backend/data/
    README.md                 how to run the app

Planned, not built yet: Telraam download and count validation, an evidence dashboard,
and a live-camera mode.

Specs: keep requirements.md, design.md and tasks.md short. No more than 5 acceptance
criteria per requirement. Skip diagrams and long test plans.

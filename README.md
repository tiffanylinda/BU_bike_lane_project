# BU_bike_lane_project
This repo is for BU Hackathon submission

## From video to the app

```
raw video --detect.py--> detections CSV --build_demo.py (LaneMonitor + counting)--> events.json --> app
```

1. **Detect** (Colab, GPU): see `notebooks/run_detection.ipynb`, or

   ```bash
   python -m src.detect --input /content/drive/MyDrive/<folder>/commave_camA_2026-10-24_1200.mp4 \
       --output /content/drive/MyDrive/<folder>/detections --save-annotated
   ```

   Settings come from `config/camA.yaml`. It analyses 5 frames per second
   (`detection.sample_fps`) and only looks at a crop around the far-side lane, upscaled
   (`detection.roi_pad`, `model.imgsz`). Small far-away vehicles become visible to YOLO
   and the run is much faster. Check the `_annotated.mp4`: the yellow outline is the lane
   polygon and the blue box is the crop. Every vehicle you want caught must have its
   wheels on the yellow outline.

2. **Build events** (laptop, no GPU needed): pick the demo clip's window in that video.

   ```bash
   python -m src.build_demo --detections <detections>/commave_camA_2026-10-24_1200_detections.csv \
       --config config/camA.yaml --start 120 --end 185
   ```

   This writes `app/frontend/public/data/events.json`. Cut the same window of the raw
   video into `app/frontend/public/media/demo_clip.mp4` (see `app/README.md`).

3. **Tests:** `python -m pytest tests -q`

Known limitation: the bike lane is on the far side of Comm Ave, so vehicles and
especially bikes are small and often hidden by traffic and the Green Line. LaneMonitor
holds a stopped vehicle for `merge_gap_s` while it is hidden, but a camera on the lane's
side of the street would be far more reliable.

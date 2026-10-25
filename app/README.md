# Comm Ave Lane Watch (app/)

- `frontend/`: React + Vite. It runs entirely from static files (no backend needed), so it
  can be hosted on GitHub Pages as a public testing link. Two pages:
  - `index.html`, the **replay demo**: the recorded clip next to a phone mock-up, for presenting.
  - `rider.html`, the **rider web app**: full-screen and mobile first, with no video. It is the
    prototype of the future mobile app. For now it replays the recorded events on a loop (the
    "demo feed"). On a phone, "Add to Home Screen" opens it like an installed app.
- `backend/`: an optional FastAPI API (lane status, blockages, stats, rider reports) over the
  sample CSVs in `backend/data/`.

## Run the front end

```bash
cd app/frontend
npm install
npm run dev        # open the URL Vite prints; add /rider.html for the rider web app

npm run build      # production build into app/frontend/dist/
npm run preview    # serve the built dist/ to check it
```

Events come from `frontend/public/data/events.json` (written by `src/build_demo.py`). If it is
missing, the app uses `sample_events.json` and shows a "sample data" notice.

The replay clip is local only: video files are gitignored. Without a clip, the replay demo
shows a placeholder and still plays the status and alerts. See
[frontend/README.md](frontend/README.md) for adding a clip and publishing to GitHub Pages.

## Run the backend (optional)

```bash
# from the repo root
python -m venv .venv && source .venv/bin/activate
pip install -r app/backend/requirements.txt

cd app/backend
uvicorn main:app --reload    # then open http://127.0.0.1:8000/docs
```

Endpoints:
- `GET /api/status?t=`: lane status at second `t` of the recording
- `GET /api/blockages`: in-bike-lane blockages with `duration_seconds`
- `GET /api/stats`: totals, average/longest duration, count by vehicle, bikes by hour
- `POST /api/reports`: submit a rider report; `GET /api/reports` lists them (kept in memory)

Tests: `python -m pytest app/backend/tests -q`

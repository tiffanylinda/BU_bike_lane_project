# Comm Ave Bike Lane Monitor — Replay Demo (frontend)

A standalone React + Vite front end that plays a recorded clip next to a phone-sized
"rider app" showing lane status and alerts, played back in sync. Plain CSS, no UI library,
no charts. It runs entirely from static files, so it can be hosted on GitHub Pages.

It does **not** require the FastAPI backend. Events are read from static JSON in
`public/data/`, and if the video clip is missing the app still runs off a configured
fallback duration.

## Run it

```bash
cd app/frontend
npm install
npm run dev        # local dev server (Vite prints the URL, e.g. http://localhost:5173)
```

Build and preview the production bundle:

```bash
npm run build      # outputs static files to dist/
npm run preview    # serve the built dist/ locally to check it
```

## The video clip

The replay clip lives at `public/media/demo_clip.mov` **locally only** — it is large and
gitignored (`*.mov`), so it is never committed. The app uses it when present and falls back
to a placeholder stage (driven by `CONFIG.videoDurationSeconds`) when it is absent.

On **GitHub Pages** the `.mov` will not be there. To ship a playable clip, drop a small
compressed **`demo_clip.mp4`** into `public/media/` and point `CONFIG.videoSrc` in
`src/config.js` at it. MP4 plays reliably in browsers; `.mov` often does not.

## GitHub Pages notes

- `vite.config.js` sets `base: './'` so all built asset paths are relative and work from a
  project sub-path like `https://user.github.io/repo/`.
- Everything the deployed site needs (events JSON, CSS, JS) is part of the build. No
  backend, no localhost, no CDN.

## Where to tune things

`src/config.js` is the single source of truth: video path, fallback duration, the location
string, the static reroute, the bike-counter window, and the banner duration.

The data is the shared `events.json` contract (Spec 4 in `docs/KIRO_PROMPTS.md`): a list of
`possible` / `blocked` / `cleared` events and bike/pedestrian `crossings`, all in seconds from
the start of the clip. The 10 s / 30 s thresholds are applied upstream by LaneMonitor, not
here, so the demo always agrees with the batch analysis. A file in any other format is
ignored and the app falls back to `sample_events.json`.

Status logic lives in `src/lib/status.js` as a pure function `statusAt(t, events)` (the latest
event at or before `t`), so seeking, restarting, and changing speed always recompute cleanly
with no drift.

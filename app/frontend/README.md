# Front end: replay demo and rider web app

React + Vite with plain CSS. It runs entirely from static files, with no backend, so it can
be hosted on GitHub Pages.

- `index.html` → `src/App.jsx`: the **replay demo**. The recorded clip plays next to a phone
  mock-up; status and alerts play back in sync, with play/pause, 1x/2x/4x and a seekable timeline.
- `rider.html` → `src/RiderApp.jsx`: the **rider web app**, full-screen on a phone. Its data
  comes from `src/hooks/useDemoFeed.js`, which replays the recorded events on a loop. A live
  feed can replace that hook later without changing the screens.

Both pages show the same rider screen (`src/components/RiderScreen.jsx`).

## Run it

```bash
npm install
npm run dev        # http://localhost:5173 (replay demo), /rider.html (rider web app)
npm run build      # static files in dist/
npm run preview    # serve dist/ to check the build
```

## Data

`public/data/events.json` follows the shared format (Spec 4 in `docs/KIRO_PROMPTS.md`) and is
written by `src/build_demo.py`. It holds `possible` / `blocked` / `cleared` events and
bike/pedestrian `crossings`, with times in seconds from the start of the clip. The 10 s / 30 s
rules are applied by LaneMonitor in the pipeline, so the app only replays the events. If the
file is missing or in another format, the app uses `sample_events.json` and shows a notice.

`src/lib/status.js` derives everything from the current time (the latest event at or before
it), so seeking, restarting and changing speed always show the right state.

## The video clip

Video files are gitignored. Put the clip at `public/media/demo_clip.mp4`; `.mov` often doesn't
play in Chrome. To make a small browser-friendly copy:

```bash
ffmpeg -i input.mov -vf scale=1280:-2 -c:v libx264 -crf 28 -c:a aac -b:a 96k -movflags +faststart public/media/demo_clip.mp4
```

The clip path is `videoSrc` in `src/config.js`. Without a clip, the demo shows a placeholder and
still plays back, using `videoDurationSeconds`. To publish a clip on GitHub Pages, add it with
`git add -f`.

## GitHub Pages

`vite.config.js` sets `base: './'`, so the built files work from a sub-path like
`https://user.github.io/repo/`. Publish the contents of `dist/`.

## Tuning

`src/config.js` holds the video path, fallback duration, location text, reroute suggestion,
bike-counter window and banner duration.

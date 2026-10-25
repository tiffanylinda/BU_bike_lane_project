// config.js — SINGLE SOURCE OF TRUTH for every tunable number, label and path.
// Change behaviour here, not inside components, so the demo stays easy to retune.
//
// Lane-status thresholds (possible / blocked / clear) are NOT here: they live in
// config/camera.yaml and are applied by LaneMonitor when events.json is built.

export const CONFIG = {
  // Backend API base URL. Reads from the Vite env at build time with a local default.
  // Set VITE_API_BASE="" (empty) to force static-JSON mode — e.g. for GitHub Pages,
  // where there is no backend to reach and we want to serve the bundled JSON instead.
  apiBase: import.meta.env.VITE_API_BASE || 'http://localhost:8000',

  // Relative path (no leading slash) so it resolves the same way locally and on
  // GitHub Pages project sites. The clip may be absent on Pages; the app still runs.
  videoSrc: 'media/demo_clip.mov',

  // Fallback timeline length (seconds) used when the video is missing or its metadata
  // never loads. Keeps the clock, timeline and status logic working with no video.
  videoDurationSeconds: 65,

  // Where this bike lane is, shown on the rider phone (events.json location.name wins).
  location: 'Comm Ave bike lane, Essex St to Kenmore Sq',

  // Short route name shown under the lock-screen widget status.
  routeLabel: 'Comm Ave route',

  // A STATIC, illustrative reroute shown only while the lane is blocked. This is a demo
  // suggestion, not a real routing result.
  reroute: {
    name: 'Detour via Bay State Rd',
    extraMinutes: 3,
    description: 'Illustrative suggestion for this demo scenario.',
  },

  // Bike counter on the phone: bikes that crossed the counting line in this window.
  bikesWindowSeconds: 600,
  bikesWindowLabel: 'bikes in the last 10 minutes',

  // How long the slide-down notification stays visible (ms of real time).
  notificationMs: 4000,
}

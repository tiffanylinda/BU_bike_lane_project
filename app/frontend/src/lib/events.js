// events.js — load the replay events, with a sample-data fallback.
//
// The file format is the shared events.json contract (Spec 4 in docs/KIRO_PROMPTS.md),
// written by src/build_demo.py from LaneMonitor output:
//   { location, clip_start_time, video,
//     events:    [{ t, type: 'possible'|'blocked'|'cleared', vehicle, stopped_for_s, duration_s?, event_id }],
//     crossings: [{ t, mode: 'bike'|'pedestrian'|'skateboard'|'possible_scooter' }],
//     summary:   { blockages, minutes_blocked, bikes } }
// All t values are seconds from the start of the clip.
//
// WHY the fallback: on GitHub Pages (or any static host) we want the demo to work even if
// the real data/events.json is missing. If the primary fetch fails, we load
// data/sample_events.json instead and flag usedSample so the UI can warn the viewer.

// Fetch a JSON file relative to the app base. We use a relative path (no leading slash)
// so it resolves under the GitHub Pages sub-path and locally alike.
async function fetchJson(path) {
  const res = await fetch(path)
  if (!res.ok) {
    throw new Error(`Failed to load ${path}: ${res.status}`)
  }
  return res.json()
}

// Check the file follows the contract and sort by time, so status lookups can assume
// order. An old-format file (a bare array) is rejected rather than half-rendered.
function normalize(data) {
  if (!data || !Array.isArray(data.events)) {
    throw new Error('events.json is not in the Spec 4 format (missing "events" array)')
  }
  const byTime = (a, b) => a.t - b.t
  return {
    ...data,
    events: [...data.events].sort(byTime),
    crossings: [...(data.crossings || [])].sort(byTime),
  }
}

const EMPTY = { events: [], crossings: [] }

/**
 * loadEvents — try the real events first, fall back to the sample set.
 * @returns {Promise<{ data: object, usedSample: boolean }>}
 */
export async function loadEvents() {
  try {
    const data = normalize(await fetchJson('data/events.json'))
    return { data, usedSample: false }
  } catch (primaryError) {
    // Primary file missing or unreadable — try the sample set so the demo still runs.
    console.warn('events.json unavailable, falling back to sample_events.json', primaryError)
    try {
      const data = normalize(await fetchJson('data/sample_events.json'))
      return { data, usedSample: true }
    } catch (sampleError) {
      // Both failed. Return an empty set so the app renders a working (if empty) demo
      // instead of crashing.
      console.error('sample_events.json also unavailable', sampleError)
      return { data: EMPTY, usedSample: true }
    }
  }
}

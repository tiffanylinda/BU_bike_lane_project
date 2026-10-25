// status.js — PURE status logic for the rider phone.
//
// WHY pure: every function here depends ONLY on its arguments. It reads no clock and holds
// no state. That means seeking, restarting, or changing playback speed all recompute the
// exact same answer for a given time with zero drift — the UI just asks "what is the
// status at second t?" and trusts the result.
//
// The thresholds (10 s possible, 30 s blocked, clear debounce) are NOT applied here: they
// already ran inside LaneMonitor when events.json was built. The front end only replays
// the events, so the demo always agrees with the batch analysis.

// The latest event at or before t (events are sorted by t), or null before the first one.
export function latestEventAt(t, events) {
  let latest = null
  for (const event of events) {
    if (event.t > t) break
    latest = event
  }
  return latest
}

/**
 * statusAt — compute the lane status at a point in time.
 *
 * @param {number} t       seconds into the clip
 * @param {Array}  events  sorted [{ t, type, vehicle, ... }]
 * @returns {{ level:'clear'|'possible'|'blocked', vehicle:?string, event:?object, blockedForSeconds:number }}
 */
export function statusAt(t, events) {
  const event = latestEventAt(t, events)

  if (event && event.type === 'blocked') {
    // Red: blocked. blockedForSeconds counts live from the moment the lane turned red.
    return { level: 'blocked', vehicle: event.vehicle, event, blockedForSeconds: t - event.t }
  }
  if (event && event.type === 'possible') {
    return { level: 'possible', vehicle: event.vehicle, event, blockedForSeconds: 0 }
  }
  // No event yet, or the latest one is "cleared".
  return { level: 'clear', vehicle: null, event, blockedForSeconds: 0 }
}

/**
 * alertsUpTo — every event that has happened by time t, newest first. The list grows
 * while playing and shrinks correctly when you seek backward.
 */
export function alertsUpTo(t, events) {
  return events.filter((e) => e.t <= t).reverse()
}

/**
 * bikesInWindow — bikes that crossed the counting line in the last windowSeconds.
 */
export function bikesInWindow(t, crossings, windowSeconds) {
  return crossings.filter((c) => c.mode === 'bike' && c.t <= t && c.t > t - windowSeconds).length
}

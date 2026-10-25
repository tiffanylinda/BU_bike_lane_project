// format.js — tiny shared formatting helpers used across components.

// Format seconds as m:ss (e.g. 65 -> "1:05"). Used for clock readouts and alert times.
export function mmss(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds))
  const minutes = Math.floor(s / 60)
  const seconds = s % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

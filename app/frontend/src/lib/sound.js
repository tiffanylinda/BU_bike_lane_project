// sound.js — short alert chimes, generated with the Web Audio API.
//
// WHY generated instead of an audio file: nothing to download, so it works offline and on
// GitHub Pages. Browsers only allow audio after a user gesture, so unlockAudio() is called
// from the Play / Restart button clicks.

let ctx = null

export function unlockAudio() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  if (!AudioCtx) return
  if (!ctx) ctx = new AudioCtx()
  if (ctx.state === 'suspended') ctx.resume()
}

// Play one short sine tone starting `delay` seconds from now.
function tone(freq, delay, length = 0.18) {
  const start = ctx.currentTime + delay
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.frequency.value = freq
  // Quick fade in/out so the tone doesn't click.
  gain.gain.setValueAtTime(0, start)
  gain.gain.linearRampToValueAtTime(0.25, start + 0.02)
  gain.gain.exponentialRampToValueAtTime(0.001, start + length)
  osc.connect(gain).connect(ctx.destination)
  osc.start(start)
  osc.stop(start + length)
}

// Falling two-note chime for "blocked", rising for "cleared".
export function playChime(type) {
  if (!ctx || ctx.state !== 'running') return
  if (type === 'blocked') {
    tone(880, 0)
    tone(660, 0.2)
  } else {
    tone(660, 0)
    tone(880, 0.2)
  }
}

// Timeline — a scrubbable bar with a colored tick at each event (amber = possible,
// red = blocked, green = cleared).
//
// Click or drag anywhere on the bar to seek. We capture the pointer on press so dragging
// keeps working even when the cursor leaves the bar.
export default function Timeline({ currentTime, duration, events, onSeek }) {
  // Convert a pointer x-position into a time and seek there.
  const seekTo = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const fraction = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    onSeek(fraction * duration)
  }

  const handlePointerDown = (e) => {
    e.currentTarget.setPointerCapture(e.pointerId)
    seekTo(e)
  }

  const handlePointerMove = (e) => {
    if (e.currentTarget.hasPointerCapture(e.pointerId)) seekTo(e)
  }

  // Arrow keys step 5 s, so the bar is usable from the keyboard too.
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowLeft') onSeek(currentTime - 5)
    if (e.key === 'ArrowRight') onSeek(currentTime + 5)
  }

  const pct = (seconds) => `${Math.min(100, (seconds / duration) * 100)}%`

  return (
    <div
      className="timeline"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onKeyDown={handleKeyDown}
      role="slider"
      aria-label="Seek replay"
      aria-valuemin={0}
      aria-valuemax={Math.round(duration)}
      aria-valuenow={Math.round(currentTime)}
      tabIndex={0}
    >
      <div className="timeline__progress" style={{ width: pct(currentTime) }} />
      {events.map((ev) => (
        <div
          key={`${ev.event_id}-${ev.type}-${ev.t}`}
          className={`timeline__tick timeline__tick--${ev.type}`}
          style={{ left: pct(ev.t) }}
          title={`${ev.type}: ${ev.vehicle}`}
        />
      ))}
      <div className="timeline__playhead" style={{ left: pct(currentTime) }} />
    </div>
  )
}

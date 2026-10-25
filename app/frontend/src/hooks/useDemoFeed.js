import { useEffect, useState } from 'react'

// useDemoFeed — a stand-in for a live camera feed, for the rider web app prototype.
//
// It replays the recorded events.json on a loop in real time: "now" in the feed is the
// number of seconds since the page opened, wrapped around the length of the recording.
// The rider app only ever asks "what is the time in the feed?", so a real live feed can
// replace this later (e.g. polling the backend, or Server-Sent Events from the live
// pipeline) without touching the screen components.
//
// loopSeconds: how long one pass of the recording is before it starts again.
export function useDemoFeed(loopSeconds) {
  const [t, setT] = useState(0)

  useEffect(() => {
    const startedAt = performance.now()
    // 4 updates a second is plenty for a status screen (and cheap on a phone battery).
    const id = setInterval(() => {
      const elapsed = (performance.now() - startedAt) / 1000
      setT(loopSeconds > 0 ? elapsed % loopSeconds : elapsed)
    }, 250)
    return () => clearInterval(id)
  }, [loopSeconds])

  return t
}

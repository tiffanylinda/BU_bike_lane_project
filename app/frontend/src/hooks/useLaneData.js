import { useEffect, useMemo, useRef, useState } from 'react'
import { CONFIG } from '../config.js'
import { loadEvents } from '../lib/events.js'
import { statusAt, alertsUpTo, bikesInWindow } from '../lib/status.js'
import { playChime } from '../lib/sound.js'

// A banner/chime fires only when time runs naturally past an event. If the event is
// further behind than this (we seeked past it), we stay quiet instead of replaying it.
const FRESH_EVENT_SECONDS = 1

// useEventsFile — load events.json once (falling back to sample_events.json).
export function useEventsFile() {
  const [state, setState] = useState({
    data: { events: [], crossings: [] },
    usedSample: false,
    loaded: false,
  })

  useEffect(() => {
    let cancelled = false
    loadEvents().then(({ data, usedSample }) => {
      if (!cancelled) setState({ data, usedSample, loaded: true })
    })
    return () => {
      cancelled = true
    }
  }, [])

  return state
}

// useLaneState — everything the rider screen shows at second t, derived purely from t.
export function useLaneState(t, data) {
  const { events, crossings } = data
  const status = useMemo(() => statusAt(t, events), [t, events])
  const alerts = useMemo(() => alertsUpTo(t, events), [t, events])
  const bikes = useMemo(
    () => bikesInWindow(t, crossings, CONFIG.bikesWindowSeconds),
    [t, crossings],
  )
  return { status, alerts, bikes, location: data.location?.name || CONFIG.location }
}

// useLaneNotification — the slide-down banner + chime on each "blocked" and "cleared"
// event. Returns the banner state for <NotificationBanner />.
export function useLaneNotification(status, t, soundOn) {
  const [notification, setNotification] = useState({ visible: false, type: 'cleared', message: '' })
  const prevEventRef = useRef(null)
  const hideTimerRef = useRef(null)

  useEffect(() => {
    const event = status.event
    if (event === prevEventRef.current) return
    prevEventRef.current = event

    const fresh = event && t - event.t < FRESH_EVENT_SECONDS
    if (!fresh || (event.type !== 'blocked' && event.type !== 'cleared')) return

    const message =
      event.type === 'blocked' ? `Bike lane blocked - ${event.vehicle}` : 'Bike lane clear'
    setNotification({ visible: true, type: event.type, message })
    if (soundOn) playChime(event.type)

    // Auto-hide after a few seconds. Reset any pending timer first.
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current)
    hideTimerRef.current = setTimeout(() => {
      setNotification((n) => ({ ...n, visible: false }))
    }, CONFIG.notificationMs)
  }, [status.event, t, soundOn])

  // Clean up the timer on unmount.
  useEffect(() => () => hideTimerRef.current && clearTimeout(hideTimerRef.current), [])

  return notification
}

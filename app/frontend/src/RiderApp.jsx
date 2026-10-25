import { useState } from 'react'
import { CONFIG } from './config.js'
import { unlockAudio } from './lib/sound.js'
import { useDemoFeed } from './hooks/useDemoFeed.js'
import { useEventsFile, useLaneState, useLaneNotification } from './hooks/useLaneData.js'
import RiderScreen from './components/RiderScreen.jsx'
import NotificationBanner from './components/NotificationBanner.jsx'

// How long the demo feed waits after the last recorded event before looping back to the
// start, so the final "cleared" state is visible for a moment.
const LOOP_TAIL_SECONDS = 10

// RiderApp — the standalone, mobile-first RIDER WEB APP (no video). This is the prototype
// of the future mobile app: it opens straight to the lane status, full-screen on a phone.
// For now its data comes from the demo feed (the recorded events replayed on a loop).
export default function RiderApp() {
  const { data, usedSample, loaded } = useEventsFile()

  const lastEventT = Math.max(0, ...data.events.map((e) => e.t), ...data.crossings.map((c) => c.t))
  const loopSeconds = loaded ? Math.max(CONFIG.videoDurationSeconds, lastEventT + LOOP_TAIL_SECONDS) : 0
  const t = useDemoFeed(loopSeconds)

  const { status, alerts, bikes, location } = useLaneState(t, data)

  // Alerts start OFF: browsers only allow sound after a tap, so the rider turns them on.
  const [alertsOn, setAlertsOn] = useState(false)
  const notification = useLaneNotification(status, t, alertsOn)

  const toggleAlerts = () => {
    unlockAudio()
    setAlertsOn((on) => !on)
  }

  if (!loaded) return <div className="rider-app loading">Loading…</div>

  return (
    <div className="rider-app">
      <NotificationBanner
        visible={notification.visible}
        type={notification.type}
        message={notification.message}
      />

      <header className="rider-app__bar">
        <span className="rider-app__name">Comm Ave Lane Watch</span>
        <button className="btn rider-app__alerts" onClick={toggleAlerts} aria-pressed={alertsOn}>
          {alertsOn ? '🔔 Alerts on' : '🔕 Alerts off'}
        </button>
      </header>

      <div className="rider-app__feed">
        <span className={`dot dot--${status.level}`} />
        Demo feed: replaying recorded events{usedSample ? ' (sample data)' : ''}
      </div>

      <RiderScreen location={location} status={status} alerts={alerts} bikes={bikes} />

      <footer className="rider-app__footer">
        <a href="./">Open the replay demo (with video)</a>
      </footer>
    </div>
  )
}

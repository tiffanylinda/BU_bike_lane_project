import { useMemo, useState } from 'react'
import { CONFIG } from './config.js'
import { unlockAudio } from './lib/sound.js'
import { useReplayClock } from './hooks/useReplayClock.js'
import { useEventsFile, useLaneState, useLaneNotification } from './hooks/useLaneData.js'
import Header from './components/Header.jsx'
import VideoPanel from './components/VideoPanel.jsx'
import PhoneMock from './components/PhoneMock.jsx'
import LockScreenWidget from './components/LockScreenWidget.jsx'

// App — the REPLAY DEMO: the recorded clip next to the rider phone, played back in sync.
// (The standalone rider web app is RiderApp.jsx, served from rider.html.)
export default function App() {
  const { data, usedSample, loaded } = useEventsFile()

  // --- Duration: prefer the real video's metadata, fall back to the configured value. ---
  const [duration, setDuration] = useState(CONFIG.videoDurationSeconds)

  // --- The replay clock drives everything. ---
  const { currentTime, playing, speed, controls } = useReplayClock(duration)

  // --- Status, alerts and bike count, derived purely from the current time. ---
  const { status, alerts, bikes, location } = useLaneState(currentTime, data)

  // --- Sound toggle: controls the alert chimes and the clip's own audio. ---
  const [soundOn, setSoundOn] = useState(true)
  const notification = useLaneNotification(status, currentTime, soundOn)

  // Browsers only allow audio after a click, so unlock it from the Play/Restart buttons.
  const replayControls = useMemo(
    () => ({
      ...controls,
      toggle: () => {
        unlockAudio()
        controls.toggle()
      },
      restart: () => {
        unlockAudio()
        controls.restart()
      },
    }),
    [controls],
  )

  return (
    <div className="app">
      <Header />

      {loaded ? (
        <main className="layout">
          <VideoPanel
            currentTime={currentTime}
            playing={playing}
            speed={speed}
            controls={replayControls}
            duration={duration}
            events={data.events}
            soundOn={soundOn}
            onToggleSound={() => setSoundOn((s) => !s)}
            usedSample={usedSample}
            onVideoDuration={setDuration}
          />
          <PhoneMock
            location={location}
            status={status}
            alerts={alerts}
            bikes={bikes}
            notification={notification}
          />
          <LockScreenWidget status={status} />
        </main>
      ) : (
        <div className="loading">Loading replay…</div>
      )}
    </div>
  )
}

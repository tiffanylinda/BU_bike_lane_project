import RiderScreen from './RiderScreen.jsx'
import NotificationBanner from './NotificationBanner.jsx'

// PhoneMock — the phone-sized card (middle column of the replay demo) that shows the
// rider screen inside a fixed-height phone frame with a notch.
export default function PhoneMock({ location, status, alerts, bikes, notification }) {
  return (
    <div className="phone">
      <div className="phone__frame">
        <div className="phone__notch" />

        {/* Slides down over the top of the screen, like an iOS notification. */}
        <NotificationBanner
          visible={notification.visible}
          type={notification.type}
          message={notification.message}
        />

        <RiderScreen location={location} status={status} alerts={alerts} bikes={bikes} />
      </div>
    </div>
  )
}

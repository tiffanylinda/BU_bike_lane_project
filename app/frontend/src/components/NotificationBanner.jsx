// NotificationBanner — a toast that slides DOWN from the top of the phone on each
// "blocked" and "cleared" event, then auto-hides (App owns the timer).
//
// It floats over the notch and heading instead of pushing the layout down, so the status
// card never jumps around while the audience is watching. The background is solid, so the
// text underneath never shows through.
export default function NotificationBanner({ visible, type, message }) {
  return (
    <div
      className={`notification-banner notification-banner--${type} ${
        visible ? 'notification-banner--visible' : ''
      }`}
      role="alert"
      aria-hidden={!visible}
    >
      {message}
    </div>
  )
}

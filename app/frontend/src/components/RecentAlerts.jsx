import { mmss } from '../lib/format.js'

// The status-dot color for each event type ("cleared" shows green like "clear").
const DOT = { possible: 'possible', blocked: 'blocked', cleared: 'clear' }

function alertText(event) {
  if (event.type === 'blocked') return `Blocked by ${event.vehicle}`
  if (event.type === 'possible') return `${event.vehicle} stopping`
  return `Lane cleared (${event.vehicle} gone)`
}

// RecentAlerts — every event that has happened up to the current time, newest first.
// The list is derived by alertsUpTo() (pure), so it grows while playing and shrinks when
// you seek backward. It fills the spare phone height and scrolls if it overflows.
export default function RecentAlerts({ alerts }) {
  return (
    <div className="recent-alerts">
      <div className="section-heading">Recent alerts</div>
      {alerts.length === 0 ? (
        <div className="recent-alerts__empty">No alerts yet.</div>
      ) : (
        <ul className="recent-alerts__list">
          {alerts.map((a) => (
            <li key={`${a.event_id}-${a.type}-${a.t}`} className="recent-alerts__item">
              <span className={`dot dot--${DOT[a.type]}`} />
              <span className="recent-alerts__msg">{alertText(a)}</span>
              <span className="recent-alerts__time">{mmss(a.t)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

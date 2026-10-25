import { CONFIG } from '../config.js'

const TITLES = {
  clear: 'Bike lane clear',
  possible: 'Vehicle stopping',
  blocked: 'Bike lane blocked',
}

// LockScreenWidget — far-right column. A preview of the small lock-screen widget that
// mirrors the current status at a glance (color dot + short text), so the audience sees
// how a rider would get the alert without opening the app.
export default function LockScreenWidget({ status }) {
  return (
    <aside className="lockscreen">
      <div className="section-heading">Lock-screen widget preview</div>
      <div className="lockscreen__widget">
        <span className={`dot dot--lg dot--${status.level}`} />
        <div>
          <div className="lockscreen__title">{TITLES[status.level]}</div>
          <div className="lockscreen__sub">{CONFIG.routeLabel}</div>
        </div>
      </div>
    </aside>
  )
}

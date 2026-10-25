import { CONFIG } from '../config.js'

// BikeCounter — "N bikes in the last 10 minutes", counted from the crossings in
// events.json (App computes it with bikesInWindow, so seeking shows a consistent number).
export default function BikeCounter({ count }) {
  return (
    <div className="bike-counter">
      <span className="bike-counter__num">{count}</span>
      <span className="bike-counter__label">{CONFIG.bikesWindowLabel}</span>
    </div>
  )
}

// CrashHistory — bike crash records near this stretch of Comm Ave, for context on the
// phone. Static placeholder rows for now; swap in records from data/public/vision_zero.csv
// once the team has pulled them.
const ROWS = [{ date: '2019-10-11', location: 'Massachusetts Ave & Commonwealth Ave' }]

export default function CrashHistory() {
  return (
    <div className="crash-history">
      <div className="section-heading">Bike crash history (Comm Ave)</div>
      <ul className="crash-history__list">
        {ROWS.map((r) => (
          <li key={`${r.date}-${r.location}`} className="crash-history__row">
            {r.date} · {r.location}
          </li>
        ))}
      </ul>
    </div>
  )
}

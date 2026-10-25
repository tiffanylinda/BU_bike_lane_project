import StatusCard from './StatusCard.jsx'
import RerouteCard from './RerouteCard.jsx'
import RecentAlerts from './RecentAlerts.jsx'
import BikeCounter from './BikeCounter.jsx'
import CrashHistory from './CrashHistory.jsx'

// RiderScreen — the rider app's main screen. The replay demo shows it inside a phone
// frame (PhoneMock); the rider web app (RiderApp) shows it full-screen. Same component,
// so both always look and behave the same.
export default function RiderScreen({ location, status, alerts, bikes }) {
  return (
    <div className="rider-screen">
      <div className="rider-screen__heading">Bike lane status</div>
      <div className="rider-screen__location">{location}</div>

      <StatusCard status={status} />

      {/* Reroute only appears while blocked — exactly when a rider needs it. */}
      {status.level === 'blocked' && <RerouteCard />}

      <RecentAlerts alerts={alerts} />
      <BikeCounter count={bikes} />
      <CrashHistory />
    </div>
  )
}

// SampleDataWarning — shown only when the real events.json was missing and we fell back
// to sample_events.json, so viewers know the data on screen is illustrative.
export default function SampleDataWarning() {
  return (
    <div className="sample-warning" role="status">
      ⚠ Showing SAMPLE data (data/sample_events.json). Real events will load automatically once
      data/events.json exists.
    </div>
  )
}

const LABELS = ['Plan', 'Details', 'Review', 'Processing', 'Done']

export default function Stepper({ stage }) {
  return (
    <div className="stepper" role="progressbar" aria-valuenow={stage} aria-valuemin={1} aria-valuemax={5}>
      {LABELS.map((label, i) => {
        const n = i + 1
        const cls = n < stage ? 'done' : n === stage ? 'active' : 'pending'
        return (
          <div className="stepper-seg" key={label}>
            <div className={`dot ${cls}`}>
              {n < stage ? <Check /> : n}
            </div>
            {n < 5 && <div className={`line ${n < stage ? 'done' : ''}`} />}
          </div>
        )
      })}
    </div>
  )
}

function Check() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}

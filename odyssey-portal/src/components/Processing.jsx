const ORDER_STATES = ['acknowledged', 'inProgress', 'completed']
const STATE_LABELS = { acknowledged: 'Acknowledged', inProgress: 'In progress', completed: 'Completed' }

export default function Processing({ steps, stepIndex, orderState, error, onRetry, onBack }) {
  if (error) {
    return (
      <section className="section">
        <div className="section-label">Something went wrong</div>
        <div className="notice error">
          {error.message}
          {error.status ? ` (status ${error.status})` : ''}
        </div>
        <button className="btn" onClick={onRetry}>Try again</button>
        <button className="btn-ghost" onClick={onBack}>Back to review</button>
      </section>
    )
  }

  const stateIdx = orderState ? ORDER_STATES.indexOf(orderState) : -1
  const allStepsDone = stepIndex >= steps.length

  return (
    <section className="section">
      <div className="section-label">Setting up your account</div>

      <div className="proc-steps">
        {steps.map((s, i) => {
          const cls = i < stepIndex ? 'done' : i === stepIndex ? 'active' : 'pending'
          return (
            <div className={`proc-step ${cls}`} key={s.key}>
              <span className="proc-icon">
                {i < stepIndex ? <Check /> : i === stepIndex ? <Spinner /> : <Dot />}
              </span>
              <div>
                <div className="proc-label">{s.label}</div>
                <div className="proc-sub">{s.sub}</div>
              </div>
            </div>
          )
        })}
      </div>

      {allStepsDone && (
        <div className="tracker">
          <div className="review-title">Order status</div>
          <div className="tracker-states">
            {ORDER_STATES.map((st, i) => (
              <div className="tracker-node-wrap" key={st}>
                <div className="tracker-node">
                  <div className={`tracker-circle ${i < stateIdx ? 'done' : i === stateIdx ? 'active' : 'pending'}`}>
                    {i < stateIdx ? <Check /> : i === stateIdx ? <Spinner /> : <Dot />}
                  </div>
                  <div className="tracker-label">{STATE_LABELS[st]}</div>
                </div>
                {i < 2 && <div className={`tracker-conn ${i < stateIdx ? 'filled' : ''}`} />}
              </div>
            ))}
          </div>
          <div className="tracker-note">
            {orderState === 'completed'
              ? 'Order complete — preparing your SIM for dispatch…'
              : 'Processing your order — this usually takes a few seconds.'}
          </div>
        </div>
      )}
    </section>
  )
}

function Check() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}
function Spinner() {
  return (
    <svg className="spin" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  )
}
function Dot() {
  return (
    <svg width="8" height="8" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <circle cx="12" cy="12" r="6" />
    </svg>
  )
}

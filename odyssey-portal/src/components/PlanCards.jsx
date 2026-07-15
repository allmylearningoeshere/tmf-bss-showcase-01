export default function PlanCards({ plans, loading, error, selectedId, onSelect, onContinue }) {
  if (loading) {
    return (
      <section className="section">
        <div className="section-label">Choose your SIM-only plan</div>
        <div className="plan-grid">
          {[0, 1, 2].map((i) => <div className="plan-card skeleton" key={i} />)}
        </div>
        <p className="hint">Loading plans from the catalogue…</p>
      </section>
    )
  }

  if (error) {
    return (
      <section className="section">
        <div className="section-label">Choose your SIM-only plan</div>
        <div className="notice error">
          Couldn't load plans from the catalogue. The backend may be waking up —
          this can take up to a minute on the free tier. Try again shortly.
        </div>
        <button className="btn" onClick={() => window.location.reload()}>Retry</button>
      </section>
    )
  }

  if (!plans.length) {
    return (
      <section className="section">
        <div className="section-label">Choose your SIM-only plan</div>
        <div className="notice">No plans available right now. Check back soon.</div>
      </section>
    )
  }

  return (
    <section className="section">
      <div className="section-label">Choose your SIM-only plan</div>
      <div className="plan-grid">
        {plans.map((p) => (
          <div
            key={p.id}
            className={`plan-card${selectedId === p.id ? ' selected' : ''}`}
            role="radio"
            aria-checked={selectedId === p.id}
            tabIndex={0}
            onClick={() => onSelect(p.id)}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelect(p.id)}
          >
            {p.badge && <div className="plan-badge">{p.badge}</div>}
            <div className="plan-name">{p.name}</div>
            <div className="plan-price">{p.priceLabel}<span>/mo</span></div>
            <ul className="plan-feats">
              {p.features.map((f, i) => (
                <li key={i}><Tick /> {f}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <button className="btn" disabled={!selectedId} onClick={onContinue}>
        Continue
      </button>
    </section>
  )
}

function Tick() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}

export default function Confirmation({ plan, form, shipping, orderId, piRef, onRestart }) {
  return (
    <>
      <div className="success">
        <div className="success-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
        <div className="success-title">You're all set, {form.firstName}!</div>
        <div className="success-sub">
          Your {plan?.name} SIM is confirmed.{' '}
          {shipping.id === 'exp' ? 'Expected tomorrow.' : 'Expected in 3–5 working days.'}
        </div>
      </div>

      <InfoCard label="Order reference" value={orderId || '—'} mono />
      <InfoCard label="Product inventory reference" value={piRef || 'Provisioning…'} mono />
      <InfoCard label="Delivering to" value={`${form.address} ${form.houseNumber}, ${form.city}, ${form.postcode}, Germany`} />
      <InfoCard label="Plan" value={`${plan?.name} · ${plan?.priceLabel}/mo`} />

      <button className="btn" onClick={onRestart}>Place another order</button>
    </>
  )
}

function InfoCard({ label, value, mono }) {
  return (
    <div className="info-card">
      <div className="info-label">{label}</div>
      <div className={`info-value${mono ? ' mono' : ''}`}>{value}</div>
    </div>
  )
}

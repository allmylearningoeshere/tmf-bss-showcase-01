export default function ReviewOrder({ plan, form, shipping, onBack, onPlace }) {
  const total = shipping.cost > 0 ? `€${shipping.cost.toFixed(2)}` : '€0.00'

  return (
    <>
      <section className="section">
        <div className="section-label">Review your order</div>

        <div className="review-card">
          <div className="review-title">Plan</div>
          <Row label="Plan" value={plan?.name} />
          <Row label="Calls & texts" value="Unlimited" />
          <Row label="Contract" value="30-day rolling" />
          <Row label="Monthly charge" value={`${plan?.priceLabel}/mo`} accent />
        </div>

        <div className="review-card">
          <div className="review-title">Delivery</div>
          <Row label="Method" value={shipping.name} />
          <Row label="Estimated arrival" value={shipping.desc} />
          <Row label="Address" value={`${form.address}, ${form.city}, ${form.postcode}`} />
          <Row label="Country" value="Germany" />
          <Row label="Delivery cost" value={shipping.price} />
        </div>

        <div className="review-card">
          <div className="review-title">Summary</div>
          <Row label="First month" value={plan?.priceLabel} />
          <Row label="Delivery" value={shipping.price} />
          <div className="review-total">
            <span>Total today</span>
            <span className="review-total-value">{total}</span>
          </div>
        </div>
      </section>

      <button className="btn" onClick={onPlace}>Place order</button>
      <button className="btn-ghost" onClick={onBack}>Back</button>
    </>
  )
}

function Row({ label, value, accent }) {
  return (
    <div className="review-row">
      <span className="review-row-label">{label}</span>
      <span className={`review-row-value${accent ? ' accent' : ''}`}>{value}</span>
    </div>
  )
}

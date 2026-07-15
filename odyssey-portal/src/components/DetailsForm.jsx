export default function DetailsForm({
  plan, form, setForm, shipping, setShipping, shippingOptions, onBack, onContinue,
}) {
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const valid =
    form.firstName && form.lastName && form.email &&
    form.phone && form.address && form.city && form.postcode

  return (
    <>
      <div className="collapsed">
        <span className="collapsed-label">Plan</span>
        <span className="collapsed-value">{plan?.name} · {plan?.priceLabel}/mo</span>
      </div>

      <section className="section">
        <div className="section-label">Your details</div>
        <div className="form-row">
          <Field label="First name" value={form.firstName} onChange={set('firstName')} placeholder="Jana" />
          <Field label="Last name" value={form.lastName} onChange={set('lastName')} placeholder="Schmidt" />
        </div>
        <Field full label="Email address" type="email" value={form.email} onChange={set('email')} placeholder="jana@email.de" />
        <div className="form-group">
          <label>Mobile number</label>
          <div className="phone-wrap">
            <span className="phone-prefix">+49</span>
            <input
              type="tel"
              value={form.phone}
              onChange={set('phone')}
              placeholder="151 23456789"
            />
          </div>
        </div>
      </section>

      <div className="divider" />

      <section className="section">
        <div className="section-label">Delivery address</div>
        <Field full label="Street address" value={form.address} onChange={set('address')} placeholder="Musterstraße 12" />
        <div className="form-row">
          <Field label="City" value={form.city} onChange={set('city')} placeholder="Berlin" />
          <Field label="Postcode" value={form.postcode} onChange={set('postcode')} placeholder="10115" />
        </div>
        <div className="form-group">
          <label>Country</label>
          <input type="text" value="Germany" disabled readOnly aria-readonly="true" />
        </div>
      </section>

      <div className="divider" />

      <section className="section">
        <div className="section-label">Delivery method</div>
        <div className="ship-grid">
          {shippingOptions.map((s) => (
            <div
              key={s.id}
              className={`ship-card${shipping === s.id ? ' selected' : ''}`}
              role="radio"
              aria-checked={shipping === s.id}
              tabIndex={0}
              onClick={() => setShipping(s.id)}
              onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setShipping(s.id)}
            >
              <div className="ship-head">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d={s.icon} />
                </svg>
                <span className="ship-name">{s.name}</span>
              </div>
              <div className="ship-desc">{s.desc}</div>
              <div className="ship-price">{s.price}</div>
            </div>
          ))}
        </div>
      </section>

      <button className="btn" disabled={!valid} onClick={onContinue}>Review order</button>
      <button className="btn-ghost" onClick={onBack}>Back</button>
    </>
  )
}

function Field({ label, value, onChange, placeholder, type = 'text', full }) {
  return (
    <div className={`form-group${full ? ' full' : ''}`}>
      <label>{label}</label>
      <input type={type} value={value} onChange={onChange} placeholder={placeholder} />
    </div>
  )
}

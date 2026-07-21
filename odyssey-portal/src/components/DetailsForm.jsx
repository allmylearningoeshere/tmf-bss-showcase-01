import { useState } from 'react'
import { validateField } from '../lib/validation.js'
import AddressLookupModal from './AddressLookupModal.jsx'

export default function DetailsForm({
  plan, form, setForm, shipping, setShipping, shippingOptions, onBack, onContinue,
}) {
  // Track live validation errors per field.
  const [errors, setErrors] = useState({})
  const [lookupOpen, setLookupOpen] = useState(false)

  const set = (k) => (e) => {
    const value = e.target.value
    setForm({ ...form, [k]: value })
    // Live validation — recompute this field's error on every keystroke.
    setErrors((prev) => ({ ...prev, [k]: validateField(k, value) }))
  }

  const fields = ['firstName', 'lastName', 'email', 'phone', 'address', 'city', 'postcode']
  const allFilled = fields.every((f) => (form[f] ?? '').trim() !== '')
  const noErrors = fields.every((f) => !validateField(f, form[f]))
  const valid = allFilled && noErrors

  function handleLookup() {
    setLookupOpen(true)
  }

  // Fill street, city and postcode from a chosen lookup result, clearing
  // any stale validation errors on those fields.
  function applyLookup({ street, city, postcode }) {
    const next = { ...form, address: street, city, postcode }
    setForm(next)
    setErrors((prev) => ({
      ...prev,
      address: validateField('address', street),
      city: validateField('city', city),
      postcode: validateField('postcode', postcode),
    }))
  }

  return (
    <>
      <div className="collapsed">
        <span className="collapsed-label">Plan</span>
        <span className="collapsed-value">{plan?.name} · {plan?.priceLabel}/mo</span>
      </div>

      <section className="section">
        <div className="section-label">Your details</div>
        <div className="form-row">
          <Field label="First name" value={form.firstName} onChange={set('firstName')} error={errors.firstName} placeholder="Jana" />
          <Field label="Last name" value={form.lastName} onChange={set('lastName')} error={errors.lastName} placeholder="Schmidt" />
        </div>
        <Field full label="Email address" type="email" value={form.email} onChange={set('email')} error={errors.email} placeholder="jana@email.de" />
        <div className="form-group full">
          <label>Mobile number</label>
          <div className={`phone-wrap${errors.phone ? ' invalid' : ''}`}>
            <span className="phone-prefix">+49</span>
            <input type="tel" value={form.phone} onChange={set('phone')} placeholder="151 23456789" aria-invalid={!!errors.phone} />
          </div>
          {errors.phone && <span className="field-error">{errors.phone}</span>}
        </div>
      </section>

      <div className="divider" />

      <section className="section">
        <div className="section-label">Delivery address</div>
        <div className="form-group full">
          <label>Street address</label>
          <div className="lookup-wrap">
            <input
              type="text"
              value={form.address}
              onChange={set('address')}
              placeholder="Musterstraße 12"
              aria-invalid={!!errors.address}
              className={errors.address ? 'invalid' : ''}
            />
            <button type="button" className="lookup-btn" onClick={handleLookup}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              Lookup
            </button>
          </div>
          {errors.address && <span className="field-error">{errors.address}</span>}
        </div>
        <div className="form-row">
          <Field label="City" value={form.city} onChange={set('city')} error={errors.city} placeholder="Berlin" />
          <Field label="Postcode" value={form.postcode} onChange={set('postcode')} error={errors.postcode} placeholder="10115" />
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

      {lookupOpen && (
        <AddressLookupModal
          initialPostcode={form.postcode}
          onSelect={applyLookup}
          onClose={() => setLookupOpen(false)}
        />
      )}
    </>
  )
}

function Field({ label, value, onChange, placeholder, type = 'text', full, error }) {
  return (
    <div className={`form-group${full ? ' full' : ''}`}>
      <label>{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        aria-invalid={!!error}
        className={error ? 'invalid' : ''}
      />
      {error && <span className="field-error">{error}</span>}
    </div>
  )
}

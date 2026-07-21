import { useState, useEffect, useRef } from 'react'
import { lookupStreets } from '../lib/api.js'

// A modal that looks up streets for a German postcode via the backend proxy
// and lets the user pick one. On select, it hands back { street, city, postcode }.
export default function AddressLookupModal({ initialPostcode = '', onSelect, onClose }) {
  const [postcode, setPostcode] = useState(initialPostcode)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Close on Escape.
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const valid = /^\d{5}$/.test(postcode.trim())

  async function runSearch() {
    if (!valid) {
      setError('Enter a 5-digit postcode')
      return
    }
    setError('')
    setLoading(true)
    setResults(null)
    try {
      const data = await lookupStreets(postcode.trim())
      setResults(data.results || [])
    } catch (err) {
      setError(
        err.status === 504 || err.status === 502
          ? 'The address service is unavailable right now. Try again shortly.'
          : 'Could not look up that postcode.'
      )
    } finally {
      setLoading(false)
    }
  }

  function choose(r) {
    onSelect({ street: r.street, city: r.city, postcode: r.postalCode })
    onClose()
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="Address lookup"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-head">
          <div className="modal-title">Find your address</div>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="modal-search">
          <input
            ref={inputRef}
            type="text"
            inputMode="numeric"
            maxLength={5}
            value={postcode}
            onChange={(e) => setPostcode(e.target.value.replace(/\D/g, ''))}
            onKeyDown={(e) => e.key === 'Enter' && runSearch()}
            placeholder="Enter postcode, e.g. 10115"
            aria-label="Postcode"
          />
          <button className="btn modal-search-btn" onClick={runSearch} disabled={!valid || loading}>
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>

        {error && <div className="modal-error">{error}</div>}

        <div className="modal-results">
          {loading && <div className="modal-hint">Looking up streets…</div>}

          {!loading && results && results.length === 0 && (
            <div className="modal-hint">No streets found for that postcode.</div>
          )}

          {!loading && results && results.length > 0 && (
            <ul className="result-list">
              {results.map((r, i) => (
                <li key={`${r.street}-${i}`}>
                  <button className="result-item" onClick={() => choose(r)}>
                    <span className="result-street">{r.street}</span>
                    <span className="result-meta">
                      {r.postalCode} {r.city}{r.borough ? ` · ${r.borough}` : ''}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {!loading && !results && !error && (
            <div className="modal-hint">
              Enter your postcode and we'll list the streets in it.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

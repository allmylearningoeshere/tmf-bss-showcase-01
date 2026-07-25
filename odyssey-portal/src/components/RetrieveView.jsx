import { useState } from 'react'
import { getOrder, getProduct, listInventory } from '../lib/api.js'

// A retrieval surface with two tabs:
//   • Find order   — look up an order by its reference; also surfaces the
//                    product it provisioned (walking the correlation).
//   • Find product — look up a product instance directly by its reference.
export default function RetrieveView({ onBack }) {
  const [tab, setTab] = useState('order')

  return (
    <section className="section">
      <button className="link-back" onClick={onBack}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
        </svg>
        Back to store
      </button>

      <div className="section-label">Track your order</div>

      <div className="tabs" role="tablist">
        <button
          role="tab"
          aria-selected={tab === 'order'}
          className={`tab${tab === 'order' ? ' active' : ''}`}
          onClick={() => setTab('order')}
        >
          Find order
        </button>
        <button
          role="tab"
          aria-selected={tab === 'product'}
          className={`tab${tab === 'product' ? ' active' : ''}`}
          onClick={() => setTab('product')}
        >
          Find product
        </button>
      </div>

      {tab === 'order' ? <FindOrder /> : <FindProduct />}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Find order — by order reference; shows the order and its linked product
// ---------------------------------------------------------------------------

function FindOrder() {
  const [ref, setRef] = useState('')
  const [order, setOrder] = useState(null)
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function search() {
    const id = ref.trim()
    if (!id) return
    setLoading(true); setError(''); setOrder(null); setProduct(null)
    try {
      const found = await getOrder(id)
      setOrder(found)
      // Walk the correlation: find the product this order provisioned.
      try {
        const inventory = await listInventory()
        const match = (inventory || []).find((p) =>
          (p.productOrderItem || []).some((ref) => ref.id === id)
        )
        if (match) setProduct(match)
      } catch {
        // Non-fatal — the order still shows without its product.
      }
    } catch (err) {
      setError(
        err.status === 404
          ? 'No order found with that reference.'
          : 'Could not retrieve that order. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <SearchRow
        value={ref}
        onChange={setRef}
        onSearch={search}
        loading={loading}
        placeholder="Enter your order reference"
      />
      {error && <div className="notice error">{error}</div>}

      {order && (
        <>
          <OrderCard order={order} />
          {product ? (
            <ProductCard product={product} heading="Provisioned product" />
          ) : (
            <div className="info-card">
              <div className="info-label">Product</div>
              <div className="info-value">
                {isComplete(order)
                  ? 'No product linked to this order yet.'
                  : 'Your product will appear here once the order completes.'}
              </div>
            </div>
          )}
        </>
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// Find product — by product reference
// ---------------------------------------------------------------------------

function FindProduct() {
  const [ref, setRef] = useState('')
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function search() {
    const id = ref.trim()
    if (!id) return
    setLoading(true); setError(''); setProduct(null)
    try {
      const found = await getProduct(id)
      setProduct(found)
    } catch (err) {
      setError(
        err.status === 404
          ? 'No product found with that reference.'
          : 'Could not retrieve that product. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <SearchRow
        value={ref}
        onChange={setRef}
        onSearch={search}
        loading={loading}
        placeholder="Enter your product reference"
      />
      {error && <div className="notice error">{error}</div>}
      {product && <ProductCard product={product} heading="Product details" />}
    </>
  )
}

// ---------------------------------------------------------------------------
// Shared pieces
// ---------------------------------------------------------------------------

function SearchRow({ value, onChange, onSearch, loading, placeholder }) {
  return (
    <div className="retrieve-search">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && onSearch()}
        placeholder={placeholder}
        aria-label={placeholder}
      />
      <button className="btn retrieve-btn" onClick={onSearch} disabled={loading || !value.trim()}>
        {loading ? 'Searching…' : 'Search'}
      </button>
    </div>
  )
}

const STATE_LABELS = {
  acknowledged: 'Acknowledged',
  inProgress: 'In progress',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

function isComplete(order) {
  return order.state === 'completed'
}

function OrderCard({ order }) {
  const item = (order.orderItem || [])[0] || {}
  const offering = item.productOffering || {}
  return (
    <div className="review-card">
      <div className="review-title">Order</div>
      <Row label="Reference" value={order.id} mono />
      <Row label="Status" value={<StateBadge state={order.state} />} />
      <Row label="Plan" value={offering.name || '—'} />
      <Row label="Ordered" value={formatDate(order.orderDate)} />
      {order.completionDate && (
        <Row label="Completed" value={formatDate(order.completionDate)} />
      )}
    </div>
  )
}

function ProductCard({ product, heading }) {
  const offering = product.productOffering || {}
  return (
    <div className="review-card">
      <div className="review-title">{heading}</div>
      <Row label="Reference" value={product.id} mono />
      <Row label="Name" value={product.name || '—'} />
      <Row label="Status" value={<StateBadge state={product.status} />} />
      <Row label="Plan" value={offering.name || '—'} />
      {product.startDate && <Row label="Active since" value={formatDate(product.startDate)} />}
    </div>
  )
}

function StateBadge({ state }) {
  const label = STATE_LABELS[state] || state || 'Unknown'
  const cls =
    state === 'completed' || state === 'active' ? 'ok'
    : state === 'cancelled' ? 'cancelled'
    : 'progress'
  return <span className={`badge ${cls}`}>{label}</span>
}

function Row({ label, value, mono }) {
  return (
    <div className="review-row">
      <span className="review-row-label">{label}</span>
      <span className={`review-row-value${mono ? ' mono' : ''}`}>{value}</span>
    </div>
  )
}

function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

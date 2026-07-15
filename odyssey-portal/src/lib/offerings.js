// ---------------------------------------------------------------------------
// Turns raw TMF620 ProductOffering records into the compact view model the
// plan cards render. The backend embeds price detail under `_priceDetail`;
// we pull the recurring monthly charge and a couple of display features.
// ---------------------------------------------------------------------------

const BADGES = { 1: 'Most popular', 2: 'Best value' }

export function toPlanCards(offerings) {
  if (!Array.isArray(offerings)) return []

  // Prefer sellable, non-bundle offerings for a SIM-only storefront.
  const sellable = offerings.filter(
    (o) => o.isSellable !== false && o.isBundle !== true
  )
  const list = sellable.length ? sellable : offerings

  return list.map((o, i) => {
    const price = monthlyPrice(o)
    return {
      id: o.id,
      name: o.name,
      description: o.description || '',
      priceLabel: price ? formatEuro(price) : '—',
      priceValue: price,
      features: deriveFeatures(o),
      badge: BADGES[i] || null,
      raw: o,
    }
  })
}

function monthlyPrice(offering) {
  const detail = offering._priceDetail || offering.productOfferingPrice || []
  for (const p of detail) {
    const amount =
      p?.price?.taxIncludedAmount?.value ??
      p?.price?.dutyFreeAmount?.value ??
      p?.price?.value
    if (typeof amount === 'number') return amount
  }
  return null
}

function deriveFeatures(offering) {
  const feats = []
  const name = (offering.name || '').toLowerCase()
  const desc = (offering.description || '').toLowerCase()

  if (name.includes('5g') || desc.includes('5g')) feats.push('5G ready')
  if (desc.includes('unlimited') || name.includes('unlimited'))
    feats.push('Unlimited data')
  feats.push('Unlimited calls & texts')

  // Trim the description into a short third line if we have room.
  if (offering.description && feats.length < 3) {
    feats.push(offering.description)
  }
  return feats.slice(0, 3)
}

function formatEuro(value) {
  const rounded = Number.isInteger(value) ? value : value.toFixed(2)
  return `€${rounded}`
}

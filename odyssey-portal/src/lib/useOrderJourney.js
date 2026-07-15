import { useState, useCallback, useRef } from 'react'
import {
  createParty,
  createCustomer,
  createBillingAccount,
  createOrder,
  getOrder,
  listInventory,
} from './api.js'

// The four backend steps, in order. Each maps to one TMF API call and drives
// the processing animation on stage 4.
export const STEPS = [
  { key: 'party', label: 'Creating your profile', sub: 'TMF632 Party Management' },
  { key: 'customer', label: 'Registering as customer', sub: 'TMF629 Customer Management' },
  { key: 'billing', label: 'Setting up billing account', sub: 'TMF666 Account Management' },
  { key: 'order', label: 'Placing your order', sub: 'TMF622 Product Ordering' },
]

const POLL_INTERVAL_MS = 2000
const POLL_TIMEOUT_MS = 60000

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// Drives the whole submission flow and exposes reactive state the UI renders.
export function useOrderJourney() {
  const [stepIndex, setStepIndex] = useState(0)   // which backend step is active
  const [orderState, setOrderState] = useState(null) // acknowledged | inProgress | completed
  const [orderId, setOrderId] = useState(null)
  const [piRef, setPiRef] = useState(null)
  const [error, setError] = useState(null)
  const cancelled = useRef(false)

  const run = useCallback(async ({ offering, form }) => {
    cancelled.current = false
    setError(null)
    setStepIndex(0)
    setOrderState(null)
    setOrderId(null)
    setPiRef(null)

    const fullName = `${form.firstName} ${form.lastName}`.trim()

    try {
      // Step 1 — Party (TMF632)
      setStepIndex(0)
      const party = await createParty(form)

      // Step 2 — Customer (TMF629)
      setStepIndex(1)
      const customer = await createCustomer({ partyId: party.id, fullName })

      // Step 3 — Billing account (TMF666)
      setStepIndex(2)
      await createBillingAccount({ customerId: customer.id, fullName })

      // Step 4 — Order (TMF622)
      setStepIndex(3)
      const order = await createOrder({ offering, customerId: customer.id, fullName })
      setOrderId(order.id)
      setStepIndex(4) // all four done — tracker takes over
      setOrderState(order.state || 'acknowledged')

      // Poll the fulfilment state machine until completed
      const deadline = Date.now() + POLL_TIMEOUT_MS
      let current = order
      while (
        current.state !== 'completed' &&
        Date.now() < deadline &&
        !cancelled.current
      ) {
        await sleep(POLL_INTERVAL_MS)
        current = await getOrder(order.id)
        setOrderState(current.state)
      }

      if (current.state !== 'completed') {
        throw new Error('Order did not complete in time. It may still be processing.')
      }

      // Order complete — the backend auto-creates a product inventory entry.
      // Find the newest inventory item linked to this order.
      try {
        const inventory = await listInventory()
        const match = findInventoryForOrder(inventory, order.id)
        if (match) setPiRef(match.id)
      } catch {
        // Non-fatal — the order still completed; PI ref is a nice-to-have.
      }

      return { orderId: order.id }
    } catch (err) {
      if (!cancelled.current) setError(err)
      throw err
    }
  }, [])

  const cancel = useCallback(() => {
    cancelled.current = true
  }, [])

  return { run, cancel, stepIndex, orderState, orderId, piRef, error }
}

// The backend links inventory to the order via order item / related references.
// Shapes vary, so we check a few likely spots and otherwise fall back to the
// most recently created product.
function findInventoryForOrder(inventory, orderId) {
  if (!Array.isArray(inventory) || inventory.length === 0) return null

  const linked = inventory.find((p) => {
    const blob = JSON.stringify(p)
    return blob.includes(orderId)
  })
  if (linked) return linked

  // Fallback: newest by creation date, if present.
  const withDates = inventory.filter((p) => p.startDate || p.creationDate)
  if (withDates.length) {
    return withDates.sort((a, b) =>
      String(b.startDate || b.creationDate).localeCompare(
        String(a.startDate || a.creationDate)
      )
    )[0]
  }

  return inventory[inventory.length - 1]
}

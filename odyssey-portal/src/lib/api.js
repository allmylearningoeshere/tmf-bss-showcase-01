// ---------------------------------------------------------------------------
// Odyssey API client
//
// Wraps the TMF Open API BSS backend. Every call here maps to a real endpoint
// on the deployed FastAPI stack. Paths and payload shapes match the backend
// exactly (note: party is v5; customer/account/order/inventory are v4).
//
// Base URL comes from VITE_API_BASE_URL at build time. Falls back to the
// public Render deployment for local dev.
// ---------------------------------------------------------------------------

const BASE =
  import.meta.env.VITE_API_BASE_URL ||
  'https://tmf-bss-showcase-01.onrender.com'

async function request(path, { method = 'GET', body } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    let detail
    try {
      detail = await res.json()
    } catch {
      detail = await res.text()
    }
    const err = new Error(`${method} ${path} failed (${res.status})`)
    err.status = res.status
    err.detail = detail
    throw err
  }

  // 204 No Content
  if (res.status === 204) return null
  return res.json()
}

// ---------------------------------------------------------------------------
// TMF620 — Product Catalog
// ---------------------------------------------------------------------------

// Returns the raw list of seeded product offerings.
export function listOfferings() {
  return request('/productCatalog/v4/productOffering')
}

// Fetches one offering with its embedded price detail.
export function getOffering(id) {
  return request(`/productCatalog/v4/productOffering/${id}`)
}

// ---------------------------------------------------------------------------
// TMF632 — Party Management
// ---------------------------------------------------------------------------

// Creates the underlying Individual (the person behind the customer).
export function createParty({ firstName, lastName, email, phone }) {
  const fullName = `${firstName} ${lastName}`.trim()
  return request('/party/v5/individual', {
    method: 'POST',
    body: {
      fullName,
      givenName: firstName,
      familyName: lastName,
      contactMedium: [
        {
          mediumType: 'email',
          preferred: true,
          characteristic: { emailAddress: email },
        },
        {
          mediumType: 'phone',
          preferred: false,
          characteristic: { phoneNumber: phone },
        },
      ],
    },
  })
}

// ---------------------------------------------------------------------------
// TMF629 — Customer Management
// ---------------------------------------------------------------------------

// Wraps an existing party into a commercial (customer) relationship.
export function createCustomer({ partyId, fullName }) {
  return request('/customerManagement/v4/customer', {
    method: 'POST',
    body: {
      name: fullName,
      customerCategory: 'residential',
      customerRank: 'standard',
      engagedParty: {
        id: partyId,
        name: fullName,
        role: 'individual',
        '@referredType': 'Individual',
      },
      characteristic: [{ name: 'acquisitionChannel', value: 'online' }],
    },
  })
}

// ---------------------------------------------------------------------------
// TMF666 — Account Management
// ---------------------------------------------------------------------------

// Opens a billing account for the customer.
export function createBillingAccount({ customerId, fullName }) {
  return request('/accountManagement/v4/billingAccount', {
    method: 'POST',
    body: {
      name: `${fullName} - Residential`,
      accountType: 'individual',
      currency: 'EUR',
      creditLimit: { unit: 'EUR', value: 500.0 },
      billStructure: {
        cyclePeriod: 'monthly',
        billFormat: 'pdf',
        deliveryMethod: 'email',
      },
      relatedParty: [{ id: customerId, name: fullName, role: 'customer' }],
    },
  })
}

// ---------------------------------------------------------------------------
// TMF622 — Product Ordering
// ---------------------------------------------------------------------------

// Places the order for the chosen offering, referencing the customer.
export function createOrder({ offering, customerId, fullName }) {
  return request('/productOrderingManagement/v4/productOrder', {
    method: 'POST',
    body: {
      orderItem: [
        {
          id: '1',
          quantity: 1,
          action: 'add',
          productOffering: {
            id: offering.id,
            name: offering.name,
            '@referredType': 'ProductOffering',
          },
        },
      ],
      relatedParty: [
        {
          id: customerId,
          name: fullName,
          role: 'customer',
          '@referredType': 'Customer',
        },
      ],
    },
  })
}

// Retrieves an order by id — used for polling the fulfilment state machine.
export function getOrder(id) {
  return request(`/productOrderingManagement/v4/productOrder/${id}`)
}

// ---------------------------------------------------------------------------
// TMF637 — Product Inventory
// ---------------------------------------------------------------------------

// Lists product-inventory instances. The backend auto-creates one when an
// order completes, so we scan the list for a product tied to this order.
export function listInventory() {
  return request('/productInventory/v4/product')
}

export { BASE as API_BASE }

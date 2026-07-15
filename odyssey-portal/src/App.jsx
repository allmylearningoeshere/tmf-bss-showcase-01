import { useState, useEffect } from 'react'
import { listOfferings } from './lib/api.js'
import { toPlanCards } from './lib/offerings.js'
import { useOrderJourney, STEPS } from './lib/useOrderJourney.js'
import Stepper from './components/Stepper.jsx'
import PlanCards from './components/PlanCards.jsx'
import DetailsForm from './components/DetailsForm.jsx'
import ReviewOrder from './components/ReviewOrder.jsx'
import Processing from './components/Processing.jsx'
import Confirmation from './components/Confirmation.jsx'

const SHIPPING = [
  { id: 'std', name: 'Standard delivery', desc: '3–5 working days', price: 'Free', cost: 0, icon: 'M4 4h16v12H4z M4 8l8 5 8-5' },
  { id: 'exp', name: 'Express delivery', desc: 'Next working day', price: '€4.99', cost: 4.99, icon: 'M13 2L3 14h7l-1 8 10-12h-7z' },
]

const EMPTY_FORM = {
  firstName: '', lastName: '', email: '', phone: '',
  address: '', city: '', postcode: '',
}

export default function App() {
  const [stage, setStage] = useState(1)
  const [plans, setPlans] = useState([])
  const [plansError, setPlansError] = useState(null)
  const [loadingPlans, setLoadingPlans] = useState(true)
  const [selectedPlanId, setSelectedPlanId] = useState(null)
  const [shipping, setShipping] = useState('std')
  const [form, setForm] = useState(EMPTY_FORM)

  const journey = useOrderJourney()

  useEffect(() => {
    let alive = true
    listOfferings()
      .then((raw) => {
        if (!alive) return
        const cards = toPlanCards(raw)
        setPlans(cards)
        setLoadingPlans(false)
      })
      .catch((err) => {
        if (!alive) return
        setPlansError(err)
        setLoadingPlans(false)
      })
    return () => { alive = false }
  }, [])

  const selectedPlan = plans.find((p) => p.id === selectedPlanId) || null
  const selectedShipping = SHIPPING.find((s) => s.id === shipping)

  async function placeOrder() {
    setStage(4)
    try {
      await journey.run({ offering: selectedPlan.raw, form })
      setStage(5)
    } catch {
      // error surfaces inside Processing via journey.error; stay on stage 4
    }
  }

  return (
    <div className="app">
      <header className="brand">
        <div className="brand-mark">O</div>
        <div>
          <div className="brand-name">Odyssey</div>
          <div className="brand-sub">SIM-only plans</div>
        </div>
      </header>

      <Stepper stage={stage} />

      {stage === 1 && (
        <PlanCards
          plans={plans}
          loading={loadingPlans}
          error={plansError}
          selectedId={selectedPlanId}
          onSelect={setSelectedPlanId}
          onContinue={() => setStage(2)}
        />
      )}

      {stage === 2 && (
        <DetailsForm
          plan={selectedPlan}
          form={form}
          setForm={setForm}
          shipping={shipping}
          setShipping={setShipping}
          shippingOptions={SHIPPING}
          onBack={() => setStage(1)}
          onContinue={() => setStage(3)}
        />
      )}

      {stage === 3 && (
        <ReviewOrder
          plan={selectedPlan}
          form={form}
          shipping={selectedShipping}
          onBack={() => setStage(2)}
          onPlace={placeOrder}
        />
      )}

      {stage === 4 && (
        <Processing
          steps={STEPS}
          stepIndex={journey.stepIndex}
          orderState={journey.orderState}
          error={journey.error}
          onRetry={placeOrder}
          onBack={() => setStage(3)}
        />
      )}

      {stage === 5 && (
        <Confirmation
          plan={selectedPlan}
          form={form}
          shipping={selectedShipping}
          orderId={journey.orderId}
          piRef={journey.piRef}
          onRestart={() => {
            setStage(1)
            setSelectedPlanId(null)
            setForm(EMPTY_FORM)
            setShipping('std')
          }}
        />
      )}

      <footer className="foot">
        Powered by a TM Forum Open API BSS stack · TMF620 · 632 · 629 · 666 · 622 · 637
      </footer>
    </div>
  )
}

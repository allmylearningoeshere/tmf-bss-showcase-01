// ---------------------------------------------------------------------------
// Field validation rules for the details form.
//
// Each validator returns an error string when invalid, or '' when valid.
// Validation runs live as the user types (see DetailsForm).
// ---------------------------------------------------------------------------

// Letters (incl. accented), spaces, hyphens and apostrophes — no digits.
const NAME_RE = /^[\p{L}\s'-]+$/u
// Pragmatic email shape: local@domain.tld, where the domain label
// (the part before the final dot) must be at least 2 characters —
// so "d.de" fails but "gm.de" passes.
const EMAIL_RE = /^[^\s@]+@[^\s@.]{2,}(?:\.[^\s@.]+)+$/
// Mobile: digits, spaces, hyphens allowed as input; must total 10 digits.
const PHONE_DIGITS_RE = /^\d[\d\s-]*$/
// German postcode: exactly 5 digits.
const POSTCODE_RE = /^\d{5}$/
// Street name: letters (incl. accented), spaces, hyphens, periods and
// apostrophes — no digits, since the house number is now a separate field.
// Allows "Unter den Linden", "Karl-Marx-Allee", "Bäckerstr.".
const STREET_RE = /^[\p{L}\s.'-]+$/u
// House number: digits with an optional single trailing letter, e.g. "12" or
// "12a". Case-insensitive on the letter.
const HOUSE_NUMBER_RE = /^\d+[a-zA-Z]?$/

export function validateField(name, value) {
  const v = (value ?? '').trim()

  switch (name) {
    case 'firstName':
    case 'lastName': {
      if (!v) return 'Required'
      if (!NAME_RE.test(v)) return 'Letters only — no numbers'
      if (v.length < 2) return 'Too short'
      return ''
    }
    case 'email': {
      if (!v) return 'Required'
      if (!EMAIL_RE.test(v)) return 'Enter a valid email, e.g. name@email.de'
      return ''
    }
    case 'phone': {
      if (!v) return 'Required'
      if (!PHONE_DIGITS_RE.test(v)) return 'Digits only'
      const digits = v.replace(/\D/g, '')
      if (digits.length !== 10) return 'Enter a 10-digit mobile number'
      return ''
    }
    case 'address': {
      if (!v) return 'Required'
      if (!STREET_RE.test(v)) return 'Street name only — no numbers'
      if (v.length < 3) return 'Enter a street name'
      return ''
    }
    case 'houseNumber': {
      if (!v) return 'Required'
      if (!HOUSE_NUMBER_RE.test(v)) return 'e.g. 12 or 12a'
      return ''
    }
    case 'city': {
      if (!v) return 'Required'
      if (!NAME_RE.test(v)) return 'Letters only'
      return ''
    }
    case 'postcode': {
      if (!v) return 'Required'
      if (!POSTCODE_RE.test(v)) return 'Enter a 5-digit postcode'
      return ''
    }
    default:
      return ''
  }
}

// Validates the whole form; returns an { field: error } map (only non-empty).
export function validateAll(form) {
  const errors = {}
  for (const key of ['firstName', 'lastName', 'email', 'phone', 'address', 'houseNumber', 'city', 'postcode']) {
    const err = validateField(key, form[key])
    if (err) errors[key] = err
  }
  return errors
}

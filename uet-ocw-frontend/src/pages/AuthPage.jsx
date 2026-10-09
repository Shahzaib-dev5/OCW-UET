import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { sendJson } from '../data/api'
import { useAuth } from '../auth/AuthContext'

const initialForm = {
  full_name: '',
  email: '',
  date_of_birth: '',
  cnic: '',
  gender: '',
  university_name: '',
  department_name: '',
  academic_status: 'SEMESTER',
  semester: '',
  password: '',
  password_confirmation: '',
}

export default function AuthPage({ mode = 'login' }) {
  const isSignup = mode === 'signup'
  const navigate = useNavigate()
  const location = useLocation()
  const { login, register, googleLogin, verifyEmailOtp } = useAuth()
  const returnTo = new URLSearchParams(location.search).get('returnTo') || '/'
  const [form, setForm] = useState(initialForm)
  const [pendingVerification, setPendingVerification] = useState(null)
  const [otp, setOtp] = useState('')
  const [resetEmail, setResetEmail] = useState('')
  const [resetMessage, setResetMessage] = useState('')
  const [showReset, setShowReset] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const formRef = useRef(form)

  const destination = useMemo(
    () => `${isSignup ? '/login' : '/signup'}?returnTo=${encodeURIComponent(returnTo)}`,
    [isSignup, returnTo],
  )

  useEffect(() => {
    formRef.current = form
  }, [form])

  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
    const container = document.getElementById('google-signin')
    if (!clientId || !window.google?.accounts?.id || !container) return
    container.innerHTML = ''
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: async (response) => {
        try {
          if (isSignup) {
            const validation = validateForm(formRef.current, true)
            setFieldErrors(validation)
            if (Object.keys(validation).length) return
          }
          await googleLogin(response.credential, returnTo, isSignup ? signupProfile(formRef.current) : {})
          navigate(returnTo, { replace: true })
        } catch (authError) {
          setError(authError.message || 'Google sign-in failed.')
        }
      },
    })
    window.google.accounts.id.renderButton(container, {
      theme: 'outline',
      size: 'large',
      width: 280,
      text: isSignup ? 'signup_with' : 'continue_with',
    })
  }, [googleLogin, isSignup, navigate, returnTo])

  const update = (field, value) => {
    const nextValue = field === 'cnic' ? formatCnic(value) : value
    setForm((current) => ({ ...current, [field]: nextValue }))
    setFieldErrors((current) => {
      if (!current[field]) return current
      const next = { ...current }
      delete next[field]
      return next
    })
  }

  const submit = async (event) => {
    event.preventDefault()
    const validation = validateForm(form, isSignup)
    setFieldErrors(validation)
    if (Object.keys(validation).length) return

    try {
      setLoading(true)
      setError('')
      if (isSignup) {
        const payload = await register({ ...form, return_to: returnTo })
        if (payload.verification_required) {
          setPendingVerification({ email: payload.email || form.email, otp: payload.otp || '' })
          setOtp('')
          return
        }
      } else {
        await login({ email: form.email, password: form.password })
      }
      navigate(returnTo, { replace: true })
    } catch (submitError) {
      setError(submitError.message || 'Authentication failed.')
    } finally {
      setLoading(false)
    }
  }

  const verifyOtp = async (event) => {
    event.preventDefault()
    try {
      setLoading(true)
      setError('')
      await verifyEmailOtp({ email: pendingVerification?.email || form.email, otp, return_to: returnTo })
      navigate(returnTo, { replace: true })
    } catch (verifyError) {
      setError(verifyError.message || 'Unable to verify OTP.')
    } finally {
      setLoading(false)
    }
  }

  const resendOtp = async () => {
    try {
      setError('')
      const payload = await sendJson('/auth/resend-email-otp', { body: { email: pendingVerification?.email || form.email } })
      setPendingVerification((current) => ({ ...(current || {}), otp: payload.otp || '' }))
      setResetMessage(payload.otp ? `New OTP: ${payload.otp}` : payload.message)
    } catch (resendError) {
      setError(resendError.message || 'Unable to resend OTP.')
    }
  }

  const requestReset = async (event) => {
    event.preventDefault()
    try {
      setResetMessage('')
      const payload = await sendJson('/auth/forgot-password', { body: { email: resetEmail } })
      setResetMessage(payload.reset_token ? `Reset token: ${payload.reset_token}` : payload.message)
    } catch (resetError) {
      setResetMessage(resetError.message || 'Unable to start password reset.')
    }
  }

  return (
    <div className="auth-page-shell">
      <section className="auth-card" aria-label={isSignup ? 'Create your OCW account' : 'Log in to OCW'}>
        <aside className="auth-brand-panel">
          <div>
            <h1>Learn from your university's best courses, free.</h1>
            <p>Access OCW lectures, notes, slides and course resources with a verified student account.</p>
          </div>
          <div className="auth-feature-chips" aria-label="OCW features">
            <span>Watch lecture videos</span>
            <span>Download slides, PDFs and notes</span>
            <span>Follow your semester's courses</span>
          </div>
        </aside>

        <div className="auth-form-panel">
          <nav className="auth-segment" role="tablist" aria-label="Authentication mode">
            <Link role="tab" aria-selected={isSignup} className={isSignup ? 'active' : ''} to={`/signup?returnTo=${encodeURIComponent(returnTo)}`}>Sign up</Link>
            <Link role="tab" aria-selected={!isSignup} className={!isSignup ? 'active' : ''} to={`/login?returnTo=${encodeURIComponent(returnTo)}`}>Log in</Link>
          </nav>

          <div className="auth-heading">
            <h2>{isSignup ? 'Create your OCW account' : 'Welcome back'}</h2>
            <p>{isSignup ? 'Verify your email with OTP after submitting the form.' : 'Log in to continue learning.'}</p>
          </div>

          {pendingVerification ? (
            <form className="auth-form modern-auth-form" onSubmit={verifyOtp} noValidate>
              <p className="status-note auth-full">Enter the OTP sent to {pendingVerification.email}.</p>
              {pendingVerification.otp && <p className="success-box auth-full">Development OTP: {pendingVerification.otp}</p>}
              <Field label="OTP" name="otp" error={error}>
                <input id="otp" name="otp" value={otp} onChange={(event) => setOtp(event.target.value)} inputMode="numeric" pattern="[0-9]{6}" required autoComplete="one-time-code" />
              </Field>
              <div className="auth-actions auth-full">
                <button className="auth-primary-button" disabled={loading}>{loading ? 'Verifying...' : 'Verify OTP'}</button>
                <button type="button" className="auth-text-button" onClick={resendOtp}>Resend OTP</button>
              </div>
              {resetMessage && <p className="success-box auth-full">{resetMessage}</p>}
            </form>
          ) : (
            <form className="auth-form modern-auth-form" onSubmit={submit} noValidate>
              {isSignup && (
                <>
                  <Field label="Full name" name="full_name" error={fieldErrors.full_name} full>
                    <input id="full_name" name="full_name" value={form.full_name} onChange={(event) => update('full_name', event.target.value)} required autoComplete="name" />
                  </Field>
                  <Field label="Date of birth" name="date_of_birth" error={fieldErrors.date_of_birth}>
                    <input id="date_of_birth" name="date_of_birth" type="date" value={form.date_of_birth} onChange={(event) => update('date_of_birth', event.target.value)} required autoComplete="bday" />
                  </Field>
                  <Field label="CNIC" name="cnic" error={fieldErrors.cnic}>
                    <input id="cnic" name="cnic" value={form.cnic} onChange={(event) => update('cnic', event.target.value)} placeholder="12345-1234567-1" required inputMode="numeric" autoComplete="off" maxLength={15} />
                  </Field>
                  <Field label="Gender" name="gender" error={fieldErrors.gender}>
                    <select id="gender" name="gender" value={form.gender} onChange={(event) => update('gender', event.target.value)} required>
                      <option value="">Select gender</option>
                      <option value="MALE">Male</option>
                      <option value="FEMALE">Female</option>
                      <option value="OTHER">Other</option>
                      <option value="PREFER_NOT_TO_SAY">Prefer not to say</option>
                    </select>
                  </Field>
                  <Field label="Academic status" name="academic_status" error={fieldErrors.academic_status}>
                    <select id="academic_status" name="academic_status" value={form.academic_status} onChange={(event) => update('academic_status', event.target.value)} required>
                      <option value="SEMESTER">Current semester</option>
                      <option value="GRADUATE">Graduate</option>
                    </select>
                  </Field>
                  <Field label="University name" name="university_name" error={fieldErrors.university_name}>
                    <input id="university_name" name="university_name" value={form.university_name} onChange={(event) => update('university_name', event.target.value)} required autoComplete="organization" />
                  </Field>
                  <Field label="Department" name="department_name" error={fieldErrors.department_name}>
                    <input id="department_name" name="department_name" value={form.department_name} onChange={(event) => update('department_name', event.target.value)} required autoComplete="organization-title" />
                  </Field>
                  <Field label="Semester" name="semester" error={fieldErrors.semester} full>
                    <input id="semester" name="semester" value={form.semester} onChange={(event) => update('semester', event.target.value)} required={form.academic_status === 'SEMESTER'} disabled={form.academic_status === 'GRADUATE'} />
                  </Field>
                </>
              )}

              <Field label="Email" name="email" error={fieldErrors.email} full>
                <input id="email" name="email" type="email" value={form.email} onChange={(event) => update('email', event.target.value)} required autoComplete="email" />
              </Field>
              <Field label="Password" name="password" error={fieldErrors.password}>
                <PasswordInput id="password" name="password" value={form.password} onChange={(value) => update('password', value)} show={showPassword} onToggle={() => setShowPassword((current) => !current)} autoComplete={isSignup ? 'new-password' : 'current-password'} />
              </Field>
              {isSignup ? (
                <Field label="Confirm password" name="password_confirmation" error={fieldErrors.password_confirmation}>
                  <PasswordInput id="password_confirmation" name="password_confirmation" value={form.password_confirmation} onChange={(value) => update('password_confirmation', value)} show={showConfirmPassword} onToggle={() => setShowConfirmPassword((current) => !current)} autoComplete="new-password" />
                </Field>
              ) : (
                <div className="auth-login-row">
                  <label className="auth-checkbox">
                    <input type="checkbox" name="remember" />
                    <span>Keep me logged in</span>
                  </label>
                  <button type="button" className="auth-link-button" onClick={() => setShowReset((current) => !current)}>Forgot password?</button>
                </div>
              )}

              {error && <div className="alert-box compact auth-full">{error}</div>}
              <button className="auth-primary-button auth-full" disabled={loading}>{loading ? 'Please wait...' : isSignup ? 'Create account' : 'Log in'}</button>
            </form>
          )}

          {!pendingVerification && <div id="google-signin" className="google-button-wrap" />}

          {!isSignup && showReset && (
            <form className="auth-reset-form" onSubmit={requestReset} noValidate>
              <Field label="Account email" name="reset_email">
                <input id="reset_email" type="email" value={resetEmail} onChange={(event) => setResetEmail(event.target.value)} required autoComplete="email" />
              </Field>
              <button className="auth-text-button">Send reset link</button>
              {resetMessage && <p className="success-box">{resetMessage}</p>}
            </form>
          )}

          <p className="auth-switch">
            {isSignup ? 'Already have an account?' : 'New to OCW?'}{' '}
            <Link to={destination}>{isSignup ? 'Log in' : 'Create an account'}</Link>
          </p>
        </div>
      </section>
    </div>
  )
}

function Field({ label, name, error, full = false, children }) {
  return (
    <label className={full ? 'auth-field auth-full' : 'auth-field'} htmlFor={name}>
      <span>{label}</span>
      {children}
      {error && <small>{error}</small>}
    </label>
  )
}

function PasswordInput({ id, name, value, onChange, show, onToggle, autoComplete }) {
  return (
    <span className="password-field">
      <input
        id={id}
        name={name}
        type={show ? 'text' : 'password'}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required
        minLength={8}
        autoComplete={autoComplete}
      />
      <button type="button" onClick={onToggle} aria-label={show ? 'Hide password' : 'Show password'}>
        {show ? 'Hide' : 'Show'}
      </button>
    </span>
  )
}

function validateForm(form, isSignup) {
  const errors = {}
  if (isSignup) {
    required(errors, form.full_name, 'full_name', 'Full name is required.')
    required(errors, form.date_of_birth, 'date_of_birth', 'Date of birth is required.')
    required(errors, form.gender, 'gender', 'Gender is required.')
    required(errors, form.university_name, 'university_name', 'University name is required.')
    required(errors, form.department_name, 'department_name', 'Department is required.')
    required(errors, form.academic_status, 'academic_status', 'Academic status is required.')
    if (form.academic_status === 'SEMESTER') required(errors, form.semester, 'semester', 'Semester is required.')
    if (digitsOnly(form.cnic).length !== 13) errors.cnic = 'CNIC must be 13 digits.'
  }
  required(errors, form.email, 'email', 'Email is required.')
  if (form.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email)) errors.email = 'Enter a valid email address.'
  if (!form.password) errors.password = 'Password is required.'
  else if (form.password.length < 8) errors.password = 'Password must be at least 8 characters.'
  if (isSignup && form.password !== form.password_confirmation) errors.password_confirmation = 'Passwords must match.'
  return errors
}

function required(errors, value, field, message) {
  if (!String(value || '').trim()) errors[field] = message
}

function formatCnic(value) {
  const digits = digitsOnly(value).slice(0, 13)
  if (digits.length <= 5) return digits
  if (digits.length <= 12) return `${digits.slice(0, 5)}-${digits.slice(5)}`
  return `${digits.slice(0, 5)}-${digits.slice(5, 12)}-${digits.slice(12)}`
}

function digitsOnly(value) {
  return String(value || '').replace(/\D/g, '')
}

function signupProfile(form) {
  return {
    full_name: form.full_name,
    date_of_birth: form.date_of_birth,
    cnic: form.cnic,
    gender: form.gender,
    university_name: form.university_name,
    department_name: form.department_name,
    academic_status: form.academic_status,
    semester: form.academic_status === 'SEMESTER' ? form.semester : '',
  }
}

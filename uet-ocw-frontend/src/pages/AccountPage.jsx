import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { fetchJson, sendJson } from '../data/api'
import { useAuth } from '../auth/AuthContext'

export default function AccountPage() {
  const { user, loading, refreshUser, isApprovedInstructor } = useAuth()
  const [courseEnrollments, setCourseEnrollments] = useState([])
  const [resourceEnrollments, setResourceEnrollments] = useState([])
  const [application, setApplication] = useState(null)
  const [form, setForm] = useState({ qualifications: '', expertise: '', teaching_bio: '', contact_details: '', affiliation: '' })
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user) return
    Promise.all([
      fetchJson('/course-enrollments'),
      fetchJson('/course-enrollments/resources'),
      fetchJson('/instructor-applications/me'),
    ]).then(([courses, resources, app]) => {
      setCourseEnrollments(courses)
      setResourceEnrollments(resources)
      setApplication(app)
    }).catch((loadError) => setError(loadError.message || 'Unable to load account data.'))
  }, [user])

  if (loading) return <div className="container page-block"><div className="loading-box">Loading account...</div></div>
  if (!user) return <Navigate to={`/login?returnTo=${encodeURIComponent('/account')}`} replace />

  const submitApplication = async (event) => {
    event.preventDefault()
    try {
      setError('')
      const saved = await sendJson('/instructor-applications', { body: form })
      setApplication(saved)
      await refreshUser()
      setMessage('Instructor application submitted.')
    } catch (submitError) {
      setError(submitError.message || 'Unable to submit instructor application.')
    }
  }

  return (
    <div className="container page-block account-layout">
      <section className="content-panel">
        <p className="eyebrow">Account</p>
        <h2>{user.full_name || user.username}</h2>
        <p>{user.email}</p>
        <div className="status-row">
          <span>{user.role?.name || 'STUDENT'}</span>
          <span>Instructor: {user.instructor_status || 'NONE'}</span>
        </div>
      </section>

      <section className="content-panel">
        <h3>My Learning</h3>
        <EnrollmentList title="Courses" items={courseEnrollments} />
        <EnrollmentList title="Books and Skills" items={resourceEnrollments} />
      </section>

      <section className="content-panel">
        <h3>Instructor Application</h3>
        {isApprovedInstructor && (
          <div className="success-box instructor-switch-box">
            Approved. <Link to="/courses">Switch to Instructor UI</Link>
          </div>
        )}
        {application && !isApprovedInstructor && (
          <p className="status-note">Current status: {application.status}{application.review_reason ? ` - ${application.review_reason}` : ''}</p>
        )}
        {(!application || ['REJECTED', 'REVOKED'].includes(application.status)) && (
          <form className="resource-form single-column" onSubmit={submitApplication}>
            {Object.keys(form).map((field) => (
              <label className="field-label" key={field}>
                {field.replaceAll('_', ' ')}
                <textarea value={form[field]} onChange={(event) => setForm({ ...form, [field]: event.target.value })} required={field !== 'affiliation'} />
              </label>
            ))}
            <button className="primary-button auth-submit">Apply to Become an Instructor</button>
          </form>
        )}
        {message && <p className="success-box">{message}</p>}
        {error && <div className="alert-box compact">{error}</div>}
      </section>
    </div>
  )
}

function EnrollmentList({ title, items }) {
  return (
    <div className="learning-list">
      <h4>{title}</h4>
      {items.length ? items.map((item) => (
        <article key={`${title}-${item.id}`} className="learning-row">
          <strong>{item.course?.title || item.resource?.title || `${item.resource_type} #${item.resource_id}`}</strong>
          <span>{item.status}</span>
          {item.review_reason && <p>{item.review_reason}</p>}
        </article>
      )) : <p className="empty-state">No requests yet.</p>}
    </div>
  )
}

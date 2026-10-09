import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { fetchJson, sendJson } from '../data/api'
import { useAuth } from '../auth/AuthContext'

export default function AdminPage() {
  const { user, loading, isAdmin } = useAuth()
  const [applications, setApplications] = useState([])
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busyId, setBusyId] = useState(null)

  const loadApplications = () => {
    fetchJson('/instructor-applications')
      .then(setApplications)
      .catch((loadError) => setError(loadError.message || 'Unable to load instructor applications.'))
  }

  useEffect(() => {
    if (isAdmin) loadApplications()
  }, [isAdmin])

  if (loading) return <div className="container page-block"><div className="loading-box">Loading admin tools...</div></div>
  if (!user) return <Navigate to={`/login?returnTo=${encodeURIComponent('/admin')}`} replace />
  if (!isAdmin) return <Navigate to="/account" replace />

  const review = async (application, action) => {
    try {
      setBusyId(application.id)
      setError('')
      setMessage('')
      await sendJson(`/instructor-applications/${application.id}/${action}`, {
        method: 'PATCH',
        body: { reason: action === 'approve' ? 'Approved by admin' : 'Reviewed by admin' },
      })
      setMessage(`Application ${action}d.`)
      loadApplications()
    } catch (reviewError) {
      setError(reviewError.message || `Unable to ${action} application.`)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="container page-block account-layout">
      <section className="content-panel">
        <p className="eyebrow">Admin</p>
        <h2>Instructor Applications</h2>
        {message && <p className="success-box">{message}</p>}
        {error && <div className="alert-box compact">{error}</div>}
      </section>

      <section className="content-panel">
        {applications.length ? applications.map((application) => (
          <article className="admin-review-row" key={application.id}>
            <div>
              <strong>{application.user?.full_name || application.user?.username || 'Applicant'}</strong>
              <span>{application.user?.email}</span>
              <p>Status: {application.status}</p>
              <p>Expertise: {application.expertise || 'Not provided'}</p>
              <p>Qualifications: {application.qualifications || 'Not provided'}</p>
              <p>Biography: {application.teaching_bio || 'Not provided'}</p>
              <p>Contact: {application.contact_details || 'Not provided'}</p>
              <p>Affiliation: {application.affiliation || 'Not provided'}</p>
            </div>
            <div className="row-actions">
              <button type="button" disabled={busyId === application.id || application.status === 'APPROVED'} onClick={() => review(application, 'approve')}>
                Approve
              </button>
              <button type="button" disabled={busyId === application.id || application.status === 'REJECTED'} onClick={() => review(application, 'reject')}>
                Reject
              </button>
              <button type="button" disabled={busyId === application.id || application.status === 'REVOKED'} onClick={() => review(application, 'revoke')}>
                Revoke
              </button>
            </div>
          </article>
        )) : (
          <p className="empty-state">No instructor applications yet.</p>
        )}
      </section>
    </div>
  )
}

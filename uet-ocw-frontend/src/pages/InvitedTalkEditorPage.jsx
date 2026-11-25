import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { fetchJson, sendJson, uploadFile } from '../data/api'
import { useAuth } from '../auth/AuthContext'

const emptyTalk = {
  department_id: '', talk_title: '', event_title: '', presenter: '', talk_date: '',
  video_url: '', publication: '', upload_url: '', status: 'DRAFT',
}

export default function InvitedTalkEditorPage() {
  const { user, loading, isApprovedInstructor, setViewMode } = useAuth()
  const navigate = useNavigate()
  const { talkId } = useParams()
  const editing = Boolean(talkId)
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [selectedFaculty, setSelectedFaculty] = useState('')
  const [form, setForm] = useState(emptyTalk)
  const [attachment, setAttachment] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([fetchJson('/faculties'), fetchJson('/departments')])
      .then(([facultyData, departmentData]) => { setFaculties(facultyData); setDepartments(departmentData) })
      .catch((loadError) => setError(loadError.message || 'Unable to load the tech talk form.'))
  }, [])
  useEffect(() => {
    if (!editing) return
    fetchJson(`/invited-talks/${talkId}`)
      .then((talk) => {
        setForm({
          department_id: talk.department_id || '', talk_title: talk.talk_title || '',
          event_title: talk.event_title || '', presenter: talk.presenter || '', talk_date: talk.talk_date || '',
          video_url: talk.video_url || '', publication: talk.publication || '', upload_url: talk.upload_url || '',
          status: talk.status || 'DRAFT',
        })
        setSelectedFaculty(talk.department?.faculty_id || '')
      })
      .catch((loadError) => setError(loadError.message || 'Unable to load the tech talk.'))
  }, [editing, talkId])
  useEffect(() => { if (isApprovedInstructor) setViewMode('instructor') }, [isApprovedInstructor, setViewMode])

  const visibleDepartments = useMemo(() => selectedFaculty
    ? departments.filter((item) => String(item.faculty_id) === String(selectedFaculty))
    : departments, [departments, selectedFaculty])

  if (loading) return <div className="container page-block"><div className="loading-box">Loading instructor tools...</div></div>
  if (!user) return <Navigate to={`/login?returnTo=${encodeURIComponent('/invited-talks/new')}`} replace />
  if (!isApprovedInstructor) return <Navigate to="/account" replace />

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }))
  const submit = async (event) => {
    event.preventDefault()
    try {
      setSaving(true); setError('')
      let uploadUrl = form.upload_url
      if (attachment) {
        const uploaded = await uploadFile({ file: attachment, folder: 'invited-talks' })
        uploadUrl = uploaded.local_url || uploaded.public_url || uploaded.relative_path || uploadUrl
      }
      const payload = { ...form, upload_url: uploadUrl, department_id: Number(form.department_id) }
      if (editing) delete payload.status
      Object.keys(payload).forEach((key) => { if (payload[key] === '') delete payload[key] })
      const saved = await sendJson(editing ? `/invited-talks/${talkId}` : '/invited-talks', { method: editing ? 'PATCH' : 'POST', body: payload })
      navigate(`/invited-talks/${saved.id}`)
    } catch (submitError) {
      setError(submitError.message || 'Unable to create the tech talk.')
    } finally { setSaving(false) }
  }

  return <div className="course-page">
    <header className="course-hero-strip"><div className="container course-hero-inner"><div className="course-hero-copy">
      <nav className="breadcrumb-line"><Link to="/">Home</Link><span>/</span><Link to="/invited-talks">Tech Talks</Link><span>/</span><span>Add Tech Talk</span></nav>
      <h2>{editing ? 'Edit tech talk' : 'Add tech talk'}</h2><p>{editing ? 'Update your talk details and attached information.' : 'Create a draft tech talk. It appears publicly only after admin approval.'}</p>
    </div></div></header>
    <main className="container page-block course-results-wrap"><section className="content-panel">
      <form className="resource-form course-editor-form" onSubmit={submit}>
        <label className="field-label">Faculty<select value={selectedFaculty} onChange={(event) => { setSelectedFaculty(event.target.value); update('department_id', '') }}><option value="">All faculties</option>{faculties.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label className="field-label">Department<select required value={form.department_id} onChange={(event) => update('department_id', event.target.value)}><option value="">Select department</option>{visibleDepartments.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <div className="field-label course-approval-note"><span>Approval status</span><strong>Draft until admin publishes</strong></div>
        <label className="field-label">Talk title<input required value={form.talk_title} onChange={(event) => update('talk_title', event.target.value)} /></label>
        <label className="field-label">Event title<input value={form.event_title} onChange={(event) => update('event_title', event.target.value)} /></label>
        <label className="field-label">Presenter<input value={form.presenter} onChange={(event) => update('presenter', event.target.value)} /></label>
        <label className="field-label">Talk date<input type="date" value={form.talk_date} onChange={(event) => update('talk_date', event.target.value)} /></label>
        <label className="field-label wide">Video URL<input type="url" value={form.video_url} onChange={(event) => update('video_url', event.target.value)} /></label>
        <label className="field-label wide">Publication / description<textarea value={form.publication} onChange={(event) => update('publication', event.target.value)} /></label>
        <label className="field-label wide">Attachment<input type="file" onChange={(event) => setAttachment(event.target.files?.[0] || null)} /></label>
        <div className="form-actions"><button className="primary-button auth-submit" disabled={saving}>{saving ? 'Saving...' : editing ? 'Update Tech Talk' : 'Create Tech Talk'}</button><Link className="secondary-action-button" to={editing ? `/invited-talks/${talkId}` : '/invited-talks'}>Cancel</Link></div>
      </form>{error && <div className="alert-box compact">{error}</div>}
    </section></main>
  </div>
}

import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { fetchJson, sendJson, uploadFile } from '../data/api'
import { useAuth } from '../auth/AuthContext'

const emptyCourse = {
  department_id: '',
  title: '',
  slug: '',
  course_code: '',
  short_description: '',
  description: '',
  syllabus: '',
  learning_outcomes: '',
  schedule: '',
  thumbnail: '',
  access_level: 'RESTRICTED',
  login_required: false,
  status: 'DRAFT',
  course_type: 'Hybrid',
  level: 'UNDERGRADUATE',
}

export default function CourseEditorPage() {
  const { user, loading, isApprovedInstructor, setViewMode } = useAuth()
  const navigate = useNavigate()
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [selectedFaculty, setSelectedFaculty] = useState('')
  const [form, setForm] = useState(emptyCourse)
  const [thumbnailFile, setThumbnailFile] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([fetchJson('/faculties'), fetchJson('/departments')])
      .then(([facultyData, departmentData]) => {
        setFaculties(facultyData)
        setDepartments(departmentData)
      })
      .catch((loadError) => setError(loadError.message || 'Unable to load course form data.'))
  }, [])

  useEffect(() => {
    if (isApprovedInstructor) setViewMode('instructor')
  }, [isApprovedInstructor, setViewMode])

  const visibleDepartments = useMemo(() => {
    if (!selectedFaculty) return departments
    return departments.filter((department) => String(department.faculty_id) === String(selectedFaculty))
  }, [departments, selectedFaculty])

  if (loading) return <div className="container page-block"><div className="loading-box">Loading instructor tools...</div></div>
  if (!user) return <Navigate to={`/login?returnTo=${encodeURIComponent('/courses/new')}`} replace />
  if (!isApprovedInstructor) return <Navigate to="/account" replace />

  const update = (field, value) => {
    setForm((current) => ({ ...current, [field]: value, ...(field === 'title' && !current.slug ? { slug: slugify(value) } : {}) }))
  }

  const submit = async (event) => {
    event.preventDefault()
    try {
      setSaving(true)
      setError('')
      let thumbnail = form.thumbnail
      if (thumbnailFile) {
        const uploaded = await uploadFile({ file: thumbnailFile, folder: 'courses/thumbnails' })
        thumbnail = uploaded.local_url || uploaded.public_url || uploaded.relative_path || thumbnail
      }
      const payload = {
        ...form,
        thumbnail,
        department_id: Number(form.department_id),
        credit_hours: form.credit_hours ? Number(form.credit_hours) : undefined,
      }
      Object.keys(payload).forEach((key) => {
        if (payload[key] === '' || payload[key] === undefined) delete payload[key]
      })
      const saved = await sendJson('/courses', { body: payload })
      navigate(`/courses/${saved.id}`)
    } catch (submitError) {
      setError(submitError.message || 'Unable to create course.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="course-page">
      <header className="course-hero-strip">
        <div className="container course-hero-inner">
          <div className="course-hero-copy">
            <nav className="breadcrumb-line" aria-label="Breadcrumb">
              <Link to="/">Home</Link>
              <span aria-hidden="true">/</span>
              <Link to="/courses">Courses</Link>
              <span aria-hidden="true">/</span>
              <span>Add Course</span>
            </nav>
            <h2>Add course</h2>
            <p>Create a draft course. It appears to students only after admin approval.</p>
          </div>
        </div>
      </header>

      <main className="container page-block course-results-wrap">
        <section className="content-panel">
          <form className="resource-form course-editor-form" onSubmit={submit}>
            <label className="field-label">
              Faculty
              <select value={selectedFaculty} onChange={(event) => { setSelectedFaculty(event.target.value); update('department_id', '') }}>
                <option value="">All faculties</option>
                {faculties.map((faculty) => <option key={faculty.id} value={faculty.id}>{faculty.name}</option>)}
              </select>
            </label>
            <label className="field-label">
              Department
              <select value={form.department_id} onChange={(event) => update('department_id', event.target.value)} required>
                <option value="">Select department</option>
                {visibleDepartments.map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}
              </select>
            </label>
            <label className="field-label">
              Access
              <select value={form.access_level} onChange={(event) => update('access_level', event.target.value)}>
                <option value="PUBLIC">Public</option>
                <option value="RESTRICTED">Restricted</option>
              </select>
            </label>
            <label className="field-label checkbox-field">
              <input
                type="checkbox"
                checked={form.login_required}
                onChange={(event) => update('login_required', event.target.checked)}
              />
              Require login to view course detail
            </label>
            <div className="field-label course-approval-note">
              <span>Approval status</span>
              <strong>Draft until admin publishes</strong>
            </div>
            <label className="field-label">
              Title
              <input value={form.title} onChange={(event) => update('title', event.target.value)} required />
            </label>
            <label className="field-label">
              Slug
              <input value={form.slug} onChange={(event) => update('slug', event.target.value)} required />
            </label>
            <label className="field-label">
              Course code
              <input value={form.course_code} onChange={(event) => update('course_code', event.target.value)} />
            </label>
            <label className="field-label">
              Credit hours
              <input type="number" min="0" value={form.credit_hours || ''} onChange={(event) => update('credit_hours', event.target.value)} />
            </label>
            <label className="field-label">
              Type
              <input value={form.course_type} onChange={(event) => update('course_type', event.target.value)} />
            </label>
            <label className="field-label">
              Level
              <select value={form.level} onChange={(event) => update('level', event.target.value)}>
                <option value="BEGINNER">Beginner</option>
                <option value="INTERMEDIATE">Intermediate</option>
                <option value="ADVANCED">Advanced</option>
                <option value="UNDERGRADUATE">Undergraduate</option>
                <option value="GRADUATE">Graduate</option>
                <option value="OTHER">Other</option>
              </select>
            </label>
            <label className="field-label">
              Thumbnail
              <input type="file" accept="image/*" onChange={(event) => setThumbnailFile(event.target.files?.[0] || null)} />
            </label>
            {['short_description', 'description', 'syllabus', 'learning_outcomes', 'schedule'].map((field) => (
              <label className="field-label wide" key={field}>
                {field.replaceAll('_', ' ')}
                <textarea value={form[field]} onChange={(event) => update(field, event.target.value)} />
              </label>
            ))}
            <div className="form-actions">
              <button className="primary-button auth-submit" disabled={saving}>{saving ? 'Saving...' : 'Create Course'}</button>
              <Link className="secondary-action-button" to="/courses">Cancel</Link>
            </div>
          </form>
          {error && <div className="alert-box compact">{error}</div>}
        </section>
      </main>
    </div>
  )
}

function slugify(value) {
  return String(value || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

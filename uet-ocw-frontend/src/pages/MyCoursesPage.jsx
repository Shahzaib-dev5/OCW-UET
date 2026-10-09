import { useEffect, useMemo, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { fetchJson, sendJson } from '../data/api'
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
  access_level: 'RESTRICTED',
  status: 'DRAFT',
}

export default function MyCoursesPage() {
  const { user, loading, isApprovedInstructor, setViewMode } = useAuth()
  const [courses, setCourses] = useState([])
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [selectedFaculty, setSelectedFaculty] = useState('')
  const [form, setForm] = useState(emptyCourse)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isApprovedInstructor) return
    setViewMode('instructor')
    Promise.all([fetchJson('/course-enrollments/me/courses'), fetchJson('/faculties'), fetchJson('/departments')])
      .then(([courseData, facultyData, departmentData]) => {
        setCourses(courseData)
        setFaculties(facultyData)
        setDepartments(departmentData)
      })
      .catch((loadError) => setError(loadError.message || 'Unable to load instructor courses.'))
  }, [isApprovedInstructor, setViewMode])

  const visibleDepartments = useMemo(() => {
    if (!selectedFaculty) return departments
    return departments.filter((department) => String(department.faculty_id) === String(selectedFaculty))
  }, [departments, selectedFaculty])

  if (loading) return <div className="container page-block"><div className="loading-box">Loading instructor tools...</div></div>
  if (!user) return <Navigate to={`/login?returnTo=${encodeURIComponent('/my-courses')}`} replace />
  if (!isApprovedInstructor) return <Navigate to="/account" replace />

  const update = (field, value) => {
    setForm((current) => ({ ...current, [field]: value, ...(field === 'title' && !current.slug ? { slug: slugify(value) } : {}) }))
  }

  const submit = async (event) => {
    event.preventDefault()
    try {
      setError('')
      const payload = { ...form, department_id: Number(form.department_id) }
      const saved = await sendJson('/courses', { body: payload })
      setCourses((current) => [saved, ...current])
      setForm(emptyCourse)
      setMessage('Course saved. Use the existing admin/resource APIs to add lectures and files, or edit from your management workflow.')
    } catch (submitError) {
      setError(submitError.message || 'Unable to create course.')
    }
  }

  return (
    <div className="container page-block account-layout">
      <section className="content-panel">
        <div className="manager-heading">
          <div>
            <p className="eyebrow">Instructor mode</p>
            <h2>My Courses</h2>
          </div>
          <span>+ Add Course</span>
        </div>
        <form className="resource-form" onSubmit={submit}>
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
          {['title', 'slug', 'course_code', 'short_description', 'description', 'syllabus', 'learning_outcomes', 'schedule'].map((field) => (
            <label className={field.includes('description') || ['syllabus', 'learning_outcomes', 'schedule'].includes(field) ? 'field-label wide' : 'field-label'} key={field}>
              {field.replaceAll('_', ' ')}
              {field.includes('description') || ['syllabus', 'learning_outcomes', 'schedule'].includes(field)
                ? <textarea value={form[field]} onChange={(event) => update(field, event.target.value)} />
                : <input value={form[field]} onChange={(event) => update(field, event.target.value)} required={['title', 'slug'].includes(field)} />}
            </label>
          ))}
          <button className="primary-button auth-submit">Create Course</button>
        </form>
        {message && <p className="success-box">{message}</p>}
        {error && <div className="alert-box compact">{error}</div>}
      </section>

      <section className="content-panel">
        <h3>Owned and Approved Courses</h3>
        {courses.length ? courses.map((course) => (
          <article className="learning-row" key={course.id}>
            <strong>{course.title}</strong>
            <span>{course.status || 'DRAFT'}</span>
          </article>
        )) : <p className="empty-state">No courses yet.</p>}
      </section>
    </div>
  )
}

function slugify(value) {
  return String(value || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchJson, fileNameFromUrl, fileUrl, sendJson, uploadFile } from '../data/api'

const initialForm = {
  course_id: '',
  title: '',
  description: '',
  external_url: '',
  display_order: '',
  token: '',
  file: null,
}

export default function BooksPage() {
  const [courses, setCourses] = useState([])
  const [resources, setResources] = useState([])
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    async function loadBooks() {
      try {
        setLoading(true)
        setError('')
        const [coursesData, resourcesData] = await Promise.all([
          fetchJson('/courses'),
          fetchJson('/course-resources'),
        ])

        setCourses(coursesData)
        setResources(resourcesData)
        if (coursesData[0]) {
          setForm((current) => ({ ...current, course_id: String(coursesData[0].id) }))
        }
      } catch (loadError) {
        setError(loadError.message || 'Unable to load books.')
      } finally {
        setLoading(false)
      }
    }

    loadBooks()
  }, [])

  const books = useMemo(
    () => resources.filter((resource) => resource.resource_type === 'BOOK'),
    [resources],
  )

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')

    try {
      const token = form.token.trim()
      if (token) {
        localStorage.setItem('ocw_access_token', token)
      }

      let filePayload = {}
      if (form.file) {
        const uploaded = await uploadFile({
          file: form.file,
          folder: `courses/${form.course_id}/books`,
          token,
        })
        filePayload = {
          file_url: uploaded.local_url || uploaded.public_url || uploaded.file_url || uploaded.url,
          file_size: form.file.size,
          mime_type: form.file.type || null,
        }
      }

      const created = await sendJson('/course-resources', {
        token,
        body: {
          course_id: Number(form.course_id),
          title: form.title.trim(),
          resource_type: 'BOOK',
          description: form.description.trim() || null,
          external_url: form.external_url.trim() || null,
          display_order: form.display_order ? Number(form.display_order) : 0,
          is_active: true,
          ...filePayload,
        },
      })

      setResources((current) => [...current, created])
      setForm((current) => ({
        ...initialForm,
        course_id: current.course_id,
        token,
      }))
      event.currentTarget.reset()
      setSuccess('Book added successfully.')
    } catch (saveError) {
      setError(saveError.message || 'Unable to add book.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="course-page books-page">
      <section className="course-title-band">
        <div className="container">
          <h2>Books</h2>
          <div className="breadcrumb-line">
            <Link to="/">Home</Link>
            <span>/</span>
            <span>Books</span>
          </div>
        </div>
      </section>

      <div className="container page-block">
        <section className="content-panel books-hero-panel">
          <div>
            <p className="eyebrow">Book library</p>
            <h2>Add and browse course books only</h2>
            <p>
              This module stores books as course resources with the fixed type BOOK, keeping them
              separate from lectures, files and other course materials.
            </p>
          </div>
          <span>{books.length} books</span>
        </section>

        {error && <div className="alert-box">{error}</div>}
        {success && <div className="success-box">{success}</div>}

        {loading ? (
          <div className="loading-box">Loading books...</div>
        ) : (
          <div className="books-layout">
            <section className="content-panel resource-manager">
              <div className="manager-heading">
                <div>
                  <p className="eyebrow">Add book</p>
                  <h3>Book details</h3>
                </div>
                <span>BOOK only</span>
              </div>

              <form className="resource-form book-form" onSubmit={handleSubmit}>
                <label className="field-label">
                  Course
                  <select
                    value={form.course_id}
                    required
                    onChange={(event) => setForm({ ...form, course_id: event.target.value })}
                  >
                    {courses.map((course) => (
                      <option key={course.id} value={course.id}>
                        {formatCourseTitle(course)}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field-label">
                  Book title
                  <input
                    value={form.title}
                    required
                    onChange={(event) => setForm({ ...form, title: event.target.value })}
                    placeholder="Book name"
                  />
                </label>

                <label className="field-label">
                  Display order
                  <input
                    min="0"
                    type="number"
                    value={form.display_order}
                    onChange={(event) => setForm({ ...form, display_order: event.target.value })}
                    placeholder="0"
                  />
                </label>

                <label className="field-label wide">
                  Description
                  <textarea
                    rows="3"
                    value={form.description}
                    onChange={(event) => setForm({ ...form, description: event.target.value })}
                    placeholder="Short note about the book"
                  />
                </label>

                <label className="field-label">
                  Book file
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.epub,.ppt,.pptx"
                    onChange={(event) => setForm({ ...form, file: event.target.files?.[0] || null })}
                  />
                </label>

                <label className="field-label">
                  External link
                  <input
                    type="url"
                    value={form.external_url}
                    onChange={(event) => setForm({ ...form, external_url: event.target.value })}
                    placeholder="https://..."
                  />
                </label>

                <label className="field-label">
                  Access token
                  <input
                    value={form.token}
                    onChange={(event) => setForm({ ...form, token: event.target.value })}
                    placeholder="Optional if already logged in"
                  />
                </label>

                <div className="form-actions">
                  <button className="primary-button small" type="submit" disabled={saving || !courses.length}>
                    {saving ? 'Adding book...' : 'Add book'}
                  </button>
                </div>
              </form>
            </section>

            <section className="content-panel resource-manager">
              <div className="manager-heading">
                <div>
                  <p className="eyebrow">Available books</p>
                  <h3>Book resources</h3>
                </div>
                <span>{books.length} items</span>
              </div>

              <div className="resource-table">
                {books.length ? (
                  books.map((book) => (
                    <article key={book.id} className="managed-resource-row book-row">
                      <div>
                        <strong>{book.title}</strong>
                        <span>{book.course?.title || 'Course not specified'}</span>
                        {book.description && <span>{book.description}</span>}
                      </div>
                      <div className="resource-links">
                        {book.file_url && (
                          <>
                            <a href={fileUrl(book.file_url)} target="_blank" rel="noreferrer">View</a>
                            <a href={fileUrl(book.file_url)} download={fileNameFromUrl(book.file_url, book.title)}>
                              Download
                            </a>
                          </>
                        )}
                        {book.external_url && <a href={fileUrl(book.external_url)} target="_blank" rel="noreferrer">Link</a>}
                      </div>
                    </article>
                  ))
                ) : (
                  <p className="empty-state">No book resources have been added yet.</p>
                )}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}

function formatCourseTitle(course) {
  const title = course.title || 'Untitled course'
  return course.course_code ? `${title} - ${course.course_code}` : title
}

import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import TitleImageFallback from '../components/TitleImageFallback'
import { fetchJson, fileNameFromUrl, fileUrl, sendJson } from '../data/api'

export default function BooksPage() {
  const { user } = useAuth()
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [courses, setCourses] = useState([])
  const [resources, setResources] = useState([])
  const [selectedFacultyId, setSelectedFacultyId] = useState(null)
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [requestingId, setRequestingId] = useState(null)

  useEffect(() => {
    async function loadBooks() {
      try {
        setLoading(true)
        setError('')
        const [facultiesData, departmentsData, coursesData, resourcesData] = await Promise.all([
          fetchJson('/faculties'),
          fetchJson('/departments'),
          fetchJson('/courses'),
          fetchJson('/course-resources'),
        ])

        setFaculties(facultiesData)
        setDepartments(departmentsData)
        setCourses(coursesData)
        setResources(resourcesData)
      } catch (loadError) {
        setError(loadError.message || 'Unable to load books.')
      } finally {
        setLoading(false)
      }
    }

    loadBooks()
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearchTerm(searchTerm.trim().toLowerCase())
    }, 200)

    return () => window.clearTimeout(timer)
  }, [searchTerm])

  const coursesById = useMemo(() => {
    return courses.reduce((lookup, course) => {
      lookup[String(course.id)] = course
      return lookup
    }, {})
  }, [courses])

  const facultyDepartments = useMemo(() => {
    if (!selectedFacultyId) return departments
    return departments.filter((department) => String(department.faculty_id) === String(selectedFacultyId))
  }, [departments, selectedFacultyId])

  useEffect(() => {
    if (!selectedFacultyId || !selectedDepartmentId) {
      return
    }

    if (!facultyDepartments.some((department) => String(department.id) === String(selectedDepartmentId))) {
      setSelectedDepartmentId(null)
    }
  }, [facultyDepartments, selectedDepartmentId, selectedFacultyId])

  const books = useMemo(
    () => resources.filter((resource) => String(resource.resource_type || '').toUpperCase() === 'BOOK'),
    [resources],
  )

  const filteredBooks = useMemo(() => {
    return books.filter((book) => {
      const course = book.course || coursesById[String(book.course_id)] || null
      let matchesDepartment = true

      if (selectedDepartmentId) {
        matchesDepartment = String(course?.department_id) === String(selectedDepartmentId)
      } else if (selectedFacultyId) {
        const departmentIds = new Set(facultyDepartments.map((department) => String(department.id)))
        matchesDepartment = departmentIds.has(String(course?.department_id))
      }

      const haystack = `${book.title || ''} ${book.description || ''} ${course?.title || ''} ${course?.course_code || ''}`.toLowerCase()
      const matchesSearch = !debouncedSearchTerm || haystack.includes(debouncedSearchTerm)
      return matchesDepartment && matchesSearch
    })
  }, [books, coursesById, debouncedSearchTerm, facultyDepartments, selectedDepartmentId, selectedFacultyId])

  const clearFilters = () => {
    setSelectedFacultyId(null)
    setSelectedDepartmentId(null)
    setSearchTerm('')
  }

  const requestBookEnrollment = async (bookId) => {
    if (!user) return
    try {
      setRequestingId(bookId)
      await sendJson('/course-enrollments/resources', { body: { resource_type: 'BOOK', resource_id: Number(bookId) } })
      const resourcesData = await fetchJson('/course-resources')
      setResources(resourcesData)
    } catch (requestError) {
      setError(requestError.message || 'Unable to request book access.')
    } finally {
      setRequestingId(null)
    }
  }

  return (
    <div className="course-page books-page">
      <header className="course-hero-strip">
        <div className="container course-hero-inner">
          <div className="course-hero-copy">
            <nav className="breadcrumb-line" aria-label="Breadcrumb">
              <Link to="/">Home</Link>
              <span aria-hidden="true">/</span>
              <span>Books</span>
            </nav>
            <h2>Explore books</h2>
            <p>Course books and reading resources from UET Lahore</p>
          </div>

          <form className="course-toolbar" role="search" onSubmit={(event) => event.preventDefault()}>
            <select
              aria-label="Faculty"
              value={selectedFacultyId || ''}
              onChange={(event) => {
                setSelectedFacultyId(event.target.value)
                setSelectedDepartmentId(null)
              }}
            >
              <option value="">All faculties</option>
              {faculties.map((faculty) => (
                <option key={faculty.id} value={faculty.id}>
                  {faculty.name}
                </option>
              ))}
            </select>
            <select
              aria-label="Department"
              value={selectedDepartmentId || ''}
              onChange={(event) => setSelectedDepartmentId(event.target.value)}
            >
              <option value="">All departments</option>
              {facultyDepartments.map((department) => (
                <option key={department.id} value={department.id}>
                  {department.name}
                </option>
              ))}
            </select>
            <label className="visually-hidden" htmlFor="book-search">Search books</label>
            <input
              id="book-search"
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by book or course"
            />
          </form>
        </div>
      </header>

      <main className="container page-block course-results-wrap">
        {error && <div className="alert-box">{error}</div>}

        {loading ? (
          <section className="course-grid" aria-label="Loading books">
            {[1, 2, 3].map((item) => (
              <article key={item} className="course-card skeleton-card" aria-hidden="true">
                <div className="skeleton-media" />
                <div className="course-card-body">
                  <span className="skeleton-line wide" />
                  <span className="skeleton-line" />
                  <span className="skeleton-line short" />
                </div>
              </article>
            ))}
          </section>
        ) : (
          <>
            <section className="course-results-bar" aria-label="Book filters and result count">
              <div className="course-type-pills" role="list" aria-label="Book quick filters">
                <button
                  type="button"
                  className={!selectedFacultyId && !selectedDepartmentId ? 'course-pill active' : 'course-pill'}
                  aria-pressed={!selectedFacultyId && !selectedDepartmentId}
                  onClick={() => {
                    setSelectedFacultyId(null)
                    setSelectedDepartmentId(null)
                  }}
                >
                  All Books
                </button>
                <button
                  type="button"
                  className={selectedFacultyId || selectedDepartmentId ? 'course-pill active' : 'course-pill'}
                  aria-pressed={Boolean(selectedFacultyId || selectedDepartmentId)}
                  onClick={() => {
                    if (!selectedFacultyId && faculties[0]) setSelectedFacultyId(String(faculties[0].id))
                  }}
                >
                  By Faculty
                </button>
              </div>
              <p className="course-result-count" aria-live="polite">
                {filteredBooks.length} {filteredBooks.length === 1 ? 'book' : 'books'}
              </p>
            </section>

            {filteredBooks.length ? (
              <section className="course-grid" aria-label="Books">
                {filteredBooks.map((book) => {
                  const course = book.course || coursesById[String(book.course_id)] || null
                  return (
                    <article key={book.id} className="course-card book-card">
                      <div className="course-card-link">
                        <div className="course-card-media-wrap">
                          <TitleImageFallback
                            className="course-card-media"
                            title={book.title || 'Course Book'}
                            label="Book"
                          />
                          <span className="course-type-badge">BOOK</span>
                        </div>

                        <div className="course-card-body">
                          <h3>{book.title || 'Untitled book'}</h3>
                          <div className="teacher-strip compact">
                            <span className="teacher-avatar">{initials(course?.title || book.title)}</span>
                            <span>{course ? formatCourseTitle(course) : 'Course not specified'}</span>
                          </div>
                          <p className={book.description ? 'course-card-description' : 'course-card-description empty'}>
                            {book.description || 'Book details are available in the course reading catalog.'}
                          </p>
                        </div>

                        <footer className="course-card-footer">
                          <div className="course-card-meta" aria-label="Book facts">
                            <span>{formatFileSize(book.file_size)}</span>
                            {book.external_url && <span>External link</span>}
                          </div>
                          <div className="book-card-actions">
                            {book.can_access_materials && book.file_url && (
                              <>
                                <a href={fileUrl(book.file_url)} target="_blank" rel="noreferrer">View</a>
                                <a href={fileUrl(book.file_url)} download={fileNameFromUrl(book.file_url, book.title)}>Download</a>
                              </>
                            )}
                            {book.can_access_materials && book.external_url && <a href={fileUrl(book.external_url)} target="_blank" rel="noreferrer">Link</a>}
                            {!book.can_access_materials && (
                              user ? (
                                <button type="button" onClick={() => requestBookEnrollment(book.id)} disabled={requestingId === book.id}>
                                  {book.enrollment?.status === 'PENDING' ? 'Awaiting Approval' : ['REJECTED', 'REVOKED'].includes(book.enrollment?.status) ? 'Reapply' : 'Request Enrollment'}
                                </button>
                              ) : (
                                <Link to={`/login?returnTo=${encodeURIComponent('/books')}`}>Login to Request</Link>
                              )
                            )}
                          </div>
                        </footer>
                      </div>
                    </article>
                  )
                })}
              </section>
            ) : (
              <section className="course-empty-state" aria-live="polite">
                <h3>No books match your search</h3>
                <p>Try a different keyword, faculty, or department.</p>
                <button type="button" className="details-button" onClick={clearFilters}>
                  Clear filters
                </button>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  )
}

function formatCourseTitle(course) {
  const title = course.title || 'Untitled course'
  return course.course_code ? `${title} - ${course.course_code}` : title
}

function formatFileSize(size) {
  const bytes = Number(size)
  if (!Number.isFinite(bytes) || bytes <= 0) return 'Book resource'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function initials(name) {
  const value = String(name || '').trim()
  if (!value) return 'BK'
  return value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

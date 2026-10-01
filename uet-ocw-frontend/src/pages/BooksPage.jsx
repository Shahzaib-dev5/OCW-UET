import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import TitleImageFallback from '../components/TitleImageFallback'
import { fetchJson, fileNameFromUrl, fileUrl } from '../data/api'

export default function BooksPage() {
  const [courses, setCourses] = useState([])
  const [resources, setResources] = useState([])
  const [selectedCourseId, setSelectedCourseId] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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

  const books = useMemo(
    () => resources.filter((resource) => String(resource.resource_type || '').toUpperCase() === 'BOOK'),
    [resources],
  )

  const filteredBooks = useMemo(() => {
    return books.filter((book) => {
      const course = book.course || coursesById[String(book.course_id)] || null
      const matchesCourse = !selectedCourseId || String(book.course_id) === String(selectedCourseId)
      const haystack = `${book.title || ''} ${book.description || ''} ${course?.title || ''} ${course?.course_code || ''}`.toLowerCase()
      const matchesSearch = !debouncedSearchTerm || haystack.includes(debouncedSearchTerm)
      return matchesCourse && matchesSearch
    })
  }, [books, coursesById, debouncedSearchTerm, selectedCourseId])

  const clearFilters = () => {
    setSelectedCourseId('')
    setSearchTerm('')
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
            <label className="visually-hidden" htmlFor="book-search">Search books</label>
            <input
              id="book-search"
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by book or course"
            />
            <select
              aria-label="Course"
              value={selectedCourseId}
              onChange={(event) => setSelectedCourseId(event.target.value)}
            >
              <option value="">All courses</option>
              {courses.map((course) => (
                <option key={course.id} value={course.id}>
                  {formatCourseTitle(course)}
                </option>
              ))}
            </select>
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
                  className={!selectedCourseId ? 'course-pill active' : 'course-pill'}
                  aria-pressed={!selectedCourseId}
                  onClick={() => setSelectedCourseId('')}
                >
                  All Books
                </button>
                <button
                  type="button"
                  className={selectedCourseId ? 'course-pill active' : 'course-pill'}
                  aria-pressed={Boolean(selectedCourseId)}
                  onClick={() => {
                    if (!selectedCourseId && courses[0]) setSelectedCourseId(String(courses[0].id))
                  }}
                >
                  By Course
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
                            {book.file_url && (
                              <>
                                <a href={fileUrl(book.file_url)} target="_blank" rel="noreferrer">View</a>
                                <a href={fileUrl(book.file_url)} download={fileNameFromUrl(book.file_url, book.title)}>Download</a>
                              </>
                            )}
                            {book.external_url && <a href={fileUrl(book.external_url)} target="_blank" rel="noreferrer">Link</a>}
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
                <p>Try a different keyword or course filter.</p>
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

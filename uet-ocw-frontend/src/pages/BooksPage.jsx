import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import TitleImageFallback from '../components/TitleImageFallback'
import { deleteJson, fetchJson, fileNameFromUrl, fileUrl, sendJson, uploadFile } from '../data/api'

export default function BooksPage() {
  const { user, isInstructorMode, isAdmin } = useAuth()
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
  const [savingBook, setSavingBook] = useState(false)
  const [deletingBookId, setDeletingBookId] = useState(null)
  const [isBookFormOpen, setIsBookFormOpen] = useState(false)
  const [editingBookId, setEditingBookId] = useState(null)
  const [bookFile, setBookFile] = useState(null)
  const [bookThumbnailFile, setBookThumbnailFile] = useState(null)
  const [bookFileInputKey, setBookFileInputKey] = useState(0)
  const [bookThumbnailInputKey, setBookThumbnailInputKey] = useState(0)
  const [bookForm, setBookForm] = useState({
    is_generic: false,
    faculty_id: '',
    department_id: '',
    course_id: '',
    title: '',
    description: '',
    thumbnail: '',
    external_url: '',
  })

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

  const manageableCourses = useMemo(
    () => courses.filter((course) => course.can_manage),
    [courses],
  )

  const canManageBooks = isInstructorMode || isAdmin

  const formDepartments = useMemo(() => {
    if (!bookForm.faculty_id) return departments
    return departments.filter((department) => String(department.faculty_id) === String(bookForm.faculty_id))
  }, [bookForm.faculty_id, departments])

  const formCourses = useMemo(() => {
    return manageableCourses.filter((course) => {
      if (bookForm.department_id) return String(course.department_id) === String(bookForm.department_id)
      if (bookForm.faculty_id) {
        const departmentIds = new Set(formDepartments.map((department) => String(department.id)))
        return departmentIds.has(String(course.department_id))
      }
      return true
    })
  }, [bookForm.department_id, bookForm.faculty_id, formDepartments, manageableCourses])

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

  const reloadBooks = async () => {
    const resourcesData = await fetchJson('/course-resources')
    setResources(resourcesData)
  }

  const resetBookForm = () => {
    setBookForm({
      is_generic: false,
      faculty_id: '',
      department_id: '',
      course_id: '',
      title: '',
      description: '',
      thumbnail: '',
      external_url: '',
    })
    setBookFile(null)
    setBookThumbnailFile(null)
    setEditingBookId(null)
    setBookFileInputKey((current) => current + 1)
    setBookThumbnailInputKey((current) => current + 1)
  }

  const openAddBookForm = () => {
    resetBookForm()
    setIsBookFormOpen(true)
  }

  const openEditBookForm = (book) => {
    const course = book.course || coursesById[String(book.course_id)] || null
    const department = departments.find((item) => String(item.id) === String(course?.department_id))
    setEditingBookId(book.id)
    setBookForm({
      is_generic: !book.course_id,
      faculty_id: department?.faculty_id ? String(department.faculty_id) : '',
      department_id: course?.department_id ? String(course.department_id) : '',
      course_id: book.course_id ? String(book.course_id) : '',
      title: book.title || '',
      description: book.description || '',
      thumbnail: book.thumbnail || '',
      external_url: book.external_url || '',
    })
    setBookFile(null)
    setBookThumbnailFile(null)
    setBookFileInputKey((current) => current + 1)
    setBookThumbnailInputKey((current) => current + 1)
    setIsBookFormOpen(true)
  }

  const closeBookForm = () => {
    setIsBookFormOpen(false)
    resetBookForm()
  }

  const submitBook = async (event) => {
    event.preventDefault()
    const isEditingBook = Boolean(editingBookId)
    try {
      setSavingBook(true)
      setError('')
      let fileUrlValue = ''
      let fileSize = null
      let mimeType = ''
      let thumbnailValue = bookForm.thumbnail.trim()
      const bookFolder = bookForm.is_generic ? 'books/resources' : `courses/${bookForm.course_id}/books`
      if (bookFile) {
        const uploaded = await uploadFile({ file: bookFile, folder: bookFolder })
        fileUrlValue = uploaded.local_url || uploaded.public_url || uploaded.relative_path || ''
        fileSize = uploaded.size || bookFile.size || null
        mimeType = uploaded.mime_type || bookFile.type || ''
      }
      if (bookThumbnailFile) {
        const uploaded = await uploadFile({ file: bookThumbnailFile, folder: 'books/thumbnails' })
        thumbnailValue = uploaded.local_url || uploaded.public_url || uploaded.relative_path || thumbnailValue
      }

      const selectedCourse = coursesById[String(bookForm.course_id)]
      await sendJson(isEditingBook ? `/course-resources/${editingBookId}` : '/course-resources', {
        method: isEditingBook ? 'PATCH' : 'POST',
        body: {
          course_id: bookForm.is_generic ? null : Number(bookForm.course_id),
          title: bookForm.title,
          resource_type: 'BOOK',
          description: bookForm.description || null,
          thumbnail: thumbnailValue || null,
          external_url: bookForm.external_url || null,
          ...(bookFile ? {
            file_url: fileUrlValue || null,
            file_size: fileSize,
            mime_type: mimeType || null,
          } : {}),
          access_level: selectedCourse?.access_level || 'PUBLIC',
          is_active: true,
        },
      })
      closeBookForm()
      await reloadBooks()
    } catch (saveError) {
      setError(saveError.message || 'Unable to save book.')
    } finally {
      setSavingBook(false)
    }
  }

  const requestBookEnrollment = async (bookId) => {
    if (!user) return
    try {
      setRequestingId(bookId)
      await sendJson('/course-enrollments/resources', { body: { resource_type: 'BOOK', resource_id: Number(bookId) } })
      await reloadBooks()
    } catch (requestError) {
      setError(requestError.message || 'Unable to request book access.')
    } finally {
      setRequestingId(null)
    }
  }

  const deleteBook = async (book) => {
    if (!window.confirm(`Delete "${book.title || 'this book'}"?`)) return
    try {
      setDeletingBookId(book.id)
      setError('')
      await deleteJson(`/course-resources/${book.id}`)
      await reloadBooks()
    } catch (deleteError) {
      setError(deleteError.message || 'Unable to delete book.')
    } finally {
      setDeletingBookId(null)
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
        {canManageBooks && isBookFormOpen && (
          <BookFormDialog
            editing={Boolean(editingBookId)}
            bookForm={bookForm}
            setBookForm={setBookForm}
            faculties={faculties}
            departments={formDepartments}
            courses={formCourses}
            bookFileInputKey={bookFileInputKey}
            bookThumbnailInputKey={bookThumbnailInputKey}
            setBookFile={setBookFile}
            setBookThumbnailFile={setBookThumbnailFile}
            saving={savingBook}
            onSubmit={submitBook}
            onClose={closeBookForm}
          />
        )}

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
              <div className="books-result-actions">
                <p className="course-result-count" aria-live="polite">
                  {filteredBooks.length} {filteredBooks.length === 1 ? 'book' : 'books'}
                </p>
                {canManageBooks && (
                  <button
                    type="button"
                    className="lecture-add-button"
                    aria-label="Add book"
                    onClick={openAddBookForm}
                  >
                    <PlusIcon />
                  </button>
                )}
              </div>
            </section>

            {filteredBooks.length ? (
              <section className="course-grid" aria-label="Books">
                {filteredBooks.map((book) => {
                  const course = book.course || coursesById[String(book.course_id)] || null
                  const canEditBook = Boolean(book.can_manage)
                  return (
                    <article key={book.id} className="course-card book-card">
                      <div className="course-card-link">
                        <div className="course-card-media-wrap">
                          {canEditBook && (
                            <div className="book-card-controls">
                              <button
                                type="button"
                                className="lecture-edit-button book-edit-button"
                                aria-label={`Edit ${book.title || 'book'}`}
                                onClick={() => openEditBookForm(book)}
                              >
                                <EditIcon />
                              </button>
                              <button
                                type="button"
                                className="lecture-delete-button book-delete-button"
                                aria-label={`Delete ${book.title || 'book'}`}
                                disabled={deletingBookId === book.id}
                                onClick={() => deleteBook(book)}
                              >
                                <TrashIcon />
                              </button>
                            </div>
                          )}
                          <TitleImageFallback
                            className="course-card-media"
                            src={book.thumbnail ? fileUrl(book.thumbnail) : ''}
                            alt={`${book.title || 'Course Book'} thumbnail`}
                            title={book.title || 'Course Book'}
                            label="Book"
                          />
                          <span className="course-type-badge">BOOK</span>
                        </div>

                        <div className="course-card-body">
                          <h3>{book.title || 'Untitled book'}</h3>
                          <div className="teacher-strip compact">
                            <span className="teacher-avatar">{initials(course?.title || book.title)}</span>
                            <span>{course ? formatCourseTitle(course) : 'Generic book'}</span>
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

function BookFormDialog({
  editing,
  bookForm,
  setBookForm,
  faculties,
  departments,
  courses,
  bookFileInputKey,
  bookThumbnailInputKey,
  setBookFile,
  setBookThumbnailFile,
  saving,
  onSubmit,
  onClose,
}) {
  return (
    <div className="lecture-dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="lecture-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="book-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="lecture-dialog-header">
          <h3 id="book-dialog-title">{editing ? 'Edit book' : 'Add book'}</h3>
          <button type="button" className="dialog-close-button" aria-label="Close book form" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>
        <form className="instructor-upload-form lecture-dialog-form" onSubmit={onSubmit}>
          <label className="wide checkbox-field">
            <input
              type="checkbox"
              checked={bookForm.is_generic}
              onChange={(event) => setBookForm({ ...bookForm, is_generic: event.target.checked, faculty_id: '', department_id: '', course_id: '' })}
            />
            Generic book
          </label>
          <label>
            Faculty
            <select
              value={bookForm.faculty_id}
              onChange={(event) => setBookForm({ ...bookForm, faculty_id: event.target.value, department_id: '', course_id: '' })}
              disabled={bookForm.is_generic}
            >
              <option value="">All faculties</option>
              {faculties.map((faculty) => (
                <option key={faculty.id} value={faculty.id}>{faculty.name}</option>
              ))}
            </select>
          </label>
          <label>
            Department
            <select
              value={bookForm.department_id}
              onChange={(event) => setBookForm({ ...bookForm, department_id: event.target.value, course_id: '' })}
              disabled={bookForm.is_generic}
            >
              <option value="">All departments</option>
              {departments.map((department) => (
                <option key={department.id} value={department.id}>{department.name}</option>
              ))}
            </select>
          </label>
          <label>
            Course
            <select
              value={bookForm.course_id}
              onChange={(event) => setBookForm({ ...bookForm, course_id: event.target.value })}
              disabled={bookForm.is_generic}
              required={!bookForm.is_generic}
            >
              <option value="">Select course</option>
              {courses.map((course) => (
                <option key={course.id} value={course.id}>{formatCourseTitle(course)}</option>
              ))}
            </select>
          </label>
          <label>
            Title
            <input value={bookForm.title} onChange={(event) => setBookForm({ ...bookForm, title: event.target.value })} required />
          </label>
          <label className="wide">
            Description
            <textarea value={bookForm.description} onChange={(event) => setBookForm({ ...bookForm, description: event.target.value })} />
          </label>
          <label>
            Thumbnail image
            <input key={bookThumbnailInputKey} type="file" accept="image/*" onChange={(event) => setBookThumbnailFile(event.target.files?.[0] || null)} />
          </label>
          <label>
            Thumbnail URL
            <input value={bookForm.thumbnail} onChange={(event) => setBookForm({ ...bookForm, thumbnail: event.target.value })} />
          </label>
          <label>
            File
            <input key={bookFileInputKey} type="file" onChange={(event) => setBookFile(event.target.files?.[0] || null)} />
          </label>
          <label>
            External link
            <input value={bookForm.external_url} onChange={(event) => setBookForm({ ...bookForm, external_url: event.target.value })} />
          </label>
          <div className="lecture-dialog-actions wide">
            <button className="primary-button auth-submit" disabled={saving}>{saving ? 'Saving...' : editing ? 'Update Book' : 'Upload Book'}</button>
            <button type="button" className="secondary-action-button" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </section>
    </div>
  )
}

function PlusIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
      <path d="M8 3v10M3 8h10" />
    </svg>
  )
}

function EditIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
      <path d="M3 11.5V13h1.5l7.1-7.1-1.5-1.5L3 11.5zM10.8 3.7l1.5 1.5.7-.7a1.05 1.05 0 0 0-1.5-1.5z" />
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
      <path d="M4.5 4.5 11.5 11.5M11.5 4.5 4.5 11.5" />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
      <path d="M3 4.5h10M6 4.5V3h4v1.5M5 6v6.5h6V6M7 7.5v3.5M9 7.5v3.5" />
    </svg>
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

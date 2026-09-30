import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchJson, fileUrl } from '../data/api'

export default function CoursePage() {
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [courses, setCourses] = useState([])
  const [lectureCounts, setLectureCounts] = useState({})
  const [selectedFacultyId, setSelectedFacultyId] = useState(null)
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null)
  const [selectedType, setSelectedType] = useState('All')
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        setError('')
        const [facultiesData, departmentsData, coursesData, lecturesData] = await Promise.all([
          fetchJson('/faculties'),
          fetchJson('/departments'),
          fetchJson('/courses'),
          fetchJson('/lectures'),
        ])

        setFaculties(facultiesData)
        setDepartments(departmentsData)
        setCourses(coursesData)
        setLectureCounts(countLecturesByCourse(lecturesData))

      } catch (loadError) {
        setError(loadError.message || 'Unable to load course information.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearchTerm(searchTerm.trim().toLowerCase())
    }, 200)

    return () => window.clearTimeout(timer)
  }, [searchTerm])

  const facultyDepartments = useMemo(() => {
    if (!selectedFacultyId) return departments
    return departments.filter((department) => String(department.faculty_id) === String(selectedFacultyId))
  }, [departments, selectedFacultyId])

  useEffect(() => {
    if (!selectedFacultyId || !facultyDepartments.length) {
      setSelectedDepartmentId(null)
      return
    }

    if (!facultyDepartments.some((department) => String(department.id) === String(selectedDepartmentId))) {
      setSelectedDepartmentId(null)
    }
  }, [facultyDepartments, selectedDepartmentId, selectedFacultyId])

  const availableTypes = useMemo(() => {
    const values = courses.map(getCourseType).filter(Boolean)
    return ['All', ...sortCourseTypes([...new Set(values)])]
  }, [courses])

  const activeType = availableTypes.includes(selectedType) ? selectedType : 'All'

  const filteredCourses = useMemo(() => {
    let visibleCourses = courses

    if (selectedDepartmentId) {
      visibleCourses = visibleCourses.filter((course) => String(course.department_id) === String(selectedDepartmentId))
    } else if (selectedFacultyId) {
      const departmentIds = new Set(facultyDepartments.map((department) => String(department.id)))
      visibleCourses = visibleCourses.filter((course) => departmentIds.has(String(course.department_id)))
    }

    if (activeType !== 'All') {
      visibleCourses = visibleCourses.filter((course) => getCourseType(course) === activeType)
    }

    if (debouncedSearchTerm) {
      visibleCourses = visibleCourses.filter((course) => {
        const haystack = `${course.title || ''} ${course.course_code || ''} ${course.instructor_name || ''}`.toLowerCase()
        return haystack.includes(debouncedSearchTerm)
      })
    }

    return visibleCourses
  }, [activeType, courses, debouncedSearchTerm, facultyDepartments, selectedDepartmentId, selectedFacultyId])

  const clearFilters = () => {
    setSelectedFacultyId(null)
    setSelectedDepartmentId(null)
    setSelectedType('All')
    setSearchTerm('')
  }

  return (
    <div className="course-page">
      <header className="course-hero-strip">
        <div className="container course-hero-inner">
          <div className="course-hero-copy">
            <nav className="breadcrumb-line" aria-label="Breadcrumb">
              <Link to="/">Home</Link>
              <span aria-hidden="true">/</span>
              <span>Hybrid Courses</span>
            </nav>
            <h2>Explore courses</h2>
            <p>Free lectures, notes, and resources from UET Lahore</p>
          </div>

          <form className="course-toolbar" role="search" onSubmit={(event) => event.preventDefault()}>
            <label className="visually-hidden" htmlFor="course-search">Search courses</label>
            <input
              id="course-search"
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by course or instructor"
            />
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
              onChange={(event) => {
                setSelectedDepartmentId(event.target.value)
              }}
            >
              <option value="">All departments</option>
              {facultyDepartments.map((department) => (
                <option key={department.id} value={department.id}>
                  {department.name}
                </option>
              ))}
            </select>
          </form>
        </div>
      </header>

      <main className="container page-block course-results-wrap">
        {error && <div className="alert-box">{error}</div>}

        {loading ? (
          <section className="course-grid" aria-label="Loading courses">
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
            <section className="course-results-bar" aria-label="Course filters and result count">
              <div className="course-type-pills" role="list" aria-label="Course type filters">
                {availableTypes.map((type) => (
                  <button
                    key={type}
                    type="button"
                    className={activeType === type ? 'course-pill active' : 'course-pill'}
                    aria-pressed={activeType === type}
                    onClick={() => setSelectedType(type)}
                  >
                    {type}
                  </button>
                ))}
              </div>
              <p className="course-result-count" aria-live="polite">
                {filteredCourses.length} {filteredCourses.length === 1 ? 'course' : 'courses'}
              </p>
            </section>

            {filteredCourses.length ? (
              <section className="course-grid" aria-label="Courses">
                {filteredCourses.map((course) => (
                  <article key={course.id} className="course-card">
                    <Link className="course-card-link" to={`/courses/${course.id}`} aria-label={`View ${formatCourseTitle(course)}`}>
                      <div className="course-card-media-wrap">
                        {course.thumbnail ? (
                          <img
                            className="course-card-media"
                            src={fileUrl(course.thumbnail)}
                            alt={`${formatCourseTitle(course)} course thumbnail`}
                            loading="lazy"
                          />
                        ) : (
                          <div className="course-card-media placeholder" aria-hidden="true">
                            <span>OCW</span>
                          </div>
                        )}
                        <span className="course-type-badge">{getCourseType(course)}</span>
                      </div>

                      <div className="course-card-body">
                        <h3>{formatCourseTitle(course)}</h3>
                        <div className={course.instructor_name ? 'teacher-strip compact' : 'teacher-strip compact missing'}>
                          <span className="teacher-avatar">{initials(course.instructor_name)}</span>
                          <span>{course.instructor_name || 'Instructor not specified'}</span>
                        </div>
                        <p className={getCourseDescription(course) ? 'course-card-description' : 'course-card-description empty'}>
                          {getCourseDescription(course) || 'No description available'}
                        </p>
                      </div>

                      <footer className="course-card-footer">
                        <div className="course-card-meta" aria-label="Course facts">
                          <span className={lectureCounts[course.id] ? '' : 'muted-meta'}>{formatLectureCount(lectureCounts[course.id])}</span>
                          {(course.credit_hours || course.credits) && (
                            <span>{formatCreditHours(course.credit_hours || course.credits)}</span>
                          )}
                        </div>
                        <span className="course-view-link">
                          View course
                          <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
                            <path d="M6 3.5 10.5 8 6 12.5" />
                          </svg>
                        </span>
                      </footer>
                    </Link>
                  </article>
                ))}
              </section>
            ) : (
              <section className="course-empty-state" aria-live="polite">
                <h3>No courses match your search</h3>
                <p>Try a different keyword, faculty, department, or course type.</p>
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

function countLecturesByCourse(lectures) {
  return lectures.reduce((counts, lecture) => {
    counts[lecture.course_id] = (counts[lecture.course_id] || 0) + 1
    return counts
  }, {})
}

function sortCourseTypes(types) {
  const preferredOrder = ['Hybrid', 'Bootcamp', 'Bootcamps', 'Semester']
  return types.sort((left, right) => {
    const leftOrder = preferredOrder.indexOf(left)
    const rightOrder = preferredOrder.indexOf(right)
    if (leftOrder !== -1 || rightOrder !== -1) {
      return (leftOrder === -1 ? Number.MAX_SAFE_INTEGER : leftOrder) - (rightOrder === -1 ? Number.MAX_SAFE_INTEGER : rightOrder)
    }
    return left.localeCompare(right)
  })
}

function getCourseType(course) {
  const rawType = course.course_type || course.category || (course.semester ? 'Semester' : 'Hybrid')
  return titleCaseType(rawType)
}

function titleCaseType(value) {
  return String(value || 'Hybrid')
    .trim()
    .replace(/[_-]+/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatCreditHours(value) {
  const count = Number(value)
  if (!Number.isFinite(count)) return `${value} CH`
  return `${count} CH`
}

function formatCourseTitle(course) {
  const title = course.title || 'Untitled course'
  return course.course_code ? `${title} - ${course.course_code}` : title
}

function formatLectureCount(count = 0) {
  if (!count) return 'No lectures yet'
  return `${count} ${count === 1 ? 'lecture' : 'lectures'}`
}

function getCourseDescription(course) {
  const description = String(course.short_description || course.description || '').trim()
  if (!description || description === 'Course details are available in the backend data.') return ''
  return description
}

function initials(name) {
  const value = String(name || '').trim()
  if (!value) return 'IN'
  return value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

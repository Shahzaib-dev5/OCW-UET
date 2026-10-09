import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchJson } from '../data/api'

export default function InvitedTalkPage() {
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [talks, setTalks] = useState([])
  const [selectedFacultyId, setSelectedFacultyId] = useState(null)
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        setError('')
        const [facultiesData, departmentsData, talksData] = await Promise.all([
          fetchJson('/faculties'),
          fetchJson('/departments'),
          fetchJson('/invited-talks'),
        ])

        setFaculties(facultiesData)
        setDepartments(departmentsData)
        setTalks(talksData)
      } catch (loadError) {
        setError(loadError.message || 'Unable to load tech talks.')
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
    if (!selectedFacultyId || !selectedDepartmentId) {
      return
    }

    if (!facultyDepartments.some((department) => String(department.id) === String(selectedDepartmentId))) {
      setSelectedDepartmentId(null)
    }
  }, [facultyDepartments, selectedDepartmentId, selectedFacultyId])

  const filteredTalks = useMemo(() => {
    let visibleTalks = talks

    if (selectedDepartmentId) {
      visibleTalks = visibleTalks.filter((talk) => String(talk.department_id) === String(selectedDepartmentId))
    } else if (selectedFacultyId) {
      const departmentIds = new Set(facultyDepartments.map((department) => String(department.id)))
      visibleTalks = visibleTalks.filter((talk) => departmentIds.has(String(talk.department_id)))
    }

    if (debouncedSearchTerm) {
      visibleTalks = visibleTalks.filter((talk) => {
        const haystack = `${talk.talk_title || ''} ${talk.event_title || ''} ${talk.presenter || ''} ${talk.publication || ''}`.toLowerCase()
        return haystack.includes(debouncedSearchTerm)
      })
    }

    return visibleTalks
  }, [debouncedSearchTerm, facultyDepartments, selectedDepartmentId, selectedFacultyId, talks])

  const clearFilters = () => {
    setSelectedFacultyId(null)
    setSelectedDepartmentId(null)
    setSearchTerm('')
  }

  return (
    <div className="course-page invited-talks-page">
      <header className="course-hero-strip">
        <div className="container course-hero-inner">
          <div className="course-hero-copy">
            <nav className="breadcrumb-line" aria-label="Breadcrumb">
              <Link to="/">Home</Link>
              <span aria-hidden="true">/</span>
              <span>Tech Talks</span>
            </nav>
            <h2>Tech talks</h2>
            <p>Department seminars, guest lectures, recordings, and publications</p>
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
            <label className="visually-hidden" htmlFor="talk-search">Search tech talks</label>
            <input
              id="talk-search"
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by talk, event, or presenter"
            />
          </form>
        </div>
      </header>

      <main className="container page-block course-results-wrap">
        {error && <div className="alert-box">{error}</div>}

        {loading ? (
          <section className="course-grid" aria-label="Loading tech talks">
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
            <section className="course-results-bar" aria-label="Tech talk result count">
              <p className="course-result-count" aria-live="polite">
                {filteredTalks.length} {filteredTalks.length === 1 ? 'talk' : 'talks'}
              </p>
            </section>

            {filteredTalks.length ? (
              <section className="course-grid" aria-label="Tech talks">
                {filteredTalks.map((talk) => (
                  <article key={talk.id} className="course-card research-card">
                    <Link className="course-card-link" to={`/invited-talks/${talk.id}`} aria-label={`View ${talk.talk_title || 'tech talk'}`}>
                      <div className="course-card-media-wrap">
                        <div className="course-card-media placeholder research-card-media" aria-hidden="true">
                          <span>Talk</span>
                        </div>
                        <span className="course-type-badge">{talk.department?.short_name || talk.department?.name || 'UET'}</span>
                      </div>

                      <div className="course-card-body">
                        <h3>{talk.talk_title || 'Untitled talk'}</h3>
                        <div className={talk.presenter ? 'teacher-strip compact' : 'teacher-strip compact missing'}>
                          <span className="teacher-avatar">{initials(talk.presenter)}</span>
                          <span>{talk.presenter || 'Presenter not specified'}</span>
                        </div>
                        <p className={talk.event_title || talk.publication ? 'course-card-description' : 'course-card-description empty'}>
                          {talk.event_title || talk.publication || 'No event details available'}
                        </p>
                      </div>

                      <footer className="course-card-footer">
                        <div className="course-card-meta" aria-label="Tech talk facts">
                          <span>{formatDate(talk.talk_date)}</span>
                          {talk.video_url && <span>Video</span>}
                          {talk.upload_url && <span>Upload</span>}
                        </div>
                        <span className="course-view-link">
                          View talk
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
                <h3>No tech talks match your search</h3>
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

function formatDate(value) {
  if (!value) return 'Date not set'
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

function initials(name) {
  const value = String(name || '').trim()
  if (!value) return 'PR'
  return value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

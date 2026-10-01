import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchJson, fileUrl } from '../data/api'

export default function InternshipPage() {
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [programs, setPrograms] = useState([])
  const [resources, setResources] = useState([])
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
        const [facultiesData, departmentsData, programsData, resourcesData] = await Promise.all([
          fetchJson('/faculties'),
          fetchJson('/departments'),
          fetchJson('/skills-development'),
          fetchJson('/skills-development-resources'),
        ])

        setFaculties(facultiesData)
        setDepartments(departmentsData)
        setPrograms(programsData)
        setResources(resourcesData)
      } catch (loadError) {
        setError(loadError.message || 'Unable to load skills development information.')
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
    const values = programs.map(getProgramType).filter(Boolean)
    return ['All', ...sortProgramTypes([...new Set(values)])]
  }, [programs])

  const activeType = availableTypes.includes(selectedType) ? selectedType : 'All'

  const resourceCounts = useMemo(() => countResourcesByProgram(resources), [resources])

  const filteredPrograms = useMemo(() => {
    let visiblePrograms = programs

    if (selectedDepartmentId) {
      visiblePrograms = visiblePrograms.filter((program) => String(program.department_id) === String(selectedDepartmentId))
    } else if (selectedFacultyId) {
      const departmentIds = new Set(facultyDepartments.map((department) => String(department.id)))
      visiblePrograms = visiblePrograms.filter((program) => departmentIds.has(String(program.department_id)))
    }

    if (activeType !== 'All') {
      visiblePrograms = visiblePrograms.filter((program) => getProgramType(program) === activeType)
    }

    if (debouncedSearchTerm) {
      visiblePrograms = visiblePrograms.filter((program) => {
        const haystack = `${program.title || ''} ${program.description || ''} ${program.category || ''} ${program.duration || ''}`.toLowerCase()
        return haystack.includes(debouncedSearchTerm)
      })
    }

    return visiblePrograms
  }, [activeType, debouncedSearchTerm, facultyDepartments, programs, selectedDepartmentId, selectedFacultyId])

  const clearFilters = () => {
    setSelectedFacultyId(null)
    setSelectedDepartmentId(null)
    setSelectedType('All')
    setSearchTerm('')
  }

  return (
    <div className="course-page skills-development-page">
      <header className="course-hero-strip">
        <div className="container course-hero-inner">
          <div className="course-hero-copy">
            <nav className="breadcrumb-line" aria-label="Breadcrumb">
              <Link to="/">Home</Link>
              <span aria-hidden="true">/</span>
              <span>Skills Development</span>
            </nav>
            <h2>Explore skills development</h2>
            <p>Practical programs, files, and career-focused learning resources from UET Lahore</p>
          </div>

          <form className="course-toolbar" role="search" onSubmit={(event) => event.preventDefault()}>
            <label className="visually-hidden" htmlFor="skills-search">Search skills development programs</label>
            <input
              id="skills-search"
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by title, category, or duration"
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
              onChange={(event) => setSelectedDepartmentId(event.target.value)}
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
          <section className="course-grid" aria-label="Loading skills development programs">
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
            <section className="course-results-bar" aria-label="Skills development filters and result count">
              <div className="course-type-pills" role="list" aria-label="Skills development type filters">
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
                {filteredPrograms.length} {filteredPrograms.length === 1 ? 'program' : 'programs'}
              </p>
            </section>

            {filteredPrograms.length ? (
              <section className="course-grid" aria-label="Skills development programs">
                {filteredPrograms.map((program) => (
                  <article key={program.id} className="course-card">
                    <Link className="course-card-link" to={`/skills-development/${program.id}`} aria-label={`View ${program.title || 'skills development program'}`}>
                      <div className="course-card-media-wrap">
                        {program.thumbnail ? (
                          <img
                            className="course-card-media"
                            src={fileUrl(program.thumbnail)}
                            alt={`${program.title || 'Skills development'} program thumbnail`}
                            loading="lazy"
                          />
                        ) : (
                          <div className="course-card-media placeholder" aria-hidden="true">
                            <span>SD</span>
                          </div>
                        )}
                        <span className="course-type-badge">{getProgramType(program)}</span>
                      </div>

                      <div className="course-card-body">
                        <h3>{program.title || 'Untitled skills development program'}</h3>
                        <div className="teacher-strip compact">
                          <span className="teacher-avatar">{initials(program.category || program.title)}</span>
                          <span>{program.category || 'Skills development'}</span>
                        </div>
                      </div>

                      <footer className="course-card-footer">
                        <div className="course-card-meta" aria-label="Skills development facts">
                          <span>{formatResourceCount(resourceCounts[program.id])}</span>
                          {program.duration && <span>{program.duration}</span>}
                          <span>{program.status || 'Open'}</span>
                        </div>
                        <span className="course-view-link">
                          View program
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
                <h3>No skills development programs match your search</h3>
                <p>Try a different keyword, faculty, department, or program type.</p>
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

function countResourcesByProgram(resources) {
  return resources.reduce((counts, resource) => {
    counts[resource.internship_id] = (counts[resource.internship_id] || 0) + 1
    return counts
  }, {})
}

function sortProgramTypes(types) {
  return types.sort((left, right) => {
    if (left === 'Skills Development') return -1
    if (right === 'Skills Development') return 1
    return left.localeCompare(right)
  })
}

function getProgramType(program) {
  return titleCaseType(program.category || 'Skills Development')
}

function formatResourceCount(count = 0) {
  if (!count) return 'No resources yet'
  return `${count} ${count === 1 ? 'resource' : 'resources'}`
}

function titleCaseType(value) {
  return String(value || '')
    .trim()
    .replace(/[_-]+/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function initials(name) {
  const value = String(name || '').trim()
  if (!value) return 'SD'
  return value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

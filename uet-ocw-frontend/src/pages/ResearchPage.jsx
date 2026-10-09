import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchJson } from '../data/api'

export default function ResearchPage() {
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [researchPapers, setResearchPapers] = useState([])
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
        const [facultiesData, departmentsData, researchPapersData] = await Promise.all([
          fetchJson('/faculties'),
          fetchJson('/departments'),
          fetchJson('/research-papers'),
        ])

        setFaculties(facultiesData)
        setDepartments(departmentsData)
        setResearchPapers(researchPapersData)
      } catch (loadError) {
        setError(loadError.message || 'Unable to load research papers.')
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

  const availableTypes = useMemo(() => {
    const values = researchPapers.map(getPaperType).filter(Boolean)
    return ['All', ...sortPaperTypes([...new Set(values)])]
  }, [researchPapers])

  const activeType = availableTypes.includes(selectedType) ? selectedType : 'All'

  const filteredPapers = useMemo(() => {
    let visiblePapers = researchPapers

    if (selectedDepartmentId) {
      visiblePapers = visiblePapers.filter((paper) => String(paper.department_id) === String(selectedDepartmentId))
    } else if (selectedFacultyId) {
      const departmentIds = new Set(facultyDepartments.map((department) => String(department.id)))
      visiblePapers = visiblePapers.filter((paper) => departmentIds.has(String(paper.department_id)))
    }

    if (activeType !== 'All') {
      visiblePapers = visiblePapers.filter((paper) => getPaperType(paper) === activeType)
    }

    if (debouncedSearchTerm) {
      visiblePapers = visiblePapers.filter((paper) => {
        const haystack = `${paper.title || ''} ${paper.authors || ''} ${paper.journal_name || ''} ${paper.conference_name || ''}`.toLowerCase()
        return haystack.includes(debouncedSearchTerm)
      })
    }

    return visiblePapers
  }, [activeType, debouncedSearchTerm, facultyDepartments, researchPapers, selectedDepartmentId, selectedFacultyId])

  const clearFilters = () => {
    setSelectedFacultyId(null)
    setSelectedDepartmentId(null)
    setSelectedType('All')
    setSearchTerm('')
  }

  return (
    <div className="research-page">
      <header className="course-hero-strip">
        <div className="container course-hero-inner">
          <div className="course-hero-copy">
            <nav className="breadcrumb-line" aria-label="Breadcrumb">
              <Link to="/">Home</Link>
              <span aria-hidden="true">/</span>
              <span>Research</span>
            </nav>
            <h2>Explore research</h2>
            <p>Publications, papers, and academic work from UET Lahore</p>
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
                <option key={faculty.id} value={faculty.id}>{faculty.name}</option>
              ))}
            </select>
            <select
              aria-label="Department"
              value={selectedDepartmentId || ''}
              onChange={(event) => setSelectedDepartmentId(event.target.value)}
            >
              <option value="">All departments</option>
              {facultyDepartments.map((department) => (
                <option key={department.id} value={department.id}>{department.name}</option>
              ))}
            </select>
            <label className="visually-hidden" htmlFor="research-search">Search research papers</label>
            <input
              id="research-search"
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by title, author, or venue"
            />
          </form>
        </div>
      </header>

      <main className="container page-block course-results-wrap">
        {error && <div className="alert-box">{error}</div>}

        {loading ? (
          <section className="course-grid" aria-label="Loading research papers">
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
            <section className="course-results-bar" aria-label="Research filters and result count">
              <div className="course-type-pills" role="list" aria-label="Publication type filters">
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
                {filteredPapers.length} {filteredPapers.length === 1 ? 'paper' : 'papers'}
              </p>
            </section>

            {filteredPapers.length ? (
              <section className="course-grid" aria-label="Research papers">
                {filteredPapers.map((paper) => (
                  <article key={paper.id} className="course-card research-card">
                    <Link className="course-card-link" to={`/research/${paper.id}`} aria-label={`Read ${paper.title || 'research paper'}`}>
                      <div className="course-card-media-wrap">
                        <div className="course-card-media placeholder research-card-media" aria-hidden="true">
                          <span>{paper.title?.slice(0, 2).toUpperCase() || 'RP'}</span>
                        </div>
                        <span className="course-type-badge">{getPaperType(paper)}</span>
                      </div>

                      <div className="course-card-body">
                        <h3>{paper.title || 'Untitled research paper'}</h3>
                        <div className={paper.authors ? 'teacher-strip compact' : 'teacher-strip compact missing'}>
                          <span className="teacher-avatar">{initials(paper.authors || paper.title)}</span>
                          <span>{paper.authors || 'Authors not specified'}</span>
                        </div>
                        <p className={getPaperSummary(paper) ? 'course-card-description' : 'course-card-description empty'}>
                          {getPaperSummary(paper) || 'No abstract available'}
                        </p>
                      </div>

                      <footer className="course-card-footer">
                        <div className="course-card-meta" aria-label="Research paper facts">
                          <span>{paper.publication_year || 'Year unknown'}</span>
                          <span>{paper.status || 'Published'}</span>
                        </div>
                        <span className="course-view-link">
                          Read paper
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
                <h3>No research papers match your search</h3>
                <p>Try a different keyword, faculty, department, or publication type.</p>
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

function sortPaperTypes(types) {
  const preferredOrder = ['Journal', 'Conference', 'Publication']
  return types.sort((left, right) => {
    const leftOrder = preferredOrder.indexOf(left)
    const rightOrder = preferredOrder.indexOf(right)
    if (leftOrder !== -1 || rightOrder !== -1) {
      return (leftOrder === -1 ? Number.MAX_SAFE_INTEGER : leftOrder) - (rightOrder === -1 ? Number.MAX_SAFE_INTEGER : rightOrder)
    }
    return left.localeCompare(right)
  })
}

function getPaperType(paper) {
  return titleCaseText(paper.publication_type || 'Publication')
}

function getPaperSummary(paper) {
  return stripHtml(paper.abstract || '')
}

function stripHtml(value) {
  return String(value || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
}

function titleCaseText(value) {
  return String(value || '')
    .trim()
    .replace(/[_-]+/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function initials(name) {
  const value = String(name || '').trim()
  if (!value) return 'RP'
  return value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

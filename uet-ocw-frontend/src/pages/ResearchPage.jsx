import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchJson } from '../data/api'

export default function ResearchPage() {
  const navigate = useNavigate()
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [researchPapers, setResearchPapers] = useState([])
  const [selectedFacultyId, setSelectedFacultyId] = useState(null)
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null)
  const [selectedPaperId, setSelectedPaperId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const [facultiesData, departmentsData, researchPapersData] = await Promise.all([
          fetchJson('/faculties'),
          fetchJson('/departments'),
          fetchJson('/research-papers'),
        ])

        setFaculties(facultiesData)
        setDepartments(departmentsData)
        setResearchPapers(researchPapersData)

        if (facultiesData[0]) {
          setSelectedFacultyId(facultiesData[0].id)
        }
      } catch (loadError) {
        setError(loadError.message || 'Unable to load research papers.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const facultyDepartments = useMemo(() => {
    if (!selectedFacultyId) return []
    return departments.filter((department) => String(department.faculty_id) === String(selectedFacultyId))
  }, [departments, selectedFacultyId])

  useEffect(() => {
    if (!facultyDepartments.length) {
      setSelectedDepartmentId(null)
      return
    }

    if (!facultyDepartments.some((department) => String(department.id) === String(selectedDepartmentId))) {
      setSelectedDepartmentId(facultyDepartments[0].id)
    }
  }, [facultyDepartments, selectedDepartmentId])

  const departmentPapers = useMemo(() => {
    if (!selectedDepartmentId) return []
    return researchPapers.filter((paper) => String(paper.department_id) === String(selectedDepartmentId))
  }, [researchPapers, selectedDepartmentId])

  useEffect(() => {
    if (!departmentPapers.length) {
      setSelectedPaperId(null)
      return
    }

    if (!departmentPapers.some((paper) => String(paper.id) === String(selectedPaperId))) {
      setSelectedPaperId(departmentPapers[0].id)
    }
  }, [departmentPapers, selectedPaperId])

  const selectedPaper = useMemo(
    () => departmentPapers.find((paper) => String(paper.id) === String(selectedPaperId)) || null,
    [departmentPapers, selectedPaperId],
  )

  return (
    <div className="container page-block">
      <section className="content-panel">
        <p className="eyebrow">Research papers</p>
        <h2>Explore publications by faculty and department</h2>
      </section>

      {error && <div className="alert-box">{error}</div>}

      {loading ? (
        <div className="loading-box">Loading research papers...</div>
      ) : (
        <>
          <section className="content-panel catalog-filters">
            <label className="field-label">
              Faculty
              <select
                value={selectedFacultyId || ''}
                onChange={(event) => {
                  setSelectedFacultyId(event.target.value)
                  setSelectedDepartmentId(null)
                  setSelectedPaperId(null)
                }}
              >
                {faculties.map((faculty) => (
                  <option key={faculty.id} value={faculty.id}>{faculty.name}</option>
                ))}
              </select>
            </label>
            <label className="field-label">
              Department
              <select
                value={selectedDepartmentId || ''}
                onChange={(event) => {
                  setSelectedDepartmentId(event.target.value)
                  setSelectedPaperId(null)
                }}
              >
                {facultyDepartments.map((department) => (
                  <option key={department.id} value={department.id}>{department.name}</option>
                ))}
              </select>
            </label>
          </section>

          <section className="catalog-results">
            <div className="section-heading-row">
              <h3>Research papers</h3>
              <span>{departmentPapers.length} available</span>
            </div>
            <div className="card-grid catalog-grid">
              {departmentPapers.map((paper) => (
                <article
                  key={paper.id}
                  className={String(selectedPaperId) === String(paper.id) ? 'catalog-card selected' : 'catalog-card'}
                >
                  <div className="catalog-card-media placeholder">{paper.title?.slice(0, 1) || 'R'}</div>
                  <button
                    type="button"
                    className="catalog-card-button"
                    onClick={() => setSelectedPaperId(paper.id)}
                  >
                    <strong>{paper.title}</strong>
                    <span>{paper.publication_year || 'Year unknown'}</span>
                  </button>
                  <button
                    type="button"
                    className="read-more-button"
                    onClick={() => navigate(`/research/${paper.id}`)}
                  >
                    Read more
                  </button>
                </article>
              ))}
            </div>
          </section>
        </>
      )}

      {selectedPaper && (
        <section className="content-panel detail-panel">
          <p className="eyebrow">Selected paper</p>
          <h3>{selectedPaper.title}</h3>
          {selectedPaper.abstract ? (
            <div
              className="html-content"
              dangerouslySetInnerHTML={{ __html: selectedPaper.abstract }}
            />
          ) : (
            <p>Research paper abstract is available in the backend.</p>
          )}
          <div className="meta-row">
            <span>{selectedPaper.publication_type || 'Publication'}</span>
            <span>{selectedPaper.publication_year || 'Year unknown'}</span>
            <span>{selectedPaper.status || 'Published'}</span>
          </div>

          <Link to={`/research/${selectedPaper.id}`} className="primary-button small">Read more</Link>
        </section>
      )}
    </div>
  )
}

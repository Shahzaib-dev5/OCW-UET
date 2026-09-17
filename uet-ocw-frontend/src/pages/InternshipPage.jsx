import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchJson, fileNameFromUrl, fileUrl } from '../data/api'

export default function InternshipPage() {
  const navigate = useNavigate()
  const [faculties, setFaculties] = useState([])
  const [departments, setDepartments] = useState([])
  const [internships, setInternships] = useState([])
  const [resources, setResources] = useState([])
  const [selectedFacultyId, setSelectedFacultyId] = useState(null)
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null)
  const [selectedInternshipId, setSelectedInternshipId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const [facultiesData, departmentsData, internshipsData, resourcesData] = await Promise.all([
          fetchJson('/faculties'),
          fetchJson('/departments'),
          fetchJson('/internships'),
          fetchJson('/internship-resources'),
        ])

        setFaculties(facultiesData)
        setDepartments(departmentsData)
        setInternships(internshipsData)
        setResources(resourcesData)

        if (facultiesData[0]) {
          setSelectedFacultyId(facultiesData[0].id)
        }
      } catch (loadError) {
        setError(loadError.message || 'Unable to load internship information.')
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

  const departmentInternships = useMemo(() => {
    if (!selectedDepartmentId) return []
    return internships.filter((internship) => String(internship.department_id) === String(selectedDepartmentId))
  }, [internships, selectedDepartmentId])

  useEffect(() => {
    if (!departmentInternships.length) {
      setSelectedInternshipId(null)
      return
    }

    if (!departmentInternships.some((internship) => String(internship.id) === String(selectedInternshipId))) {
      setSelectedInternshipId(departmentInternships[0].id)
    }
  }, [departmentInternships, selectedInternshipId])

  const selectedInternship = useMemo(
    () => departmentInternships.find((internship) => String(internship.id) === String(selectedInternshipId)) || null,
    [departmentInternships, selectedInternshipId],
  )

  const selectedInternshipResources = useMemo(() => {
    if (!selectedInternshipId) return []
    return resources.filter((resource) => String(resource.internship_id) === String(selectedInternshipId))
  }, [resources, selectedInternshipId])

  return (
    <div className="container page-block">
      <section className="content-panel">
        <p className="eyebrow">Internship opportunities</p>
        <h2>Explore internships by faculty and department</h2>
      </section>

      {error && <div className="alert-box">{error}</div>}

      {loading ? (
        <div className="loading-box">Loading internships...</div>
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
                  setSelectedInternshipId(null)
                }}
              >
                {faculties.map((faculty) => (
                  <option key={faculty.id} value={faculty.id}>
                    {faculty.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field-label">
              Department
              <select
                value={selectedDepartmentId || ''}
                onChange={(event) => {
                  setSelectedDepartmentId(event.target.value)
                  setSelectedInternshipId(null)
                }}
              >
                {facultyDepartments.map((department) => (
                  <option key={department.id} value={department.id}>
                    {department.name}
                  </option>
                ))}
              </select>
            </label>
          </section>

          <section className="catalog-results">
            <div className="section-heading-row">
              <h3>Internships</h3>
              <span>{departmentInternships.length} available</span>
            </div>
            <div className="card-grid catalog-grid">
              {departmentInternships.map((internship) => (
                <article
                  key={internship.id}
                  className={String(selectedInternshipId) === String(internship.id) ? 'catalog-card selected' : 'catalog-card'}
                >
                  {internship.thumbnail ? (
                    <img className="catalog-card-media" src={fileUrl(internship.thumbnail)} alt="" />
                  ) : (
                    <div className="catalog-card-media placeholder">{internship.title?.slice(0, 1) || 'I'}</div>
                  )}
                  <button
                    type="button"
                    className="catalog-card-button"
                    onClick={() => setSelectedInternshipId(internship.id)}
                  >
                    <strong>{internship.title}</strong>
                    <span>{internship.status || 'Open'}</span>
                  </button>
                  <button
                    type="button"
                    className="read-more-button"
                    onClick={() => navigate(`/internships/${internship.id}`)}
                  >
                    Read more
                  </button>
                </article>
              ))}
            </div>
          </section>
        </>
      )}

      {selectedInternship && (
        <section className="content-panel detail-panel">
          <p className="eyebrow">Selected internship</p>
          <h3>{selectedInternship.title}</h3>
          <p>{selectedInternship.description || 'Internship details are available from the backend.'}</p>
          <div className="meta-row">
            <span>{selectedInternship.category || 'General internship'}</span>
            <span>{selectedInternship.duration || 'Flexible duration'}</span>
            <span>{selectedInternship.status || 'Open'}</span>
          </div>

          <Link to={`/internships/${selectedInternship.id}`} className="primary-button small">Read more</Link>
        </section>
      )}

      {selectedInternship && (
        <section className="content-panel resource-manager">
          <div className="manager-heading">
            <div>
              <p className="eyebrow">Resources</p>
              <h3>Books and files</h3>
            </div>
            <span>{selectedInternshipResources.length} resources</span>
          </div>

          <div className="resource-table">
            {selectedInternshipResources.length ? (
              selectedInternshipResources.map((resource) => (
                <div key={resource.id} className="managed-resource-row">
                  <div>
                    <strong>{resource.title}</strong>
                    <span>{resource.resource_type} | Order {resource.display_order || 0}</span>
                  </div>
                  <div className="resource-links">
                    {resource.file_url && (
                      <>
                        <a href={fileUrl(resource.file_url)} target="_blank" rel="noreferrer">View</a>
                        <a href={fileUrl(resource.file_url)} download={fileNameFromUrl(resource.file_url, resource.title)}>
                          Download
                        </a>
                      </>
                    )}
                    {resource.external_url && <a href={fileUrl(resource.external_url)} target="_blank" rel="noreferrer">Link</a>}
                  </div>
                </div>
              ))
            ) : (
              <p className="empty-state">No resources are linked to this internship yet.</p>
            )}
          </div>
        </section>
      )}
    </div>
  )
}

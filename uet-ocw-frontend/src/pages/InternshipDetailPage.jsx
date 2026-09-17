import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchJson, fileNameFromUrl, fileUrl } from '../data/api'

export default function InternshipDetailPage() {
  const { internshipId } = useParams()
  const [internship, setInternship] = useState(null)
  const [resources, setResources] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadInternship() {
      try {
        setLoading(true)
        setError('')

        const [internshipData, resourceData] = await Promise.all([
          fetchJson(`/internships/${internshipId}`),
          fetchJson(`/internship-resources/internship/${internshipId}`),
        ])

        setInternship(internshipData)
        setResources(resourceData)
      } catch (loadError) {
        setError(loadError.message || 'Unable to load internship details.')
      } finally {
        setLoading(false)
      }
    }

    loadInternship()
  }, [internshipId])

  if (loading) {
    return <div className="container page-block"><div className="loading-box">Loading internship details...</div></div>
  }

  if (error) {
    return (
      <div className="container page-block">
        <div className="alert-box">{error}</div>
        <Link to="/internships" className="primary-button small">Back to internships</Link>
      </div>
    )
  }

  if (!internship) {
    return (
      <div className="container page-block">
        <div className="content-panel">
          <p className="eyebrow">Internship not found</p>
          <h2>We could not find this internship.</h2>
          <Link to="/internships" className="primary-button small">Back to internships</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container page-block">
      <section className="content-panel detail-panel">
        <p className="eyebrow">Internship details</p>
        <h2>{internship.title}</h2>
        <p>{internship.description || 'Internship details are available from the backend.'}</p>

        <div className="meta-row">
          <span>{internship.category || 'General internship'}</span>
          <span>{internship.duration || 'Flexible duration'}</span>
          <span>{internship.status || 'Open'}</span>
        </div>

        <div className="resource-list">
          <h3>Internship resources</h3>
          {resources.length ? (
            resources.map((resource) => (
              <div key={resource.id} className="resource-item">
                <strong>{resource.title}</strong>
                <span>{resource.resource_type}</span>
                {resource.description && <span>{resource.description}</span>}
                {resource.file_url && (
                  <div className="resource-links">
                    <a href={fileUrl(resource.file_url)} target="_blank" rel="noreferrer">View file</a>
                    <a href={fileUrl(resource.file_url)} download={fileNameFromUrl(resource.file_url, resource.title)}>
                      Download file
                    </a>
                  </div>
                )}
                {resource.external_url && (
                  <a href={fileUrl(resource.external_url)} target="_blank" rel="noreferrer">Open link</a>
                )}
              </div>
            ))
          ) : (
            <p>No internship resources are available for this opportunity yet.</p>
          )}
        </div>

        <div className="hero-actions">
          <Link to="/internships" className="primary-button small">Back to internships</Link>
          {internship.application_url && (
            <a href={internship.application_url} target="_blank" rel="noreferrer" className="secondary-button">
              Apply now
            </a>
          )}
        </div>
      </section>
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import TitleImageFallback from '../components/TitleImageFallback'
import { fetchJson, fileNameFromUrl, fileUrl, sendJson } from '../data/api'

export default function InternshipDetailPage() {
  const { internshipId } = useParams()
  const { user } = useAuth()
  const [internship, setInternship] = useState(null)
  const [resources, setResources] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [shareStatus, setShareStatus] = useState('')
  const [selectedResourceType, setSelectedResourceType] = useState('All')
  const [actionStatus, setActionStatus] = useState('')
  const shareTimerRef = useRef(null)

  useEffect(() => {
    async function loadInternship() {
      try {
        setLoading(true)
        setError('')

        const [internshipData, resourceData] = await Promise.all([
          fetchJson(`/skills-development/${internshipId}`),
          fetchJson(`/skills-development-resources/skills-development/${internshipId}`),
        ])

        setInternship(internshipData)
        setResources(resourceData)
      } catch (loadError) {
        setError(loadError.message || 'Unable to load skills development details.')
      } finally {
        setLoading(false)
      }
    }

    loadInternship()
  }, [internshipId])

  useEffect(() => () => {
    if (shareTimerRef.current) window.clearTimeout(shareTimerRef.current)
  }, [])

  if (loading) {
    return <div className="container page-block"><div className="loading-box">Loading skills development details...</div></div>
  }

  if (error) {
    return (
      <div className="container page-block">
        <div className="alert-box">{error}</div>
        <Link to="/skills-development" className="primary-button small">Back to skills development</Link>
      </div>
    )
  }

  if (!internship) {
    return (
      <div className="container page-block">
        <div className="content-panel">
          <p className="eyebrow">Skills development program not found</p>
          <h2>We could not find this skills development program.</h2>
          <Link to="/skills-development" className="primary-button small">Back to skills development</Link>
        </div>
      </div>
    )
  }

  const programType = displayProgramType(internship.category)
  const programName = internship.department?.short_name || internship.department?.name || programType
  const status = displayStatus(internship.status)
  const description = realDescription(internship.description)
  const hasAboutCard = Boolean(description || internship.thumbnail)
  const resourceTypes = uniqueResourceTypes(resources)
  const activeResourceType = resourceTypes.includes(selectedResourceType) ? selectedResourceType : 'All'
  const filteredResources = activeResourceType === 'All'
    ? resources
    : resources.filter((resource) => displayResourceType(resource.resource_type) === activeResourceType)
  const firstResourceUrl = resourceUrl(resources[0])
  const canAccessMaterials = resources.some((resource) => resource.can_access_materials) || internship.access_level === 'PUBLIC'
  const enrollment = resources.find((resource) => resource.enrollment)?.enrollment

  const handleShare = async () => {
    const shareData = {
      title: internship.title,
      text: description || 'Skills development program from UET Lahore Open Courseware',
      url: window.location.href,
    }

    try {
      if (navigator.share) {
        await navigator.share(shareData)
        return
      }

      await navigator.clipboard.writeText(window.location.href)
      setShareStatus('Link copied')
      if (shareTimerRef.current) window.clearTimeout(shareTimerRef.current)
      shareTimerRef.current = window.setTimeout(() => setShareStatus(''), 1800)
    } catch {
      setShareStatus('Unable to share')
      if (shareTimerRef.current) window.clearTimeout(shareTimerRef.current)
      shareTimerRef.current = window.setTimeout(() => setShareStatus(''), 1800)
    }
  }

  const requestEnrollment = async () => {
    if (!user) return
    try {
      setActionStatus('Sending request...')
      await sendJson('/course-enrollments/resources', { body: { resource_type: 'SKILL', resource_id: Number(internshipId) } })
      const resourceData = await fetchJson(`/skills-development-resources/skills-development/${internshipId}`)
      setResources(resourceData)
      setActionStatus('Enrollment request submitted.')
    } catch (requestError) {
      setActionStatus(requestError.message || 'Unable to request enrollment.')
    }
  }

  return (
    <div className="skills-development-detail-page">
      <header className="skills-detail-hero">
        <div className="skills-detail-container">
          <nav className="skills-detail-breadcrumb" aria-label="Breadcrumb">
            <Link to="/skills-development">Skills development</Link>
            <span aria-hidden="true">/</span>
            <span>{programType}</span>
            <span aria-hidden="true">/</span>
            <span>{internship.title}</span>
          </nav>

          <div className="skills-detail-badges" aria-label="Program labels">
            <span>{programType}</span>
            <span className={status.toLowerCase() === 'open' ? 'open' : ''}>{status}</span>
          </div>
          <h1>{internship.title}</h1>
          {description && <p>{description}</p>}
        </div>
      </header>

      <main className="skills-detail-container skills-detail-layout">
        <aside className="skills-facts-card" aria-label="Skills development facts and actions">
          <dl className="skills-facts-grid">
            <div>
              <dt><ProgramIcon name="resources" />Resources</dt>
              <dd>{resources.length}</dd>
            </div>
            <div>
              <dt><ProgramIcon name="duration" />Duration</dt>
              <dd>{internship.duration || 'Flexible'}</dd>
            </div>
            <div>
              <dt><ProgramIcon name="status" />Status</dt>
              <dd>{status}</dd>
            </div>
            <div>
              <dt><ProgramIcon name="category" />Program</dt>
              <dd title={programName}>{programName}</dd>
            </div>
          </dl>

          <div className="skills-facts-actions">
            {firstResourceUrl ? (
              <a className="course-start-button" href={firstResourceUrl} target="_blank" rel="noreferrer">Start learning</a>
            ) : !canAccessMaterials && !user ? (
              <Link className="course-start-button" to={`/login?returnTo=${encodeURIComponent(`/skills-development/${internshipId}`)}`}>Login to Request Enrollment</Link>
            ) : !canAccessMaterials ? (
              <button className="course-start-button" type="button" onClick={requestEnrollment} disabled={enrollment?.status === 'PENDING'}>
                {enrollment?.status === 'PENDING' ? 'Awaiting Admin Approval' : ['REJECTED', 'REVOKED'].includes(enrollment?.status) ? 'Request Enrollment Again' : 'Request Enrollment'}
              </button>
            ) : (
              <a className="course-start-button" href="#skills-resources">Start learning</a>
            )}
            <button type="button" className="skills-share-button" onClick={handleShare}>Share</button>
            {shareStatus && <p className="share-toast" role="status">{shareStatus}</p>}
            {actionStatus && <p className="share-toast" role="status">{actionStatus}</p>}
          </div>
        </aside>

        <div className="skills-detail-main">
          {hasAboutCard && (
            <section id="program-overview" className="skills-info-card">
              <h2>About this program</h2>
              <div className={internship.thumbnail ? 'skills-about-grid' : 'skills-about-grid no-media'}>
                {internship.thumbnail && (
                  <figure className="skills-program-media">
                    <TitleImageFallback
                      className="skills-program-image"
                      src={internship.thumbnail ? fileUrl(internship.thumbnail) : ''}
                      alt={`${internship.title || 'Skills development'} poster`}
                      title={internship.title || 'Skills Development'}
                      label={programType}
                    />
                  </figure>
                )}
                {description && <p>{description}</p>}
              </div>
            </section>
          )}

        <section id="skills-resources" className="skills-info-card">
          <div className="skills-card-heading">
            <h2>Resources</h2>
            <span>{formatFileCount(filteredResources.length)}</span>
          </div>
          {!canAccessMaterials && (
            <p className="lock-notice">{enrollment?.status === 'PENDING' ? 'Your request is awaiting admin approval.' : enrollment?.review_reason || 'Learning material is locked until your enrollment is approved.'}</p>
          )}

          {resources.length > 5 && (
            <div className="skills-resource-filters" role="list" aria-label="Resource type filters">
              {resourceTypes.map((type) => (
                <button
                  key={type}
                  type="button"
                  className={activeResourceType === type ? 'active' : ''}
                  aria-pressed={activeResourceType === type}
                  onClick={() => setSelectedResourceType(type)}
                >
                  {type}
                </button>
              ))}
            </div>
          )}

          {resources.length ? (
            <ul className="skills-resource-list">
              {filteredResources.map((resource) => (
                <li key={resource.id} className="skills-resource-row">
                  <span className={`skills-file-icon ${resourceTypeClass(resource.resource_type)}`} aria-hidden="true">
                    {resourceTypeShort(resource.resource_type)}
                  </span>
                  <div className="skills-resource-copy">
                    <h3>{resource.title}</h3>
                    <p>{resourceMeta(resource)}</p>
                  </div>
                  <div className="skills-resource-actions">
                    {resourceUrl(resource) && (
                      <a href={resourceUrl(resource)} target="_blank" rel="noreferrer" aria-label={`View ${resource.title}`}>
                        <ActionIcon name="view" />
                        <span>View</span>
                      </a>
                    )}
                    {resource.file_url && (
                      <a href={fileUrl(resource.file_url)} download={fileNameFromUrl(resource.file_url, resource.title)} aria-label={`Download ${resource.title}`}>
                        <ActionIcon name="download" />
                        <span>Download</span>
                      </a>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="skills-empty-text">No resources are available for this program yet.</p>
          )}
        </section>
        </div>
      </main>
    </div>
  )
}

function ActionIcon({ name }) {
  const paths = {
    view: 'M2.8 8s1.8-3 5.2-3 5.2 3 5.2 3-1.8 3-5.2 3S2.8 8 2.8 8z M8 6.4a1.6 1.6 0 1 0 0 3.2 1.6 1.6 0 0 0 0-3.2z',
    download: 'M8 3v6 M5.5 6.8 8 9.3l2.5-2.5 M3.5 12.5h9',
  }

  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
      <path d={paths[name]} />
    </svg>
  )
}

function uniqueResourceTypes(resources) {
  return ['All', ...new Set(resources.map((resource) => displayResourceType(resource.resource_type)))]
}

function resourceUrl(resource) {
  if (!resource) return ''
  if (resource.file_url) return fileUrl(resource.file_url)
  if (resource.external_url) return fileUrl(resource.external_url)
  return ''
}

function resourceMeta(resource) {
  const type = displayResourceType(resource.resource_type)
  const size = formatFileSize(resource.file_size)
  return size ? `${type} | ${size}` : type
}

function formatFileSize(size) {
  const bytes = Number(size)
  if (!Number.isFinite(bytes) || bytes <= 0) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatFileCount(count) {
  return `${count} ${count === 1 ? 'file' : 'files'}`
}

function realDescription(value) {
  const description = String(value || '').trim()
  if (!description) return ''
  if (/details are available from the backend/i.test(description)) return ''
  return description
}

function displayProgramType(value) {
  const normalized = String(value || '').trim()
  if (/^intership$/i.test(normalized) || /^internship$/i.test(normalized)) return 'Training Program'
  return titleCase(normalized || 'Training Program')
}

function displayStatus(value) {
  return titleCase(String(value || 'Open'))
}

function displayResourceType(value) {
  return titleCase(String(value || 'Other'))
}

function resourceTypeShort(value) {
  const type = displayResourceType(value)
  if (/pdf/i.test(type)) return 'PDF'
  if (/ppt|presentation/i.test(type)) return 'PPT'
  if (/doc|document/i.test(type)) return 'DOC'
  if (/video/i.test(type)) return 'VID'
  if (/link/i.test(type)) return 'URL'
  return 'FILE'
}

function resourceTypeClass(value) {
  const type = displayResourceType(value)
  if (/pdf/i.test(type)) return 'pdf'
  if (/ppt|presentation/i.test(type)) return 'ppt'
  if (/doc|document/i.test(type)) return 'doc'
  return 'other'
}

function titleCase(value) {
  return String(value || '')
    .trim()
    .replace(/[_-]+/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function ProgramIcon({ name }) {
  const paths = {
    resources: 'M3 3.5h10v9H3z M5 6h6 M5 8h6 M5 10h3',
    duration: 'M8 3a5 5 0 1 0 0 10A5 5 0 0 0 8 3z M8 5.5V8l1.8 1.2',
    status: 'M3.2 8.2 6.3 11.3 12.8 4.7',
    category: 'M2.8 4.2h4.6l1 1.3h4.8v6.3H2.8z',
  }

  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false" className={`fact-icon ${name}`}>
      <path d={paths[name]} />
    </svg>
  )
}

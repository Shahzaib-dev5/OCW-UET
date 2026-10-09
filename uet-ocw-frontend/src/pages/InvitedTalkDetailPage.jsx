import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchJson, fileNameFromUrl, fileUrl } from '../data/api'

export default function InvitedTalkDetailPage() {
  const { talkId } = useParams()
  const [talk, setTalk] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [shareStatus, setShareStatus] = useState('')
  const shareTimerRef = useRef(null)

  useEffect(() => {
    async function loadTalk() {
      try {
        setLoading(true)
        setError('')
        const talkData = await fetchJson(`/invited-talks/${talkId}`)
        setTalk(talkData)
      } catch (loadError) {
        setError(loadError.message || 'Unable to load tech talk details.')
      } finally {
        setLoading(false)
      }
    }

    loadTalk()
  }, [talkId])

  useEffect(() => () => {
    if (shareTimerRef.current) window.clearTimeout(shareTimerRef.current)
  }, [])

  if (loading) {
    return <div className="container page-block"><div className="loading-box">Loading tech talk...</div></div>
  }

  if (error) {
    return (
      <div className="container page-block">
        <div className="alert-box">{error}</div>
        <Link to="/invited-talks" className="primary-button small">Back to tech talks</Link>
      </div>
    )
  }

  if (!talk) {
    return (
      <div className="container page-block">
        <div className="content-panel">
          <p className="eyebrow">Tech talk not found</p>
          <h2>We could not find this tech talk.</h2>
          <Link to="/invited-talks" className="primary-button small">Back to tech talks</Link>
        </div>
      </div>
    )
  }

  const departmentName = talk.department?.name || 'Department not specified'
  const summary = talk.event_title || talk.publication || 'Tech talk details are available from the backend.'

  const handleShare = async () => {
    const shareData = {
      title: talk.talk_title || 'Tech talk',
      text: summary,
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

  return (
    <div className="course-detail-page invited-talk-detail-page">
      <header className="course-detail-hero research-detail-hero">
        <div className="container course-detail-hero-inner">
          <div className="course-detail-summary">
            <div className="course-detail-badges" aria-label="Tech talk labels">
              <span>Tech Talk</span>
              <span>{departmentName}</span>
            </div>
            <h1>{talk.talk_title || 'Untitled talk'}</h1>
            {summary && <p className="course-detail-summary-text">{summary}</p>}
            <div className="course-detail-teacher">
              <div className="teacher-fact">
                <span className="teacher-avatar">{initials(talk.presenter)}</span>
                <div>
                  <small>Presenter</small>
                  <strong>{talk.presenter || 'Presenter not specified'}</strong>
                </div>
              </div>
            </div>
          </div>

          <aside className="course-quick-card" aria-label="Tech talk quick facts and actions">
            <dl className="course-quick-facts">
              <div>
                <dt><Icon />Date</dt>
                <dd>{formatDate(talk.talk_date)}</dd>
              </div>
              <div>
                <dt><Icon />Department</dt>
                <dd title={departmentName}>{departmentName}</dd>
              </div>
              <div>
                <dt><Icon />Video</dt>
                <dd className={!talk.video_url ? 'muted-value' : ''}>{talk.video_url ? 'Available' : 'Not set'}</dd>
              </div>
              <div>
                <dt><Icon />Upload</dt>
                <dd className={!talk.upload_url ? 'muted-value' : ''}>{talk.upload_url ? 'Available' : 'Not set'}</dd>
              </div>
            </dl>

            <div className="course-quick-actions">
              {talk.video_url ? <a className="course-start-button" href={fileUrl(talk.video_url)} target="_blank" rel="noreferrer">Watch video</a> : <a className="course-start-button" href="#talk-details">View details</a>}
              <div className="course-secondary-actions">
                {talk.upload_url && <a href={fileUrl(talk.upload_url)} target="_blank" rel="noreferrer">Upload</a>}
                <button type="button" onClick={handleShare}>Share</button>
              </div>
              {shareStatus && <p className="share-toast" role="status">{shareStatus}</p>}
            </div>
          </aside>
        </div>
      </header>

      <div className="container course-detail-layout">
        <aside className="course-menu" aria-label="Tech talk menu">
          <h3>Talk Menu</h3>
          <a href="#talk-details">Details</a>
          <a href="#media">Media</a>
          <a href="#publication">Publication</a>
        </aside>

        <main className="course-detail-content">
          <section id="talk-details" className="course-section">
            <h3>Talk Details</h3>
            <table className="highlight-table">
              <tbody>
                <tr>
                  <th>Talk title</th>
                  <td>{talk.talk_title || 'Untitled talk'}</td>
                </tr>
                <tr>
                  <th>Event title</th>
                  <td>{talk.event_title || 'Not specified'}</td>
                </tr>
                <tr>
                  <th>Presenter</th>
                  <td>{talk.presenter || 'Not specified'}</td>
                </tr>
                <tr>
                  <th>Date</th>
                  <td>{formatDate(talk.talk_date)}</td>
                </tr>
              </tbody>
            </table>
          </section>

          <section id="media" className="course-section">
            <h3>Video And Upload</h3>
            <table className="course-resource-table">
              <tbody>
                <tr>
                  <td>
                    <strong>Video upload link</strong>
                    <span>{talk.video_url || 'No video link has been added.'}</span>
                  </td>
                  <td>{talk.video_url ? <a href={fileUrl(talk.video_url)} target="_blank" rel="noreferrer">watch</a> : <span className="muted-resource">video</span>}</td>
                </tr>
                <tr>
                  <td>
                    <strong>Uploaded file</strong>
                    <span>{talk.upload_url ? fileNameFromUrl(talk.upload_url, 'uploaded file') : 'No upload is available.'}</span>
                  </td>
                  <td>
                    {talk.upload_url ? (
                      <>
                        <a href={fileUrl(talk.upload_url)} target="_blank" rel="noreferrer">view</a>
                        <a href={fileUrl(talk.upload_url)} download={fileNameFromUrl(talk.upload_url, talk.talk_title)}>download</a>
                      </>
                    ) : (
                      <span className="muted-resource">upload</span>
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
          </section>

          <section id="publication" className="course-section">
            <h3>Publication</h3>
            <div className="section-rule" />
            <p className="section-copy">{talk.publication || 'No publication details have been added.'}</p>
          </section>
        </main>
      </div>
    </div>
  )
}

function Icon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false" className="fact-icon">
      <path d="M3 3.5h10v9H3z M5 6h6 M5 8h6 M5 10h3" />
    </svg>
  )
}

function formatDate(value) {
  if (!value) return 'Not set'
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
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

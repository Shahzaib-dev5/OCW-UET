import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchJson, fileNameFromUrl, fileUrl } from '../data/api'

export default function ResearchDetailPage() {
  const { researchId } = useParams()
  const [paper, setPaper] = useState(null)
  const [authors, setAuthors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [shareStatus, setShareStatus] = useState('')
  const shareTimerRef = useRef(null)

  useEffect(() => {
    async function loadPaper() {
      try {
        setLoading(true)
        setError('')

        const [paperData, authorLinks] = await Promise.all([
          fetchJson(`/research-papers/${researchId}`),
          fetchJson(`/research-paper-authors/paper/${researchId}`),
        ])

        setPaper(paperData)

        const authorResults = await Promise.all(
          authorLinks.map(async (link) => {
            const author = await fetchJson(`/authors/${link.author_id}`)
            return { ...author, author_order: link.author_order }
          })
        )

        setAuthors(authorResults.sort((a, b) => (a.author_order || 0) - (b.author_order || 0)))
      } catch (loadError) {
        setError(loadError.message || 'Unable to load research paper details.')
      } finally {
        setLoading(false)
      }
    }

    loadPaper()
  }, [researchId])

  useEffect(() => () => {
    if (shareTimerRef.current) window.clearTimeout(shareTimerRef.current)
  }, [])

  if (loading) {
    return <div className="container page-block"><div className="loading-box">Loading research paper details...</div></div>
  }

  if (error) {
    return (
      <div className="container page-block">
        <div className="alert-box">{error}</div>
        <Link to="/research" className="primary-button small">Back to research</Link>
      </div>
    )
  }

  if (!paper) {
    return (
      <div className="container page-block">
        <div className="content-panel">
          <p className="eyebrow">Research paper not found</p>
          <h2>We could not find this paper.</h2>
          <Link to="/research" className="primary-button small">Back to research</Link>
        </div>
      </div>
    )
  }

  const authorCount = authors.length || countLegacyAuthors(paper.authors)
  const publicationVenue = paper.journal_name || paper.conference_name || 'Not specified'
  const paperLink = paper.pdf_url || paper.paper_url
  const summary = stripHtml(paper.abstract || '')

  const handleShare = async () => {
    const shareData = {
      title: paper.title,
      text: summary || 'Research paper from UET Lahore Open Courseware',
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
    <div className="research-detail-page">
      <header className="course-detail-hero research-detail-hero">
        <div className="container course-detail-hero-inner">
          <div className="course-detail-summary">
            <div className="course-detail-badges" aria-label="Research paper labels">
              <span>{paper.publication_type || 'Publication'}</span>
              <span>{paper.status || 'Published'}</span>
            </div>
            <h1>{paper.title}</h1>
            {summary && <p className="course-detail-summary-text">{summary}</p>}
            <div className="research-author-strip">
              <span className="teacher-avatar">{initials(authors[0]?.name || paper.authors || paper.title)}</span>
              <div>
                <small>Authors</small>
                <strong>{formatAuthors(authors, paper.authors)}</strong>
              </div>
            </div>
          </div>

          <aside className="course-quick-card" aria-label="Research paper quick facts and actions">
            <dl className="course-quick-facts">
              <div>
                <dt><ResearchIcon name="authors" />Authors</dt>
                <dd>{authorCount || 'Not set'}</dd>
              </div>
              <div>
                <dt><ResearchIcon name="year" />Year</dt>
                <dd>{paper.publication_year || 'Unknown'}</dd>
              </div>
              <div>
                <dt><ResearchIcon name="department" />Department</dt>
                <dd title={paper.department?.name || 'Not specified'}>{paper.department?.name || 'Not set'}</dd>
              </div>
              <div>
                <dt><ResearchIcon name="venue" />Venue</dt>
                <dd title={publicationVenue}>{publicationVenue}</dd>
              </div>
            </dl>

            <div className="course-quick-actions">
              {paperLink ? (
                <a className="course-start-button" href={fileUrl(paperLink)} target="_blank" rel="noreferrer">Read paper</a>
              ) : (
                <span className="course-start-button disabled">Paper link unavailable</span>
              )}
              <div className="course-secondary-actions">
                {paper.pdf_url ? (
                  <a href={fileUrl(paper.pdf_url)} download={fileNameFromUrl(paper.pdf_url, paper.title)}>Download PDF</a>
                ) : (
                  <a href="#paper-details">Details</a>
                )}
                <button type="button" onClick={handleShare}>Share</button>
              </div>
              {shareStatus && <p className="share-toast" role="status">{shareStatus}</p>}
            </div>
          </aside>
        </div>
      </header>

      <div className="container page-block research-detail-body">
        <section className="content-panel detail-panel">
          <p className="eyebrow">Abstract</p>
          {paper.abstract ? (
            <div className="html-content" dangerouslySetInnerHTML={{ __html: paper.abstract }} />
          ) : (
            <p>No abstract provided.</p>
          )}
        </section>

        <section className="content-panel detail-panel">
          <h3>Authors</h3>
          {authors.length ? (
            authors.map((author) => (
              <div key={author.id} className="resource-item">
                <strong>{author.name}</strong>
                <span>{author.affiliation || 'Affiliation not specified'}</span>
                {author.email && <a href={`mailto:${author.email}`}>{author.email}</a>}
              </div>
            ))
          ) : paper.authors ? (
            <div className="resource-item">
              <strong>{paper.authors}</strong>
              <span></span>
            </div>
          ) : (
            <p>No authors are linked to this research paper.</p>
          )}
        </section>

        <section id="paper-details" className="content-panel detail-panel">
          <h3>Paper details</h3>
          {paper.journal_name && <div className="resource-item"><strong>Journal</strong><span>{paper.journal_name}</span></div>}
          {paper.conference_name && <div className="resource-item"><strong>Conference</strong><span>{paper.conference_name}</span></div>}
          {paper.publication_date && <div className="resource-item"><strong>Publication date</strong><span>{paper.publication_date}</span></div>}
          {paper.doi && <div className="resource-item"><strong>DOI</strong><span>{paper.doi}</span></div>}
          {paper.keywords && <div className="resource-item"><strong>Keywords</strong><span>{paper.keywords}</span></div>}
          {paper.paper_url && <a href={fileUrl(paper.paper_url)} target="_blank" rel="noreferrer" className="primary-button small">Open paper</a>}
          {paper.pdf_url && (
            <div className="hero-actions">
              <a href={fileUrl(paper.pdf_url)} target="_blank" rel="noreferrer" className="primary-button small">View PDF</a>
              <a href={fileUrl(paper.pdf_url)} download={fileNameFromUrl(paper.pdf_url, paper.title)} className="secondary-action-button">Download PDF</a>
            </div>
          )}
        </section>

        <div className="hero-actions">
          <Link to="/research" className="primary-button small">Back to research</Link>
        </div>
      </div>
    </div>
  )
}

function ResearchIcon({ name }) {
  const paths = {
    authors: 'M5.5 7.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z M2.8 13a2.8 2.8 0 0 1 5.4 0 M11.2 7.7a1.7 1.7 0 1 0 0-3.4 M10.1 10.2a2.5 2.5 0 0 1 3.1 2.8',
    year: 'M3 4h10v9H3z M5 2.8v2.4 M11 2.8v2.4 M3 6.5h10',
    department: 'M2.8 13V5.2L8 3l5.2 2.2V13 M5.2 13V8h5.6v5',
    venue: 'M3 4.5h10v7H3z M5 6.5h6 M5 8.5h4',
  }

  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false" className={`fact-icon ${name}`}>
      <path d={paths[name]} />
    </svg>
  )
}

function formatAuthors(authors, legacyAuthors) {
  if (authors.length) {
    const names = authors.map((author) => author.name).filter(Boolean)
    if (names.length <= 2) return names.join(', ')
    return `${names.slice(0, 2).join(', ')} +${names.length - 2} more`
  }

  return legacyAuthors || 'Authors not specified'
}

function countLegacyAuthors(value) {
  if (!value) return 0
  return String(value).split(/,|;| and /i).map((item) => item.trim()).filter(Boolean).length || 1
}

function stripHtml(value) {
  return String(value || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
}

function initials(name) {
  const value = String(name || '').trim()
  if (!value) return 'R'
  return value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

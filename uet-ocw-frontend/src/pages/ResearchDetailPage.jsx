import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchJson, fileNameFromUrl, fileUrl } from '../data/api'

export default function ResearchDetailPage() {
  const { researchId } = useParams()
  const [paper, setPaper] = useState(null)
  const [authors, setAuthors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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

  return (
    <div className="container page-block">
      <section className="content-panel detail-panel">
        <p className="eyebrow">Research paper</p>
        <h2>{paper.title}</h2>
        {paper.abstract ? (
          <div className="html-content" dangerouslySetInnerHTML={{ __html: paper.abstract }} />
        ) : (
          <p>No abstract provided.</p>
        )}

        <div className="meta-row">
          <span>{paper.publication_type || 'Publication'}</span>
          <span>{paper.publication_year || 'Year unknown'}</span>
          <span>{paper.status || 'Published'}</span>
        </div>

        <div className="resource-list">
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
        </div>

        <div className="resource-list">
          <h3>Paper details</h3>
          {paper.journal_name && <div className="resource-item"><strong>Journal</strong><span>{paper.journal_name}</span></div>}
          {paper.conference_name && <div className="resource-item"><strong>Conference</strong><span>{paper.conference_name}</span></div>}
          {paper.doi && <div className="resource-item"><strong>DOI</strong><span>{paper.doi}</span></div>}
          {paper.paper_url && <a href={fileUrl(paper.paper_url)} target="_blank" rel="noreferrer" className="primary-button small">Open paper</a>}
          {paper.pdf_url && (
            <div className="hero-actions">
              <a href={fileUrl(paper.pdf_url)} target="_blank" rel="noreferrer" className="primary-button small">View PDF</a>
              <a href={fileUrl(paper.pdf_url)} download={fileNameFromUrl(paper.pdf_url, paper.title)} className="secondary-action-button">Download PDF</a>
            </div>
          )}
        </div>

        <div className="hero-actions">
          <Link to="/research" className="primary-button small">Back to research</Link>
        </div>
      </section>
    </div>
  )
}

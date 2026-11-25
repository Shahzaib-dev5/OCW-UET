import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { deleteJson, fetchJson, fileNameFromUrl, fileUrl, sendJson, uploadFile } from '../data/api'
import { useAuth } from '../auth/AuthContext'
import TitleImageFallback from '../components/TitleImageFallback'

export default function InvitedTalkDetailPage() {
  const { talkId } = useParams()
  const { isInstructorMode } = useAuth()
  const [talk, setTalk] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [shareStatus, setShareStatus] = useState('')
  const [resources, setResources] = useState([])
  const [resourceForm, setResourceForm] = useState({ title: '', resource_type: 'VIDEO', url: '', description: '' })
  const [resourceFile, setResourceFile] = useState(null)
  const [resourceStack, setResourceStack] = useState([])
  const [editingResourceId, setEditingResourceId] = useState(null)
  const [deletedResourceIds, setDeletedResourceIds] = useState([])
  const [showResourceForm, setShowResourceForm] = useState(false)
  const [savingResource, setSavingResource] = useState(false)
  const [actionStatus, setActionStatus] = useState('')
  const shareTimerRef = useRef(null)

  useEffect(() => {
    async function loadTalk() {
      try {
        setLoading(true)
        setError('')
        const talkData = await fetchJson(`/invited-talks/${talkId}`)
        setTalk(talkData)
        setResources(talkData.resources || [])
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
  const canManage = Boolean(talk.can_manage && isInstructorMode)

  const openResourceForm = (resource = null) => {
    const stack = resources.map((item) => ({
      ...item, persistedId: item.id, stackId: `existing-${item.id}`, file: null,
    }))
    const selected = resource ? stack.find((item) => item.persistedId === resource.id) : null
    setEditingResourceId(selected?.stackId || null)
    setResourceForm(resource ? {
      title: resource.title || '', resource_type: resource.resource_type || 'LINK',
      url: resource.url || '', description: resource.description || '',
    } : { title: '', resource_type: 'VIDEO', url: '', description: '' })
    setResourceFile(null)
    setResourceStack(stack)
    setDeletedResourceIds([])
    setActionStatus('')
    setShowResourceForm(true)
  }

  const addResourceToStack = () => {
    if (!resourceForm.title.trim()) {
      setActionStatus('Add a resource title first.')
      return
    }
    if (!resourceForm.url.trim() && !resourceFile) {
      setActionStatus('Add an external URL or choose a file.')
      return
    }
    const stackedItem = {
      ...resourceForm,
      title: resourceForm.title.trim(),
      file: resourceFile,
      stackId: editingResourceId || `${Date.now()}-${Math.random()}`,
    }
    setResourceStack((current) => editingResourceId
      ? current.map((item) => item.stackId === editingResourceId ? { ...item, ...stackedItem } : item)
      : [...current, stackedItem])
    setResourceForm({ title: '', resource_type: 'VIDEO', url: '', description: '' })
    setResourceFile(null)
    setEditingResourceId(null)
    setActionStatus(editingResourceId ? 'Resource updated in stack.' : 'Resource added to stack. Add another or save all resources.')
  }

  const editStackResource = (item) => {
    setEditingResourceId(item.stackId)
    setResourceForm({
      title: item.title || '', resource_type: item.resource_type || 'LINK',
      url: item.url || '', description: item.description || '',
    })
    setResourceFile(item.file || null)
    setActionStatus(`Editing "${item.title}". Update it in the stack when ready.`)
  }

  const removeStackResource = (item) => {
    if (item.persistedId) setDeletedResourceIds((current) => [...new Set([...current, item.persistedId])])
    setResourceStack((current) => current.filter((entry) => entry.stackId !== item.stackId))
    if (editingResourceId === item.stackId) {
      setEditingResourceId(null)
      setResourceForm({ title: '', resource_type: 'VIDEO', url: '', description: '' })
      setResourceFile(null)
    }
    setActionStatus(`"${item.title}" will be deleted when you save changes.`)
  }

  const submitResource = async (event) => {
    event.preventDefault()
    try {
      setSavingResource(true); setActionStatus('')
      if (editingResourceId) throw new Error('Update the selected resource in the stack before saving.')
      const items = resourceStack
      const savedItems = []
      for (const item of items) {
        let resourceUrl = item.url
        if (item.file) {
          const uploaded = await uploadFile({ file: item.file, folder: `invited-talks/${talkId}/resources` })
          resourceUrl = uploaded.local_url || uploaded.public_url || uploaded.relative_path || resourceUrl
        }
        if (!resourceUrl) throw new Error(`Add a URL or file for "${item.title}".`)
        const saved = await sendJson(item.persistedId ? `/invited-talks/resources/${item.persistedId}` : `/invited-talks/${talkId}/resources`, {
          method: item.persistedId ? 'PATCH' : 'POST',
          body: { title: item.title, resource_type: item.resource_type, url: resourceUrl, description: item.description },
        })
        savedItems.push(saved)
      }
      for (const resourceId of deletedResourceIds) await deleteJson(`/invited-talks/resources/${resourceId}`)
      setResources(savedItems)
      setShowResourceForm(false); setEditingResourceId(null); setResourceFile(null)
      setResourceStack([]); setDeletedResourceIds([])
      setActionStatus('Resource changes saved.')
    } catch (saveError) { setActionStatus(saveError.message || 'Unable to save the resource.') }
    finally { setSavingResource(false) }
  }

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
          <a href="#talk-details">Talk Introduction</a>
          <a href="#media">Videos / Resources</a>
          <a href="#publication">Publication</a>
        </aside>

        <main className="course-detail-content">
          <section id="talk-details" className="course-section">
            <h3>Talk Introduction</h3>
            <div className="course-intro-grid">
              <figure className="course-intro-media"><TitleImageFallback className="course-intro-image" title={talk.talk_title || 'Tech Talk'} label="Tech Talk" alt={`${talk.talk_title || 'Tech talk'} cover`} /></figure>
              <div className="about-course">
                <h4>About The Talk</h4>
                <p>{talk.publication || talk.event_title || 'Talk details have not been added yet.'}</p>
                <table className="highlight-table"><tbody>
                  <tr><th>Event</th><td>{talk.event_title || 'Not specified'}</td></tr>
                  <tr><th>Presenter</th><td>{talk.presenter || 'Not specified'}</td></tr>
                  <tr><th>Date</th><td>{formatDate(talk.talk_date)}</td></tr>
                </tbody></table>
              </div>
            </div>
          </section>

          <section id="media" className="course-section">
            <div className="section-heading-with-action"><h3>Talk Videos / Resources</h3>{canManage && <div className="form-actions"><button type="button" className="secondary-action-button" onClick={() => openResourceForm()}>Manage Resources</button><button type="button" className="lecture-add-button" aria-label="Add talk resources" onClick={() => openResourceForm()}><PlusIcon /></button></div>}</div>
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
                {resources.map((resource) => (
                  <tr key={resource.id}>
                    <td><strong>{resource.title}</strong><span>{resource.description || resource.resource_type}</span></td>
                    <td>
                      <a href={fileUrl(resource.url)} target="_blank" rel="noreferrer">{resource.resource_type === 'VIDEO' ? 'watch' : 'view'}</a>
                      {canManage && <button type="button" className="lecture-edit-button" onClick={() => openResourceForm(resource)}>manage</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {actionStatus && <p className="share-toast" role="status">{actionStatus}</p>}
          </section>

          <section id="publication" className="course-section">
            <h3>Publication</h3>
            <div className="section-rule" />
            <p className="section-copy">{talk.publication || 'No publication details have been added.'}</p>
          </section>
        </main>
      </div>
      {showResourceForm && <div className="lecture-dialog-backdrop" role="presentation" onMouseDown={() => setShowResourceForm(false)}>
        <section className="lecture-dialog" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
          <div className="lecture-dialog-header"><h3>Manage Talk Resources</h3><button type="button" className="dialog-close-button" onClick={() => setShowResourceForm(false)}>×</button></div>
          <form className="instructor-upload-form lecture-dialog-form" onSubmit={submitResource}>
            <div className="lecture-material-builder">
              <label className="wide">Resource title<input value={resourceForm.title} onChange={(event) => setResourceForm({ ...resourceForm, title: event.target.value })} placeholder="e.g. Keynote video or Presentation slides" /></label>
              <label>Type<select value={resourceForm.resource_type} onChange={(event) => setResourceForm({ ...resourceForm, resource_type: event.target.value })}><option value="VIDEO">Video</option><option value="SLIDES">Slides</option><option value="DOCUMENT">Document</option><option value="FILE">File</option><option value="LINK">Link</option></select></label>
              <label>External URL<input type="url" value={resourceForm.url} onChange={(event) => setResourceForm({ ...resourceForm, url: event.target.value })} placeholder="https://..." /></label>
              <label className="wide">Or upload a file<input key={`${resourceStack.length}-${editingResourceId || 'new'}`} type="file" onChange={(event) => setResourceFile(event.target.files?.[0] || null)} /></label>
              <label className="wide">Description<textarea value={resourceForm.description} onChange={(event) => setResourceForm({ ...resourceForm, description: event.target.value })} /></label>
              <button type="button" className="secondary-action-button lecture-stack-add" onClick={addResourceToStack}>{editingResourceId ? 'Update in Stack' : 'Add to Stack'}</button>
            </div>
            <div className="lecture-stack-list">
              {resourceStack.length ? resourceStack.map((item, index) => <div className="lecture-stack-item" key={item.stackId}>
                <span>{index + 1}</span><strong>{item.title}</strong><small>{item.resource_type} · {item.file?.name || item.url}</small>
                <div className="talk-resource-stack-actions"><button type="button" aria-label={`Edit ${item.title}`} onClick={() => editStackResource(item)}>Edit</button><button type="button" aria-label={`Delete ${item.title}`} onClick={() => removeStackResource(item)}>Delete</button></div>
              </div>) : <p>No material added yet.</p>}
            </div>
            {actionStatus && <p className="course-details-feedback" role="status">{actionStatus}</p>}
            <div className="lecture-dialog-actions"><button className="primary-button auth-submit" disabled={savingResource || Boolean(editingResourceId) || (!resourceStack.length && !deletedResourceIds.length)}>{savingResource ? 'Saving...' : `Save Changes (${resourceStack.length})`}</button><button type="button" className="secondary-action-button" onClick={() => setShowResourceForm(false)}>Cancel</button></div>
          </form>
        </section>
      </div>}
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

function PlusIcon() {
  return <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false"><path d="M8 3v10M3 8h10" /></svg>
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

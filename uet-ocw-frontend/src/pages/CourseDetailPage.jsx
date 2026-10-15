import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import TitleImageFallback from '../components/TitleImageFallback'
import { deleteJson, fetchJson, fileNameFromUrl, fileUrl, sendJson, uploadFile } from '../data/api'

const menuItems = [
  { href: '#introduction', label: 'Introduction' },
  { href: '#syllabus', label: 'Syllabus' },
  { href: '#calendar', label: 'Calendar' },
  { href: '#materials', label: 'Material/Videos' },
  { href: '#reading', label: 'Reading Resources' },
]

export default function CourseDetailPage() {
  const { courseId } = useParams()
  const { user, isInstructorMode } = useAuth()
  const [course, setCourse] = useState(null)
  const [resources, setResources] = useState([])
  const [lectures, setLectures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [shareStatus, setShareStatus] = useState('')
  const [actionStatus, setActionStatus] = useState('')
  const [resourceForm, setResourceForm] = useState({ title: '', resource_type: 'PDF', description: '', external_url: '', use_external_link: false })
  const [resourceFile, setResourceFile] = useState(null)
  const [resourceFileInputKey, setResourceFileInputKey] = useState(0)
  const [editingResourceId, setEditingResourceId] = useState(null)
  const [isResourceFormOpen, setIsResourceFormOpen] = useState(false)
  const [lectureForm, setLectureForm] = useState({ lecture_number: '', title: '', description: '', duration_minutes: '' })
  const [lectureItems, setLectureItems] = useState([])
  const [deletedLectureResourceIds, setDeletedLectureResourceIds] = useState([])
  const [lectureItemDraft, setLectureItemDraft] = useState({ resource_type: 'PDF', external_url: '', file: null, use_external_link: false })
  const [lectureFileInputKey, setLectureFileInputKey] = useState(0)
  const [editingLectureId, setEditingLectureId] = useState(null)
  const [isLectureFormOpen, setIsLectureFormOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const shareTimerRef = useRef(null)

  useEffect(() => {
    async function loadCourse() {
      try {
        setLoading(true)
        setError('')

        const courseData = await fetchJson(`/courses/${courseId}`)
        const [resourceResult, lectureResult] = await Promise.allSettled([
          fetchJson(`/course-resources/course/${courseId}`),
          fetchJson(`/lectures/course/${courseId}`),
        ])
        const resourceData = resourceResult.status === 'fulfilled' ? resourceResult.value : []
        const lectureData = lectureResult.status === 'fulfilled' ? lectureResult.value : []
        setCourse(courseData)
        setResources(resourceData)
        setLectures(lectureData)
      } catch (loadError) {
        setError(loadError.message || 'Unable to load course details.')
      } finally {
        setLoading(false)
      }
    }

    loadCourse()
  }, [courseId])

  useEffect(() => () => {
    if (shareTimerRef.current) window.clearTimeout(shareTimerRef.current)
  }, [])

  const readingResources = useMemo(
    () => resources.filter((resource) => resource.lecture_number == null),
    [resources],
  )

  const resourcesByLectureNumber = useMemo(() => (
    resources.reduce((grouped, resource) => {
      if (resource.lecture_number == null) return grouped
      const key = String(resource.lecture_number)
      grouped[key] = grouped[key] || []
      grouped[key].push(resource)
      return grouped
    }, {})
  ), [resources])

  if (loading) {
    return <div className="container page-block"><div className="loading-box">Loading course details...</div></div>
  }

  if (error) {
    const loginRequired = /awaiting admin approval|login|required/i.test(error)
    return (
      <div className="container page-block">
        <div className="alert-box">{error}</div>
        {loginRequired && !user && (
          <Link to={`/login?returnTo=${encodeURIComponent(`/courses/${courseId}`)}`} className="primary-button small">
            Login to View Course
          </Link>
        )}
        <Link to="/courses" className="primary-button small">Back to courses</Link>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="container page-block">
        <div className="content-panel">
          <p className="eyebrow">Course not found</p>
          <h2>We could not find this course.</h2>
          <Link to="/courses" className="primary-button small">Back to courses</Link>
        </div>
      </div>
    )
  }

  const creditHours = course.credit_hours ? `${course.credit_hours} CH` : 'Not set'
  const aboutText = course.description || course.short_description || 'Course details are available from the backend.'
  const category = course.category || course.department?.name || 'General'
  const courseType = getCourseType(course)
  const courseLevel = titleCaseText(course.level || 'Not specified')
  const summary = getCourseSummary(course)
  const canAccessMaterials = Boolean(course.can_access_materials)
  const canManageCourse = Boolean(course.can_manage)
  const enrollment = course.enrollment
  const scheduleText = String(course.schedule || '').trim()

  const handleShare = async () => {
    const shareData = {
      title: formatCourseTitle(course),
      text: summary || aboutText,
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
      await sendJson('/course-enrollments/resources', { body: { resource_type: 'COURSE', resource_id: Number(courseId) } })
      const refreshed = await fetchJson(`/courses/${courseId}`)
      setCourse(refreshed)
      setActionStatus('Enrollment request submitted.')
    } catch (requestError) {
      setActionStatus(requestError.message || 'Unable to request enrollment.')
    }
  }

  const reloadMaterials = async () => {
    const [resourceData, lectureData, refreshedCourse] = await Promise.all([
      fetchJson(`/course-resources/course/${courseId}`),
      fetchJson(`/lectures/course/${courseId}`),
      fetchJson(`/courses/${courseId}`),
    ])
    setResources(resourceData)
    setLectures(lectureData)
    setCourse(refreshedCourse)
  }

  const resetResourceForm = () => {
    setResourceForm({ title: '', resource_type: 'PDF', description: '', external_url: '', use_external_link: false })
    setResourceFile(null)
    setEditingResourceId(null)
    setResourceFileInputKey((current) => current + 1)
  }

  const openAddResourceForm = () => {
    resetResourceForm()
    setIsResourceFormOpen(true)
  }

  const openEditResourceForm = (resource) => {
    setEditingResourceId(resource.id)
    setResourceForm({
      title: resource.title || '',
      resource_type: resource.resource_type || 'PDF',
      description: resource.description || '',
      external_url: resource.external_url || '',
      use_external_link: resource.resource_type === 'LINK' || Boolean(resource.external_url && !resource.file_url),
    })
    setResourceFile(null)
    setResourceFileInputKey((current) => current + 1)
    setIsResourceFormOpen(true)
  }

  const closeResourceForm = () => {
    setIsResourceFormOpen(false)
    resetResourceForm()
  }

  const submitResource = async (event) => {
    event.preventDefault()
    const isEditingResource = Boolean(editingResourceId)
    const usesExternalLink = shouldUseExternalLink(resourceForm)
    if (usesExternalLink && !resourceForm.external_url.trim()) {
      setActionStatus('Add the external link first.')
      return
    }
    if (!usesExternalLink && !isEditingResource && !resourceFile) {
      setActionStatus('Choose a file first.')
      return
    }
    try {
      setUploading(true)
      setActionStatus(isEditingResource ? 'Updating resource...' : 'Uploading resource...')
      let fileUrlValue = ''
      let fileSize = null
      let mimeType = ''
      if (resourceFile) {
        const uploaded = await uploadFile({ file: resourceFile, folder: `courses/${courseId}/resources` })
        fileUrlValue = uploaded.local_url || uploaded.public_url || uploaded.relative_path || ''
        fileSize = uploaded.size || null
        mimeType = uploaded.mime_type || ''
      }
      await sendJson(isEditingResource ? `/course-resources/${editingResourceId}` : '/course-resources', {
        method: isEditingResource ? 'PATCH' : 'POST',
        body: {
          course_id: Number(courseId),
          title: resourceForm.title,
          resource_type: resourceForm.resource_type,
          description: resourceForm.description || null,
          external_url: shouldUseExternalLink(resourceForm) ? resourceForm.external_url || null : null,
          ...(resourceFile ? {
            file_url: fileUrlValue || null,
            file_size: fileSize,
            mime_type: mimeType || null,
          } : {}),
          access_level: course.access_level || 'PUBLIC',
          is_active: true,
        },
      })
      closeResourceForm()
      await reloadMaterials()
      setActionStatus(isEditingResource ? 'Resource updated.' : 'Resource uploaded.')
    } catch (uploadError) {
      setActionStatus(uploadError.message || 'Unable to save resource.')
    } finally {
      setUploading(false)
    }
  }

  const openAddLectureForm = () => {
    setEditingLectureId(null)
    setLectureForm({ lecture_number: '', title: '', description: '', duration_minutes: '' })
    setLectureItems([])
    setDeletedLectureResourceIds([])
    setLectureItemDraft({ resource_type: 'PDF', external_url: '', file: null, use_external_link: false })
    setLectureFileInputKey((current) => current + 1)
    setIsLectureFormOpen(true)
  }

  const openEditLectureForm = (lecture) => {
    const existingItems = (resourcesByLectureNumber[String(lecture.lecture_number)] || []).map(resourceToLectureItem)
    setEditingLectureId(lecture.id)
    setLectureForm({
      lecture_number: String(lecture.lecture_number || ''),
      title: lecture.title || '',
      description: lecture.description || '',
      duration_minutes: lecture.duration_minutes == null ? '' : String(lecture.duration_minutes),
    })
    setLectureItems(existingItems)
    setDeletedLectureResourceIds([])
    setLectureItemDraft({ resource_type: 'PDF', external_url: '', file: null, use_external_link: false })
    setLectureFileInputKey((current) => current + 1)
    setIsLectureFormOpen(true)
  }

  const closeLectureForm = () => {
    setIsLectureFormOpen(false)
    setEditingLectureId(null)
    setLectureForm({ lecture_number: '', title: '', description: '', duration_minutes: '' })
    setLectureItems([])
    setDeletedLectureResourceIds([])
    setLectureItemDraft({ resource_type: 'PDF', external_url: '', file: null, use_external_link: false })
    setLectureFileInputKey((current) => current + 1)
  }

  const addLectureItem = () => {
    const usesExternalLink = shouldUseExternalLink(lectureItemDraft)
    const externalUrl = lectureItemDraft.external_url.trim()
    const file = lectureItemDraft.file
    if (usesExternalLink && !externalUrl) {
      setActionStatus('Add the external link first.')
      return
    }
    if (!usesExternalLink && !file) {
      setActionStatus('Choose a file first.')
      return
    }

    setLectureItems((current) => [
      ...current,
      {
        id: `${Date.now()}-${current.length}`,
        resource_type: lectureItemDraft.resource_type,
        file: usesExternalLink ? null : file,
        external_url: usesExternalLink ? externalUrl : '',
      },
    ])
    setLectureItemDraft({
      resource_type: lectureItemDraft.resource_type,
      external_url: '',
      file: null,
      use_external_link: lectureItemDraft.use_external_link,
    })
    setLectureFileInputKey((current) => current + 1)
  }

  const removeLectureItem = (itemId) => {
    const item = lectureItems.find((entry) => entry.id === itemId)
    if (item?.existingResourceId) {
      setDeletedLectureResourceIds((ids) => [...new Set([...ids, item.existingResourceId])])
    }
    setLectureItems((current) => current.filter((entry) => entry.id !== itemId))
  }

  const submitLecture = async (event) => {
    event.preventDefault()
    try {
      setUploading(true)
      setActionStatus('Saving lecture...')
      const lectureNumber = Number(lectureForm.lecture_number)
      const existingLecture = lectures.find((lecture) => String(lecture.lecture_number) === String(lectureNumber))
      const targetLectureId = editingLectureId || existingLecture?.id
      const existingItems = lectureItems.filter((item) => item.existingResourceId)
      const uploadedItems = await uploadLectureItems(lectureItems.filter((item) => !item.existingResourceId), `courses/${courseId}/lectures`)
      const primaryUrls = targetLectureId ? {} : getPrimaryLectureUrls(uploadedItems)

      await sendJson(targetLectureId ? `/lectures/${targetLectureId}` : '/lectures', {
        method: targetLectureId ? 'PATCH' : 'POST',
        body: {
          course_id: Number(courseId),
          lecture_number: lectureNumber,
          title: lectureForm.title,
          description: lectureForm.description || null,
          duration_minutes: lectureForm.duration_minutes ? Number(lectureForm.duration_minutes) : null,
          is_published: true,
          ...primaryUrls,
        },
      })

      await saveLectureResources({
        courseId,
        course,
        lectureNumber,
        title: lectureForm.title,
        items: uploadedItems,
      })
      await updateExistingLectureResources({
        courseId,
        course,
        lectureNumber,
        items: existingItems,
      })
      await Promise.all(deletedLectureResourceIds.map((resourceId) => deleteJson(`/course-resources/${resourceId}`)))

      await reloadMaterials()
      closeLectureForm()
      setActionStatus(targetLectureId ? 'Lecture updated.' : 'Lecture saved.')
    } catch (uploadError) {
      setActionStatus(uploadError.message || 'Unable to save lecture.')
    } finally {
      setUploading(false)
    }
  }

  const deleteLecture = async (lecture) => {
    if (!window.confirm(`Delete lecture ${lecture.lecture_number}?`)) return
    try {
      setActionStatus('Deleting lecture...')
      await deleteJson(`/lectures/${lecture.id}`)
      const linkedResources = resources.filter((resource) => String(resource.lecture_number) === String(lecture.lecture_number))
      await Promise.all(linkedResources.map((resource) => deleteJson(`/course-resources/${resource.id}`)))
      await reloadMaterials()
      setActionStatus('Lecture deleted.')
    } catch (deleteError) {
      setActionStatus(deleteError.message || 'Unable to delete lecture.')
    }
  }

  return (
    <div className="course-detail-page">
      <header className="course-detail-hero">
        <div className="container course-detail-hero-inner">
          <div className="course-detail-summary">
            <div className="course-detail-badges" aria-label="Course labels">
              <span>{courseType}</span>
              <span>{courseLevel}</span>
            </div>
            <h1>{formatCourseTitle(course)}</h1>
            {summary && <p className="course-detail-summary-text">{summary}</p>}
            <div className="course-detail-teacher">
              <div className="teacher-fact">
                <span className="teacher-avatar">{initials(course.instructor_name)}</span>
                <div>
                  <small>Teacher</small>
                  <strong>{course.instructor_name || 'Teacher not specified'}</strong>
                </div>
              </div>
            </div>
          </div>

          <aside className="course-quick-card" aria-label="Course quick facts and actions">
            <dl className="course-quick-facts">
              <div>
                <dt><Icon name="lectures" />Lectures</dt>
                <dd>{lectures.length}</dd>
              </div>
              <div>
                <dt><Icon name="lessons" />Lessons</dt>
                <dd>{resources.length}</dd>
              </div>
              <div>
                <dt><Icon name="credits" />Credit hours</dt>
                <dd className={!course.credit_hours ? 'muted-value' : ''}>{creditHours}</dd>
              </div>
              <div>
                <dt><Icon name="category" />Category</dt>
                <dd title={category}>{category}</dd>
              </div>
            </dl>

            <div className="course-quick-actions">
              <EnrollmentAction
                user={user}
                enrollment={enrollment}
                canAccess={canAccessMaterials}
                loginTo={`/login?returnTo=${encodeURIComponent(`/courses/${courseId}`)}`}
                onRequest={requestEnrollment}
              />
              <div className="course-secondary-actions">
                <a href="#syllabus">Syllabus</a>
                <button type="button" onClick={handleShare}>Share</button>
              </div>
              {shareStatus && <p className="share-toast" role="status">{shareStatus}</p>}
              {actionStatus && <p className="share-toast" role="status">{actionStatus}</p>}
            </div>
          </aside>
        </div>
      </header>

      <div className="container course-detail-layout">
        <aside className="course-menu" aria-label="Course menu">
          <h3>Course Menu</h3>
          {menuItems.map((item) => (
            <a key={item.href} href={item.href}>{item.label}</a>
          ))}
        </aside>

        <main className="course-detail-content">
          <section id="introduction" className="course-section">
            <h3>Course Introduction</h3>
            <div className="course-intro-grid">
              <figure className="course-intro-media">
                <TitleImageFallback
                  className="course-intro-image"
                  src={course.thumbnail ? fileUrl(course.thumbnail) : ''}
                  alt={`${formatCourseTitle(course)} course poster`}
                  title={formatCourseTitle(course)}
                  label={courseType}
                />
              </figure>
              <div className="about-course">
                <h4>About The Course</h4>
                <p>{aboutText}</p>
              </div>
            </div>
          </section>

          <section id="syllabus" className="course-section">
            <h3>Syllabus</h3>
            <div className="section-rule" />
            <p className="section-copy">{course.syllabus || course.short_description || 'Syllabus details can be added from the admin course form.'}</p>
          </section>

          <section id="calendar" className="course-section">
            <h3>Course Calendar</h3>
            {scheduleText ? (
              <p className="section-copy">{scheduleText}</p>
            ) : (
              <table className="course-calendar-table">
                <thead>
                  <tr>
                    <th>Lecture</th>
                    <th>Topics</th>
                  </tr>
                </thead>
                <tbody>
                  {lectures.length ? (
                    lectures.map((lecture) => (
                      <tr key={lecture.id}>
                        <td>{lecture.lecture_number}</td>
                        <td>{lecture.title}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="2">Calendar details can be added from the course schedule.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </section>

          <section id="materials" className="course-section">
            <h3>Course Material/Videos</h3>
            {!canAccessMaterials ? (
              <LockNotice user={user} enrollment={enrollment} />
            ) : (
              <table className="course-resource-table">
                <thead>
                  <tr>
                    <th>
                      <span className="materials-heading-cell">
                        Available Resources
                        {canManageCourse && isInstructorMode && (
                          <button
                            type="button"
                            className="lecture-add-button"
                            aria-label="Add lecture"
                            onClick={openAddLectureForm}
                          >
                            <PlusIcon />
                          </button>
                        )}
                      </span>
                    </th>
                    <th>Links</th>
                  </tr>
                </thead>
                <tbody>
                  {lectures.length ? (
                    lectures.map((lecture) => (
                      <tr key={lecture.id}>
                        <td>
                          <span className="lecture-title-cell">
                            <span>
                              <strong>Lecture {lecture.lecture_number}</strong>
                              {' - '}
                              {lecture.title}
                            </span>
                            {canManageCourse && isInstructorMode && (
                              <button
                                type="button"
                                className="lecture-edit-button"
                                aria-label={`Edit lecture ${lecture.lecture_number}`}
                                onClick={() => openEditLectureForm(lecture)}
                              >
                                <EditIcon />
                              </button>
                            )}
                          </span>
                        </td>
                        <td>
                          {(resourcesByLectureNumber[String(lecture.lecture_number)] || []).length ? (
                            <LectureResourceLinks resources={resourcesByLectureNumber[String(lecture.lecture_number)] || []} />
                          ) : (
                            <>
                              <LectureLink href={lecture.video_url} label="video" />
                              <LectureLink href={lecture.presentation_url} label="ppt" />
                              <LectureLink href={lecture.notes_url} label="pdf" />
                            </>
                          )}
                          {canManageCourse && isInstructorMode && (
                            <button
                              type="button"
                              className="lecture-delete-button"
                              aria-label={`Delete lecture ${lecture.lecture_number}`}
                              onClick={() => deleteLecture(lecture)}
                            >
                              <TrashIcon />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="2">No lecture material is available yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </section>

          {canManageCourse && isInstructorMode && isLectureFormOpen && (
            <LectureFormDialog
              editing={Boolean(editingLectureId)}
              lectureForm={lectureForm}
              setLectureForm={setLectureForm}
              lectureItems={lectureItems}
              lectureItemDraft={lectureItemDraft}
              lectureFileInputKey={lectureFileInputKey}
              setLectureItemDraft={setLectureItemDraft}
              addLectureItem={addLectureItem}
              removeLectureItem={removeLectureItem}
              uploading={uploading}
              onSubmit={submitLecture}
              onClose={closeLectureForm}
            />
          )}

          {canManageCourse && isInstructorMode && isResourceFormOpen && (
            <ResourceFormDialog
              editing={Boolean(editingResourceId)}
              resourceForm={resourceForm}
              setResourceForm={setResourceForm}
              setResourceFile={setResourceFile}
              resourceFileInputKey={resourceFileInputKey}
              uploading={uploading}
              onSubmit={submitResource}
              onClose={closeResourceForm}
            />
          )}

          <section id="reading" className="course-section">
            <h3 className="section-heading-with-action">
              <span>Reading Resources</span>
              {canManageCourse && isInstructorMode && (
                <button
                  type="button"
                  className="lecture-add-button"
                  aria-label="Add reading resource"
                  onClick={openAddResourceForm}
                >
                  <PlusIcon />
                </button>
              )}
            </h3>
            {!canAccessMaterials ? (
              <LockNotice user={user} enrollment={enrollment} />
            ) : (
              <ResourceRows
                resources={readingResources}
                emptyText="No reading resources are available yet."
                canManage={canManageCourse && isInstructorMode}
                onEdit={openEditResourceForm}
              />
            )}
          </section>
        </main>
      </div>
    </div>
  )
}

function ResourceFormDialog({
  editing,
  resourceForm,
  setResourceForm,
  setResourceFile,
  resourceFileInputKey,
  uploading,
  onSubmit,
  onClose,
}) {
  const usesExternalLink = shouldUseExternalLink(resourceForm)
  const showExternalToggle = !isLinkResource(resourceForm.resource_type)

  const updateResourceType = (resourceType) => {
    setResourceFile(null)
    setResourceForm({
      ...resourceForm,
      resource_type: resourceType,
      external_url: '',
      use_external_link: false,
    })
  }

  return (
    <div className="lecture-dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="lecture-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="resource-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="lecture-dialog-header">
          <h3 id="resource-dialog-title">{editing ? 'Edit reading resource' : 'Add reading resource'}</h3>
          <button type="button" className="dialog-close-button" aria-label="Close resource form" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>
        <form className="instructor-upload-form lecture-dialog-form" onSubmit={onSubmit}>
          <label>
            Title
            <input value={resourceForm.title} onChange={(event) => setResourceForm({ ...resourceForm, title: event.target.value })} required />
          </label>
          <label>
            Type
            <select value={resourceForm.resource_type} onChange={(event) => updateResourceType(event.target.value)}>
              <option value="PDF">PDF</option>
              <option value="POWERPOINT">PowerPoint</option>
              <option value="VIDEO">Video</option>
              <option value="BOOK">Book</option>
              <option value="DOCUMENT">Document</option>
              <option value="LINK">Link</option>
              <option value="OTHER">Other</option>
            </select>
          </label>
          <label className="wide">
            Description
            <textarea value={resourceForm.description} onChange={(event) => setResourceForm({ ...resourceForm, description: event.target.value })} />
          </label>
          {showExternalToggle && (
            <label className="checkbox-field resource-source-toggle wide">
              <input
                type="checkbox"
                checked={resourceForm.use_external_link}
                onChange={(event) => {
                  setResourceFile(null)
                  setResourceForm({ ...resourceForm, use_external_link: event.target.checked, external_url: '' })
                }}
              />
              Upload from external link
            </label>
          )}
          {usesExternalLink ? (
            <label className="wide">
              External link
              <input value={resourceForm.external_url} onChange={(event) => setResourceForm({ ...resourceForm, external_url: event.target.value })} placeholder="https://example.com/resource" />
            </label>
          ) : (
            <label>
              Upload
              <input key={`${resourceFileInputKey}-${resourceForm.resource_type}-${resourceForm.use_external_link}`} type="file" onChange={(event) => setResourceFile(event.target.files?.[0] || null)} />
            </label>
          )}
          <div className="lecture-dialog-actions wide">
            <button className="primary-button auth-submit" disabled={uploading}>{uploading ? 'Saving...' : editing ? 'Update Resource' : 'Upload Resource'}</button>
            <button type="button" className="secondary-action-button" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </section>
    </div>
  )
}

function LectureFormDialog({
  editing,
  lectureForm,
  setLectureForm,
  lectureItems,
  lectureItemDraft,
  lectureFileInputKey,
  setLectureItemDraft,
  addLectureItem,
  removeLectureItem,
  uploading,
  onSubmit,
  onClose,
}) {
  const usesExternalLink = shouldUseExternalLink(lectureItemDraft)
  const showExternalToggle = !isLinkResource(lectureItemDraft.resource_type)

  const updateDraftType = (resourceType) => {
    setLectureItemDraft({
      resource_type: resourceType,
      external_url: '',
      file: null,
      use_external_link: false,
    })
  }

  return (
    <div className="lecture-dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="lecture-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lecture-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="lecture-dialog-header">
          <h3 id="lecture-dialog-title">{editing ? 'Edit lecture' : 'Add lecture'}</h3>
          <button type="button" className="dialog-close-button" aria-label="Close lecture form" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>
        <form className="instructor-upload-form lecture-dialog-form" onSubmit={onSubmit}>
          <label>
            Lecture number
            <input type="number" min="1" value={lectureForm.lecture_number} onChange={(event) => setLectureForm({ ...lectureForm, lecture_number: event.target.value })} required />
          </label>
          <label>
            Title
            <input value={lectureForm.title} onChange={(event) => setLectureForm({ ...lectureForm, title: event.target.value })} required />
          </label>
          <label>
            Duration minutes
            <input type="number" min="0" value={lectureForm.duration_minutes} onChange={(event) => setLectureForm({ ...lectureForm, duration_minutes: event.target.value })} />
          </label>
          <label className="wide">
            Description
            <textarea value={lectureForm.description} onChange={(event) => setLectureForm({ ...lectureForm, description: event.target.value })} />
          </label>
          <div className="lecture-material-builder">
            <label>
              Type
              <select value={lectureItemDraft.resource_type} onChange={(event) => updateDraftType(event.target.value)}>
                <option value="VIDEO">Video lecture</option>
                <option value="POWERPOINT">PPT / slides</option>
                <option value="PDF">PDF</option>
                <option value="DOCUMENT">Document</option>
                <option value="LINK">Link</option>
              </select>
            </label>
            {showExternalToggle && (
              <label className="checkbox-field resource-source-toggle">
                <input
                  type="checkbox"
                  checked={lectureItemDraft.use_external_link}
                  onChange={(event) => setLectureItemDraft({
                    ...lectureItemDraft,
                    use_external_link: event.target.checked,
                    external_url: '',
                    file: null,
                  })}
                />
                Upload from external link
              </label>
            )}
            {usesExternalLink ? (
              <label className="wide">
                External link
                <input value={lectureItemDraft.external_url} onChange={(event) => setLectureItemDraft({ ...lectureItemDraft, external_url: event.target.value })} placeholder="https://example.com/lecture-resource" />
              </label>
            ) : (
              <label>
                Upload
                <input key={`${lectureFileInputKey}-${lectureItemDraft.resource_type}-${lectureItemDraft.use_external_link}`} type="file" onChange={(event) => setLectureItemDraft({ ...lectureItemDraft, file: event.target.files?.[0] || null })} />
              </label>
            )}
            <button type="button" className="secondary-action-button lecture-stack-add" onClick={addLectureItem}>
              Add to Stack
            </button>
          </div>
          <div className="lecture-stack-list">
            {lectureItems.length ? (
              lectureItems.map((item, index) => (
                <div className="lecture-stack-item" key={item.id}>
                  <span>{index + 1}</span>
                  <strong>{formatMaterialType(item.resource_type)}</strong>
                  <small>{getLectureItemSummary(item)}</small>
                  <button type="button" aria-label="Remove material" onClick={() => removeLectureItem(item.id)}>
                    <CloseIcon />
                  </button>
                </div>
              ))
            ) : (
              <p>No material added yet.</p>
            )}
          </div>
          <div className="lecture-dialog-actions">
            <button className="primary-button auth-submit" disabled={uploading}>{uploading ? 'Saving...' : editing ? 'Update Lecture' : 'Save Lecture'}</button>
            <button type="button" className="secondary-action-button" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </section>
    </div>
  )
}

function PlusIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
      <path d="M8 3v10M3 8h10" />
    </svg>
  )
}

function EditIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
      <path d="M3 11.5V13h1.5l7.1-7.1-1.5-1.5L3 11.5zM10.8 3.7l1.5 1.5.7-.7a1.05 1.05 0 0 0-1.5-1.5z" />
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
      <path d="M4.5 4.5 11.5 11.5M11.5 4.5 4.5 11.5" />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
      <path d="M3 4.5h10M6 4.5V3h4v1.5M5 6v6.5h6V6M7 7.5v3.5M9 7.5v3.5" />
    </svg>
  )
}

function EnrollmentAction({ user, enrollment, canAccess, loginTo, onRequest }) {
  if (canAccess) return <a className="course-start-button" href="#materials">Access Content</a>
  if (!user) return <Link className="course-start-button" to={loginTo}>Login to Request Enrollment</Link>
  if (enrollment?.status === 'PENDING') return <button className="course-start-button" type="button" disabled>Awaiting Admin Approval</button>
  if (['REJECTED', 'REVOKED'].includes(enrollment?.status)) return <button className="course-start-button" type="button" onClick={onRequest}>Request Enrollment Again</button>
  return <button className="course-start-button" type="button" onClick={onRequest}>Request Enrollment</button>
}

function LockNotice({ user, enrollment }) {
  const reason = enrollment?.review_reason
  const text = !user
    ? 'Login to request enrollment for the learning material.'
    : enrollment?.status === 'PENDING'
      ? 'Your enrollment request is awaiting admin approval.'
      : reason || 'Learning material is locked until your enrollment is approved.'
  return <p className="lock-notice">{text}</p>
}

function Icon({ name }) {
  const paths = {
    lectures: 'M3 3.5h10v9H3z M5 6h6 M5 8h6 M5 10h3',
    lessons: 'M3 4h4.5A2.5 2.5 0 0 1 10 6.5V13a2.5 2.5 0 0 0-2.5-2.5H3z M10 6.5A2.5 2.5 0 0 1 12.5 4H13v6.5h-.5A2.5 2.5 0 0 0 10 13z',
    credits: 'M8 2.75 9.55 5.9l3.48.51-2.52 2.46.6 3.46L8 10.7l-3.11 1.63.6-3.46-2.52-2.46 3.48-.51z',
    category: 'M2.8 4.2h4.6l1 1.3h4.8v6.3H2.8z',
  }

  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false" className={`fact-icon ${name}`}>
      <path d={paths[name]} />
    </svg>
  )
}

function LectureLink({ href, label }) {
  if (!href) return <span className="muted-resource">{label}</span>
  return <a href={fileUrl(href)} target="_blank" rel="noreferrer">{label}</a>
}

function LectureResourceLinks({ resources }) {
  return resources.map((resource) => {
    const href = resource.file_url || resource.external_url
    if (!href) return null
    return (
      <a key={resource.id} href={fileUrl(href)} target="_blank" rel="noreferrer">
        {formatResourceLinkLabel(resource)}
      </a>
    )
  })
}

function resourceToLectureItem(resource) {
  return {
    id: `resource-${resource.id}`,
    existingResourceId: resource.id,
    resource_type: resource.resource_type || 'PDF',
    title: resource.title || '',
    file_url: resource.file_url || '',
    external_url: resource.external_url || '',
    file_size: resource.file_size || null,
    mime_type: resource.mime_type || null,
  }
}

function getLectureItemSummary(item) {
  return item.file?.name || item.title || item.external_url || fileNameFromUrl(item.file_url, 'Saved resource')
}

function isLinkResource(resourceType) {
  return String(resourceType || '').toUpperCase() === 'LINK'
}

function shouldUseExternalLink(resource) {
  return isLinkResource(resource.resource_type) || Boolean(resource.use_external_link)
}

async function uploadLectureItems(items, folder) {
  const uploadedItems = []
  for (const item of items) {
    if (item.file) {
      const uploaded = await uploadFile({ file: item.file, folder })
      const url = uploaded.local_url || uploaded.public_url || uploaded.relative_path || ''
      if (url) {
        uploadedItems.push({
          ...item,
          file_url: url,
          file_size: uploaded.size || item.file.size || null,
          mime_type: uploaded.mime_type || item.file.type || null,
        })
      }
      continue
    }

    if (item.external_url) uploadedItems.push(item)
  }
  return uploadedItems
}

async function saveLectureResources({ courseId, course, lectureNumber, title, items }) {
  const resourceRequests = items.map((item, index) => sendJson('/course-resources', {
    body: {
      course_id: Number(courseId),
      title: `${title} - ${item.file?.name || formatMaterialType(item.resource_type)} ${index + 1}`,
      resource_type: item.resource_type,
      file_url: item.file_url || null,
      external_url: item.external_url || null,
      file_size: item.file_size || null,
      mime_type: item.mime_type || null,
      lecture_number: lectureNumber,
      access_level: course.access_level || 'PUBLIC',
      is_active: true,
    },
  }))

  await Promise.all(resourceRequests)
}

async function updateExistingLectureResources({ courseId, course, lectureNumber, items }) {
  const updateRequests = items.map((item, index) => sendJson(`/course-resources/${item.existingResourceId}`, {
    method: 'PATCH',
    body: {
      course_id: Number(courseId),
      resource_type: item.resource_type,
      file_url: item.file_url || null,
      external_url: item.external_url || null,
      file_size: item.file_size || null,
      mime_type: item.mime_type || null,
      lecture_number: lectureNumber,
      display_order: index + 1,
      access_level: course.access_level || 'PUBLIC',
      is_active: true,
    },
  }))

  await Promise.all(updateRequests)
}

function getPrimaryLectureUrls(items) {
  const firstVideo = items.find((item) => item.resource_type === 'VIDEO' && (item.file_url || item.external_url))
  const firstPresentation = items.find((item) => item.resource_type === 'POWERPOINT' && (item.file_url || item.external_url))
  const firstPdf = items.find((item) => ['PDF', 'DOCUMENT'].includes(item.resource_type) && (item.file_url || item.external_url))

  return {
    ...(firstVideo ? { video_url: firstVideo.file_url || firstVideo.external_url } : {}),
    ...(firstPresentation ? { presentation_url: firstPresentation.file_url || firstPresentation.external_url } : {}),
    ...(firstPdf ? { notes_url: firstPdf.file_url || firstPdf.external_url } : {}),
  }
}

function formatResourceLinkLabel(resource) {
  const type = String(resource.resource_type || '').toLowerCase()
  if (type.includes('power')) return 'ppt'
  if (type.includes('video')) return 'video'
  if (type.includes('pdf') || type.includes('document') || type.includes('book')) return 'pdf'
  if (resource.external_url) return 'link'
  return 'file'
}

function formatMaterialType(type) {
  const normalized = String(type || '').toUpperCase()
  if (normalized === 'POWERPOINT') return 'PPT'
  if (normalized === 'VIDEO') return 'Video'
  if (normalized === 'PDF') return 'PDF'
  if (normalized === 'DOCUMENT') return 'Document'
  if (normalized === 'LINK') return 'Link'
  return 'File'
}

function ResourceRows({ resources, emptyText, canManage = false, onEdit }) {
  if (!resources.length) return <p className="empty-state">{emptyText}</p>

  return (
    <table className="course-resource-table">
      <tbody>
        {resources.map((resource) => (
          <tr key={resource.id}>
            <td>
              <strong>{resource.title}</strong>
              {resource.description && <span>{resource.description}</span>}
            </td>
            <td>
              {resource.external_url && <a href={fileUrl(resource.external_url)} target="_blank" rel="noreferrer">link</a>}
              {resource.file_url && (
                <>
                  <a href={fileUrl(resource.file_url)} target="_blank" rel="noreferrer">view</a>
                  <a href={fileUrl(resource.file_url)} download={fileNameFromUrl(resource.file_url, resource.title)}>download</a>
                </>
              )}
              {canManage && (
                <button
                  type="button"
                  className="lecture-edit-button resource-edit-button"
                  aria-label={`Edit ${resource.title}`}
                  onClick={() => onEdit(resource)}
                >
                  <EditIcon />
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function formatCourseTitle(course) {
  const title = course.title || 'Untitled course'
  return course.course_code ? `${title} - ${course.course_code}` : title
}

function getCourseType(course) {
  return titleCaseText(course.course_type || course.category || (course.semester ? 'Semester' : 'Hybrid'))
}

function getCourseSummary(course) {
  const value = String(course.short_description || course.description || '').trim()
  if (!value || value === 'Course details are available from the backend.') return ''
  return value
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
  if (!value) return 'T'
  return value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

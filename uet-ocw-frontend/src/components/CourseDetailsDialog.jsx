import { useEffect, useRef, useState } from 'react'
import { fileUrl, sendJson, uploadFile } from '../data/api'
import TitleImageFallback from './TitleImageFallback'

const textFields = [
  ['short_description', 'Short description'],
  ['description', 'About the course'],
  ['syllabus', 'Syllabus'],
  ['learning_outcomes', 'Learning outcomes'],
  ['schedule', 'Course calendar'],
]

export default function CourseDetailsDialog({ course, initialField = 'title', onSaved, onClose }) {
  const dialogRef = useRef(null)
  const fileInputRef = useRef(null)
  const [form, setForm] = useState(() => ({
    title: course.title || '',
    thumbnail: course.thumbnail || '',
    ...Object.fromEntries(textFields.map(([field]) => [field, course[field] || ''])),
  }))
  const [thumbnailFile, setThumbnailFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const dialog = dialogRef.current
    dialog.showModal()
    dialog.querySelector(`[name="${initialField}"]`)?.focus()
    return () => dialog.close()
  }, [initialField])

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }))

  const selectImage = (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setError('Choose an image file for the course image.')
      event.target.value = ''
      return
    }
    setError('')
    setThumbnailFile(file)
    setPreviewUrl(URL.createObjectURL(file))
  }

  const removeImage = () => {
    setThumbnailFile(null)
    setPreviewUrl('')
    update('thumbnail', '')
    fileInputRef.current.value = ''
  }

  const submit = async (event) => {
    event.preventDefault()
    if (saving) return
    if (!form.title.trim()) {
      setError('Enter a course name.')
      dialogRef.current.querySelector('[name="title"]')?.focus()
      return
    }

    try {
      setSaving(true)
      setError('')
      let thumbnail = form.thumbnail
      if (thumbnailFile) {
        const uploaded = await uploadFile({ file: thumbnailFile, folder: `courses/${course.id}/thumbnails` })
        thumbnail = uploaded.local_url || uploaded.public_url || uploaded.relative_path
        if (!thumbnail) throw new Error('The image upload did not return a file URL. Please try again.')
        // Keep the uploaded image if saving the course fails, so a retry reuses it.
        update('thumbnail', thumbnail)
        setThumbnailFile(null)
        setPreviewUrl('')
        fileInputRef.current.value = ''
      }
      const saved = await sendJson(`/courses/${course.id}`, {
        method: 'PATCH',
        body: {
          title: form.title.trim(),
          thumbnail: thumbnail || null,
          ...Object.fromEntries(textFields.map(([field]) => [field, form[field].trim() || null])),
        },
      })
      onSaved(saved)
    } catch (saveError) {
      setError(saveError.message || 'Unable to save course details. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="lecture-dialog course-details-dialog"
      aria-labelledby="course-details-dialog-title"
      onCancel={(event) => {
        event.preventDefault()
        if (!saving) onClose()
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget && !saving) onClose()
      }}
    >
      <div className="lecture-dialog-header">
        <h3 id="course-details-dialog-title">Edit course details</h3>
        <button type="button" className="dialog-close-button" aria-label="Close course details" disabled={saving} onClick={onClose}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg>
        </button>
      </div>
      <form onSubmit={submit}>
        <fieldset className="instructor-upload-form lecture-dialog-form course-details-fields" disabled={saving}>
          <label className="wide">
            Course name
            <input name="title" value={form.title} onChange={(event) => update('title', event.target.value)} maxLength={255} required />
          </label>
          <div className="course-image-editor">
            <TitleImageFallback
              className="course-details-image-preview"
              src={previewUrl || fileUrl(form.thumbnail)}
              alt="Course image preview"
              title={form.title}
            />
            <label>
              Course image
              <input ref={fileInputRef} type="file" accept="image/*" onChange={selectImage} />
            </label>
            <p>Choose a new image to replace the current one.</p>
            {(form.thumbnail || thumbnailFile) && (
              <button type="button" className="secondary-action-button" onClick={removeImage}>Remove image</button>
            )}
          </div>
          {textFields.map(([field, label]) => (
            <label className="wide" key={field}>
              {label}
              <textarea name={field} value={form[field]} onChange={(event) => update(field, event.target.value)} rows={field === 'short_description' ? 2 : 4} />
            </label>
          ))}
          {error && <div className="alert-box course-details-feedback" role="alert">{error}</div>}
          <div className="lecture-dialog-actions">
            <button type="submit" className="primary-button auth-submit">{saving ? 'Saving...' : 'Save changes'}</button>
            <button type="button" className="secondary-action-button" onClick={onClose}>Cancel</button>
          </div>
        </fieldset>
      </form>
    </dialog>
  )
}

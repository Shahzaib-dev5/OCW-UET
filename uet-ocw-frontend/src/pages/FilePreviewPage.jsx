import { useEffect, useState } from 'react'
import DOMPurify from 'dompurify'
import mammoth from 'mammoth/mammoth.browser'
import { authenticatedUploadHeaders, fileNameFromUrl } from '../data/api'

const WORD_DOCUMENT = /\.(docx)(?:[?#]|$)/i

export default function FilePreviewPage() {
  const source = new URLSearchParams(window.location.search).get('file') || ''
  const [preview, setPreview] = useState({ loading: true, error: '', html: '', objectUrl: '', type: '' })

  useEffect(() => {
    let active = true
    let objectUrl = ''

    async function loadPreview() {
      if (!source) {
        setPreview({ loading: false, error: 'No file was selected for preview.', html: '', objectUrl: '', type: '' })
        return
      }
      try {
        const response = await fetch(source, { headers: authenticatedUploadHeaders(source) })
        if (!response.ok) throw new Error(response.status === 403 ? 'You do not have permission to view this file.' : 'Unable to load this file.')
        const blob = await response.blob()

        if (WORD_DOCUMENT.test(source)) {
          const result = await mammoth.convertToHtml({ arrayBuffer: await blob.arrayBuffer() })
          if (active) setPreview({ loading: false, error: '', html: DOMPurify.sanitize(result.value), objectUrl: '', type: 'word' })
          return
        }

        objectUrl = URL.createObjectURL(blob)
        if (active) setPreview({ loading: false, error: '', html: '', objectUrl, type: blob.type })
      } catch (error) {
        if (active) setPreview({ loading: false, error: error.message || 'Unable to preview this file.', html: '', objectUrl: '', type: '' })
      }
    }

    loadPreview()
    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [source])

  return (
    <section className="file-preview-page">
      <header className="file-preview-header">
        <div>
          <p className="eyebrow">Document preview</p>
          <h1>{fileNameFromUrl(source, 'Resource')}</h1>
        </div>
        {source && <a className="secondary-action-button" href={source} download={fileNameFromUrl(source)}>Download</a>}
      </header>
      {preview.loading && <p className="status-note">Loading preview...</p>}
      {preview.error && <p className="status-note error">{preview.error}</p>}
      {preview.html && <article className="word-document-preview" dangerouslySetInnerHTML={{ __html: preview.html }} />}
      {preview.objectUrl && <object className="native-file-preview" data={preview.objectUrl} type={preview.type} aria-label="File preview"><p>This file cannot be previewed by your browser. Use Download instead.</p></object>}
    </section>
  )
}

import { useEffect, useState } from 'react'
import DOMPurify from 'dompurify'
import mammoth from 'mammoth/mammoth.browser'
import { authenticatedUploadHeaders, fileNameFromUrl, wordPreviewUrl } from '../data/api'
import { readWordPreview } from '../data/readWordPreview'

const WORD_DOCUMENT = /\.(docx)(?:[?#]|$)/i

export default function FilePreviewPage() {
  const source = new URLSearchParams(window.location.search).get('file') || ''
  const [preview, setPreview] = useState({
    loading: true, error: '', html: '', objectUrl: '', type: '', loaded: 0, total: 0, stage: 'download',
  })

  useEffect(() => {
    let active = true
    let objectUrl = ''
    const controller = new AbortController()

    async function loadPreview() {
      if (!source) {
        setPreview({ loading: false, error: 'No file was selected for preview.', html: '', objectUrl: '', type: '', loaded: 0, total: 0, stage: '' })
        return
      }
      try {
        if (WORD_DOCUMENT.test(source)) {
          const arrayBuffer = await readWordPreview(
            wordPreviewUrl(source), authenticatedUploadHeaders(source), controller.signal,
            ({ loaded, total }) => {
              if (active) setPreview((current) => ({ ...current, loaded, total, stage: 'download' }))
            },
          )
          if (active) setPreview((current) => ({ ...current, stage: 'convert' }))
          const result = await mammoth.convertToHtml({ arrayBuffer })
          if (active) setPreview({ loading: false, error: '', html: DOMPurify.sanitize(result.value), objectUrl: '', type: 'word', loaded: arrayBuffer.byteLength, total: arrayBuffer.byteLength, stage: '' })
          return
        }

        const requestUrl = new URL(source, window.location.href)
        requestUrl.searchParams.set('_preview', Date.now().toString())
        const response = await fetch(requestUrl, {
          headers: authenticatedUploadHeaders(source),
          cache: 'no-store',
          signal: controller.signal,
        })
        if (!response.ok) {
          throw new Error(response.status === 403
            ? 'You do not have permission to view this file.'
            : `Unable to load this file (HTTP ${response.status}).`)
        }
        const blob = await readResponseBlob(response, ({ loaded, total }) => {
          if (active) setPreview((current) => ({ ...current, loaded, total, stage: 'download' }))
        })

        if (!active) return
        objectUrl = URL.createObjectURL(blob)
        setPreview({ loading: false, error: '', html: '', objectUrl, type: blob.type, loaded: blob.size, total: blob.size, stage: '' })
      } catch (error) {
        if (active) setPreview({ loading: false, error: error.message || 'Unable to preview this file.', html: '', objectUrl: '', type: '', loaded: 0, total: 0, stage: '' })
      }
    }

    loadPreview()
    return () => {
      active = false
      controller.abort()
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
      {preview.loading && <PreviewProgress preview={preview} />}
      {preview.error && <p className="status-note error">{preview.error}</p>}
      {preview.html && <article className="word-document-preview" dangerouslySetInnerHTML={{ __html: preview.html }} />}
      {preview.objectUrl && <object className="native-file-preview" data={preview.objectUrl} type={preview.type} aria-label="File preview"><p>This file cannot be previewed by your browser. Use Download instead.</p></object>}
    </section>
  )
}

function PreviewProgress({ preview }) {
  const percent = preview.total ? Math.min(100, Math.round((preview.loaded / preview.total) * 100)) : 0
  const message = preview.stage === 'convert'
    ? 'Preparing document preview...'
    : preview.total
      ? `Downloading preview... ${percent}%`
      : 'Starting preview download...'

  return (
    <div className="preview-progress status-note" role="status" aria-live="polite">
      <p>{message}</p>
      {preview.stage === 'download' && preview.total > 0 && (
        <progress max="100" value={percent} aria-label={`Preview download ${percent}%`} />
      )}
    </div>
  )
}

async function readResponseBlob(response, onProgress) {
  const total = Number(response.headers.get('Content-Length')) || 0
  if (!response.body?.getReader) return response.blob()

  const reader = response.body.getReader()
  const chunks = []
  let loaded = 0
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    chunks.push(value)
    loaded += value.byteLength
    onProgress({ loaded, total })
  }
  return new Blob(chunks, { type: response.headers.get('Content-Type') || 'application/octet-stream' })
}

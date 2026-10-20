import { useEffect, useState } from 'react'
import { authenticatedUploadHeaders } from '../data/api'

export default function TitleImageFallback(props) {
  const authorization = authenticatedUploadHeaders(props.src).Authorization
  if (authorization) {
    return <AuthenticatedImage key={`${props.src}:${authorization}`} {...props} authorization={authorization} />
  }
  return <ImageWithFallback {...props} />
}

function AuthenticatedImage({ src, authorization, ...props }) {
  const [imageSrc, setImageSrc] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    let objectUrl = ''

    async function loadImage() {
      try {
        const response = await fetch(src, {
          headers: { Authorization: authorization },
          signal: controller.signal,
          redirect: 'error',
        })
        if (!response.ok) throw new Error('Unable to load image')
        const blob = await response.blob()
        if (controller.signal.aborted) return
        objectUrl = URL.createObjectURL(blob)
        setImageSrc(objectUrl)
      } catch {
        if (!controller.signal.aborted) setImageSrc('')
      }
    }

    loadImage()
    return () => {
      controller.abort()
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [src, authorization])

  return <ImageWithFallback {...props} src={imageSrc} />
}

function ImageWithFallback({
  src,
  alt = '',
  title,
  label,
  className = '',
  loading = 'lazy',
}) {
  const [failedSrc, setFailedSrc] = useState('')

  const hasFailed = Boolean(src && failedSrc === src)

  if (src && !hasFailed) {
    return (
      <img
        className={className}
        src={src}
        alt={alt}
        loading={loading}
        onError={() => setFailedSrc(src)}
      />
    )
  }

  return (
    <div className={`${className} title-image-fallback`} role={alt ? 'img' : undefined} aria-label={alt || undefined}>
      {label && <span className="title-image-label">{label}</span>}
      <strong>{title || 'Open Courseware'}</strong>
    </div>
  )
}

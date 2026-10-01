import { useState } from 'react'

export default function TitleImageFallback({
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

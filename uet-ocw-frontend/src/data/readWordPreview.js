const CHUNK_SIZE = 2 * 1024 * 1024
const CONTENT_RANGE = /^bytes (\d+)-(\d+)\/(\d+)$/

export async function readWordPreview(url, headers, signal) {
  const parts = []
  let offset = 0
  let total

  do {
    const end = Math.min(offset + CHUNK_SIZE, total ?? Infinity) - 1
    const { body, range } = await readChunk(url, headers, signal, offset, end)
    if (total !== undefined && total !== range.total) {
      throw new Error('The file changed while loading. Reopen the preview to try again.')
    }
    parts.push(body)
    total = range.total
    offset = range.end + 1
  } while (offset < total)

  return new Blob(parts).arrayBuffer()
}

async function readChunk(url, headers, signal, offset, end) {
  for (let attempt = 1; ; attempt += 1) {
    try {
      const response = await fetch(url, {
        headers: { ...headers, Range: `bytes=${offset}-${end}` },
        cache: 'no-store',
        signal,
      })
      if (response.status === 401 || response.status === 403) {
        throw new Error('You do not have permission to view this file.')
      }
      if (response.status !== 206) {
        throw new Error(`Unable to load this file (HTTP ${response.status}).`)
      }

      const match = CONTENT_RANGE.exec(response.headers.get('Content-Range') || '')
      const body = await response.arrayBuffer()
      if (match) {
        const [, rangeStart, rangeEnd, rangeTotal] = match.map(Number)
        if (rangeStart === offset && rangeEnd === Math.min(end, rangeTotal - 1)
          && body.byteLength === rangeEnd - rangeStart + 1 && body.byteLength > 0) {
          return { body, range: { end: rangeEnd, total: rangeTotal } }
        }
      }
      throw new TypeError('The server returned an incomplete part of the document.')
    } catch (error) {
      if (signal.aborted || !(error instanceof TypeError)) throw error
      if (attempt === 3) throw new Error('The connection was interrupted while loading the document. Reopen the preview to retry.')
    }
  }
}

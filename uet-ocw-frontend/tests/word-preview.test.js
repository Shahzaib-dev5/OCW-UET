import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readWordPreview } from '../src/data/readWordPreview.js'

test('retries an interrupted chunk and reconstructs the whole document', async (t) => {
  const chunkSize = 2 * 1024 * 1024
  const file = new Uint8Array(chunkSize + 5).fill(23)
  file.fill(42, chunkSize)
  const ranges = []

  t.mock.method(globalThis, 'fetch', async (url, { headers }) => {
    assert.equal(headers.Authorization, 'Bearer sample')
    ranges.push(headers.Range)
    const [, start, requestedEnd] = /^bytes=(\d+)-(\d+)$/.exec(headers.Range).map(Number)
    const end = Math.min(requestedEnd, file.length - 1)
    const bytes = file.subarray(start, end + 1)

    return new Response(ranges.length === 2 ? bytes.subarray(0, 2) : bytes, {
      status: 206,
      headers: { 'Content-Range': `bytes ${start}-${end}/${file.length}` },
    })
  })

  const result = await readWordPreview('/api/upload-preview', { Authorization: 'Bearer sample' }, new AbortController().signal)
  const finalRange = `bytes=${chunkSize}-${file.length - 1}`
  assert.deepEqual(ranges, [`bytes=0-${chunkSize - 1}`, finalRange, finalRange])
  assert.deepEqual(new Uint8Array(result), file)
})

test('downloads later chunks concurrently and reports progress', async (t) => {
  const chunkSize = 2 * 1024 * 1024
  const file = new Uint8Array((chunkSize * 3) + 7).fill(17)
  const inFlight = new Set()
  let maximumInFlight = 0
  const progress = []

  t.mock.method(globalThis, 'fetch', async (url, { headers }) => {
    const [, start, requestedEnd] = /^bytes=(\d+)-(\d+)$/.exec(headers.Range).map(Number)
    const end = Math.min(requestedEnd, file.length - 1)
    inFlight.add(start)
    maximumInFlight = Math.max(maximumInFlight, inFlight.size)
    await new Promise((resolve) => setTimeout(resolve, start === 0 ? 0 : 5))
    inFlight.delete(start)
    return new Response(file.subarray(start, end + 1), {
      status: 206,
      headers: { 'Content-Range': `bytes ${start}-${end}/${file.length}` },
    })
  })

  const result = await readWordPreview(
    '/api/upload-preview', {}, new AbortController().signal,
    ({ loaded, total }) => progress.push([loaded, total]),
  )

  assert.deepEqual(new Uint8Array(result), file)
  assert.ok(maximumInFlight > 1)
  assert.deepEqual(progress.at(-1), [file.length, file.length])
})

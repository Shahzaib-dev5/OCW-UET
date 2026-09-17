const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export async function fetchJson(endpoint) {
  const response = await fetch(`${API_BASE_URL}/api${endpoint}`)
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.message || 'Unable to load data.')
  }

  const data = payload.data ?? []
  if (Array.isArray(data) && data.some((item) => Object.prototype.hasOwnProperty.call(item, 'display_order'))) {
    return [...data].sort(byDisplayOrder)
  }

  return data
}

export async function sendJson(endpoint, { method = 'POST', body, token } = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...authHeader(token),
  }

  const response = await fetch(`${API_BASE_URL}/api${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.message || 'Unable to save data.')
  }

  return payload.data ?? payload
}

export async function deleteJson(endpoint, { token } = {}) {
  const response = await fetch(`${API_BASE_URL}/api${endpoint}`, {
    method: 'DELETE',
    headers: authHeader(token),
  })
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.message || 'Unable to delete data.')
  }

  return payload
}

export async function uploadFile({ file, folder, token }) {
  const formData = new FormData()
  formData.append('file', file)
  if (folder) formData.append('folder', folder)

  const response = await fetch(`${API_BASE_URL}/api/uploads`, {
    method: 'POST',
    headers: authHeader(token),
    body: formData,
  })
  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(payload.message || 'Unable to upload file.')
  }

  return payload
}

export function fileUrl(url) {
  if (!url) return ''
  if (/^(https?:)?\/\//i.test(url) || url.startsWith('data:') || url.startsWith('blob:')) {
    return url
  }
  const path = url.startsWith('/') ? url : `/${url}`
  return `${API_BASE_URL}${path}`
}

export function fileNameFromUrl(url, fallback = 'resource') {
  const value = String(url || '').split('?')[0].split('#')[0]
  const filename = value.split('/').filter(Boolean).pop()
  return filename || fallback
}

function authHeader(token) {
  const value = token || localStorage.getItem('ocw_access_token') || ''
  return value ? { Authorization: `Bearer ${value}` } : {}
}

function byDisplayOrder(left, right) {
  const leftOrder = normalizedOrder(left.display_order)
  const rightOrder = normalizedOrder(right.display_order)

  if (leftOrder !== rightOrder) return leftOrder - rightOrder
  return Number(left.id || 0) - Number(right.id || 0)
}

function normalizedOrder(value) {
  const order = Number(value)
  if (!Number.isFinite(order) || order <= 0) return Number.MAX_SAFE_INTEGER
  return order
}

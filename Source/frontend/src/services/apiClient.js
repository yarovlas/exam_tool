import { getRawToken } from './authStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

function buildUrl(path, query = {}) {
  const url = new URL(`${API_BASE_URL}${path}`)

  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, String(value))
    }
  })

  return url.toString()
}

async function readError(response) {
  const payload = await response.json().catch(() => null)

  if (payload?.detail) {
    return typeof payload.detail === 'string' ? payload.detail : 'Verzoek mislukt'
  }

  return `Verzoek mislukt (${response.status})`
}

export async function request(path, options = {}) {
  const token = getRawToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers ?? {}),
  }

  const response = await fetch(buildUrl(path, options.query), {
    method: options.method ?? 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  if (response.status === 204) return null

  return response.json()
}

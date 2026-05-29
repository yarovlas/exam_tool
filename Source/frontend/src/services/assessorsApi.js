const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

const buildUrl = (path, query = {}) => {
  const url = new URL(`${API_BASE_URL}${path}`)

  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, String(value))
    }
  })

  return url.toString()
}

const readError = async (response) => {
  const payload = await response.json().catch(() => null)

  if (payload?.detail) {
    return typeof payload.detail === 'string' ? payload.detail : 'Verzoek mislukt'
  }

  return `Verzoek mislukt (${response.status})`
}

const request = async (path, options = {}) => {
  const response = await fetch(buildUrl(path, options.query), {
    method: options.method ?? 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  if (response.status === 204) return null

  return response.json()
}

export const listAssessors = ({ assessor_type = null, limit = 100, offset = 0, q = '' } = {}) => {
  const query = { limit, offset }
  if (assessor_type) query.assessor_type = assessor_type
  if (q) query.q = q
  return request('/assessors', { query })
}

export const createAssessor = (payload) => {
  return request('/assessors', { method: 'POST', body: payload })
}

export const getAssessor = (id) => {
  return request(`/assessors/${id}`)
}

export const updateAssessor = (id, payload) => {
  return request(`/assessors/${id}`, { method: 'PATCH', body: payload })
}

export const deleteAssessor = (id) => {
  return request(`/assessors/${id}`, { method: 'DELETE' })
}

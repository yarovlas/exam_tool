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

  return response.json()
}

export const listExamPlanning = ({ limit = 50, offset = 0 } = {}) => {
  return request('/exam-planning', { query: { limit, offset } })
}

export const createExamPlanning = (payload) => {
  return request('/exam-planning', {
    method: 'POST',
    body: payload,
  })
}

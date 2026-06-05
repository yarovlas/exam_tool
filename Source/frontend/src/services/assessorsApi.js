import { request } from './apiClient'

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

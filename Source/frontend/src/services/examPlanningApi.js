import { request } from './apiClient'

export const listExamPlanning = ({ limit = 50, offset = 0 } = {}) => {
  return request('/exam-planning', { query: { limit, offset } })
}

export const createExamPlanning = (payload) => {
  return request('/exam-planning', {
    method: 'POST',
    body: payload,
  })
}

export const updateExamPlanning = (id, payload) => {
  return request(`/exam-planning/${id}`, {
    method: 'PATCH',
    body: payload,
  })
}

export const deleteExamPlanning = (id) => {
  return request(`/exam-planning/${id}`, {
    method: 'DELETE',
  })
}

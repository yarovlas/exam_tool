import { request } from './apiClient'

export const listStudents = ({ limit = 500, offset = 0 } = {}) => {
  return request('/students', { query: { limit, offset } })
}

export const getStudent = (id) => {
  return request(`/students/${id}`)
}

export const createStudent = (payload) => {
  return request('/students', { method: 'POST', body: payload })
}

export const updateStudent = (id, payload) => {
  return request(`/students/${id}`, { method: 'PATCH', body: payload })
}

export const deleteStudent = (id) => {
  return request(`/students/${id}`, { method: 'DELETE' })
}

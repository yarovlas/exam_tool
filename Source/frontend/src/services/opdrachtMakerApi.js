import { request } from './apiClient'

export const getOpdrachtMakerContext = (examStudentId) => {
  return request(`/opdracht-maker/context/${examStudentId}`)
}

export const getOpdrachtMakerContextByExamStudent = (examId, studentId) => {
  return request(`/opdracht-maker/context/${examId}/${studentId}`)
}

export const calculateOpdracht = (payload) => {
  return request('/opdracht-maker/calculate', { method: 'POST', body: payload })
}

export const createOpdracht = (payload) => {
  return request('/opdracht-maker/create', { method: 'POST', body: payload })
}

export const autoAssignSurprises = (payload) => {
  return request('/opdracht-maker/batch/auto-assign-surprises', { method: 'POST', body: payload })
}

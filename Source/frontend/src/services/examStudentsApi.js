import { request } from './apiClient'

export const listExamStudents = ({ exam_planning_id = null, student_id = null, limit = 500, offset = 0 } = {}) => {
  const query = { limit, offset }
  if (exam_planning_id) query.exam_planning_id = exam_planning_id
  if (student_id) query.student_id = student_id
  return request('/exam-students', { query })
}

export const createExamStudent = (payload) => {
  return request('/exam-students', { method: 'POST', body: payload })
}

export const updateExamStudent = (id, payload) => {
  return request(`/exam-students/${id}`, { method: 'PATCH', body: payload })
}

export const deleteExamStudent = (id) => {
  return request(`/exam-students/${id}`, { method: 'DELETE' })
}

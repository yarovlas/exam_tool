import { request } from './apiClient'

export const listExamAssessors = ({ exam_planning_id = null, limit = 500, offset = 0 } = {}) => {
  const query = { limit, offset }
  if (exam_planning_id) query.exam_planning_id = exam_planning_id
  return request('/exam-assessors', { query })
}

export const getExamAssessor = (id) => request(`/exam-assessors/${id}`)

export const createExamAssessor = (payload) => request('/exam-assessors', { method: 'POST', body: payload })

export const deleteExamAssessor = (id) => request(`/exam-assessors/${id}`, { method: 'DELETE' })

import { request } from './apiClient'

export function login(email, password) {
  return request('/auth/login', {
    method: 'POST',
    body: { email, password },
  })
}

export function me() {
  return request('/auth/me')
}

export function changePassword(currentPassword, newPassword) {
  return request('/auth/password', {
    method: 'PUT',
    body: { current_password: currentPassword, new_password: newPassword },
  })
}

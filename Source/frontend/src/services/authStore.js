import { reactive, computed } from 'vue'

const state = reactive({
  token: localStorage.getItem('auth_token') || null,
  email: localStorage.getItem('auth_email') || null,
})

function decodeToken(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return null
  }
}

export function isTokenExpired(token) {
  const decoded = decodeToken(token)
  if (!decoded || !decoded.exp) return true
  return Date.now() >= decoded.exp * 1000
}

export function clearAuth() {
  state.token = null
  state.email = null
  localStorage.removeItem('auth_token')
  localStorage.removeItem('auth_email')
}

export function useAuthStore() {
  const isAuthenticated = computed(() => !!state.token)

  function setAuth(token, email) {
    state.token = token
    state.email = email
    localStorage.setItem('auth_token', token)
    localStorage.setItem('auth_email', email)
  }

  return { state, isAuthenticated, setAuth, clearAuth }
}

export function getRawToken() {
  return state.token
}

import { reactive, computed } from 'vue'

const state = reactive({
  token: localStorage.getItem('auth_token') || null,
  email: localStorage.getItem('auth_email') || null,
})

export function useAuthStore() {
  const isAuthenticated = computed(() => !!state.token)

  function setAuth(token, email) {
    state.token = token
    state.email = email
    localStorage.setItem('auth_token', token)
    localStorage.setItem('auth_email', email)
  }

  function clearAuth() {
    state.token = null
    state.email = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_email')
  }

  return { state, isAuthenticated, setAuth, clearAuth }
}

export function getRawToken() {
  return state.token
}

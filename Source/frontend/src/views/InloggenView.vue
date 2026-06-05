<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { login } from '../services/authApi'
import { useAuthStore } from '../services/authStore'

const route = useRoute()
const router = useRouter()

const { setAuth } = useAuthStore()

const email = ref('')
const password = ref('')

const loginError = ref('')
const loginLoading = ref(false)

const submitLogin = async () => {
  loginError.value = ''

  if (!email.value || !password.value) {
    loginError.value = 'Vul alle velden in'
    return
  }

  loginLoading.value = true

  try {
    const result = await login(email.value, password.value)
    setAuth(result.access_token, email.value)
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (error) {
    loginError.value =
      error instanceof Error
        ? error.message
        : 'Inloggen mislukt'
  } finally {
    loginLoading.value = false
  }
}
</script>

<template>
  <main class="main-content">
    <div class="login-layout">
      <section class="login-card">
        <div class="login-header">
          <h1>Inloggen</h1>
        </div>

        <form class="login-form" @submit.prevent="submitLogin">
          <label class="login-field">
            <span>Email</span>
            <input v-model="email" type="email"/>
          </label>

          <label class="login-field">
            <span>Wachtwoord</span>

            <input v-model="password" type="password"/>
          </label>

          <p v-if="loginError" class="login-error">
            {{ loginError }}
          </p>

          <button type="submit" class="btn-primary">
            {{ loginLoading ? 'Bezig...' : 'Inloggen' }}
          </button>
        </form>
      </section>
    </div>
  </main>
</template>

<style scoped>
.login-layout {
  min-height: calc(100vh - 120px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background-color: white;
  border-radius: 0.75rem;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  gap: 3rem;
}

.login-header {
  margin-bottom: 2rem;
}

.login-header h1 {
  font-size: 2rem;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.login-header p {
  color: #666;
  font-size: 0.95rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.login-field span {
  font-size: 0.875rem;
  color: #374151;
  font-weight: 600;
}

.login-field input {
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  padding: 0.7rem 0.75rem;
  font-size: 0.95rem;
  font-family: inherit;
}

.login-field input:focus {
  outline: none;
  border-color: #7c3aed;
}

.login-error {
  font-size: 0.85rem;
  color: #b91c1c;
}
.btn-primary {
  margin-top: 1rem;
}
</style>

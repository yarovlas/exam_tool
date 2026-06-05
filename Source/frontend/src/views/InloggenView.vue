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
.login-header p {
  color: #666;
  font-size: 0.95rem;
}
</style>

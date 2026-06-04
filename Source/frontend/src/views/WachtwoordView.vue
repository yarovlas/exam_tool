<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { changePassword } from '../services/authApi'

const router = useRouter()

const currentPassword = ref('')
const newPassword = ref('')
const newPasswordConfirm = ref('')

const error = ref('')
const success = ref('')
const loading = ref(false)

const submit = async () => {
  error.value = ''
  success.value = ''

  if (!currentPassword.value || !newPassword.value || !newPasswordConfirm.value) {
    error.value = 'Vul alle velden in'
    return
  }

  if (newPassword.value.length < 6) {
    error.value = 'Wachtwoord moet minimaal 6 tekens bevatten'
    return
  }

  if (newPassword.value !== newPasswordConfirm.value) {
    error.value = 'De wachtwoorden komen niet overeen'
    return
  }

  loading.value = true

  try {
    await changePassword(currentPassword.value, newPassword.value)
    success.value = 'Wachtwoord gewijzigd. U wordt doorgestuurd...'
    await new Promise((resolve) => setTimeout(resolve, 1000))
    router.push('/')
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Wijzigen mislukt'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="main-content">
    <div class="login-layout">
      <section class="login-card">
        <div class="login-header">
          <h1>Wachtwoord wijzigen</h1>
        </div>

        <form class="login-form" @submit.prevent="submit">
          <label class="login-field">
            <span>Huidig wachtwoord</span>
            <input v-model="currentPassword" type="password" />
          </label>

          <label class="login-field">
            <span>Nieuw wachtwoord</span>
            <input v-model="newPassword" type="password" />
          </label>

          <label class="login-field">
            <span>Nieuw wachtwoord bevestigen</span>
            <input v-model="newPasswordConfirm" type="password" />
          </label>

          <p v-if="error" class="login-error">{{ error }}</p>
          <p v-if="success" class="login-success">{{ success }}</p>

          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Bezig...' : 'Wijzigen' }}
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

.login-success {
  font-size: 0.85rem;
  color: #15803d;
}

.btn-primary {
  margin-top: 1rem;
}
</style>

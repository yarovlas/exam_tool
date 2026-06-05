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

<style scoped></style>

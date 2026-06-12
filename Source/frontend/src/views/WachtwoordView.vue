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
  <main class="mx-auto w-[1400px] px-3xl">
    <div class="flex min-h-[calc(100vh-120px)] items-center justify-center">
      <section class="w-full max-w-[420px] rounded-lg bg-surface p-3xl shadow-sidebar">
        <div class="mb-3xl">
          <h1 class="text-5xl text-heading">Wachtwoord wijzigen</h1>
        </div>

        <form class="flex flex-col gap-lg" @submit.prevent="submit">
          <label class="flex flex-col gap-[0.4rem]">
            <span class="text-sm font-semibold text-gray-700">Huidig wachtwoord</span>
            <input v-model="currentPassword" type="password" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.7rem] text-md focus:border-brand focus:outline-none" />
          </label>

          <label class="flex flex-col gap-[0.4rem]">
            <span class="text-sm font-semibold text-gray-700">Nieuw wachtwoord</span>
            <input v-model="newPassword" type="password" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.7rem] text-md focus:border-brand focus:outline-none" />
          </label>

          <label class="flex flex-col gap-[0.4rem]">
            <span class="text-sm font-semibold text-gray-700">Nieuw wachtwoord bevestigen</span>
            <input v-model="newPasswordConfirm" type="password" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.7rem] text-md focus:border-brand focus:outline-none" />
          </label>

          <p v-if="error" class="text-sm text-error">{{ error }}</p>
          <p v-if="success" class="text-sm text-success">{{ success }}</p>

          <button type="submit" class="mt-lg cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-65" :disabled="loading">
            {{ loading ? 'Bezig...' : 'Wijzigen' }}
          </button>
        </form>
      </section>
    </div>
  </main>
</template>

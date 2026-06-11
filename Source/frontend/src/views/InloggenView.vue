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
  <main class="mx-auto w-[1400px] px-3xl">
    <div class="flex min-h-[calc(100vh-120px)] items-center justify-center">
      <section class="w-full max-w-[420px] rounded-lg bg-surface p-3xl shadow-sidebar">
        <div class="mb-3xl">
          <h1 class="text-5xl text-heading">Inloggen</h1>
        </div>

        <form class="flex flex-col gap-lg" @submit.prevent="submitLogin">
          <label class="flex flex-col gap-[0.4rem]">
            <span class="text-sm font-semibold text-gray-700">Email</span>
            <input v-model="email" type="email" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.7rem] text-md focus:border-brand focus:outline-none" />
          </label>

          <label class="flex flex-col gap-[0.4rem]">
            <span class="text-sm font-semibold text-gray-700">Wachtwoord</span>
            <input v-model="password" type="password" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.7rem] text-md focus:border-brand focus:outline-none" />
          </label>

          <p v-if="loginError" class="text-sm text-error">
            {{ loginError }}
          </p>

          <button type="submit" class="mt-lg cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-65">
            {{ loginLoading ? 'Bezig...' : 'Inloggen' }}
          </button>
        </form>
      </section>
    </div>
  </main>
</template>

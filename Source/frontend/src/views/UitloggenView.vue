<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../services/authStore'

const router = useRouter()
const { clearAuth } = useAuthStore()

onMounted(() => {
  clearAuth()
  router.replace('/inloggen')
})
</script>

<template>
  <main class="mx-auto w-[1400px] px-3xl">
    <p>U wordt uitgelogd...</p>
  </main>
</template>

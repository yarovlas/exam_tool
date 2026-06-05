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
  <main class="main-content">
    <p>U wordt uitgelogd...</p>
  </main>
</template>

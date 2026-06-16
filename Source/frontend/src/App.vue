<script setup>
import AppHeader from './components/AppHeader.vue'
</script>

<template>
  <div class="min-h-screen bg-bg font-sans">
    <AppHeader />
    <div class="min-h-[calc(100vh-4rem)]">
      <RouterView />
    </div>
  </div>
</template>

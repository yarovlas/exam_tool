<script setup>
import { computed } from 'vue'
import { navItems } from '../constants/dashboard'
import { useAuthStore } from '../services/authStore'

const { isAuthenticated } = useAuthStore()

const visibleNavItems = computed(() => {
  if (!isAuthenticated.value) {
    return [{ label: 'Inloggen', to: '/inloggen' }]
  }

  return [
    ...navItems,
    { label: 'Uitloggen', to: '/uitloggen' },
  ]
})
</script>

<template>
  <header class="header">
    <div class="header-content">
      <div class="logo">
        <span class="logo-text">Talland</span>
        <span class="logo-sub">COLLEGE</span>
      </div>
      <nav class="nav">
        <RouterLink
          v-for="item in visibleNavItems"
          :key="item.label"
          :to="item.to"
          class="nav-item"
          active-class="active"
          exact-active-class="active"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

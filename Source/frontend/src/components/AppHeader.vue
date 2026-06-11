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
  <header class="sticky top-0 z-100 border-b border-[#e0e0e0] bg-surface py-lg">
    <div class="mx-auto flex w-[1400px] items-center gap-3xl px-3xl">
      <div class="flex items-center gap-xs font-bold text-xl">
        <span class="text-heading">Talland</span>
        <span class="text-xs tracking-[0.1em] text-text-light">COLLEGE</span>
      </div>
      <nav class="flex flex-1 gap-2xl">
        <RouterLink
          v-for="item in visibleNavItems"
          :key="item.label"
          :to="item.to"
          class="inline-flex cursor-pointer items-center rounded-full border-none bg-none px-lg py-sm text-md text-text-light no-underline transition-all duration-300"
          :class="$route.path === item.to || ($route.path.startsWith(item.to) && item.to !== '/') ? 'bg-brand-light text-brand' : 'hover:bg-brand-light hover:text-brand'"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

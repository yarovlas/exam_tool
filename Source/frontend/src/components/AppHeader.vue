<script setup>
import { navItems } from '../constants/dashboard'
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
          v-for="item in navItems"
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

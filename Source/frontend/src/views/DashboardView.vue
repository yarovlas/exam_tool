<script setup>
import { eventTypes } from '../constants/dashboard'
import { useCalendar } from '../composables/useCalendar'

const { calendarDays, monthYear, nextMonth, previousMonth } = useCalendar()
</script>

<template>
  <main class="main-content">
    <div class="dashboard-grid">
      <section class="calendar-section">
        <div class="calendar-header">
          <h1>Dashboard</h1>
          <button class="btn-new-exam">+ Nieuw Examen</button>
        </div>

        <div class="calendar-card">
          <div class="month-nav">
            <button class="nav-btn" @click="previousMonth">←</button>
            <h2 class="month-title">{{ monthYear }}</h2>
            <button class="nav-btn" @click="nextMonth">→</button>
          </div>

          <div class="calendar-weekdays">
            <div v-for="day in ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo']" :key="day" class="weekday">{{ day }}</div>
          </div>

          <div class="calendar-grid">
            <div v-for="(day, index) in calendarDays" :key="index" class="calendar-day" :class="{ empty: !day }">
              <span v-if="day">{{ day }}</span>
            </div>
          </div>
        </div>
      </section>

      <aside class="sidebar">
        <div class="sidebar-card">
          <h3 class="card-title">Komende Examens</h3>
          <p class="card-subtitle">API-koppeling komt hier</p>
        </div>

        <div class="sidebar-card">
          <h3 class="card-title">Statistieken</h3>
          <div class="stats">
            <div class="stat-row">
              <span>Total studenten:</span>
              <span>--</span>
            </div>
            <div class="stat-row">
              <span>Total examens:</span>
              <span>--</span>
            </div>
          </div>
        </div>

        <div class="sidebar-card">
          <h3 class="card-title">Legenda</h3>
          <div class="legend">
            <div v-for="type in eventTypes" :key="type.label" class="legend-item">
              <div class="legend-color" :style="{ backgroundColor: type.color }"></div>
              <span>{{ type.label }}</span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </main>
</template>

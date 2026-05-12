<script setup>
import { ref } from 'vue'
import ExamMakingContextWindow from '../components/ExamMakingContextWindow.vue'
import { eventTypes } from '../constants/dashboard'
import { useCalendar } from '../composables/useCalendar'

const { calendarDays, currentDate, monthYear, nextMonth, previousMonth } = useCalendar()

const isExamContextOpen = ref(false)
const examContextMode = ref('manual')
const examFormDate = ref('')

const padDatePart = (value) => String(value).padStart(2, '0')

const toIsoDate = (year, monthIndex, day) => {
  return `${year}-${padDatePart(monthIndex + 1)}-${padDatePart(day)}`
}

const openExamContextFromCalendar = (day) => {
  if (!day) {
    return
  }

  examContextMode.value = 'calendar'
  examFormDate.value = toIsoDate(currentDate.value.getFullYear(), currentDate.value.getMonth(), day)
  isExamContextOpen.value = true
}

const openExamContextManual = () => {
  examContextMode.value = 'manual'
  examFormDate.value = ''
  isExamContextOpen.value = true
}

const closeExamContext = () => {
  isExamContextOpen.value = false
}
</script>

<template>
  <main class="main-content">
    <div class="dashboard-grid">
      <section class="calendar-section">
        <div class="calendar-header">
          <h1>Dashboard</h1>
          <button class="btn-new-exam" @click="openExamContextManual">+ Nieuw Examen</button>
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
            <div
              v-for="(day, index) in calendarDays"
              :key="index"
              class="calendar-day"
              :class="{ empty: !day }"
              @click="openExamContextFromCalendar(day)"
            >
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

  <ExamMakingContextWindow
    :is-open="isExamContextOpen"
    :mode="examContextMode"
    :date="examFormDate"
    @close="closeExamContext"
    @update:date="examFormDate = $event"
  />
</template>

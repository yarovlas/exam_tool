<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import ExamMakingContextWindow from '../components/ExamMakingContextWindow.vue'
import { eventTypes } from '../constants/dashboard'
import { useCalendar } from '../composables/useCalendar'
import { createExamPlanning, listExamPlanning } from '../services/examPlanningApi'

const { calendarDays, currentDate, monthYear, nextMonth, previousMonth } = useCalendar()

const isExamContextOpen = ref(false)
const examContextMode = ref('manual')
const examFormDate = ref('')
const examPlanningItems = ref([])
const examPlanningLoading = ref(false)
const examPlanningError = ref('')
const saveExamLoading = ref(false)
const saveExamError = ref('')

const eventTypesByValue = Object.fromEntries(eventTypes.map((type) => [type.value, type]))

const padDatePart = (value) => String(value).padStart(2, '0')

const toIsoDate = (year, monthIndex, day) => {
  return `${year}-${padDatePart(monthIndex + 1)}-${padDatePart(day)}`
}

const openExamContextFromCalendar = (day) => {
  if (!day) {
    return
  }

  saveExamError.value = ''
  examContextMode.value = 'calendar'
  examFormDate.value = toIsoDate(currentDate.value.getFullYear(), currentDate.value.getMonth(), day)
  isExamContextOpen.value = true
}

const openExamContextManual = () => {
  saveExamError.value = ''
  examContextMode.value = 'manual'
  examFormDate.value = ''
  isExamContextOpen.value = true
}

const closeExamContext = () => {
  saveExamError.value = ''
  isExamContextOpen.value = false
}

const examDateFormatter = new Intl.DateTimeFormat('nl-NL', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
})

const examTimeFormatter = new Intl.DateTimeFormat('nl-NL', {
  hour: '2-digit',
  minute: '2-digit',
})

const formatExamDate = (value) => {
  const date = new Date(`${value}T00:00:00`)
  return examDateFormatter.format(date)
}

const formatExamTime = (value) => {
  const date = new Date(`1970-01-01T${value}`)
  return examTimeFormatter.format(date)
}

const loadExamPlanning = async () => {
  examPlanningLoading.value = true
  examPlanningError.value = ''

  try {
    examPlanningItems.value = await listExamPlanning()
  } catch (error) {
    examPlanningError.value = error instanceof Error ? error.message : 'Kon examens niet ophalen'
  } finally {
    examPlanningLoading.value = false
  }
}

const examPlanningByDate = computed(() => {
  const grouped = new Map()

  for (const exam of examPlanningItems.value) {
    const examsForDate = grouped.get(exam.exam_date) ?? []
    examsForDate.push(exam)
    grouped.set(exam.exam_date, examsForDate)
  }

  return grouped
})

const getExamPlanningForDay = (day) => {
  if (!day) {
    return []
  }

  const dayKey = toIsoDate(currentDate.value.getFullYear(), currentDate.value.getMonth(), day)
  return examPlanningByDate.value.get(dayKey) ?? []
}

const getExamTooltip = (exam) => {
  if (!exam) return ''

  const date = formatExamDate(exam.exam_date)
  const time = formatExamTime(exam.exam_time)
  const type = eventTypesByValue[exam.exam_type]?.label ?? exam.exam_type

  return `${type} · ${exam.room} · ${date} ${time}`
}

const submitExamPlanning = async (payload) => {
  saveExamLoading.value = true
  saveExamError.value = ''

  try {
    await createExamPlanning(payload)
    closeExamContext()
    await loadExamPlanning()
  } catch (error) {
    saveExamError.value = error instanceof Error ? error.message : 'Opslaan is mislukt'
  } finally {
    saveExamLoading.value = false
  }
}

const totalExamens = computed(() => examPlanningItems.value.length)
const upcomingExamens = computed(() => examPlanningItems.value.slice(0, 5))

onMounted(() => {
  loadExamPlanning()
})
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

              <template v-if="getExamPlanningForDay(day).length > 0">
                <div class="calendar-day-indicators">
                  <RouterLink
                    v-for="exam in getExamPlanningForDay(day)"
                    :key="exam.id"
                    class="indicator"
                    :to="{ path: '/examens', query: { exam: exam.id } }"
                    :style="{ backgroundColor: eventTypesByValue[exam.exam_type]?.color }"
                    :title="getExamTooltip(exam)"
                    :aria-label="getExamTooltip(exam)"
                  />
                </div>
              </template>
            </div>
          </div>
        </div>
      </section>

      <aside class="sidebar">
        <div class="sidebar-card">
          <h3 class="card-title">Komende Examens</h3>
          <p v-if="examPlanningLoading" class="card-subtitle">Laden...</p>
          <p v-else-if="examPlanningError" class="card-error">{{ examPlanningError }}</p>
          <p v-else-if="upcomingExamens.length === 0" class="card-subtitle">Nog geen examens gepland</p>
          <div v-else class="exam-list">
            <article v-for="exam in upcomingExamens" :key="exam.id" class="exam-item">
              <p class="exam-item-date">{{ formatExamDate(exam.exam_date) }} · {{ formatExamTime(exam.exam_time) }}</p>
              <p class="exam-item-title">{{ exam.exam_type }} · {{ exam.room }}</p>
              <p class="exam-item-status">{{ exam.status }}</p>
            </article>
          </div>
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
              <span>{{ totalExamens }}</span>
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
    :is-saving="saveExamLoading"
    :submit-error="saveExamError"
    @close="closeExamContext"
    @update:date="examFormDate = $event"
    @submit="submitExamPlanning"
  />
</template>

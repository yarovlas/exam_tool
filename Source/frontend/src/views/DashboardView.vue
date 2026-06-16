<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import ExamMakingContextWindow from '../components/ExamMakingContextWindow.vue'
import { eventTypes, examStatusLabels } from '../constants/dashboard'
import { useCalendar } from '../composables/useCalendar'
import { createExamPlanning, listExamPlanning } from '../services/examPlanningApi'
import { listStudents } from '../services/studentsApi'

const { calendarDays, currentDate, monthYear, nextMonth, previousMonth } = useCalendar()

const isExamContextOpen = ref(false)
const examContextMode = ref('manual')
const examFormDate = ref('')
const examPlanningItems = ref([])
const examPlanningLoading = ref(false)
const examPlanningError = ref('')
const saveExamLoading = ref(false)
const saveExamError = ref('')
const totalStudents = ref(0)

const eventTypesByValue = Object.fromEntries(eventTypes.map((type) => [type.value, type]))

const padDatePart = (value) => String(value).padStart(2, '0')
const getExamTypeLabel = (value) => eventTypesByValue[value]?.label ?? value
const getExamStatusLabel = (value) => examStatusLabels[value] ?? value

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

const loadStudents = async () => {
  try {
    const students = await listStudents()
    totalStudents.value = students.length
  } catch (error) {
    totalStudents.value = 0
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
  const type = getExamTypeLabel(exam.exam_type)

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
  loadStudents()
})
</script>

<template>
  <main class="mx-auto w-[1400px] px-3xl my-3xl">
    <div class="grid gap-3xl" style="grid-template-columns: 1000px 300px">
      <section class="flex flex-col gap-2xl">
              <div class="flex items-center justify-between gap-lg">
          <h1 class="text-5xl text-heading">Dashboard</h1>
          <button class="cursor-pointer whitespace-nowrap rounded-md border-none bg-brand px-2xl py-md text-md font-semibold text-surface transition-colors hover:bg-brand-hover" @click="openExamContextManual">+ Nieuw examen</button>
        </div>

        <div class="rounded-lg bg-surface p-3xl shadow-sidebar">
          <div class="mb-3xl flex items-center justify-between">
            <button class="cursor-pointer rounded-sm border-none bg-none px-sm py-sm text-2xl text-text-light hover:bg-gray-100 hover:text-heading" @click="previousMonth">←</button>
            <h2 class="text-3xl capitalize text-heading">{{ monthYear }}</h2>
            <button class="cursor-pointer rounded-sm border-none bg-none px-sm py-sm text-2xl text-text-light hover:bg-gray-100 hover:text-heading" @click="nextMonth">→</button>
          </div>

          <div class="mb-lg grid grid-cols-7 gap-md">
            <div v-for="day in ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo']" :key="day" class="py-sm text-center text-sm font-semibold text-text-light">{{ day }}</div>
          </div>

          <div class="grid grid-cols-7 gap-md">
            <div
              v-for="(day, index) in calendarDays"
              :key="index"
              class="relative flex aspect-square items-center justify-center rounded-sm transition-transform duration-300"
              :class="day ? 'cursor-pointer border border-[#e8e8e8] bg-[#f9f9f9] hover:scale-105 hover:shadow-[0_4px_12px_rgba(0,0,0,0.1)]' : 'cursor-default border-none bg-transparent'"
              @click="openExamContextFromCalendar(day)"
            >
              <span v-if="day" :class="{ 'font-semibold text-primary': getExamPlanningForDay(day).length > 0 }">{{ day }}</span>

              <template v-if="getExamPlanningForDay(day).length > 0">
                <div class="absolute bottom-[0.35rem] left-[0.35rem] right-[0.35rem] flex justify-start gap-[0.35rem]">
                  <RouterLink
                    v-for="exam in getExamPlanningForDay(day)"
                    :key="exam.id"
                    class="inline-flex flex-none rounded-full border-2 border-white/90 transition-transform duration-300 hover:scale-120 hover:shadow-[0_4px_12px_rgba(0,0,0,0.15)]"
                    :to="{ path: '/examens', query: { exam: exam.id } }"
                    :style="{ backgroundColor: eventTypesByValue[exam.exam_type]?.color, width: '1.3rem', height: '1.3rem' }"
                    :title="getExamTooltip(exam)"
                    :aria-label="getExamTooltip(exam)"
                  />
                </div>
              </template>
            </div>
          </div>
        </div>
      </section>

      <aside class="flex flex-col gap-2xl">
        <div class="rounded-lg bg-surface p-2xl shadow-sidebar min-h-[280px]">
          <h3 class="mb-md text-lg font-semibold text-heading">Komende Examens</h3>
          <p v-if="examPlanningLoading" class="text-sm text-[#999]">Laden...</p>
          <p v-else-if="examPlanningError" class="text-sm text-error">{{ examPlanningError }}</p>
          <p v-else-if="upcomingExamens.length === 0" class="text-sm text-[#999]">Nog geen examens gepland</p>
          <div v-else class="flex flex-col gap-md">
            <RouterLink
              v-for="exam in upcomingExamens"
              :key="exam.id"
              class="block rounded-md border border-border-lighter px-[0.65rem] py-[0.65rem] text-inherit no-underline transition-shadow duration-200 hover:translate-y-[-1px] hover:border-[#c7d2fe] hover:shadow-[0_8px_20px_rgba(15,23,42,0.08)] focus-visible:outline-none"
              :to="{ path: '/examens', query: { exam: exam.id } }"
              :title="getExamTooltip(exam)"
              :aria-label="getExamTooltip(exam)"
            >
              <p class="mb-xs text-sm text-text-secondary">{{ formatExamDate(exam.exam_date) }} · {{ formatExamTime(exam.exam_time) }}</p>
              <p class="mb-xs text-md capitalize text-text-primary">{{ getExamTypeLabel(exam.exam_type) }} · {{ exam.room }}</p>
              <p class="inline-block rounded-full bg-[#efe9ff] px-[0.5rem] py-[0.15rem] text-xs capitalize text-[#6d28d9]">{{ getExamStatusLabel(exam.status) }}</p>
            </RouterLink>
          </div>
        </div>

        <div class="rounded-lg bg-surface p-2xl shadow-sidebar min-h-[100px]">
          <h3 class="mb-md text-lg font-semibold text-heading">Statistieken</h3>
          <div class="flex flex-col gap-md">
            <div class="flex justify-between text-sm text-text-light">
              <span>Totaal studenten:</span>
              <span>{{ totalStudents }}</span>
            </div>
            <div class="flex justify-between text-sm text-text-light">
              <span>Totaal examens:</span>
              <span>{{ totalExamens }}</span>
            </div>
          </div>
        </div>

        <div class="rounded-lg bg-surface p-2xl shadow-sidebar">
          <h3 class="mb-md text-lg font-semibold text-heading">Legenda</h3>
          <div class="flex flex-col gap-sm">
            <div v-for="type in eventTypes" :key="type.label" class="flex items-center gap-md text-sm">
              <div class="size-4 shrink-0 rounded-xs" :style="{ backgroundColor: type.color }"></div>
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

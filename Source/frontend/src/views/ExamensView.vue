<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { eventTypes, examStatusLabels } from '../constants/dashboard'
import { listExamPlanning } from '../services/examPlanningApi'

const route = useRoute()
const router = useRouter()

const examPlanningItems = ref([])
const examPlanningLoading = ref(false)
const examPlanningError = ref('')

const eventTypesByValue = Object.fromEntries(eventTypes.map((type) => [type.value, type]))

const examDateFormatter = new Intl.DateTimeFormat('nl-NL', {
  weekday: 'long',
  day: '2-digit',
  month: 'long',
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

const getExamTypeLabel = (value) => eventTypesByValue[value]?.label ?? value
const getExamStatusLabel = (value) => examStatusLabels[value] ?? value

const getSelectedExamId = () => {
  const rawId = Array.isArray(route.query.exam) ? route.query.exam[0] : route.query.exam
  const parsedId = Number(rawId)

  return Number.isFinite(parsedId) ? parsedId : null
}

const selectedExamId = computed(() => getSelectedExamId())

const selectedExam = computed(() => {
  return examPlanningItems.value.find((exam) => exam.id === selectedExamId.value) ?? null
})

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

watch(
  [examPlanningItems, selectedExamId],
  ([items, selectedId]) => {
    if (!items.length) {
      return
    }

    const currentSelectionExists = selectedId !== null && items.some((exam) => exam.id === selectedId)

    if (currentSelectionExists) {
      return
    }

    router.replace({ name: 'examens', query: { exam: items[0].id } })
  },
  { immediate: true },
)

onMounted(() => {
  loadExamPlanning()
})
</script>

<template>
  <main class="examens-page">
    <section class="examens-hero">
      <div>
        <p class="eyebrow">Examens</p>
        <h1>Overzicht van geplande examens</h1>
        <p class="hero-copy">
          Selecteer een examen uit de lijst om de detailpagina te openen. De toegewezen studentenlijst komt hier later.
        </p>
      </div>

      <div class="examens-summary-card">
        <span class="summary-label">Totaal gepland</span>
        <strong>{{ examPlanningItems.length }}</strong>
      </div>
    </section>

    <section class="examens-layout">
      <aside class="examens-list-panel">
        <div class="panel-header">
          <h2>Examenlijst</h2>
          <p>{{ examPlanningLoading ? 'Laden...' : `${examPlanningItems.length} examens` }}</p>
        </div>

        <p v-if="examPlanningError" class="panel-error">{{ examPlanningError }}</p>

        <div v-else class="examens-list">
          <RouterLink
            v-for="exam in examPlanningItems"
            :key="exam.id"
            class="exam-card"
            :class="{ active: exam.id === selectedExamId }"
            :to="{ name: 'examens', query: { exam: exam.id } }"
          >
            <div class="exam-card-top">
              <span class="exam-card-date">{{ formatExamDate(exam.exam_date) }}</span>
              <span class="exam-card-status">{{ getExamStatusLabel(exam.status) }}</span>
            </div>

            <h3>{{ getExamTypeLabel(exam.exam_type) }}</h3>
            <p class="exam-card-meta">{{ formatExamTime(exam.exam_time) }} · {{ exam.room }}</p>
          </RouterLink>
        </div>
      </aside>

      <section class="examens-detail-panel">
        <div v-if="selectedExam" class="detail-card">
          <div class="detail-header">
            <div>
              <p class="eyebrow">Detailweergave</p>
              <h2>{{ getExamTypeLabel(selectedExam.exam_type) }}</h2>
            </div>
            <span class="detail-status">{{ getExamStatusLabel(selectedExam.status) }}</span>
          </div>

          <div class="detail-grid">
            <div class="detail-item">
              <span>Datum</span>
              <strong>{{ formatExamDate(selectedExam.exam_date) }}</strong>
            </div>
            <div class="detail-item">
              <span>Tijd</span>
              <strong>{{ formatExamTime(selectedExam.exam_time) }}</strong>
            </div>
            <div class="detail-item">
              <span>Locatie</span>
              <strong>{{ selectedExam.room }}</strong>
            </div>
            <div class="detail-item">
              <span>Type</span>
              <strong>{{ getExamTypeLabel(selectedExam.exam_type) }}</strong>
            </div>
          </div>

          <div class="detail-section">
            <h3>Toegewezen studenten</h3>
            <p class="placeholder-copy">
              Deze lijst wordt later toegevoegd zodra studenttoewijzingen beschikbaar zijn.
            </p>
            <div class="placeholder-box">
              <span>Voorbeeld</span>
              <p>Hier komt een lijst met studenten die aan dit examen zijn gekoppeld.</p>
            </div>
          </div>
        </div>

        <div v-else class="detail-empty">
          <h2>Kies een examen</h2>
          <p>Selecteer links een examen om de detailinformatie te bekijken.</p>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.examens-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.examens-hero {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.examens-hero h1,
.detail-empty h2 {
  font-size: 2rem;
  color: #111827;
  margin: 0;
}

.hero-copy {
  margin-top: 0.75rem;
  color: #6b7280;
  max-width: 60ch;
}

.examens-summary-card {
  min-width: 180px;
  padding: 1rem 1.25rem;
  border-radius: 1rem;
  background: linear-gradient(135deg, #111827, #374151);
  color: #fff;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.75);
}

.examens-summary-card strong {
  font-size: 2rem;
}

.examens-layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 1.5rem;
}

.examens-list-panel,
.examens-detail-panel,
.detail-card,
.detail-empty {
  background: #fff;
  border-radius: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.examens-list-panel {
  padding: 1.25rem;
}

.panel-header {
  margin-bottom: 1rem;
}

.panel-header h2 {
  margin: 0;
  color: #111827;
}

.panel-header p,
.panel-error {
  margin-top: 0.35rem;
  color: #6b7280;
  font-size: 0.9rem;
}

.panel-error {
  color: #b91c1c;
}

.examens-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.exam-card {
  display: block;
  padding: 1rem;
  border-radius: 0.9rem;
  border: 1px solid #e5e7eb;
  text-decoration: none;
  color: inherit;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.exam-card:hover,
.exam-card.active {
  transform: translateY(-1px);
  border-color: #9ca3af;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.exam-card-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.65rem;
}

.exam-card-date,
.exam-card-meta {
  color: #6b7280;
  font-size: 0.9rem;
}

.exam-card h3 {
  margin: 0;
  font-size: 1.05rem;
  color: #111827;
}

.exam-card-status,
.detail-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: #eef2ff;
  color: #4338ca;
  font-size: 0.75rem;
  text-transform: capitalize;
}

.examens-detail-panel {
  padding: 1.25rem;
}

.detail-card,
.detail-empty {
  padding: 1.5rem;
  min-height: 100%;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1.25rem;
}

.detail-header h2 {
  margin: 0;
  font-size: 1.8rem;
  color: #111827;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.detail-item {
  padding: 0.95rem 1rem;
  border-radius: 0.85rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.detail-item span,
.placeholder-copy {
  color: #6b7280;
  font-size: 0.9rem;
}

.detail-item strong {
  color: #111827;
  font-size: 1rem;
}

.detail-section h3 {
  margin: 0 0 0.75rem;
  color: #111827;
}

.placeholder-box {
  border: 1px dashed #cbd5e1;
  border-radius: 0.85rem;
  padding: 1rem;
  background: #f8fafc;
}

.placeholder-box span {
  display: inline-flex;
  margin-bottom: 0.5rem;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #64748b;
}

.placeholder-box p,
.detail-empty p {
  margin: 0;
  color: #475569;
}

.detail-empty {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  min-height: 420px;
}

@media (max-width: 960px) {
  .examens-hero,
  .examens-layout {
    grid-template-columns: 1fr;
    display: grid;
  }

  .examens-hero {
    display: flex;
    flex-direction: column;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<script setup>
import { computed, onMounted, ref, reactive, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { eventTypes, examStatusLabels } from '../constants/dashboard'
import { listExamPlanning, updateExamPlanning, deleteExamPlanning } from '../services/examPlanningApi'
import { listAssessors } from '../services/assessorsApi'
import { listStudents } from '../services/studentsApi'
import { createExamStudent, deleteExamStudent } from '../services/examStudentsApi'

const route = useRoute()
const router = useRouter()

const examPlanningItems = ref([])
const examPlanningLoading = ref(false)
const examPlanningError = ref('')

const saveLoading = ref(false)
const saveError = ref('')
const deleteLoading = ref(false)
const deleteError = ref('')
const isEditing = ref(false)

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

const editForm = reactive({
  exam_date: '',
  exam_time: '09:00',
  room: '',
  exam_type: 'practical',
  status: 'planned',
  assessor_slot_1: null,
  assessor_slot_2: null,
})

const assessorsOptions = ref([])
const studentsOptions = ref([])

watch(selectedExam, (exam) => {
  isEditing.value = false
  saveError.value = ''
  deleteError.value = ''

  if (exam) {
    editForm.exam_date = exam.exam_date || ''
    editForm.exam_time = exam.exam_time || '09:00'
    editForm.room = exam.room || ''
    editForm.exam_type = exam.exam_type || 'practical'
    editForm.status = exam.status || 'planned'

    // populate assessor slots from exam_assessors
    editForm.assessor_slot_1 = null
    editForm.assessor_slot_2 = null
    if (Array.isArray(exam.exam_assessors)) {
      for (const ea of exam.exam_assessors) {
        if (ea.assessor_order === 1) editForm.assessor_slot_1 = ea.assessor.id
        if (ea.assessor_order === 2) editForm.assessor_slot_2 = ea.assessor.id
      }
    }

  }
})

const loadAssessors = async () => {
  try {
    assessorsOptions.value = await listAssessors({ limit: 500 })
  } catch (e) {
    assessorsOptions.value = []
  }
}

const loadStudents = async () => {
  try {
    studentsOptions.value = await listStudents({ limit: 500 })
  } catch (e) {
    studentsOptions.value = []
  }
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

const startEdit = () => {
  if (!selectedExam.value) return
  saveError.value = ''
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
  saveError.value = ''
  if (selectedExam.value) {
    // reset fields
    editForm.exam_date = selectedExam.value.exam_date
    editForm.exam_time = selectedExam.value.exam_time
    editForm.room = selectedExam.value.room
    editForm.exam_type = selectedExam.value.exam_type
    editForm.status = selectedExam.value.status

    // reset assessor slots
    editForm.assessor_slot_1 = null
    editForm.assessor_slot_2 = null
    if (Array.isArray(selectedExam.value.exam_assessors)) {
      for (const ea of selectedExam.value.exam_assessors) {
        if (ea.assessor_order === 1) editForm.assessor_slot_1 = ea.assessor.id
        if (ea.assessor_order === 2) editForm.assessor_slot_2 = ea.assessor.id
      }
    }

  }
}

const saveEdit = async () => {
  if (!selectedExam.value) return
  saveLoading.value = true
  saveError.value = ''

  try {
    const payload = {
      exam_date: editForm.exam_date,
      exam_time: editForm.exam_time,
      room: editForm.room,
      exam_type: editForm.exam_type,
      status: editForm.status,
    }

    // build assessors array if any selected
    const assessorsPayload = []
    if (editForm.assessor_slot_1) assessorsPayload.push({ assessor_id: Number(editForm.assessor_slot_1), assessor_order: 1 })
    if (editForm.assessor_slot_2) assessorsPayload.push({ assessor_id: Number(editForm.assessor_slot_2), assessor_order: 2 })

    payload.assessors = assessorsPayload

    await updateExamPlanning(selectedExam.value.id, payload)
    await loadExamPlanning()
    isEditing.value = false
    // ensure the same exam remains selected
    router.replace({ name: 'examens', query: { exam: selectedExam.value.id } })
  } catch (error) {
    saveError.value = error instanceof Error ? error.message : 'Opslaan mislukt'
  } finally {
    saveLoading.value = false
  }
}

const confirmAndDelete = async () => {
  if (!selectedExam.value) return

  const ok = window.confirm('Weet je zeker dat je dit examen wilt verwijderen? Deze actie kan niet ongedaan worden gemaakt.')
  if (!ok) return

  deleteLoading.value = true
  deleteError.value = ''

  try {
    await deleteExamPlanning(selectedExam.value.id)
    await loadExamPlanning()

    // select first exam if available, else clear selection
    if (examPlanningItems.value.length > 0) {
      router.replace({ name: 'examens', query: { exam: examPlanningItems.value[0].id } })
    } else {
      router.replace({ name: 'examens', query: {} })
    }
  } catch (error) {
    deleteError.value = error instanceof Error ? error.message : 'Verwijderen mislukt'
  } finally {
    deleteLoading.value = false
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

onMounted(async () => {
  await Promise.all([loadExamPlanning(), loadAssessors(), loadStudents()])
})

const linkingStudentId = ref(null)
const studentActionLoading = ref(false)

const availableStudents = computed(() => {
  if (!selectedExam.value) return studentsOptions.value
  const linkedIds = new Set(
    (selectedExam.value.exam_students || []).map((es) => es.student_id)
  )
  return studentsOptions.value.filter((s) => !linkedIds.has(s.id))
})

const linkStudent = async () => {
  if (!linkingStudentId.value || !selectedExam.value) return
  studentActionLoading.value = true
  try {
    await createExamStudent({
      exam_planning_id: selectedExam.value.id,
      student_id: linkingStudentId.value,
      phase: '',
    })
    linkingStudentId.value = null
    await loadExamPlanning()
    router.replace({ name: 'examens', query: { exam: selectedExam.value.id } })
  } catch (e) {
    console.error(e)
  } finally {
    studentActionLoading.value = false
  }
}

const unlinkStudent = async (examStudentId) => {
  studentActionLoading.value = true
  try {
    await deleteExamStudent(examStudentId)
    await loadExamPlanning()
    if (selectedExam.value) {
      router.replace({ name: 'examens', query: { exam: selectedExam.value.id } })
    }
  } catch (e) {
    console.error(e)
  } finally {
    studentActionLoading.value = false
  }
}
</script>

<template>
  <main class="examens-page">
    <section class="examens-hero">
      <div>
        <p class="eyebrow">Examens</p>
        <h1>Overzicht van geplande examens</h1>
        <p class="hero-copy">
          Selecteer een examen uit de lijst om de detailpagina te openen.
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

            <div class="detail-actions">
              <span class="detail-status">{{ getExamStatusLabel(selectedExam.status) }}</span>

              <div class="actions">
                <button v-if="!isEditing" class="btn-secondary" type="button" @click="startEdit">Bewerken</button>
                <button v-if="!isEditing" class="btn-secondary" type="button" @click="confirmAndDelete" :disabled="deleteLoading">{{ deleteLoading ? 'Verwijderen...' : 'Verwijderen' }}</button>

                <button v-if="isEditing" class="btn-secondary" type="button" @click="cancelEdit">Annuleren</button>
                <button v-if="isEditing" class="btn-primary" type="button" @click="saveEdit" :disabled="saveLoading">{{ saveLoading ? 'Opslaan...' : 'Opslaan' }}</button>
              </div>
            </div>
          </div>

          <div>
            <div v-if="!isEditing" class="detail-grid">
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

            <div v-else class="edit-form">
              <label>
                <span>Datum</span>
                <input type="date" v-model="editForm.exam_date" />
              </label>
              <label>
                <span>Tijd</span>
                <input type="time" v-model="editForm.exam_time" step="60" />
              </label>
              <label>
                <span>Locatie</span>
                <input type="text" v-model.trim="editForm.room" />
              </label>
              <label>
                <span>Type</span>
                <select v-model="editForm.exam_type" aria-label="Examentype">
                  <option v-for="type in eventTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
                </select>
              </label>
              <label>
                <span>Status</span>
                <select v-model="editForm.status" aria-label="Status">
                  <option v-for="(label, key) in examStatusLabels" :key="key" :value="key">{{ label }}</option>
                </select>
              </label>
            </div>
          </div>

          <div class="detail-section">
            <h3>Beoordelaars</h3>

            <div v-if="!isEditing">
              <div v-if="selectedExam.exam_assessors && selectedExam.exam_assessors.length">
                <ul style="list-style:none; padding:0; display:flex; gap:0.75rem; flex-direction:row">
                  <li v-for="ea in selectedExam.exam_assessors" :key="ea.id">
                    <div style="padding:0.5rem 0.75rem; border-radius:0.6rem; background:#f8fafc; border:1px solid #e5e7eb">
                      <div style="font-weight:600">{{ ea.assessor.name }}</div>
                      <div style="font-size:0.85rem; color:#6b7280">{{ ea.assessor.organization || '—' }} · Slot {{ ea.assessor_order }}</div>
                    </div>
                  </li>
                </ul>
              </div>
              <div v-else>
                <p class="placeholder-copy">Nog geen beoordelaars toegewezen.</p>
              </div>
            </div>

            <div v-else style="display:flex; flex-direction:column; gap:0.6rem; align-items:flex-start; width:100%">
              <div style="display:flex; gap:0.6rem; width:100%">
                <label style="flex:1">
                  <span>Beoordelaar slot 1</span>
                  <select v-model="editForm.assessor_slot_1">
                    <option :value="null">— Geen —</option>
                    <option v-for="a in assessorsOptions" :key="a.id" :value="a.id" :disabled="editForm.assessor_slot_2 && Number(editForm.assessor_slot_2) === a.id">
                      {{ a.name }}{{ a.organization ? ' · ' + a.organization : '' }}
                    </option>
                  </select>
                </label>

                <label style="flex:1">
                  <span>Beoordelaar slot 2</span>
                  <select v-model="editForm.assessor_slot_2">
                    <option :value="null">— Geen —</option>
                    <option v-for="a in assessorsOptions" :key="a.id" :value="a.id" :disabled="editForm.assessor_slot_1 && Number(editForm.assessor_slot_1) === a.id">
                      {{ a.name }}{{ a.organization ? ' · ' + a.organization : '' }}
                    </option>
                  </select>
                </label>
              </div>

              <p v-if="saveError" class="panel-error">{{ saveError }}</p>
            </div>
          </div>

          <div class="detail-section">
            <h3>Toegewezen studenten</h3>

            <div v-if="selectedExam.exam_students && selectedExam.exam_students.length">
              <ul style="list-style:none; padding:0; display:flex; flex-direction:column; gap:0.5rem">
                <li v-for="es in selectedExam.exam_students" :key="es.id" style="display:flex; justify-content:space-between; align-items:center; padding:0.5rem 0.75rem; border-radius:0.6rem; background:#f8fafc; border:1px solid #e5e7eb">
                  <div>
                    <div style="font-weight:600">{{ es.student.name }}</div>
                    <div style="font-size:0.85rem; color:#6b7280">{{ es.student.student_number }}</div>
                  </div>
                  <button type="button" style="border:none; background:none; cursor:pointer; font-size:1.1rem; color:#b91c1c; padding:0.25rem" :disabled="studentActionLoading" @click="unlinkStudent(es.id)">×</button>
                </li>
              </ul>
            </div>
            <div v-else>
              <p class="placeholder-copy">Nog geen studenten toegewezen.</p>
            </div>

            <div style="display:flex; gap:0.5rem; margin-top:0.75rem; align-items:center">
              <select v-model="linkingStudentId" style="flex:1; border:1px solid #d1d5db; border-radius:0.5rem; padding:0.45rem 0.55rem; font-size:0.9rem">
                <option :value="null">— Voeg student toe —</option>
                <option v-for="s in availableStudents" :key="s.id" :value="s.id">{{ s.name }} · {{ s.student_number }}</option>
              </select>
              <button class="btn-secondary" type="button" style="padding:0.45rem 0.7rem; font-size:0.85rem" :disabled="!linkingStudentId || studentActionLoading" @click="linkStudent">Toevoegen</button>
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

.detail-card {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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

.detail-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.detail-actions .actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.detail-grid,
.edit-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.edit-form label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.edit-form input,
.edit-form select {
  width: 100%;
  min-width: 0;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  padding: 0.55rem 0.65rem;
  background: #fff;
  color: #111827;
  font-size: 0.95rem;
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
.placeholder-copy,
.edit-form label span {
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

  .detail-header,
  .detail-actions,
  .detail-actions .actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .detail-grid,
  .edit-form {
    grid-template-columns: 1fr;
  }
}
</style>

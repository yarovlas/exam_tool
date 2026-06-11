<script setup>
import { computed, onMounted, ref, reactive, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { eventTypes, examStatusLabels } from '../constants/dashboard'
import { listExamPlanning, updateExamPlanning, deleteExamPlanning } from '../services/examPlanningApi'
import { listAssessors } from '../services/assessorsApi'
import { listStudents } from '../services/studentsApi'
import { createExamStudent, updateExamStudent, deleteExamStudent } from '../services/examStudentsApi'
import { createExamAssessor, deleteExamAssessor } from '../services/examAssessorsApi'

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
const studentSearch = ref('')
const showSuggestions = ref(false)
const highlightIndex = ref(0)
const studentActionLoading = ref(false)

const availableStudents = computed(() => {
  if (!selectedExam.value) return studentsOptions.value
  const linkedIds = new Set(
    (selectedExam.value.exam_students || []).map((es) => es.student_id)
  )
  return studentsOptions.value.filter((s) => !linkedIds.has(s.id))
})

const filteredStudents = computed(() => {
  if (!studentSearch.value) return availableStudents.value
  const q = studentSearch.value.toLowerCase()
  return availableStudents.value.filter(
    (s) => s.name.toLowerCase().includes(q) || s.student_number.toLowerCase().includes(q)
  )
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

const selectStudent = async (student) => {
  if (!selectedExam.value) return
  linkingStudentId.value = student.id
  showSuggestions.value = false
  highlightIndex.value = 0
  await linkStudent()
  studentSearch.value = ''
}

const onSearchInput = () => {
  showSuggestions.value = true
  highlightIndex.value = 0
}

const hideSuggestions = () => {
  setTimeout(() => { showSuggestions.value = false }, 150)
}

const onSearchKeydown = (e) => {
  if (e.key === 'Escape') {
    showSuggestions.value = false
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    highlightIndex.value = Math.min(highlightIndex.value + 1, filteredStudents.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    highlightIndex.value = Math.max(highlightIndex.value - 1, 0)
  } else if (e.key === 'Enter' && filteredStudents.value[highlightIndex.value]) {
    selectStudent(filteredStudents.value[highlightIndex.value])
  }
}

const updateStudentField = async (examStudentId, field, value) => {
  try {
    await updateExamStudent(examStudentId, { [field]: value })
    await loadExamPlanning()
    if (selectedExam.value) {
      router.replace({ name: 'examens', query: { exam: selectedExam.value.id } })
    }
  } catch (e) {
    console.error(e)
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

const assessorActionLoading = ref(false)

const getSlotAssessorId = (slotOrder) => {
  if (!selectedExam.value) return null
  const ea = (selectedExam.value.exam_assessors || []).find((ea) => ea.assessor_order === slotOrder)
  return ea ? ea.assessor_id : null
}

const onSlotChange = async (slotOrder, event) => {
  const newAssessorId = event.target.value ? Number(event.target.value) : null
  if (!selectedExam.value) return
  assessorActionLoading.value = true
  try {
    const current = (selectedExam.value.exam_assessors || []).find((ea) => ea.assessor_order === slotOrder)
    if (newAssessorId) {
      if (current) {
        await deleteExamAssessor(current.id)
      }
      await createExamAssessor({
        exam_planning_id: selectedExam.value.id,
        assessor_id: newAssessorId,
        assessor_order: slotOrder,
      })
    } else if (current) {
      await deleteExamAssessor(current.id)
    }
    await loadExamPlanning()
    router.replace({ name: 'examens', query: { exam: selectedExam.value.id } })
  } catch (e) {
    console.error(e)
  } finally {
    assessorActionLoading.value = false
  }
}

const unlinkAssessor = async (examAssessorId) => {
  assessorActionLoading.value = true
  try {
    await deleteExamAssessor(examAssessorId)
    await loadExamPlanning()
    if (selectedExam.value) {
      router.replace({ name: 'examens', query: { exam: selectedExam.value.id } })
    }
  } catch (e) {
    console.error(e)
  } finally {
    assessorActionLoading.value = false
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

            <div style="display:flex; gap:0.6rem; width:100%">
              <label style="flex:1; display:flex; flex-direction:column; gap:0.25rem">
                <span style="font-size:0.85rem; color:#6b7280">Slot 1</span>
                <select style="border:1px solid #d1d5db; border-radius:0.5rem; padding:0.45rem 0.55rem; font-size:0.9rem" :value="getSlotAssessorId(1)" :disabled="assessorActionLoading" @change="onSlotChange(1, $event)">
                  <option value="">— Geen —</option>
                  <option v-for="a in assessorsOptions" :key="a.id" :value="a.id" :disabled="getSlotAssessorId(2) === a.id">{{ a.name }}{{ a.organization ? ' · ' + a.organization : '' }}</option>
                </select>
              </label>
              <label style="flex:1; display:flex; flex-direction:column; gap:0.25rem">
                <span style="font-size:0.85rem; color:#6b7280">Slot 2</span>
                <select style="border:1px solid #d1d5db; border-radius:0.5rem; padding:0.45rem 0.55rem; font-size:0.9rem" :value="getSlotAssessorId(2)" :disabled="assessorActionLoading" @change="onSlotChange(2, $event)">
                  <option value="">— Geen —</option>
                  <option v-for="a in assessorsOptions" :key="a.id" :value="a.id" :disabled="getSlotAssessorId(1) === a.id">{{ a.name }}{{ a.organization ? ' · ' + a.organization : '' }}</option>
                </select>
              </label>
            </div>
          </div>

            <div class="detail-section">
            <h3>Toegewezen studenten</h3>

            <div style="display:flex; gap:0.5rem; margin-bottom:0.75rem; align-items:center">
              <div style="flex:1; position:relative">
                <input v-model="studentSearch" placeholder="Zoek student op naam of schoolID..." style="width:100%; border:1px solid #d1d5db; border-radius:0.5rem; padding:0.45rem 0.55rem; font-size:0.9rem; box-sizing:border-box" @focus="showSuggestions = true" @blur="hideSuggestions" @input="onSearchInput" @keydown="onSearchKeydown" />
                <ul v-if="showSuggestions && filteredStudents.length" style="position:absolute; top:100%; left:0; right:0; background:#fff; border:1px solid #d1d5db; border-radius:0 0 0.5rem 0.5rem; margin:0; padding:0; list-style:none; max-height:200px; overflow-y:auto; z-index:10; box-shadow:0 4px 12px rgba(0,0,0,0.15)">
                  <li v-for="(s, i) in filteredStudents" :key="s.id" :style="{ padding: '0.45rem 0.55rem', cursor: 'pointer', fontSize: '0.9rem', display: 'flex', justifyContent: 'space-between', gap: '0.5rem', background: i === highlightIndex ? '#f3f4f6' : 'transparent' }" @mousedown.prevent="selectStudent(s)" @mouseenter="highlightIndex = i">
                    <span>{{ s.name }}</span>
                    <span style="color:#6b7280; font-size:0.85rem">{{ s.student_number }}</span>
                  </li>
                </ul>
                <p v-else-if="showSuggestions && studentSearch && !filteredStudents.length" style="position:absolute; top:100%; left:0; right:0; background:#fff; border:1px solid #d1d5db; border-radius:0 0 0.5rem 0.5rem; margin:0; padding:0.45rem 0.55rem; font-size:0.9rem; color:#6b7280; z-index:10; box-shadow:0 4px 12px rgba(0,0,0,0.15)">
                  Geen studenten gevonden
                </p>
              </div>
              <button class="btn-secondary" type="button" style="padding:0.45rem 0.7rem; font-size:0.85rem" :disabled="!linkingStudentId || studentActionLoading" @click="linkStudent">Toevoegen</button>
            </div>

            <div v-if="selectedExam.exam_students && selectedExam.exam_students.length" style="overflow-x:auto">
              <table style="width:100%; border-collapse:collapse; font-size:0.9rem">
                <thead>
                  <tr style="border-bottom:2px solid #e5e7eb">
                    <th style="text-align:left; padding:0.5rem 0.75rem; color:#6b7280; font-weight:600">Naam</th>
                    <th style="text-align:left; padding:0.5rem 0.75rem; color:#6b7280; font-weight:600">SchoolID</th>
                    <th style="text-align:left; padding:0.5rem 0.75rem; color:#6b7280; font-weight:600">Opdracht</th>
                    <th style="text-align:left; padding:0.5rem 0.75rem; color:#6b7280; font-weight:600">Resultaat</th>
                    <th style="padding:0.5rem 0.75rem; width:40px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="es in selectedExam.exam_students" :key="es.id" style="border-bottom:1px solid #f3f4f6">
                    <td style="padding:0.5rem 0.75rem; font-weight:600">{{ es.student.name }}</td>
                    <td style="padding:0.5rem 0.75rem; color:#6b7280">{{ es.student.student_number }}</td>
                    <td style="padding:0.35rem 0.75rem">
                      <div style="display:flex; align-items:center; gap:0.4rem">
                        <span style="font-size:0.85rem; color:#374151">—</span>
                        <button type="button" style="border:1px solid #d1d5db; border-radius:0.4rem; padding:0.25rem 0.5rem; font-size:0.8rem; background:#fff; cursor:pointer; color:#374151">Bekijken</button>
                        <button type="button" style="border:1px solid #d1d5db; border-radius:0.4rem; padding:0.25rem 0.5rem; font-size:0.8rem; background:#fff; cursor:pointer; color:#374151; white-space:nowrap">Toewijzen</button>
                      </div>
                    </td>
                    <td style="padding:0.35rem 0.75rem">
                      <input type="text" :value="es.result || ''" @blur="updateStudentField(es.id, 'result', $event.target.value || null)" style="width:100%; min-width:80px; border:1px solid #d1d5db; border-radius:0.4rem; padding:0.35rem 0.5rem; font-size:0.85rem; background:#fff" placeholder="—" />
                    </td>
                    <td style="padding:0.5rem 0.75rem">
                      <button type="button" style="border:none; background:none; cursor:pointer; font-size:1.1rem; color:#b91c1c; padding:0.25rem" :disabled="studentActionLoading" @click="unlinkStudent(es.id)">×</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else>
              <p class="placeholder-copy">Nog geen studenten toegewezen.</p>
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
.detail-card {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.exam-card-status,
.detail-status {
  text-transform: capitalize;
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

.placeholder-box p {
  margin: 0;
  color: #475569;
}
</style>

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

const assessorTypeLabels = {
  teacher: 'Interne',
  external: 'Externe',
}

const assessorsByType = computed(() => {
  const groups = {}
  for (const a of assessorsOptions.value) {
    const type = a.assessor_type || 'other'
    if (!groups[type]) groups[type] = []
    groups[type].push(a)
  }
  return Object.entries(groups).map(([type, items]) => ({
    label: assessorTypeLabels[type] || type,
    items,
  }))
})

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
  if (field === 'result' && value !== null) {
    const num = parseFloat(value)
    if (Number.isNaN(num) || num < 0 || num > 10) {
      return
    }
  }

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
  <main class="mx-auto flex w-[1400px] flex-col p-3xl">
    <section class="mb-3xl flex items-start justify-between gap-2xl">
      <div>
        <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Examens</p>
        <h1 class="m-0 text-5xl text-text-primary">Overzicht van geplande examens</h1>
        <p class="mt-md max-w-[60ch] text-text-secondary">
          Selecteer een examen uit de lijst om de detailpagina te openen.
        </p>
      </div>

      <div class="flex min-w-[180px] flex-col gap-xs rounded-3xl bg-gradient-to-br from-primary to-[#374151] px-xl py-lg text-surface">
        <span class="text-sm text-white/75">Totaal gepland</span>
        <strong class="text-5xl">{{ examPlanningItems.length }}</strong>
      </div>
    </section>

    <section class="flex-1 grid min-h-0 gap-2xl" style="grid-template-columns: 360px 900px">
      <aside class="flex min-h-0 flex-col rounded-3xl bg-surface p-xl shadow-card">
        <div class="mb-lg">
          <h2 class="m-0 text-text-primary">Examenlijst</h2>
          <p class="mt-[0.35rem] text-base text-text-secondary">{{ examPlanningLoading ? 'Laden...' : `${examPlanningItems.length} examens` }}</p>
        </div>

        <p v-if="examPlanningError" class="mt-[0.35rem] text-base text-error">{{ examPlanningError }}</p>

        <div v-else class="flex flex-1 flex-col gap-md overflow-y-auto min-h-0 pt-px" style="max-height: calc(100vh - 300px)">
          <RouterLink
            v-for="exam in examPlanningItems"
            :key="exam.id"
            class="block w-full rounded-2xl border border-border-light bg-surface px-lg py-lg text-left text-inherit no-underline transition-all duration-200 hover:border-[#9ca3af] hover:shadow-hover"
            :class="{ 'border-[#9ca3af] shadow-hover': exam.id === selectedExamId }"
            :to="{ name: 'examens', query: { exam: exam.id } }"
          >
            <div class="mb-[0.65rem] flex justify-between gap-lg">
              <span class="text-base text-text-secondary">{{ formatExamDate(exam.exam_date) }}</span>
              <span class="inline-flex items-center justify-center rounded-full bg-badge-bg px-[0.6rem] py-[0.2rem] text-xs capitalize text-badge-text">{{ getExamStatusLabel(exam.status) }}</span>
            </div>

            <h3 class="m-0 text-lg text-text-primary">{{ getExamTypeLabel(exam.exam_type) }}</h3>
            <p class="m-0 mt-[0.35rem] text-base text-text-secondary">{{ formatExamTime(exam.exam_time) }} · {{ exam.room }}</p>
          </RouterLink>
        </div>
      </aside>

      <section class="rounded-3xl bg-surface shadow-card" :class="selectedExam ? 'p-2xl' : 'p-2xl'">
        <div v-if="selectedExam" class="flex flex-col gap-2xl">
          <div class="mb-xl flex items-start justify-between gap-lg">
            <div>
              <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Detailweergave</p>
              <h2 class="m-0 text-4xl text-text-primary">{{ getExamTypeLabel(selectedExam.exam_type) }}</h2>
            </div>

            <div class="flex items-center gap-md">
              <span class="inline-flex items-center justify-center rounded-full bg-badge-bg px-[0.6rem] py-[0.2rem] text-xs capitalize text-badge-text">{{ getExamStatusLabel(selectedExam.status) }}</span>

              <div class="flex items-center gap-sm">
                <button v-if="!isEditing" class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="startEdit">Bewerken</button>
                <button v-if="!isEditing" class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="confirmAndDelete" :disabled="deleteLoading">{{ deleteLoading ? 'Verwijderen...' : 'Verwijderen' }}</button>

                <button v-if="isEditing" class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="cancelEdit">Annuleren</button>
                <button v-if="isEditing" class="cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="saveEdit" :disabled="saveLoading">{{ saveLoading ? 'Opslaan...' : 'Opslaan' }}</button>
              </div>
            </div>
          </div>

          <div>
            <div v-if="!isEditing" class="grid grid-cols-2 gap-lg">
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Datum</span>
                <strong class="text-lg text-text-primary">{{ formatExamDate(selectedExam.exam_date) }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Tijd</span>
                <strong class="text-lg text-text-primary">{{ formatExamTime(selectedExam.exam_time) }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Locatie</span>
                <strong class="text-lg text-text-primary">{{ selectedExam.room }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Type</span>
                <strong class="text-lg text-text-primary">{{ getExamTypeLabel(selectedExam.exam_type) }}</strong>
              </div>
            </div>

            <div v-else class="grid grid-cols-2 gap-lg">
              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Datum</span>
                <input type="date" v-model="editForm.exam_date" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>
              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Tijd</span>
                <input type="time" v-model="editForm.exam_time" step="60" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>
              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Locatie</span>
                <input type="text" v-model.trim="editForm.room" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>
              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Type</span>
                <select v-model="editForm.exam_type" aria-label="Examentype" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
                  <option v-for="type in eventTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
                </select>
              </label>
              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Status</span>
                <select v-model="editForm.status" aria-label="Status" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
                  <option v-for="(label, key) in examStatusLabels" :key="key" :value="key">{{ label }}</option>
                </select>
              </label>
            </div>
          </div>

          <div>
            <h3 class="mb-md text-text-primary">Beoordelaars</h3>

            <div class="flex w-full gap-[0.6rem]">
              <label class="flex flex-1 flex-col gap-xs">
                <span class="text-sm text-text-secondary">Slot 1</span>
                <select class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" :value="getSlotAssessorId(1)" :disabled="assessorActionLoading" @change="onSlotChange(1, $event)">
                  <option value="">— Geen —</option>
                  <optgroup v-for="group in assessorsByType" :key="group.label" :label="group.label">
                    <option v-for="a in group.items" :key="a.id" :value="a.id" :disabled="getSlotAssessorId(2) === a.id">{{ a.name }}{{ a.organization ? ' · ' + a.organization : '' }}</option>
                  </optgroup>
                </select>
              </label>
              <label class="flex flex-1 flex-col gap-xs">
                <span class="text-sm text-text-secondary">Slot 2</span>
                <select class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" :value="getSlotAssessorId(2)" :disabled="assessorActionLoading" @change="onSlotChange(2, $event)">
                  <option value="">— Geen —</option>
                  <optgroup v-for="group in assessorsByType" :key="group.label" :label="group.label">
                    <option v-for="a in group.items" :key="a.id" :value="a.id" :disabled="getSlotAssessorId(1) === a.id">{{ a.name }}{{ a.organization ? ' · ' + a.organization : '' }}</option>
                  </optgroup>
                </select>
              </label>
            </div>
          </div>

          <div>
            <h3 class="mb-md text-text-primary">Toegewezen studenten</h3>

            <div class="mb-md flex items-center gap-sm">
              <div class="relative flex-1">
                <input v-model="studentSearch" placeholder="Zoek student op naam of schoolID..." class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" @focus="showSuggestions = true" @blur="hideSuggestions" @input="onSearchInput" @keydown="onSearchKeydown" />
                <ul v-if="showSuggestions && filteredStudents.length" class="absolute left-0 right-0 top-full z-10 m-0 list-none overflow-y-auto border border-border bg-surface shadow-[0_4px_12px_rgba(0,0,0,0.15)]" style="max-height:200px; border-radius: 0 0 0.5rem 0.5rem;">
                  <li v-for="(s, i) in filteredStudents" :key="s.id" class="flex cursor-pointer justify-between gap-sm px-[0.55rem] py-[0.45rem] text-md" :class="{ 'bg-gray-100': i === highlightIndex }" @mousedown.prevent="selectStudent(s)" @mouseenter="highlightIndex = i">
                    <span>{{ s.name }}</span>
                    <span class="text-sm text-text-secondary">{{ s.student_number }}</span>
                  </li>
                </ul>
                <p v-else-if="showSuggestions && studentSearch && !filteredStudents.length" class="absolute left-0 right-0 top-full z-10 m-0 border border-border bg-surface px-[0.55rem] py-[0.45rem] text-md text-text-secondary shadow-[0_4px_12px_rgba(0,0,0,0.15)]" style="border-radius: 0 0 0.5rem 0.5rem;">
                  Geen studenten gevonden
                </p>
              </div>
              <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" type="button" style="padding:0.45rem 0.7rem; font-size:0.85rem" :disabled="!linkingStudentId || studentActionLoading" @click="linkStudent">Toevoegen</button>
            </div>

            <div v-if="selectedExam.exam_students && selectedExam.exam_students.length" class="overflow-x-auto">
              <table class="w-full border-collapse text-md">
                <thead>
                  <tr class="border-b-2 border-b-border-light">
                    <th class="p-sm text-left font-semibold text-text-secondary">Naam</th>
                    <th class="p-sm text-left font-semibold text-text-secondary">SchoolID</th>
                    <th class="p-sm text-left font-semibold text-text-secondary">Opdracht</th>
                    <th class="p-sm text-left font-semibold text-text-secondary">Resultaat</th>
                    <th class="p-sm" style="width:40px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="es in selectedExam.exam_students" :key="es.id" class="border-b border-b-gray-100">
                    <td class="p-sm font-semibold">{{ es.student.name }}</td>
                    <td class="p-sm text-text-secondary">{{ es.student.student_number }}</td>
                    <td class="p-xs p-sm">
                      <div class="flex items-center gap-[0.4rem]">
                        <span class="text-sm text-gray-700">—</span>
                        <button type="button" class="cursor-pointer rounded-[0.4rem] border border-border bg-surface px-[0.5rem] py-[0.25rem] text-sm text-gray-700">Bekijken</button>
                        <button type="button" class="cursor-pointer whitespace-nowrap rounded-[0.4rem] border border-border bg-surface px-[0.5rem] py-[0.25rem] text-sm text-gray-700">Toewijzen</button>
                      </div>
                    </td>
                    <td class="p-xs p-sm">
                      <input type="number" step="0.1" min="0" max="10" :value="es.result || ''" @blur="updateStudentField(es.id, 'result', $event.target.value || null)" class="w-full min-w-0 rounded-[0.4rem] border border-border bg-surface px-[0.5rem] py-[0.35rem] text-sm text-text-primary" style="min-width:80px" placeholder="0.0–10.0" />
                    </td>
                    <td class="p-sm">
                      <button type="button" class="cursor-pointer border-none bg-none p-xs text-lg text-error" :disabled="studentActionLoading" @click="unlinkStudent(es.id)">×</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else>
              <p class="text-base text-text-secondary">Nog geen studenten toegewezen.</p>
            </div>
          </div>
        </div>

        <div v-else class="flex min-h-[420px] flex-col items-start justify-center p-2xl">
          <h2 class="m-0 text-5xl text-text-primary">Kies een examen</h2>
          <p class="mt-md text-text-muted">Selecteer links een examen om de detailinformatie te bekijken.</p>
        </div>
      </section>
    </section>
  </main>
</template>

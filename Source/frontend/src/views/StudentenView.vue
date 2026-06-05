<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { listStudents, createStudent, updateStudent, deleteStudent } from '../services/studentsApi'

const students = ref([])
const loading = ref(false)
const error = ref('')

const selectedId = ref(null)
const selected = computed(() => students.value.find(s => s.id === selectedId.value) ?? null)

const isCreating = ref(false)
const isEditing = ref(false)
const saveLoading = ref(false)
const deleteLoading = ref(false)

const filterProgram = ref('')
const filterPhase = ref('')
const filterPlacement = ref('')
const q = ref('')

const programCodes = computed(() => {
  const codes = new Set(students.value.map(s => s.program_code).filter(Boolean))
  return [...codes].sort()
})

const phases = computed(() => {
  const items = new Set(students.value.map(s => s.phase).filter(Boolean))
  return [...items].sort()
})

const placementGroups = computed(() => {
  const items = new Set(students.value.map(s => s.placement_group).filter(Boolean))
  return [...items].sort()
})

const filteredStudents = computed(() => {
  const search = q.value.trim().toLowerCase()

  return students.value.filter((s) => {
    if (filterProgram.value && s.program_code !== filterProgram.value) return false
    if (filterPhase.value && s.phase !== filterPhase.value) return false
    if (filterPlacement.value && s.placement_group !== filterPlacement.value) return false

    if (!search) return true

    return [
      s.name,
      s.email,
      s.student_number,
      s.program_code,
      s.phase,
      s.placement_group,
    ].some((value) => (value || '').toLowerCase().includes(search))
  })
})

const syncSelection = () => {
  if (isCreating.value) return

  const selectionExists = filteredStudents.value.some((s) => s.id === selectedId.value)
  if (!selectionExists) selectedId.value = filteredStudents.value.length ? filteredStudents.value[0].id : null
}

const createForm = reactive({
  student_number: '',
  name: '',
  program_code: '',
  phase: '',
  email: '',
  placement_group: '',
})

const editForm = reactive({
  student_number: '',
  name: '',
  program_code: '',
  phase: '',
  email: '',
  placement_group: '',
})

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    students.value = await listStudents({ limit: 500 })
    syncSelection()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Kon studenten niet laden'
  } finally {
    loading.value = false
  }
}

onMounted(load)

watch(q, (value) => {
  if (value === '') load()
})

watch([filterProgram, filterPhase, filterPlacement, q], syncSelection)

const openCreate = () => {
  isCreating.value = true
  isEditing.value = false
  Object.assign(createForm, {
    student_number: '',
    name: '',
    program_code: '',
    phase: '',
    email: '',
    placement_group: '',
  })
}

const cancelCreate = () => {
  isCreating.value = false
}

const submitCreate = async () => {
  saveLoading.value = true
  try {
    const created = await createStudent({ ...createForm })
    await load()
    selectedId.value = created.id
    isCreating.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Aanmaken mislukt'
  } finally {
    saveLoading.value = false
  }
}

const startEdit = () => {
  if (!selected.value) return
  isEditing.value = true
  isCreating.value = false
  Object.assign(editForm, {
    student_number: selected.value.student_number || '',
    name: selected.value.name || '',
    program_code: selected.value.program_code || '',
    phase: selected.value.phase || '',
    email: selected.value.email || '',
    placement_group: selected.value.placement_group || '',
  })
}

const cancelEdit = () => {
  isEditing.value = false
}

const submitEdit = async () => {
  if (!selected.value) return
  saveLoading.value = true
  try {
    await updateStudent(selected.value.id, { ...editForm })
    await load()
    isEditing.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Opslaan mislukt'
  } finally {
    saveLoading.value = false
  }
}

const confirmDelete = async () => {
  if (!selected.value) return
  const ok = window.confirm('Weet je zeker dat je deze student wilt verwijderen?')
  if (!ok) return
  deleteLoading.value = true
  try {
    await deleteStudent(selected.value.id)
    await load()
    syncSelection()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Verwijderen mislukt'
  } finally {
    deleteLoading.value = false
  }
}
</script>

<template>
  <main class="examens-page">
    <section class="examens-hero">
      <div>
        <p class="eyebrow">Studenten</p>
        <h1>Overzicht studenten</h1>
        <p class="hero-copy">Beheer studenten en hun gegevens. Selecteer een student om details te bekijken of toe te voegen.</p>
      </div>

      <div class="examens-summary-card">
        <span class="summary-label">Totaal</span>
        <strong>{{ students.length }}</strong>
      </div>
    </section>

    <section class="examens-layout">
      <aside class="examens-list-panel">
        <div class="panel-header">
          <h2>Studentenlijst</h2>
          <p>{{ loading ? 'Laden...' : `${filteredStudents.length} studenten` }}</p>
        </div>

        <div class="panel-controls">
          <select v-model="filterProgram" aria-label="Opleiding">
            <option value="">Alle opleidingen</option>
            <option v-for="code in programCodes" :key="code" :value="code">{{ code }}</option>
          </select>
          <select v-model="filterPhase" aria-label="Fase">
            <option value="">Alle fasen</option>
            <option v-for="p in phases" :key="p" :value="p">{{ p }}</option>
          </select>
          <select v-model="filterPlacement" aria-label="Plaatsingsgroep">
            <option value="">Alle groepen</option>
            <option v-for="g in placementGroups" :key="g" :value="g">{{ g }}</option>
          </select>
          <input v-model.trim="q" type="search" placeholder="Zoeken..." @keyup.enter="load" />
          <button class="btn-secondary" type="button" @click="load">Zoeken</button>
          <button class="btn-primary" type="button" @click="openCreate">Nieuw</button>
        </div>

        <p v-if="error" class="panel-error">{{ error }}</p>
        <p v-else-if="loading" class="panel-error">Laden...</p>

        <div v-else class="examens-list">
          <p v-if="filteredStudents.length === 0" class="panel-error">Geen studenten gevonden</p>

          <button
            v-for="s in filteredStudents"
            :key="s.id"
            class="exam-card"
            :class="{ active: s.id === selectedId && !isCreating }"
            type="button"
            @click="selectedId = s.id; isCreating = false"
          >
            <div class="exam-card-top">
              <span class="exam-card-date">{{ s.student_number }}</span>
              <span class="exam-card-status">{{ s.program_code }} · {{ s.phase }}</span>
            </div>

            <h3>{{ s.name }}</h3>
            <p class="exam-card-meta">{{ s.email || 'Geen e-mail' }}</p>
          </button>
        </div>
      </aside>

      <section class="examens-detail-panel">
        <div v-if="isCreating" class="detail-card">
          <div class="detail-header">
            <div>
              <p class="eyebrow">Nieuwe student</p>
              <h2>Student toevoegen</h2>
            </div>

            <div class="detail-actions">
              <div class="actions">
                <button class="btn-secondary" type="button" @click="cancelCreate">Annuleren</button>
                <button class="btn-primary" type="button" @click="submitCreate" :disabled="saveLoading">{{ saveLoading ? 'Opslaan...' : 'Opslaan' }}</button>
              </div>
            </div>
          </div>

          <div class="edit-form">
            <label>
              <span>Studentnummer</span>
              <input v-model.trim="createForm.student_number" type="text" />
            </label>

            <label>
              <span>Naam</span>
              <input v-model.trim="createForm.name" type="text" />
            </label>

            <label>
              <span>Opleiding</span>
              <input v-model.trim="createForm.program_code" type="text" />
            </label>

            <label>
              <span>Fase</span>
              <input v-model.trim="createForm.phase" type="text" />
            </label>

            <label>
              <span>Email</span>
              <input v-model.trim="createForm.email" type="email" />
            </label>

            <label>
              <span>Plaatsingsgroep</span>
              <input v-model.trim="createForm.placement_group" type="text" />
            </label>
          </div>
        </div>

        <div v-else-if="selected" class="detail-card">
          <div class="detail-header">
            <div>
              <p class="eyebrow">Detailweergave</p>
              <h2>{{ selected.name }}</h2>
              <p class="detail-meta">{{ selected.program_code }} · {{ selected.phase }}</p>
            </div>

            <div class="detail-actions">
              <!-- <span class="detail-status" v-if="!isEditing">{{ selected.student_number }}</span> -->

              <div class="actions">
                <button class="btn-secondary" v-if="!isEditing" type="button" @click="startEdit">Bewerken</button>
                <button class="btn-secondary" v-if="!isEditing" type="button" @click="confirmDelete" :disabled="deleteLoading">{{ deleteLoading ? 'Verwijderen...' : 'Verwijderen' }}</button>

                <button class="btn-secondary" v-if="isEditing" type="button" @click="cancelEdit">Annuleren</button>
                <button class="btn-primary" v-if="isEditing" type="button" @click="submitEdit" :disabled="saveLoading">{{ saveLoading ? 'Opslaan...' : 'Opslaan' }}</button>
              </div>
            </div>
          </div>

          <div>
            <div v-if="!isEditing" class="detail-grid">
              <div class="detail-item">
                <span>Studentnummer</span>
                <strong>{{ selected.student_number }}</strong>
              </div>
              <div class="detail-item">
                <span>Naam</span>
                <strong>{{ selected.name }}</strong>
              </div>
              <div class="detail-item">
                <span>Opleiding</span>
                <strong>{{ selected.program_code }}</strong>
              </div>
              <div class="detail-item">
                <span>Fase</span>
                <strong>{{ selected.phase }}</strong>
              </div>
              <div class="detail-item">
                <span>Email</span>
                <strong>{{ selected.email || '—' }}</strong>
              </div>
              <div class="detail-item">
                <span>Plaatsingsgroep</span>
                <strong>{{ selected.placement_group || '—' }}</strong>
              </div>
            </div>

            <div v-else class="edit-form">
              <label>
                <span>Studentnummer</span>
                <input v-model.trim="editForm.student_number" type="text" />
              </label>

              <label>
                <span>Naam</span>
                <input v-model.trim="editForm.name" type="text" />
              </label>

              <label>
                <span>Opleiding</span>
                <input v-model.trim="editForm.program_code" type="text" />
              </label>

              <label>
                <span>Fase</span>
                <input v-model.trim="editForm.phase" type="text" />
              </label>

              <label>
                <span>Email</span>
                <input v-model.trim="editForm.email" type="email" />
              </label>

              <label>
                <span>Plaatsingsgroep</span>
                <input v-model.trim="editForm.placement_group" type="text" />
              </label>
            </div>
          </div>
        </div>

        <div v-else class="detail-empty">
          <h2>Kies een student</h2>
          <p>Selecteer links een student om de details te bekijken.</p>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.panel-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr);
  gap: 0.6rem;
  margin-bottom: 1rem;
}

.examens-list {
  max-height: calc(100vh - 400px);
}
</style>

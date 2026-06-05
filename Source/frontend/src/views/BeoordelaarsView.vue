<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { listAssessors, createAssessor, updateAssessor, deleteAssessor } from '../services/assessorsApi'
import { assessorTypeColors } from '../constants/dashboard'

const assessors = ref([])
const loading = ref(false)
const error = ref('')

const selectedId = ref(null)
const selected = computed(() => assessors.value.find(a => a.id === selectedId.value) ?? null)

const isCreating = ref(false)
const isEditing = ref(false)
const saveLoading = ref(false)
const deleteLoading = ref(false)

const filterType = ref('')
const q = ref('')

const assessorTypeLabels = {
  teacher: 'Interne',
  external: 'Externe',
}

const getAssessorTypeLabel = (value) => assessorTypeLabels[value] ?? value

const getAssessorBadgeStyle = (type) => {
  const colors = assessorTypeColors[type]
  return colors ? { backgroundColor: colors.bg, color: colors.text } : {}
}

const filteredAssessors = computed(() => {
  const search = q.value.trim().toLowerCase()

  return assessors.value.filter((assessor) => {
    const matchesType = !filterType.value || assessor.assessor_type === filterType.value
    if (!matchesType) return false

    if (!search) return true

    return [
      assessor.name,
      assessor.organization,
      assessor.email,
      assessor.phone,
      assessor.address,
      assessor.postal_city,
      assessor.recruitment_status,
    ].some((value) => (value || '').toLowerCase().includes(search))
  })
})

const syncSelection = () => {
  if (isCreating.value) return

  const selectionExists = filteredAssessors.value.some((assessor) => assessor.id === selectedId.value)
  if (!selectionExists) selectedId.value = filteredAssessors.value.length ? filteredAssessors.value[0].id : null
}

const createForm = reactive({
  assessor_type: 'teacher',
  name: '',
  organization: '',
  salutation: '',
  address: '',
  postal_city: '',
  phone: '',
  email: '',
  recruitment_status: '',
})

const editForm = reactive({
  assessor_type: 'teacher',
  name: '',
  organization: '',
  salutation: '',
  address: '',
  postal_city: '',
  phone: '',
  email: '',
  recruitment_status: '',
})

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    assessors.value = await listAssessors({ limit: 500 })
    syncSelection()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Kon beoordelaars niet laden'
  } finally {
    loading.value = false
  }
}

onMounted(load)

watch(q, (value) => {
  if (value === '') load()
})

watch([filterType, q], syncSelection)

const openCreate = () => {
  isCreating.value = true
  isEditing.value = false
  Object.assign(createForm, { assessor_type: 'teacher', name: '', organization: '', salutation: '', address: '', postal_city: '', phone: '', email: '', recruitment_status: '' })
}

const cancelCreate = () => {
  isCreating.value = false
}

const submitCreate = async () => {
  saveLoading.value = true
  try {
    const created = await createAssessor({ ...createForm })
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
    assessor_type: selected.value.assessor_type,
    name: selected.value.name || '',
    organization: selected.value.organization || '',
    salutation: selected.value.salutation || '',
    address: selected.value.address || '',
    postal_city: selected.value.postal_city || '',
    phone: selected.value.phone || '',
    email: selected.value.email || '',
    recruitment_status: selected.value.recruitment_status || '',
  })
}

const cancelEdit = () => {
  isEditing.value = false
}

const submitEdit = async () => {
  if (!selected.value) return
  saveLoading.value = true
  try {
    await updateAssessor(selected.value.id, { ...editForm })
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
  const ok = window.confirm('Weet je zeker dat je deze beoordelaar wilt verwijderen?')
  if (!ok) return
  deleteLoading.value = true
  try {
    await deleteAssessor(selected.value.id)
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
        <p class="eyebrow">Beoordelaars</p>
        <h1>Overzicht beoordelaars</h1>
        <p class="hero-copy">Beheer beoordelaars en hun gegevens. Selecteer een beoordelaar om details te bekijken of toe te voegen.</p>
      </div>

      <div class="examens-summary-card">
        <span class="summary-label">Totaal</span>
        <strong>{{ assessors.length }}</strong>
      </div>
    </section>

    <section class="examens-layout">
      <aside class="examens-list-panel">
        <div class="panel-header">
          <h2>Beoordelaarslijst</h2>
          <p>{{ loading ? 'Laden...' : `${filteredAssessors.length} beoordelaars` }}</p>
        </div>

        <div class="panel-controls">
          <select v-model="filterType" aria-label="Type beoordelaar" @change="load">
            <option value="">Alle types</option>
            <option v-for="(label, val) in assessorTypeLabels" :key="val" :value="val">{{ label }}</option>
          </select>
          <input v-model.trim="q" type="search" placeholder="Zoeken..." @keyup.enter="load" />
          <button class="btn-secondary" type="button" @click="load">Zoeken</button>
          <button class="btn-primary" type="button" @click="openCreate">Nieuw</button>
        </div>

        <p v-if="error" class="panel-error">{{ error }}</p>
        <p v-else-if="loading" class="panel-error">Laden...</p>

        <div v-else class="examens-list">
          <p v-if="filteredAssessors.length === 0" class="panel-error">Geen beoordelaars gevonden</p>

          <button
            v-for="a in filteredAssessors"
            :key="a.id"
            class="exam-card assessor-card"
            :class="{ active: a.id === selectedId && !isCreating }"
            type="button"
            @click="selectedId = a.id; isCreating = false"
          >
            <div class="exam-card-top">
              <span class="exam-card-date">{{ a.organization || 'Geen organisatie' }}</span>
              <span class="exam-card-status" :style="getAssessorBadgeStyle(a.assessor_type)">{{ getAssessorTypeLabel(a.assessor_type) }}</span>
            </div>

            <h3>{{ a.name }}</h3>
            <p class="exam-card-meta">{{ a.email || 'Geen e-mail' }}</p>
          </button>
        </div>
      </aside>

      <section class="examens-detail-panel">
        <div v-if="isCreating" class="detail-card">
          <div class="detail-header">
            <div>
              <p class="eyebrow">Nieuwe beoordelaar</p>
              <h2>Beoordelaar toevoegen</h2>
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
              <span>Type</span>
              <select v-model="createForm.assessor_type">
                <option v-for="(label, val) in assessorTypeLabels" :key="val" :value="val">{{ label }}</option>
              </select>
            </label>

            <label>
              <span>Naam</span>
              <input v-model.trim="createForm.name" type="text" />
            </label>

            <label>
              <span>Organisatie</span>
              <input v-model.trim="createForm.organization" type="text" />
            </label>

            <label>
              <span>Email</span>
              <input v-model.trim="createForm.email" type="email" />
            </label>

            <label>
              <span>Telefoon</span>
              <input v-model.trim="createForm.phone" type="tel" />
            </label>

            <label>
              <span>Adres</span>
              <input v-model.trim="createForm.address" type="text" />
            </label>

            <label>
              <span>Postcode / Plaats</span>
              <input v-model.trim="createForm.postal_city" type="text" />
            </label>

            <label>
              <span>Aanspreking</span>
              <input v-model.trim="createForm.salutation" type="text" />
            </label>

            <label>
              <span>Recruitment status</span>
              <input v-model.trim="createForm.recruitment_status" type="text" />
            </label>
          </div>
        </div>

        <div v-else-if="selected" class="detail-card">
          <div class="detail-header">
            <div>
              <p class="eyebrow">Detailweergave</p>
              <h2>{{ selected.name }}</h2>
              <p class="detail-meta">{{ getAssessorTypeLabel(selected.assessor_type) }} · {{ selected.organization || 'Geen organisatie' }}</p>
            </div>

            <div class="detail-actions">
              <span class="detail-status" v-if="!isEditing" :style="getAssessorBadgeStyle(selected.assessor_type)">{{ getAssessorTypeLabel(selected.assessor_type) }}</span>

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
                <span>Email</span>
                <strong>{{ selected.email || '—' }}</strong>
              </div>
              <div class="detail-item">
                <span>Telefoon</span>
                <strong>{{ selected.phone || '—' }}</strong>
              </div>
              <div class="detail-item">
                <span>Adres</span>
                <strong>{{ selected.address || '—' }}</strong>
              </div>
              <div class="detail-item">
                <span>Postcode / Plaats</span>
                <strong>{{ selected.postal_city || '—' }}</strong>
              </div>
              <div class="detail-item">
                <span>Aanspreking</span>
                <strong>{{ selected.salutation || '—' }}</strong>
              </div>
              <div class="detail-item">
                <span>Recruitment</span>
                <strong>{{ selected.recruitment_status || '—' }}</strong>
              </div>
            </div>

            <div v-else class="edit-form">
              <label>
                <span>Type</span>
                <select v-model="editForm.assessor_type">
                  <option v-for="(label, val) in assessorTypeLabels" :key="val" :value="val">{{ label }}</option>
                </select>
              </label>

              <label>
                <span>Naam</span>
                <input v-model.trim="editForm.name" type="text" />
              </label>

              <label>
                <span>Organisatie</span>
                <input v-model.trim="editForm.organization" type="text" />
              </label>

              <label>
                <span>Email</span>
                <input v-model.trim="editForm.email" type="email" />
              </label>

              <label>
                <span>Telefoon</span>
                <input v-model.trim="editForm.phone" type="tel" />
              </label>

              <label>
                <span>Adres</span>
                <input v-model.trim="editForm.address" type="text" />
              </label>

              <label>
                <span>Postcode / Plaats</span>
                <input v-model.trim="editForm.postal_city" type="text" />
              </label>

              <label>
                <span>Aanspreking</span>
                <input v-model.trim="editForm.salutation" type="text" />
              </label>

              <label>
                <span>Recruitment status</span>
                <input v-model.trim="editForm.recruitment_status" type="text" />
              </label>
            </div>
          </div>
        </div>

        <div v-else class="detail-empty">
          <h2>Kies een beoordelaar</h2>
          <p>Selecteer links een beoordelaar om de details te bekijken.</p>
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

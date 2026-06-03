<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { listAssessors, createAssessor, updateAssessor, deleteAssessor } from '../services/assessorsApi'

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
              <span class="exam-card-status">{{ getAssessorTypeLabel(a.assessor_type) }}</span>
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
              <span class="detail-status" v-if="!isEditing">{{ getAssessorTypeLabel(selected.assessor_type) }}</span>

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

.examens-list-panel,
.examens-detail-panel {
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

.panel-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr);
  gap: 0.6rem;
  margin-bottom: 1rem;
}

.panel-controls select,
.panel-controls input,
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

.examens-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.exam-card {
  display: block;
  width: 100%;
  padding: 1rem;
  border-radius: 0.9rem;
  border: 1px solid #e5e7eb;
  background: #fff;
  text-align: left;
  color: inherit;
  cursor: pointer;
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
.exam-card-meta,
.detail-meta {
  color: #6b7280;
  font-size: 0.9rem;
}

.exam-card h3 {
  margin: 0;
  font-size: 1.05rem;
  color: #111827;
}

.exam-card-meta,
.detail-meta {
  margin: 0.35rem 0 0;
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

.btn-primary,
.btn-secondary {
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  padding: 0.55rem 0.8rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.btn-primary {
  border-color: #111827;
  background: #111827;
  color: #fff;
}

.btn-secondary {
  background: #fff;
  color: #111827;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.detail-grid,
.edit-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
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
.edit-form label span {
  color: #6b7280;
  font-size: 0.9rem;
}

.detail-item strong {
  color: #111827;
  font-size: 1rem;
}

.edit-form label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-empty {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  min-height: 420px;
}

.detail-empty p {
  margin: 0.75rem 0 0;
  color: #475569;
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
  .edit-form,
  .panel-controls {
    grid-template-columns: 1fr;
  }
}
</style>

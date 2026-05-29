<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import PageTemplate from '../components/PageTemplate.vue'
import { listAssessors, createAssessor, updateAssessor, deleteAssessor } from '../services/assessorsApi'
import { eventTypes } from '../constants/dashboard'

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
    assessors.value = await listAssessors({ assessor_type: filterType.value || null, q: q.value })
    if (!selectedId.value && assessors.value.length) selectedId.value = assessors.value[0].id
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Kon beoordelaars niet laden'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const openCreate = () => {
  isCreating.value = true
  Object.assign(createForm, { assessor_type: 'teacher', name: '', organization: '', salutation: '', address: '', postal_city: '', phone: '', email: '', recruitment_status: '' })
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
    selectedId.value = assessors.value.length ? assessors.value[0].id : null
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Verwijderen mislukt'
  } finally {
    deleteLoading.value = false
  }
}
</script>

<template>
  <main class="main-content">
    <div class="dashboard-grid">
      <section>
        <div class="calendar-header" style="margin-bottom:1rem; align-items:center">
          <h1>Beoordelaars</h1>
          <div style="margin-left:auto; display:flex; gap:0.5rem; align-items:center">
            <select v-model="filterType">
              <option value="">Alle types</option>
              <option value="teacher">Teacher</option>
              <option value="external">External</option>
            </select>
            <input v-model="q" placeholder="Zoeken..." />
            <button class="btn-primary" @click="openCreate">+ Nieuw</button>
          </div>
        </div>

        <div class="page-template" style="padding:0">
          <div style="display:grid; grid-template-columns: 1fr 2fr; gap:1rem">
            <div style="border-right:1px solid #e5e7eb; padding-right:1rem">
              <div v-if="loading">Laden...</div>
              <div v-else>
                <div v-if="assessors.length === 0">Geen beoordelaars gevonden</div>
                <ul style="list-style:none; padding:0; display:flex; flex-direction:column; gap:0.4rem">
                  <li v-for="a in assessors" :key="a.id">
                    <button style="width:100%; text-align:left; padding:0.6rem; border-radius:0.5rem; border:1px solid #ececf2; background:transparent; cursor:pointer" @click="selectedId = a.id">
                      <div style="display:flex; justify-content:space-between; align-items:center">
                        <div>
                          <div style="font-weight:600">{{ a.name }}</div>
                          <div style="font-size:0.9rem; color:#6b7280">{{ a.organization }} · {{ a.assessor_type }}</div>
                        </div>
                        <div style="font-size:0.85rem; color:#6b7280">ID {{ a.id }}</div>
                      </div>
                    </button>
                  </li>
                </ul>
              </div>
            </div>

            <div style="padding-left:1rem">
              <div v-if="selected">
                <div style="display:flex; justify-content:space-between; align-items:flex-start">
                  <div>
                    <h2 style="margin:0">{{ selected.name }}</h2>
                    <div style="color:#6b7280">{{ selected.assessor_type }} · {{ selected.organization }}</div>
                  </div>
                  <div style="display:flex; gap:0.5rem">
                    <button class="btn-secondary" v-if="!isEditing" @click="startEdit">Bewerken</button>
                    <button class="btn-secondary" v-if="!isEditing" @click="confirmDelete" :disabled="deleteLoading">{{ deleteLoading ? 'Verwijderen...' : 'Verwijderen' }}</button>
                    <button class="btn-secondary" v-if="isEditing" @click="cancelEdit">Annuleren</button>
                    <button class="btn-primary" v-if="isEditing" @click="submitEdit" :disabled="saveLoading">{{ saveLoading ? 'Opslaan...' : 'Opslaan' }}</button>
                  </div>
                </div>

                <div style="margin-top:1rem">
                  <div v-if="!isEditing">
                    <p><strong>Email:</strong> {{ selected.email || '—' }}</p>
                    <p><strong>Phone:</strong> {{ selected.phone || '—' }}</p>
                    <p><strong>Address:</strong> {{ selected.address || '—' }}</p>
                    <p><strong>Postal/City:</strong> {{ selected.postal_city || '—' }}</p>
                    <p><strong>Salutation:</strong> {{ selected.salutation || '—' }}</p>
                    <p><strong>Recruitment:</strong> {{ selected.recruitment_status || '—' }}</p>
                  </div>

                  <div v-else>
                    <label>
                      <span>Type</span>
                      <select v-model="editForm.assessor_type">
                        <option value="teacher">Teacher</option>
                        <option value="external">External</option>
                      </select>
                    </label>
                    <label>
                      <span>Naam</span>
                      <input v-model="editForm.name" />
                    </label>
                    <label>
                      <span>Organisatie</span>
                      <input v-model="editForm.organization" />
                    </label>
                    <label>
                      <span>Email</span>
                      <input v-model="editForm.email" />
                    </label>
                    <label>
                      <span>Telefoon</span>
                      <input v-model="editForm.phone" />
                    </label>
                    <label>
                      <span>Adres</span>
                      <input v-model="editForm.address" />
                    </label>
                    <label>
                      <span>Postcode / Plaats</span>
                      <input v-model="editForm.postal_city" />
                    </label>
                    <label>
                      <span>Aanspreking</span>
                      <input v-model="editForm.salutation" />
                    </label>
                    <label>
                      <span>Recruitment status</span>
                      <input v-model="editForm.recruitment_status" />
                    </label>
                  </div>
                </div>
              </div>

              <div v-else>
                <p>Kies een beoordelaar uit de lijst of maak een nieuwe aan.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Create modal simple inline -->
        <div v-if="isCreating" style="position:fixed; inset:0; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,0.4); z-index:300">
          <div style="background:white; padding:1rem; border-radius:0.5rem; width:520px">
            <h3>Nieuwe beoordelaar</h3>
            <label>
              <span>Type</span>
              <select v-model="createForm.assessor_type">
                <option value="teacher">Teacher</option>
                <option value="external">External</option>
              </select>
            </label>
            <label>
              <span>Naam</span>
              <input v-model="createForm.name" />
            </label>
            <label>
              <span>Organisatie</span>
              <input v-model="createForm.organization" />
            </label>
            <label>
              <span>Email</span>
              <input v-model="createForm.email" />
            </label>
            <div style="display:flex; gap:0.5rem; justify-content:flex-end; margin-top:0.75rem">
              <button class="btn-secondary" @click="isCreating = false">Annuleren</button>
              <button class="btn-primary" @click="submitCreate" :disabled="saveLoading">{{ saveLoading ? 'Aanmaken...' : 'Aanmaken' }}</button>
            </div>
          </div>
        </div>
      </section>

      <aside class="sidebar">
        <div class="sidebar-card">
          <h3 class="card-title">Statistieken</h3>
          <div class="stats">
            <div class="stat-row">
              <span>Totaal beoordelaars:</span>
              <span>{{ assessors.length }}</span>
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
</template>

<style scoped>
label {
  display: block;
  margin-bottom: 0.5rem;
}
label span {
  display: block;
  font-weight: 600;
  margin-bottom: 0.25rem;
}
input, select {
  padding: 0.5rem;
  border-radius: 0.5rem;
  border: 1px solid #d1d5db;
  width: 100%;
}
</style>

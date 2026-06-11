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
  <main class="mx-auto flex w-[1400px] flex-col p-3xl">
    <section class="mb-3xl flex items-start justify-between gap-2xl">
      <div>
        <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Beoordelaars</p>
        <h1 class="m-0 text-5xl text-text-primary">Overzicht beoordelaars</h1>
        <p class="mt-md max-w-[60ch] text-text-secondary">Beheer beoordelaars en hun gegevens. Selecteer een beoordelaar om details te bekijken of toe te voegen.</p>
      </div>

      <div class="flex min-w-[180px] flex-col gap-xs rounded-3xl bg-gradient-to-br from-primary to-[#374151] px-xl py-lg text-surface">
        <span class="text-sm text-white/75">Totaal</span>
        <strong class="text-5xl">{{ assessors.length }}</strong>
      </div>
    </section>

    <section class="flex-1 grid min-h-0 gap-2xl" style="grid-template-columns: 360px 900px">
      <aside class="flex min-h-0 flex-col rounded-3xl bg-surface p-xl shadow-card">
        <div class="mb-lg">
          <h2 class="m-0 text-text-primary">Beoordelaarslijst</h2>
          <p class="mt-[0.35rem] text-base text-text-secondary">{{ loading ? 'Laden...' : `${filteredAssessors.length} beoordelaars` }}</p>
        </div>

        <div class="mb-lg grid gap-[0.6rem]" style="grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr)">
          <select v-model="filterType" aria-label="Type beoordelaar" @change="load" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
            <option value="">Alle types</option>
            <option v-for="(label, val) in assessorTypeLabels" :key="val" :value="val">{{ label }}</option>
          </select>
          <input v-model.trim="q" type="search" placeholder="Zoeken..." @keyup.enter="load" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
          <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="load">Zoeken</button>
          <button class="cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="openCreate">Nieuw</button>
        </div>

        <p v-if="error" class="mt-[0.35rem] text-base text-error">{{ error }}</p>
        <p v-else-if="loading" class="mt-[0.35rem] text-base text-error">Laden...</p>

        <div v-else class="flex flex-1 flex-col gap-md overflow-y-auto" style="max-height: calc(100vh - 400px)">
          <p v-if="filteredAssessors.length === 0" class="mt-[0.35rem] text-base text-error">Geen beoordelaars gevonden</p>

          <button
            v-for="a in filteredAssessors"
            :key="a.id"
            class="block w-full rounded-2xl border border-border-light bg-surface px-lg py-lg text-left text-inherit no-underline transition-all duration-200 hover:border-[#9ca3af] hover:shadow-hover"
            :class="{ 'border-[#9ca3af] shadow-hover': a.id === selectedId && !isCreating }"
            type="button"
            @click="selectedId = a.id; isCreating = false"
          >
            <div class="mb-[0.65rem] flex justify-between gap-lg">
              <span class="text-base text-text-secondary">{{ a.organization || 'Geen organisatie' }}</span>
              <span class="inline-flex items-center justify-center max-h-6 rounded-full px-[0.6rem] py-[0.2rem] text-xs capitalize" :style="getAssessorBadgeStyle(a.assessor_type)">{{ getAssessorTypeLabel(a.assessor_type) }}</span>
            </div>

            <h3 class="m-0 text-lg text-text-primary">{{ a.name }}</h3>
            <p class="m-0 mt-[0.35rem] text-base text-text-secondary">{{ a.email || 'Geen e-mail' }}</p>
          </button>
        </div>
      </aside>

      <section class="rounded-3xl bg-surface shadow-card" :class="selected || isCreating ? 'p-2xl' : 'p-2xl'">
        <div v-if="isCreating" class="flex flex-col gap-2xl">
          <div class="mb-xl flex items-start justify-between gap-lg">
            <div>
              <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Nieuwe beoordelaar</p>
              <h2 class="m-0 text-4xl text-text-primary">Beoordelaar toevoegen</h2>
            </div>

            <div class="flex items-center gap-md">
              <div class="flex items-center gap-sm">
                <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="cancelCreate">Annuleren</button>
                <button class="cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="submitCreate" :disabled="saveLoading">{{ saveLoading ? 'Opslaan...' : 'Opslaan' }}</button>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-lg">
            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Type</span>
              <select v-model="createForm.assessor_type" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
                <option v-for="(label, val) in assessorTypeLabels" :key="val" :value="val">{{ label }}</option>
              </select>
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Naam</span>
              <input v-model.trim="createForm.name" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Organisatie</span>
              <input v-model.trim="createForm.organization" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Email</span>
              <input v-model.trim="createForm.email" type="email" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Telefoon</span>
              <input v-model.trim="createForm.phone" type="tel" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Adres</span>
              <input v-model.trim="createForm.address" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Postcode / Plaats</span>
              <input v-model.trim="createForm.postal_city" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Aanspreking</span>
              <input v-model.trim="createForm.salutation" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Recruitment status</span>
              <input v-model.trim="createForm.recruitment_status" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>
          </div>
        </div>

        <div v-else-if="selected" class="flex flex-col gap-2xl">
          <div class="mb-xl flex items-start justify-between gap-lg">
            <div>
              <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Detailweergave</p>
              <h2 class="m-0 text-4xl text-text-primary">{{ selected.name }}</h2>
              <p class="mt-[0.35rem] text-base text-text-secondary">{{ getAssessorTypeLabel(selected.assessor_type) }} · {{ selected.organization || 'Geen organisatie' }}</p>
            </div>

            <div class="flex items-center gap-md">
              <span v-if="!isEditing" class="inline-flex items-center justify-center rounded-full px-[0.6rem] py-[0.2rem] text-xs capitalize" :style="getAssessorBadgeStyle(selected.assessor_type)">{{ getAssessorTypeLabel(selected.assessor_type) }}</span>

              <div class="flex items-center gap-sm">
                <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" v-if="!isEditing" type="button" @click="startEdit">Bewerken</button>
                <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" v-if="!isEditing" type="button" @click="confirmDelete" :disabled="deleteLoading">{{ deleteLoading ? 'Verwijderen...' : 'Verwijderen' }}</button>

                <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" v-if="isEditing" type="button" @click="cancelEdit">Annuleren</button>
                <button class="cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-65" v-if="isEditing" type="button" @click="submitEdit" :disabled="saveLoading">{{ saveLoading ? 'Opslaan...' : 'Opslaan' }}</button>
              </div>
            </div>
          </div>

          <div>
            <div v-if="!isEditing" class="grid grid-cols-2 gap-lg">
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Email</span>
                <strong class="text-lg text-text-primary">{{ selected.email || '—' }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Telefoon</span>
                <strong class="text-lg text-text-primary">{{ selected.phone || '—' }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Adres</span>
                <strong class="text-lg text-text-primary">{{ selected.address || '—' }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Postcode / Plaats</span>
                <strong class="text-lg text-text-primary">{{ selected.postal_city || '—' }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Aanspreking</span>
                <strong class="text-lg text-text-primary">{{ selected.salutation || '—' }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Recruitment</span>
                <strong class="text-lg text-text-primary">{{ selected.recruitment_status || '—' }}</strong>
              </div>
            </div>

            <div v-else class="grid grid-cols-2 gap-lg">
              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Type</span>
                <select v-model="editForm.assessor_type" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
                  <option v-for="(label, val) in assessorTypeLabels" :key="val" :value="val">{{ label }}</option>
                </select>
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Naam</span>
                <input v-model.trim="editForm.name" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Organisatie</span>
                <input v-model.trim="editForm.organization" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Email</span>
                <input v-model.trim="editForm.email" type="email" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Telefoon</span>
                <input v-model.trim="editForm.phone" type="tel" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Adres</span>
                <input v-model.trim="editForm.address" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Postcode / Plaats</span>
                <input v-model.trim="editForm.postal_city" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Aanspreking</span>
                <input v-model.trim="editForm.salutation" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Recruitment status</span>
                <input v-model.trim="editForm.recruitment_status" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>
            </div>
          </div>
        </div>

        <div v-else class="flex min-h-[420px] flex-col items-start justify-center p-2xl">
          <h2 class="m-0 text-5xl text-text-primary">Kies een beoordelaar</h2>
          <p class="mt-md text-text-muted">Selecteer links een beoordelaar om de details te bekijken.</p>
        </div>
      </section>
    </section>
  </main>
</template>

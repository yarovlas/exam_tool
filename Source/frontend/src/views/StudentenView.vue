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
  <main class="mx-auto flex w-[1400px] flex-col p-3xl">
    <section class="mb-3xl flex items-start justify-between gap-2xl">
      <div>
        <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Studenten</p>
        <h1 class="m-0 text-5xl text-text-primary">Overzicht studenten</h1>
        <p class="mt-md max-w-[60ch] text-text-secondary">Beheer studenten en hun gegevens. Selecteer een student om details te bekijken of toe te voegen.</p>
      </div>

      <div class="flex min-w-[180px] flex-col gap-xs rounded-3xl bg-gradient-to-br from-primary to-[#374151] px-xl py-lg text-surface">
        <span class="text-sm text-white/75">Totaal</span>
        <strong class="text-5xl">{{ students.length }}</strong>
      </div>
    </section>

    <section class="flex-1 grid min-h-0 gap-2xl" style="grid-template-columns: 360px 900px">
      <aside class="flex min-h-0 flex-col rounded-3xl bg-surface p-xl shadow-card">
        <div class="mb-lg">
          <h2 class="m-0 text-text-primary">Studentenlijst</h2>
          <p class="mt-[0.35rem] text-base text-text-secondary">{{ loading ? 'Laden...' : `${filteredStudents.length} studenten` }}</p>
        </div>

        <div class="mb-lg grid gap-[0.6rem]" style="grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr)">
          <select v-model="filterProgram" aria-label="Opleiding" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
            <option value="">Alle opleidingen</option>
            <option v-for="code in programCodes" :key="code" :value="code">{{ code }}</option>
          </select>
          <select v-model="filterPhase" aria-label="Fase" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
            <option value="">Alle fasen</option>
            <option v-for="p in phases" :key="p" :value="p">{{ p }}</option>
          </select>
          <select v-model="filterPlacement" aria-label="Plaatsingsgroep" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
            <option value="">Alle groepen</option>
            <option v-for="g in placementGroups" :key="g" :value="g">{{ g }}</option>
          </select>
          <input v-model.trim="q" type="search" placeholder="Zoeken..." @keyup.enter="load" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
          <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="load">Zoeken</button>
          <button class="cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="openCreate">Nieuw</button>
        </div>

        <p v-if="error" class="mt-[0.35rem] text-base text-error">{{ error }}</p>
        <p v-else-if="loading" class="mt-[0.35rem] text-base text-error">Laden...</p>

        <div v-else class="flex flex-1 flex-col gap-md overflow-y-auto" style="max-height: calc(100vh - 400px)">
          <p v-if="filteredStudents.length === 0" class="mt-[0.35rem] text-base text-error">Geen studenten gevonden</p>

          <button
            v-for="s in filteredStudents"
            :key="s.id"
            class="block w-full rounded-2xl border border-border-light bg-surface px-lg py-lg text-left text-inherit no-underline transition-all duration-200 hover:border-[#9ca3af] hover:shadow-hover"
            :class="{ 'border-[#9ca3af] shadow-hover': s.id === selectedId && !isCreating }"
            type="button"
            @click="selectedId = s.id; isCreating = false"
          >
            <div class="mb-[0.65rem] flex justify-between gap-lg">
              <span class="text-base text-text-secondary">{{ s.student_number }}</span>
              <span class="inline-flex items-center justify-center rounded-full bg-badge-bg px-[0.6rem] py-[0.2rem] text-xs capitalize text-badge-text">{{ s.program_code }} · {{ s.phase }}</span>
            </div>

            <h3 class="m-0 text-lg text-text-primary">{{ s.name }}</h3>
            <p class="m-0 mt-[0.35rem] text-base text-text-secondary">{{ s.email || 'Geen e-mail' }}</p>
          </button>
        </div>
      </aside>

      <section class="rounded-3xl bg-surface shadow-card" :class="selected || isCreating ? 'p-2xl' : 'p-2xl'">
        <div v-if="isCreating" class="flex flex-col gap-2xl">
          <div class="mb-xl flex items-start justify-between gap-lg">
            <div>
              <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Nieuwe student</p>
              <h2 class="m-0 text-4xl text-text-primary">Student toevoegen</h2>
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
              <span class="text-base text-text-secondary">Studentnummer</span>
              <input v-model.trim="createForm.student_number" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Naam</span>
              <input v-model.trim="createForm.name" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Opleiding</span>
              <input v-model.trim="createForm.program_code" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Fase</span>
              <input v-model.trim="createForm.phase" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Email</span>
              <input v-model.trim="createForm.email" type="email" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>

            <label class="flex flex-col gap-xs">
              <span class="text-base text-text-secondary">Plaatsingsgroep</span>
              <input v-model.trim="createForm.placement_group" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
            </label>
          </div>
        </div>

        <div v-else-if="selected" class="flex flex-col gap-2xl">
          <div class="mb-xl flex items-start justify-between gap-lg">
            <div>
              <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Detailweergave</p>
              <h2 class="m-0 text-4xl text-text-primary">{{ selected.name }}</h2>
              <p class="mt-[0.35rem] text-base text-text-secondary">{{ selected.program_code }} · {{ selected.phase }}</p>
            </div>

            <div class="flex items-center gap-md">
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
                <span class="text-base text-text-secondary">Studentnummer</span>
                <strong class="text-lg text-text-primary">{{ selected.student_number }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Naam</span>
                <strong class="text-lg text-text-primary">{{ selected.name }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Opleiding</span>
                <strong class="text-lg text-text-primary">{{ selected.program_code }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Fase</span>
                <strong class="text-lg text-text-primary">{{ selected.phase }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Email</span>
                <strong class="text-lg text-text-primary">{{ selected.email || '—' }}</strong>
              </div>
              <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
                <span class="text-base text-text-secondary">Plaatsingsgroep</span>
                <strong class="text-lg text-text-primary">{{ selected.placement_group || '—' }}</strong>
              </div>
            </div>

            <div v-else class="grid grid-cols-2 gap-lg">
              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Studentnummer</span>
                <input v-model.trim="editForm.student_number" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Naam</span>
                <input v-model.trim="editForm.name" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Opleiding</span>
                <input v-model.trim="editForm.program_code" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Fase</span>
                <input v-model.trim="editForm.phase" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Email</span>
                <input v-model.trim="editForm.email" type="email" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>

              <label class="flex flex-col gap-xs">
                <span class="text-base text-text-secondary">Plaatsingsgroep</span>
                <input v-model.trim="editForm.placement_group" type="text" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary" />
              </label>
            </div>
          </div>
        </div>

        <div v-else class="flex min-h-[420px] flex-col items-start justify-center p-2xl">
          <h2 class="m-0 text-5xl text-text-primary">Kies een student</h2>
          <p class="mt-md text-text-muted">Selecteer links een student om de details te bekijken.</p>
        </div>
      </section>
    </section>
  </main>
</template>

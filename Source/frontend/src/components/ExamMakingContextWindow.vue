<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { listAssessors } from '../services/assessorsApi'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  mode: {
    type: String,
    default: 'manual',
  },
  date: {
    type: String,
    default: '',
  },
  isSaving: {
    type: Boolean,
    default: false,
  },
  submitError: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close', 'update:date', 'submit'])

const form = reactive({
  examDate: '',
  examTime: '09:00',
  room: '',
  examType: 'practical',
  status: 'planned',
  assessor_slot_1: null,
  assessor_slot_2: null,
})

const assessorsOptions = ref([])
const localError = ref('')

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

const modeText = computed(() => {
  if (props.mode === 'calendar') {
    return 'Datum is automatisch ingevuld op basis van je kalenderselectie.'
  }

  return 'Kies handmatig een datum om verder te gaan.'
})

const resetForm = (selectedDate = '') => {
  form.examDate = selectedDate
  form.examTime = '09:00'
  form.room = ''
  form.examType = 'practical'
  form.status = 'planned'
  form.assessor_slot_1 = null
  form.assessor_slot_2 = null
  localError.value = ''
}

watch(
  () => props.isOpen,
  async (isOpen) => {
    if (isOpen) {
      resetForm(props.date)
      await loadAssessors()
      validateSelectedDateTime()
    }
  },
)

watch(
  () => props.date,
  (newDate) => {
    form.examDate = newDate
    if (props.isOpen) validateSelectedDateTime()
  },
)

// validate when date or time change while dialog is open
watch(
  () => [form.examDate, form.examTime],
  () => {
    if (props.isOpen) validateSelectedDateTime()
  },
)

const loadAssessors = async () => {
  try {
    assessorsOptions.value = await listAssessors({ limit: 500 })
  } catch (e) {
    assessorsOptions.value = []
  }
}

const validateSelectedDateTime = () => {
  localError.value = ''

  if (!form.examDate) {
    localError.value = 'Kies een geldige datum'
    return false
  }

  const selectedIso = `${form.examDate}T${toExamTime(form.examTime)}`
  const selected = new Date(selectedIso)
  const now = new Date()

  if (Number.isNaN(selected.getTime())) {
    localError.value = 'Ongeldige datum/tijd'
    return false
  }

  if (selected < now) {
    localError.value = 'Je kunt geen examen in het verleden plannen'
    return false
  }

  localError.value = ''
  return true
}

const updateDate = (event) => {
  form.examDate = event.target.value
  emit('update:date', event.target.value)
}

const toExamTime = (value) => {
  if (value.length === 5) {
    return `${value}:00`
  }

  return value
}

const submitForm = () => {
  localError.value = ''

  if (!form.examDate) {
    localError.value = 'Kies een geldige datum'
    return
  }

  // parse selected datetime and compare to now
  const selectedIso = `${form.examDate}T${toExamTime(form.examTime)}`
  const selected = new Date(selectedIso)
  const now = new Date()

  if (Number.isNaN(selected.getTime())) {
    localError.value = 'Ongeldige datum/tijd'
    return
  }

  if (selected < now) {
    localError.value = 'Je kunt geen examen in het verleden plannen'
    return
  }

  const payload = {
    exam_date: form.examDate,
    exam_type: form.examType,
    room: form.room.trim(),
    exam_time: toExamTime(form.examTime),
    status: form.status,
  }

  const assessorsPayload = []
  if (form.assessor_slot_1) assessorsPayload.push({ assessor_id: Number(form.assessor_slot_1), assessor_order: 1 })
  if (form.assessor_slot_2) assessorsPayload.push({ assessor_id: Number(form.assessor_slot_2), assessor_order: 2 })

  if (assessorsPayload.length) payload.assessors = assessorsPayload

  emit('submit', payload)
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-200 flex justify-end bg-[rgba(17,24,39,0.45)]" @click.self="emit('close')">
    <aside class="h-full w-[min(100%,440px)] overflow-y-auto bg-surface p-3xl shadow-[-8px_0_28px_rgba(15,23,42,0.18)]" role="dialog" aria-modal="true" aria-label="Nieuw examen">
      <div class="mb-md flex items-center justify-between">
        <h2 class="text-2xl text-heading">Nieuw examen</h2>
        <button class="h-8 w-8 cursor-pointer rounded-full border-none bg-gray-100 text-xl leading-none text-gray-800" type="button" @click="emit('close')">×</button>
      </div>

      <p class="mb-lg text-base text-text-secondary">{{ modeText }}</p>

      <form class="flex flex-col gap-lg" @submit.prevent="submitForm">
        <label class="flex flex-col gap-[0.4rem]">
          <span class="text-sm font-semibold text-gray-700">Datum</span>
          <input type="date" :value="form.examDate" required @input="updateDate" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.65rem] text-md" />
        </label>

        <label class="flex flex-col gap-[0.4rem]">
          <span class="text-sm font-semibold text-gray-700">Tijd</span>
          <input v-model="form.examTime" type="time" step="60" required class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.65rem] text-md" />
        </label>

        <label class="flex flex-col gap-[0.4rem]">
          <span class="text-sm font-semibold text-gray-700">Locatie</span>
          <input v-model.trim="form.room" type="text" maxlength="100" placeholder="Bijv. Lokaal B-204" required class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.65rem] text-md" />
        </label>

        <label class="flex flex-col gap-[0.4rem]">
          <span class="text-sm font-semibold text-gray-700">Examentype</span>
          <select v-model="form.examType" required class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.65rem] text-md">
            <option value="practical">Praktijk</option>
            <option value="avo">AVO</option>
            <option value="keuzedeel">Keuzedeel</option>
            <option value="profialdeel">Profialdeel</option>
          </select>
        </label>

        <label class="flex flex-col gap-[0.4rem]">
          <span class="text-sm font-semibold text-gray-700">Beoordelaar slot 1</span>
          <select v-model="form.assessor_slot_1" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.65rem] text-md">
            <option :value="null">— Geen —</option>
            <optgroup v-for="group in assessorsByType" :key="group.label" :label="group.label">
              <option v-for="a in group.items" :key="a.id" :value="a.id" :disabled="form.assessor_slot_2 && Number(form.assessor_slot_2) === a.id">
                {{ a.name }}{{ a.organization ? ' · ' + a.organization : '' }}
              </option>
            </optgroup>
          </select>
        </label>

        <label class="flex flex-col gap-[0.4rem]">
          <span class="text-sm font-semibold text-gray-700">Beoordelaar slot 2</span>
          <select v-model="form.assessor_slot_2" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.75rem] py-[0.65rem] text-md">
            <option :value="null">— Geen —</option>
            <optgroup v-for="group in assessorsByType" :key="group.label" :label="group.label">
              <option v-for="a in group.items" :key="a.id" :value="a.id" :disabled="form.assessor_slot_1 && Number(form.assessor_slot_1) === a.id">
                {{ a.name }}{{ a.organization ? ' · ' + a.organization : '' }}
              </option>
            </optgroup>
          </select>
        </label>

        <p v-if="localError" class="text-sm text-error">{{ localError }}</p>
        <p v-else-if="submitError" class="text-sm text-error">{{ submitError }}</p>

        <div class="mt-xs flex justify-end gap-md">
          <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="emit('close')">Annuleren</button>
          <button class="cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-65" type="submit" :disabled="isSaving">
            {{ isSaving ? 'Opslaan...' : 'Opslaan' }}
          </button>
        </div>
      </form>
    </aside>
  </div>
</template>

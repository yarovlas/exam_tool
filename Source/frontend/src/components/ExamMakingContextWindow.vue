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
  <div v-if="isOpen" class="context-window-backdrop" @click.self="emit('close')">
    <aside class="context-window" role="dialog" aria-modal="true" aria-label="Nieuw examen">
      <div class="context-window-header">
        <h2>Nieuw examen</h2>
        <button class="context-window-close" type="button" @click="emit('close')">×</button>
      </div>

      <p class="context-window-hint">{{ modeText }}</p>

      <form class="context-window-form" @submit.prevent="submitForm">
        <label>
          <span>Datum</span>
          <input type="date" :value="form.examDate" required @input="updateDate" />
        </label>

        <label>
          <span>Tijd</span>
          <input v-model="form.examTime" type="time" step="60" required />
        </label>

        <label>
          <span>Locatie</span>
          <input v-model.trim="form.room" type="text" maxlength="100" placeholder="Bijv. Lokaal B-204" required />
        </label>

        <label>
          <span>Examentype</span>
          <select v-model="form.examType" required>
            <option value="practical">Praktijk</option>
            <option value="avo">AVO</option>
            <option value="keuzedeel">Keuzedeel</option>
            <option value="profialdeel">Profialdeel</option>
          </select>
        </label>

        <label>
          <span>Beoordelaar slot 1</span>
          <select v-model="form.assessor_slot_1">
            <option :value="null">— Geen —</option>
            <option v-for="a in assessorsOptions" :key="a.id" :value="a.id" :disabled="form.assessor_slot_2 && Number(form.assessor_slot_2) === a.id">
              {{ a.name }}{{ a.organization ? ' · ' + a.organization : '' }}
            </option>
          </select>
        </label>

        <label>
          <span>Beoordelaar slot 2</span>
          <select v-model="form.assessor_slot_2">
            <option :value="null">— Geen —</option>
            <option v-for="a in assessorsOptions" :key="a.id" :value="a.id" :disabled="form.assessor_slot_1 && Number(form.assessor_slot_1) === a.id">
              {{ a.name }}{{ a.organization ? ' · ' + a.organization : '' }}
            </option>
          </select>
        </label>

        <p v-if="localError" class="context-window-error">{{ localError }}</p>
        <p v-else-if="submitError" class="context-window-error">{{ submitError }}</p>

        <div class="context-window-actions">
          <button class="btn-secondary" type="button" @click="emit('close')">Annuleren</button>
          <button class="btn-primary" type="submit" :disabled="isSaving">
            {{ isSaving ? 'Opslaan...' : 'Opslaan' }}
          </button>
        </div>
      </form>
    </aside>
  </div>
</template>

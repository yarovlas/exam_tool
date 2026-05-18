<script setup>
import { computed, reactive, watch } from 'vue'

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
}

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      resetForm(props.date)
    }
  },
)

watch(
  () => props.date,
  (newDate) => {
    form.examDate = newDate
  },
)

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
  emit('submit', {
    exam_date: form.examDate,
    exam_type: form.examType,
    room: form.room.trim(),
    exam_time: toExamTime(form.examTime),
    status: form.status,
  })
}
</script>

<template>
  <div v-if="isOpen" class="context-window-backdrop" @click.self="emit('close')">
    <aside class="context-window" role="dialog" aria-modal="true" aria-label="Nieuw examen">
      <div class="context-window-header">
        <h2>Nieuw Examen</h2>
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
          <span>Examtype</span>
          <select v-model="form.examType" required>
            <option value="practical">Praktijk</option>
            <option value="avo">AVO</option>
            <option value="keuzedeel">Keuzedeel</option>
            <option value="profialdeel">Profialdeel</option>
          </select>
        </label>

        <p v-if="submitError" class="context-window-error">{{ submitError }}</p>

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

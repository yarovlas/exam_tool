<script setup>
import { computed } from 'vue'

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
})

const emit = defineEmits(['close', 'update:date'])

const modeText = computed(() => {
  if (props.mode === 'calendar') {
    return 'Datum is automatisch ingevuld op basis van je kalenderselectie.'
  }

  return 'Kies handmatig een datum om verder te gaan.'
})

const updateDate = (event) => {
  emit('update:date', event.target.value)
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

      <form class="context-window-form" @submit.prevent>
        <label>
          <span>Examennaam</span>
          <input type="text" placeholder="Bijv. Nederlands praktijkexamen" />
        </label>

        <label>
          <span>Datum</span>
          <input type="date" :value="date" @input="updateDate" />
        </label>

        <label>
          <span>Tijd</span>
          <input type="time" />
        </label>

        <label>
          <span>Locatie</span>
          <input type="text" placeholder="Bijv. Lokaal B-204" />
        </label>

        <label>
          <span>Notities</span>
          <textarea rows="4" placeholder="Template: extra informatie voor dit examen"></textarea>
        </label>

        <div class="context-window-actions">
          <button class="btn-secondary" type="button" @click="emit('close')">Annuleren</button>
          <button class="btn-primary" type="button">Opslaan (template)</button>
        </div>
      </form>
    </aside>
  </div>
</template>

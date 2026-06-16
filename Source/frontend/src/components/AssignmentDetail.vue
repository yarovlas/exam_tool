<script setup>
const props = defineProps({
  assignment: { type: Object, required: true },
  assignmentProducts: { type: Array, default: () => [] },
  productsMap: { type: Object, default: () => ({}) },
  student: { type: Object, default: null },
})

const emit = defineEmits(['close', 'edit', 'delete'])

const roleLabels = {
  required: 'Verplicht',
  choice: 'Keuze',
  surprise: 'Verrassing',
}

const getProductName = (ap) => {
  if (ap.product_text) return ap.product_text
  if (ap.product_id && props.productsMap[ap.product_id]) return props.productsMap[ap.product_id].name
  return `Product #${ap.product_id}`
}

const handleDelete = () => {
  if (window.confirm('Weet je zeker dat je deze opdracht wilt verwijderen?')) {
    emit('delete', props.assignment.id)
  }
}
</script>

<template>
  <div class="fixed inset-0 z-200 flex justify-end bg-[rgba(17,24,39,0.45)]" @click.self="emit('close')">
    <aside class="h-full w-[min(100%,440px)] overflow-y-auto bg-surface p-3xl shadow-[-8px_0_28px_rgba(15,23,42,0.18)]" role="dialog" aria-modal="true" aria-label="Opdracht details">
      <div class="mb-md flex items-center justify-between">
        <h2 class="text-2xl text-heading">Opdracht details</h2>
        <button class="h-8 w-8 cursor-pointer rounded-full border-none bg-gray-100 text-xl leading-none text-gray-800" type="button" @click="emit('close')">×</button>
      </div>

      <div v-if="student" class="mb-lg flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
        <p class="text-sm text-text-secondary">Student</p>
        <p class="font-semibold text-text-primary">{{ student.name }}</p>
        <p class="text-sm text-text-secondary">{{ student.student_number }}</p>
        <p class="mt-xs text-sm text-text-secondary" v-if="student.program_code">Programma: {{ student.program_code }}</p>
      </div>

      <div class="mb-lg flex flex-col gap-sm rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
        <p class="text-sm font-semibold text-gray-700">Producten</p>
        <div v-for="ap in assignmentProducts" :key="ap.id" class="flex items-center justify-between border-b border-gray-100 py-xs last:border-b-0">
          <div>
            <span class="inline-flex items-center justify-center rounded-full bg-badge-bg px-[0.6rem] py-[0.2rem] text-xs capitalize text-badge-text mr-xs">
              {{ roleLabels[ap.product_role] || ap.product_role }}
            </span>
            <span class="text-sm text-text-primary">{{ getProductName(ap) }}</span>
          </div>
          <span class="text-sm font-semibold text-text-primary">{{ ap.stars }}★</span>
        </div>
      </div>

      <div class="mb-lg flex flex-col gap-sm rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
        <p class="text-sm font-semibold text-gray-700">Sterrenoverzicht</p>
        <p class="text-sm text-text-secondary">Regulier: {{ assignment.regular_stars }}★</p>
        <p class="text-sm text-text-secondary">Verrassing benodigd: {{ assignment.required_stars }}★</p>
        <p class="text-sm font-semibold text-text-primary">Totaal: {{ assignment.total_stars }}★</p>
      </div>

      <div v-if="assignment.result" class="mb-lg flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
        <p class="text-sm text-text-secondary">Resultaat</p>
        <p class="font-semibold text-text-primary">{{ assignment.result }}</p>
      </div>

      <div class="mt-xs flex justify-end gap-md">
        <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100" type="button" @click="handleDelete">
          Verwijderen
        </button>
        <button class="cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover" type="button" @click="emit('edit')">
          Bewerken
        </button>
      </div>
    </aside>
  </div>
</template>

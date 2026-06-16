<script setup>
import { computed, reactive, ref, watch, onMounted } from 'vue'
import { getOpdrachtMakerContext, calculateOpdracht, createOpdracht } from '../services/opdrachtMakerApi'

const props = defineProps({
  examStudentId: { type: Number, required: true },
  replaceExisting: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'created'])

const loading = ref(true)
const error = ref('')
const saving = ref(false)
const saveError = ref('')
const saved = ref(false)
const savedData = ref(null)
const calculating = ref(false)
const calcTimeout = ref(null)

const context = ref(null)
const calculation = ref(null)

const selections = reactive({
  products: [],
  allow_reuse: false,
  replace_existing: false,
})

const loadContext = async () => {
  loading.value = true
  error.value = ''
  try {
    const ctx = await getOpdrachtMakerContext(props.examStudentId)
    context.value = ctx
    selections.products = ctx.required_groups.map((g) => ({
      product_id: null,
      product_role: g.role,
      product_order: g.order,
    }))
    if (ctx.choice_groups.length) {
      selections.products.push({
        product_id: null,
        product_role: 'choice',
        product_order: 1,
      })
    }
    selections.products.push({
      product_id: null,
      product_role: 'surprise',
      product_order: 1,
    })
    if (props.replaceExisting) {
      selections.replace_existing = true
    }
    triggerCalculation()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Context laden mislukt'
  } finally {
    loading.value = false
  }
}

const hasChoiceGroup = computed(() => (context.value?.choice_groups?.length ?? 0) > 0)

const choiceProducts = computed(() => {
  if (!context.value) return []
  const all = []
  for (const group of context.value.choice_groups) {
    all.push(...group.products)
  }
  return all
})

const selectedIds = computed(() =>
  selections.products.filter((s) => s.product_id !== null).map((s) => s.product_id),
)

const duplicateSelectedIds = computed(() => {
  if (!context.value || !calculation.value) return []
  return calculation.value.duplicate_product_ids.filter((id) => selectedIds.value.includes(id))
})

const hasDuplicates = computed(() => duplicateSelectedIds.value.length > 0)

const canSave = computed(() => {
  if (saving.value || saved.value) return false
  if (!calculation.value) return false
  if (!calculation.value.regular_valid) return false
  if (!calculation.value.total_valid) return false
  if (hasDuplicates.value && !selections.allow_reuse) return false
  const allSelected = selections.products
    .filter((s) => s.product_role !== 'surprise')
    .every((s) => s.product_id !== null)
  if (!allSelected) return false
  return true
})

const regularStarsText = computed(() => {
  if (!calculation.value) return ''
  return `${calculation.value.regular_stars}★ / min ${calculation.value.min_regular_stars}★`
})

const requiredStarsText = computed(() => {
  if (!calculation.value) return ''
  return `${calculation.value.required_stars}★`
})

const totalStarsText = computed(() => {
  if (!calculation.value) return ''
  return `${calculation.value.total_stars}★ / min ${calculation.value.min_total_stars}★`
})

const regularValidClass = computed(() => {
  if (!calculation.value) return 'text-text-secondary'
  return calculation.value.regular_valid ? 'text-green-600' : 'text-error'
})

const totalValidClass = computed(() => {
  if (!calculation.value) return 'text-text-secondary'
  return calculation.value.total_valid ? 'text-green-600' : 'text-error'
})

const debouncedCalculate = () => {
  if (calcTimeout.value) clearTimeout(calcTimeout.value)
  calcTimeout.value = setTimeout(() => {
    triggerCalculation()
  }, 300)
}

const triggerCalculation = async () => {
  const validProducts = selections.products.filter((s) => s.product_id !== null)
  if (validProducts.length === 0) return
  calculating.value = true
  try {
    const result = await calculateOpdracht({
      exam_student_id: props.examStudentId,
      products: validProducts,
    })
    calculation.value = result
  } catch (e) {
    calculation.value = null
  } finally {
    calculating.value = false
  }
}

watch(
  () => selections.products.map((s) => s.product_id),
  () => {
    debouncedCalculate()
  },
  { deep: true },
)

const handleSave = async () => {
  saving.value = true
  saveError.value = ''
  try {
    const validProducts = selections.products.filter((s) => s.product_id !== null)
    const result = await createOpdracht({
      exam_student_id: props.examStudentId,
      products: validProducts,
      allow_reuse: selections.allow_reuse,
      replace_existing: selections.replace_existing,
      status: 'draft',
    })
    saved.value = true
    savedData.value = result
    emit('created', result)
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Opslaan mislukt'
    if (msg.includes('already exists')) {
      saveError.value = 'Er bestaat al een opdracht voor deze student. Vink "Vervangen" aan en probeer opnieuw.'
    } else {
      saveError.value = msg
    }
  } finally {
    saving.value = false
  }
}

onMounted(loadContext)
</script>

<template>
  <div class="fixed inset-0 z-200 flex justify-end bg-[rgba(17,24,39,0.45)]" @click.self="emit('close')">
    <aside class="h-full w-[min(100%,440px)] overflow-y-auto bg-surface p-3xl shadow-[-8px_0_28px_rgba(15,23,42,0.18)]" role="dialog" aria-modal="true" aria-label="Opdracht toewijzen">
      <div v-if="loading" class="flex items-center justify-center py-3xl">
        <p class="text-text-secondary">Laden...</p>
      </div>

      <div v-else-if="error" class="flex flex-col gap-md py-3xl">
        <p class="text-error">{{ error }}</p>
        <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100" type="button" @click="loadContext">
          Opnieuw proberen
        </button>
      </div>

      <div v-else-if="saved && savedData">
        <div class="mb-md flex items-center justify-between">
          <h2 class="text-2xl text-heading">Opdracht opgeslagen</h2>
          <button class="h-8 w-8 cursor-pointer rounded-full border-none bg-gray-100 text-xl leading-none text-gray-800" type="button" @click="emit('close')">×</button>
        </div>
        <div class="flex flex-col gap-md">
          <div class="rounded-xl border border-green-200 bg-green-50 px-lg py-md">
            <p class="font-semibold text-green-800">De opdracht is succesvol toegewezen.</p>
          </div>
          <div class="flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
            <p class="text-sm text-text-secondary">Totaal sterren</p>
            <p class="font-semibold text-text-primary">{{ savedData.calculation.total_stars }}★</p>
          </div>
          <div class="mt-xs flex justify-end gap-md">
            <button class="cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover" type="button" @click="emit('close')">
              Sluiten
            </button>
          </div>
        </div>
      </div>

      <div v-else-if="context">
        <div class="mb-md flex items-center justify-between">
          <h2 class="text-2xl text-heading">Opdracht toewijzen</h2>
          <button class="h-8 w-8 cursor-pointer rounded-full border-none bg-gray-100 text-xl leading-none text-gray-800" type="button" @click="emit('close')">×</button>
        </div>

        <div class="mb-lg flex flex-col gap-[0.35rem] rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
          <p class="text-sm text-text-secondary">Student</p>
          <p class="font-semibold text-text-primary">{{ context.student.name }}</p>
          <p class="text-sm text-text-secondary">{{ context.student.student_number }}</p>
          <p class="mt-xs text-sm text-text-secondary">Programma: {{ context.student.program_code }} · Fase: {{ context.student.phase }}</p>
          <p class="text-sm text-text-secondary" v-if="context.norm">
            Norm: Minimaal {{ context.norm.min_regular_stars }}★ regulier, {{ context.norm.min_total_stars }}★ totaal
          </p>
        </div>

        <div class="mb-lg flex flex-col gap-lg">
          <div v-for="group in context.required_groups" :key="group.order" class="flex flex-col gap-xs">
            <label class="text-sm font-semibold text-gray-700">{{ group.label }}</label>
            <select v-model="selections.products.find((s) => s.product_role === 'required' && s.product_order === group.order).product_id" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
              <option :value="null">— Selecteer —</option>
              <option v-for="p in group.products" :key="p.id" :value="p.id" :disabled="selectedIds.includes(p.id) && selections.products.find((s) => s.product_role === 'required' && s.product_order === group.order).product_id !== p.id">
                {{ p.name }} ({{ p.stars }}★)
              </option>
            </select>
          </div>

          <div v-if="hasChoiceGroup" class="flex flex-col gap-xs">
            <label class="text-sm font-semibold text-gray-700">Keuze</label>
            <select v-model="selections.products.find((s) => s.product_role === 'choice').product_id" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
              <option :value="null">— Selecteer —</option>
              <option v-for="p in choiceProducts" :key="p.id" :value="p.id" :disabled="selectedIds.includes(p.id) && selections.products.find((s) => s.product_role === 'choice').product_id !== p.id">
                {{ p.name }} ({{ p.stars }}★)
              </option>
            </select>
          </div>
        </div>

        <div class="mb-lg rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
          <p class="mb-sm text-sm font-semibold text-gray-700">Verrassing</p>
          <div v-if="calculation && calculation.surprise_suggestions && calculation.surprise_suggestions.length">
            <select v-model="selections.products.find((s) => s.product_role === 'surprise').product_id" class="w-full min-w-0 rounded-md border border-border bg-surface px-[0.65rem] py-[0.55rem] text-md text-text-primary">
              <option :value="null">— Minimaal {{ calculation.required_stars }}★ —</option>
              <option v-for="p in calculation.surprise_suggestions" :key="p.id" :value="p.id">
                {{ p.name }} ({{ p.stars }}★)
              </option>
            </select>
          </div>
          <p v-else class="text-sm text-text-secondary">Minimaal {{ calculation ? calculation.required_stars : '?' }}★ verrassing</p>
        </div>

        <div class="mb-lg flex flex-col gap-sm rounded-xl border border-border-light bg-detail-bg px-lg py-[0.95rem]">
          <p class="text-sm font-semibold text-gray-700">Sterrenoverzicht</p>
          <div v-if="calculating" class="text-sm text-text-secondary">Berekenen...</div>
          <div v-else-if="calculation">
            <p class="text-sm" :class="regularValidClass">Regulier: {{ regularStarsText }}</p>
            <p class="text-sm text-text-secondary">Verrassing benodigd: {{ requiredStarsText }}</p>
            <p class="text-sm" :class="totalValidClass">Totaal: {{ totalStarsText }}</p>
          </div>
          <p v-else class="text-sm text-text-secondary">Selecteer producten om sterren te berekenen</p>
        </div>

        <div v-if="hasDuplicates" class="mb-lg rounded-xl border border-amber-200 bg-amber-50 px-lg py-md">
          <p class="mb-xs text-sm font-semibold text-amber-800">Product(en) al gebruikt in eerdere fase</p>
          <p class="mb-sm text-sm text-amber-700">Sommige geselecteerde producten worden al gebruikt in een andere fase.</p>
          <label class="flex items-center gap-sm cursor-pointer">
            <input type="checkbox" v-model="selections.allow_reuse" class="h-4 w-4 rounded border-gray-300" />
            <span class="text-sm text-amber-800">Sta hergebruik toe</span>
          </label>
        </div>

        <p v-if="saveError" class="mb-sm text-sm text-error">{{ saveError }}</p>

        <div class="mt-xs flex justify-end gap-md">
          <button class="cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-65" type="button" @click="emit('close')">
            Annuleren
          </button>
          <button class="cursor-pointer whitespace-nowrap rounded-md border border-primary bg-primary px-[0.8rem] py-[0.55rem] font-semibold text-surface transition-colors hover:border-primary-hover hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-65" type="button" :disabled="!canSave || saving" @click="handleSave">
            {{ saving ? 'Opslaan...' : 'Opslaan' }}
          </button>
        </div>
      </div>
    </aside>
  </div>
</template>

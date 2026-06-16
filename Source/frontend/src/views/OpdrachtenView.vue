<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listExamPlanning } from '../services/examPlanningApi'
import { request } from '../services/apiClient'
import { getOpdrachtMakerContext } from '../services/opdrachtMakerApi'
import OpdrachtMakerWizard from '../components/OpdrachtMakerWizard.vue'
import AssignmentDetail from '../components/AssignmentDetail.vue'

const route = useRoute()
const router = useRouter()

const examPlanningItems = ref([])
const examPlanningLoading = ref(false)
const examPlanningError = ref('')
const assignmentsMap = ref({})

const selectedExamId = computed(() => {
  const raw = route.query.exam_id
  const parsed = Number(raw)
  return Number.isFinite(parsed) ? parsed : null
})

const examStudentId = computed(() => {
  const raw = route.query.exam_student_id
  const parsed = Number(raw)
  return Number.isFinite(parsed) ? parsed : null
})

const viewMode = computed(() => route.query.view || null)

const selectedExam = computed(() =>
  examPlanningItems.value.find((e) => e.id === selectedExamId.value) ?? null,
)

const examStudents = computed(() => selectedExam.value?.exam_students ?? [])

const wizardStudentId = computed(() => {
  if (viewMode.value === 'wizard' && examStudentId.value) return examStudentId.value
  return null
})

const detailAssignment = ref(null)
const detailProducts = ref([])
const detailProductsMap = ref({})
const detailStudent = ref(null)
const detailLoading = ref(false)
const detailError = ref('')

const loadExamPlanning = async () => {
  examPlanningLoading.value = true
  examPlanningError.value = ''
  try {
    examPlanningItems.value = await listExamPlanning()
  } catch (e) {
    examPlanningError.value = e instanceof Error ? e.message : 'Examens laden mislukt'
  } finally {
    examPlanningLoading.value = false
  }
}

const formatDate = (value) => {
  const d = new Date(`${value}T00:00:00`)
  return d.toLocaleDateString('nl-NL', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })
}

const formatTime = (value) => {
  const d = new Date(`1970-01-01T${value}`)
  return d.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })
}

const loadAssignments = async () => {
  const students = examStudents.value
  if (!students.length) return
  const map = {}
  try {
    const results = await Promise.allSettled(
      students.map((es) =>
        request('/assignments', { query: { exam_student_id: es.id, limit: 1 } }),
      ),
    )
    students.forEach((es, i) => {
      const r = results[i]
      if (r.status === 'fulfilled' && r.value && r.value.length > 0) {
        map[es.id] = r.value[0]
      }
    })
  } catch (e) {
    // ignore
  }
  assignmentsMap.value = map
}

watch(selectedExam, () => {
  loadAssignments()
})

const hasAssignment = (esId) => !!assignmentsMap.value[esId]

const openWizard = (esId) => {
  router.push({ name: 'opdrachten', query: { exam_student_id: esId, view: 'wizard', exam_id: selectedExamId.value } })
}

const openEdit = (esId) => {
  router.push({ name: 'opdrachten', query: { exam_student_id: esId, view: 'wizard', exam_id: selectedExamId.value, replace: '1' } })
}

const openDetail = async (esId) => {
  detailLoading.value = true
  detailError.value = ''
  detailAssignment.value = null
  detailProducts.value = []
  detailProductsMap.value = {}

  router.push({ name: 'opdrachten', query: { exam_student_id: esId, view: 'detail', exam_id: selectedExamId.value } })

  try {
    const ctx = await getOpdrachtMakerContext(esId)
    detailStudent.value = ctx.student
    const assignments = await request('/assignments', { query: { exam_student_id: esId } })
    if (assignments && assignments.length > 0) {
      const assignment = assignments[0]
      const products = await request('/assignment-products', { query: { assignment_id: assignment.id } })
      detailAssignment.value = assignment
      detailProducts.value = products

      const productIds = [...new Set(products.filter((p) => p.product_id).map((p) => p.product_id))]
      if (productIds.length) {
        const productData = await Promise.allSettled(
          productIds.map((id) => request(`/products/${id}`)),
        )
        const map = {}
        productData.forEach((result) => {
          if (result.status === 'fulfilled' && result.value) {
            map[result.value.id] = result.value
          }
        })
        detailProductsMap.value = map
      }
    } else {
      detailError.value = 'Geen opdracht gevonden voor deze student'
    }
  } catch (e) {
    detailError.value = e instanceof Error ? e.message : 'Opdracht laden mislukt'
  } finally {
    detailLoading.value = false
  }
}

const closeSlideover = () => {
  detailAssignment.value = null
  detailProducts.value = []
  detailProductsMap.value = {}
  detailStudent.value = null
  detailError.value = ''
  router.push({ name: 'opdrachten', query: { exam_id: selectedExamId.value } })
}

const onWizardCreated = () => {
  closeSlideover()
}

const onDeleteAssignment = async (assignmentId) => {
  try {
    await request(`/assignments/${assignmentId}`, { method: 'DELETE' })
    closeSlideover()
  } catch (e) {
    // handled by component
  }
}

onMounted(async () => {
  await loadExamPlanning()
  if (examStudentId.value && viewMode.value === 'detail') {
    openDetail(examStudentId.value)
  }
})
</script>

<template>
  <main class="mx-auto flex w-[1400px] flex-col p-3xl">
    <section class="mb-3xl flex items-start justify-between gap-2xl">
      <div>
        <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Opdrachten</p>
        <h1 class="m-0 text-5xl text-text-primary">Praktijkopdrachten beheren</h1>
        <p class="mt-md max-w-[60ch] text-text-secondary">
          Selecteer een examen om opdrachten toe te wijzen aan studenten.
        </p>
      </div>
    </section>

    <section v-if="examPlanningLoading" class="py-3xl">
      <p class="text-text-secondary">Examens laden...</p>
    </section>

    <section v-else-if="examPlanningError" class="py-3xl">
      <p class="text-error">{{ examPlanningError }}</p>
      <button class="mt-md cursor-pointer whitespace-nowrap rounded-md border border-border bg-surface px-[0.8rem] py-[0.55rem] font-semibold text-primary transition-colors hover:bg-gray-100" type="button" @click="loadExamPlanning">
        Opnieuw proberen
      </button>
    </section>

    <section v-else-if="!examPlanningItems.length" class="py-3xl">
      <p class="text-text-secondary">Er zijn nog geen examens aangemaakt.</p>
    </section>

    <template v-else>
      <section class="flex-1 grid min-h-0 gap-2xl" style="grid-template-columns: 360px 900px">
        <aside class="flex min-h-0 flex-col rounded-3xl bg-surface p-xl shadow-card">
          <div class="mb-lg">
            <h2 class="m-0 text-text-primary">Examenlijst</h2>
            <p class="mt-[0.35rem] text-base text-text-secondary">{{ examPlanningItems.length }} examens</p>
          </div>

          <div class="flex flex-1 flex-col gap-md overflow-y-auto min-h-0 pt-px" style="max-height: calc(100vh - 300px)">
            <RouterLink
              v-for="exam in examPlanningItems"
              :key="exam.id"
              class="block w-full rounded-2xl border border-border-light bg-surface px-lg py-lg text-left text-inherit no-underline transition-all duration-200 hover:border-[#9ca3af] hover:shadow-hover"
              :class="{ 'border-[#9ca3af] shadow-hover': exam.id === selectedExamId }"
              :to="{ name: 'opdrachten', query: { exam_id: exam.id } }"
            >
              <div class="mb-[0.65rem]">
                <span class="text-base text-text-secondary">{{ formatDate(exam.exam_date) }}</span>
              </div>
              <h3 class="m-0 text-lg text-text-primary">{{ exam.exam_type }}</h3>
              <p class="m-0 mt-[0.35rem] text-base text-text-secondary">{{ formatTime(exam.exam_time) }} · {{ exam.room }} · {{ (exam.exam_students || []).length }} studenten</p>
            </RouterLink>
          </div>
        </aside>

        <section class="rounded-3xl bg-surface p-2xl shadow-card">
          <div v-if="!selectedExam" class="flex min-h-[300px] flex-col items-start justify-center">
            <h2 class="m-0 text-4xl text-text-primary">Selecteer een examen</h2>
            <p class="mt-md text-text-muted">Kies links een examen om de studenten te bekijken.</p>
          </div>

          <div v-else-if="!examStudents.length">
            <div class="mb-xl flex items-start justify-between gap-lg">
              <div>
                <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Studenten</p>
                <h2 class="m-0 text-4xl text-text-primary">{{ selectedExam.exam_type }}</h2>
              </div>
            </div>
            <p class="text-text-secondary">Nog geen studenten toegewezen aan dit examen.</p>
          </div>

          <div v-else>
            <div class="mb-xl flex items-start justify-between gap-lg">
              <div>
                <p class="mb-sm text-xs uppercase tracking-[0.14em] text-text-secondary">Studenten</p>
                <h2 class="m-0 text-4xl text-text-primary">{{ selectedExam.exam_type }}</h2>
              </div>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full border-collapse text-md">
                <thead>
                  <tr class="border-b-2 border-b-border-light">
                    <th class="p-sm text-left font-semibold text-text-secondary">Naam</th>
                    <th class="p-sm text-left font-semibold text-text-secondary">SchoolID</th>
                    <th class="p-sm text-left font-semibold text-text-secondary">Actie</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="es in examStudents" :key="es.id" class="border-b border-b-gray-100">
                    <td class="p-sm font-semibold">{{ es.student.name }}</td>
                    <td class="p-sm text-text-secondary">{{ es.student.student_number }}</td>
                    <td class="p-sm">
                      <div class="flex items-center gap-[0.4rem]">
                        <button type="button"
                          class="cursor-pointer rounded-[0.4rem] border border-border bg-surface px-[0.5rem] py-[0.25rem] text-sm text-gray-700 hover:bg-gray-100"
                          @click="openDetail(es.id)"
                        >
                          Bekijken
                        </button>
                        <button v-if="hasAssignment(es.id)" type="button"
                          class="cursor-pointer whitespace-nowrap rounded-[0.4rem] border border-primary bg-primary px-[0.5rem] py-[0.25rem] text-sm text-surface hover:bg-primary-hover"
                          @click="openEdit(es.id)"
                        >
                          Bewerken
                        </button>
                        <button v-else type="button"
                          class="cursor-pointer whitespace-nowrap rounded-[0.4rem] border border-border bg-surface px-[0.5rem] py-[0.25rem] text-sm text-gray-700 hover:bg-gray-100"
                          @click="openWizard(es.id)"
                        >
                          Toewijzen
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </section>
    </template>

    <OpdrachtMakerWizard
      v-if="wizardStudentId"
      :examStudentId="wizardStudentId"
      :replaceExisting="route.query.replace === '1'"
      @close="closeSlideover"
      @created="onWizardCreated"
    />

    <AssignmentDetail
      v-if="detailAssignment && viewMode === 'detail'"
      :assignment="detailAssignment"
      :assignmentProducts="detailProducts"
      :productsMap="detailProductsMap"
      :student="detailStudent"
      @close="closeSlideover"
      @edit="openEdit(examStudentId)"
      @delete="onDeleteAssignment"
    />

    <div v-if="detailLoading && viewMode === 'detail' && !detailAssignment" class="fixed inset-0 z-200 flex justify-end bg-[rgba(17,24,39,0.45)]">
      <aside class="h-full w-[min(100%,440px)] overflow-y-auto bg-surface p-3xl shadow-[-8px_0_28px_rgba(15,23,42,0.18)]">
        <p class="text-text-secondary">Opdracht laden...</p>
      </aside>
    </div>

    <div v-if="detailError && viewMode === 'detail' && !detailAssignment" class="fixed inset-0 z-200 flex justify-end bg-[rgba(17,24,39,0.45)]" @click.self="closeSlideover">
      <aside class="h-full w-[min(100%,440px)] overflow-y-auto bg-surface p-3xl shadow-[-8px_0_28px_rgba(15,23,42,0.18)]">
        <div class="mb-md flex items-center justify-between">
          <h2 class="text-2xl text-heading">Opdracht details</h2>
          <button class="h-8 w-8 cursor-pointer rounded-full border-none bg-gray-100 text-xl leading-none text-gray-800" type="button" @click="closeSlideover">×</button>
        </div>
        <p class="text-error">{{ detailError }}</p>
      </aside>
    </div>
  </main>
</template>

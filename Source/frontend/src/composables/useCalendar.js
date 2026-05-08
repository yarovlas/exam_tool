import { computed, ref } from 'vue'

export function useCalendar() {
  const currentDate = ref(new Date())

  const monthYear = computed(() => {
    return currentDate.value
      .toLocaleDateString('nl-NL', { month: 'long', year: 'numeric' })
      .replace(/^\w/, (char) => char.toUpperCase())
  })

  const daysInMonth = computed(() => {
    return new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1, 0).getDate()
  })

  const firstDayOfMonth = computed(() => {
    return new Date(currentDate.value.getFullYear(), currentDate.value.getMonth(), 1).getDay()
  })

  const calendarDays = computed(() => {
    const days = []
    const startDay = firstDayOfMonth.value || 7

    for (let i = 1; i < startDay; i += 1) {
      days.push(null)
    }

    for (let i = 1; i <= daysInMonth.value; i += 1) {
      days.push(i)
    }

    return days
  })

  const previousMonth = () => {
    currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1)
  }

  const nextMonth = () => {
    currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1)
  }

  return {
    calendarDays,
    monthYear,
    nextMonth,
    previousMonth,
  }
}

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <main class="mx-auto w-[1400px] px-3xl">
    <section class="rounded-lg bg-surface p-3xl shadow-card">
      <h1 class="mb-md text-5xl text-heading">{{ title }}</h1>
      <p class="text-md text-text-light">Deze pagina is klaar voor verdere implementatie.</p>
    </section>
  </main>
</template>

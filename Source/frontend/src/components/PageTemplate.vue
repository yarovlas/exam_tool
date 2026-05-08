<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <main class="main-content">
    <section class="page-template">
      <h1>{{ title }}</h1>
      <p>Deze pagina is klaar voor verdere implementatie.</p>
    </section>
  </main>
</template>

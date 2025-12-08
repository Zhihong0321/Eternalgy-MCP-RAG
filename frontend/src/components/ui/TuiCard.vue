<script setup>
const props = defineProps({
  title: String,
  subtitle: String
})
</script>

<template>
  <section class="tui-surface rounded-xl border border-slate-200 p-5 shadow-[0_12px_40px_rgba(15,23,42,0.08)]">
    <header v-if="title || subtitle" class="mb-4 flex items-start justify-between gap-3">
      <div class="space-y-1">
        <p v-if="subtitle" class="text-[11px] uppercase tracking-[0.22em] text-slate-500">
          {{ subtitle }}
        </p>
        <h3 v-if="title" class="text-lg font-semibold text-slate-900">{{ title }}</h3>
      </div>
      <div>
        <slot name="actions" />
      </div>
    </header>
    <div>
      <slot />
    </div>
  </section>
</template>

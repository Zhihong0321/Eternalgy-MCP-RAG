<script setup>
const props = defineProps({
  title: String,
  subtitle: String
})
</script>

<template>
  <section class="tui-surface rounded-none border border-[var(--border)] p-5">
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

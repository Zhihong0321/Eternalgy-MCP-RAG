<script setup>
const props = defineProps({
  title: String,
  subtitle: String
})
</script>

<template>
  <section class="tui-surface rounded-lg border border-[var(--border)] p-5">
    <header v-if="title || subtitle" class="mb-4 flex items-start justify-between gap-3">
      <div class="space-y-1">
        <p v-if="subtitle" class="text-xs uppercase tracking-wider text-[var(--muted)]">
          {{ subtitle }}
        </p>
        <h3 v-if="title" class="text-lg font-semibold text-[var(--text)]">{{ title }}</h3>
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

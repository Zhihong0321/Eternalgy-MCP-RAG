<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'muted'
  }
})

const variants = {
  success:
    'border-slate-900 bg-slate-900 text-white',
  info:
    'border-slate-600 bg-slate-100 text-slate-900',
  warning:
    'border-slate-400 bg-slate-50 text-slate-700',
  muted:
    'border-slate-300 bg-white text-slate-700'
}

const classes = computed(() => [
  'inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]',
  variants[props.variant] || variants.muted
])
</script>

<template>
  <span :class="classes">
    <slot />
  </span>
</template>

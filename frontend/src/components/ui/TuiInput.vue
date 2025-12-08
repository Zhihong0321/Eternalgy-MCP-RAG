<script setup>
const props = defineProps({
  label: String,
  hint: String,
  placeholder: {
    type: String,
    default: ''
  },
  modelValue: {
    type: [String, Number],
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  }
})

const emit = defineEmits(['update:modelValue'])

const onInput = (event) => {
  emit('update:modelValue', event.target.value)
}
</script>

<template>
  <label class="flex flex-col gap-2 text-sm text-slate-800">
    <div class="flex items-center justify-between">
      <span class="text-[11px] uppercase tracking-[0.2em] text-slate-600">{{ label }}</span>
      <span v-if="hint" class="text-[11px] text-slate-500">{{ hint }}</span>
    </div>
    <div class="breathing-ring">
      <input
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-[inset_0_1px_1px_rgba(15,23,42,0.06)] focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200"
        @input="onInput"
      />
    </div>
  </label>
</template>

<style scoped>
.breathing-ring {
  position: relative;
  border-radius: 0.5rem;
}

.breathing-ring::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: inherit;
  background: linear-gradient(120deg, #16f2b3, #7c3aed, #06b6d4, #16f2b3);
  background-size: 220% 220%;
  opacity: 0;
  z-index: 0;
  filter: blur(0.5px);
  transition: opacity 0.3s ease;
  animation: breatheGradient 3s ease-in-out infinite;
  pointer-events: none;
}

.breathing-ring:focus-within::after {
  opacity: 0.65;
}

.breathing-ring > input {
  position: relative;
  z-index: 1;
}

@keyframes breatheGradient {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}
</style>

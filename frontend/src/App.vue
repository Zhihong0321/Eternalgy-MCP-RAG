<script setup>
</script>

<template>
  <div class="relative min-h-screen text-gray-900">
    <div class="pointer-events-none absolute inset-0 tui-grid opacity-60" aria-hidden="true"></div>
    <div class="pointer-events-none absolute inset-0 bg-aurora opacity-80" aria-hidden="true"></div>
    <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/80 via-white/60 to-transparent" aria-hidden="true"></div>
    <div class="relative min-h-screen">
      <router-view />
    </div>
  </div>
</template>

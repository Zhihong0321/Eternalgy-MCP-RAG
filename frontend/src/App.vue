<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTheme } from './composables/theme'

const route = useRoute()
const { theme } = useTheme()

const isActive = (path) => computed(() => route.path === path || route.path.startsWith(path))
const showNav = computed(() => !route.meta?.bare)
</script>

<template>
  <div :class="['relative min-h-screen', theme === 'dark' ? 'text-slate-100' : 'text-gray-900']">
    <div class="pointer-events-none absolute inset-0 tui-grid opacity-60" aria-hidden="true"></div>
    <div class="pointer-events-none absolute inset-0 bg-aurora opacity-80" aria-hidden="true"></div>
    <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/80 via-white/60 to-transparent" aria-hidden="true"></div>
    <div class="relative min-h-screen">
      <header v-if="showNav" class="sticky top-0 z-30 bg-white/70 backdrop-blur">
        <nav class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <router-link to="/" class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-900">
            z.ai admin
          </router-link>
          <div class="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em]">
            <router-link
              to="/"
              :class="[
                'rounded-md px-3 py-2 transition hover:bg-slate-900 hover:text-white',
                isActive('/').value ? 'bg-slate-900 text-white' : 'text-slate-700'
              ]"
            >
              dashboard
            </router-link>
            <router-link
              to="/agents"
              :class="[
                'rounded-md px-3 py-2 transition hover:bg-slate-900 hover:text-white',
                isActive('/agents').value ? 'bg-slate-900 text-white' : 'text-slate-700'
              ]"
            >
              agents
            </router-link>
            <router-link
              to="/mcps"
              :class="[
                'rounded-md px-3 py-2 transition hover:bg-slate-900 hover:text-white',
                isActive('/mcps').value ? 'bg-slate-900 text-white' : 'text-slate-700'
              ]"
            >
              mcps
            </router-link>
            <router-link
              to="/chat"
              :class="[
                'rounded-md px-3 py-2 transition hover:bg-slate-900 hover:text-white',
                isActive('/chat').value ? 'bg-slate-900 text-white' : 'text-slate-700'
              ]"
            >
              chat
            </router-link>
            <router-link
              to="/components"
              :class="[
                'rounded-md px-3 py-2 transition hover:bg-slate-900 hover:text-white',
                isActive('/components').value ? 'bg-slate-900 text-white' : 'text-slate-700'
              ]"
            >
              components
            </router-link>
            <router-link
              to="/settings"
              :class="[
                'rounded-md px-3 py-2 transition hover:bg-slate-900 hover:text-white',
                isActive('/settings').value ? 'bg-slate-900 text-white' : 'text-slate-700'
              ]"
            >
              settings
            </router-link>
          </div>
        </nav>
      </header>
      <router-view />
    </div>
  </div>
</template>

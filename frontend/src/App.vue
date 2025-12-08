<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTheme } from './composables/theme'

const route = useRoute()
const { theme } = useTheme()
const isDark = computed(() => theme.value === 'dark')

const isActive = (path) => computed(() => route.path === path || route.path.startsWith(path))
const showNav = computed(() => !route.meta?.bare)
</script>

<template>
  <div :class="['relative min-h-screen', isDark ? 'text-slate-100' : 'text-gray-900']">
    <div class="pointer-events-none absolute inset-0 tui-grid opacity-60" aria-hidden="true"></div>
    <div class="pointer-events-none absolute inset-0 bg-aurora opacity-80" aria-hidden="true"></div>
    <div
      class="pointer-events-none absolute inset-0"
      :class="
        isDark
          ? 'bg-gradient-to-br from-slate-950/90 via-slate-950/85 to-black'
          : 'bg-gradient-to-br from-white/80 via-white/60 to-transparent'
      "
      aria-hidden="true"
    ></div>
    <div class="relative min-h-screen">
      <header
        v-if="showNav"
        :class="[
          'sticky top-0 z-30 backdrop-blur transition-colors',
          isDark ? 'bg-slate-950/80 border-b border-slate-900' : 'bg-white/70'
        ]"
      >
        <nav class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <router-link
            to="/"
            :class="[
              'text-xs font-semibold uppercase tracking-[0.24em]',
              isDark ? 'text-slate-100' : 'text-slate-900'
            ]"
          >
            z.ai admin
          </router-link>
          <div class="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em]">
            <router-link
              to="/"
              :class="[
                'rounded-md px-3 py-2 transition',
                isDark ? 'hover:bg-slate-800 hover:text-white' : 'hover:bg-slate-900 hover:text-white',
                isActive('/').value
                  ? isDark
                    ? 'bg-slate-800 text-white'
                    : 'bg-slate-900 text-white'
                  : isDark
                    ? 'text-slate-200'
                    : 'text-slate-700'
              ]"
            >
              dashboard
            </router-link>
            <router-link
              to="/agents"
              :class="[
                'rounded-md px-3 py-2 transition',
                isDark ? 'hover:bg-slate-800 hover:text-white' : 'hover:bg-slate-900 hover:text-white',
                isActive('/agents').value
                  ? isDark
                    ? 'bg-slate-800 text-white'
                    : 'bg-slate-900 text-white'
                  : isDark
                    ? 'text-slate-200'
                    : 'text-slate-700'
              ]"
            >
              agents
            </router-link>
            <router-link
              to="/mcps"
              :class="[
                'rounded-md px-3 py-2 transition',
                isDark ? 'hover:bg-slate-800 hover:text-white' : 'hover:bg-slate-900 hover:text-white',
                isActive('/mcps').value
                  ? isDark
                    ? 'bg-slate-800 text-white'
                    : 'bg-slate-900 text-white'
                  : isDark
                    ? 'text-slate-200'
                    : 'text-slate-700'
              ]"
            >
              mcps
            </router-link>
            <router-link
              to="/chat"
              :class="[
                'rounded-md px-3 py-2 transition',
                isDark ? 'hover:bg-slate-800 hover:text-white' : 'hover:bg-slate-900 hover:text-white',
                isActive('/chat').value
                  ? isDark
                    ? 'bg-slate-800 text-white'
                    : 'bg-slate-900 text-white'
                  : isDark
                    ? 'text-slate-200'
                    : 'text-slate-700'
              ]"
            >
              chat
            </router-link>
            <router-link
              to="/components"
              :class="[
                'rounded-md px-3 py-2 transition',
                isDark ? 'hover:bg-slate-800 hover:text-white' : 'hover:bg-slate-900 hover:text-white',
                isActive('/components').value
                  ? isDark
                    ? 'bg-slate-800 text-white'
                    : 'bg-slate-900 text-white'
                  : isDark
                    ? 'text-slate-200'
                    : 'text-slate-700'
              ]"
            >
              components
            </router-link>
            <router-link
              to="/settings"
              :class="[
                'rounded-md px-3 py-2 transition',
                isDark ? 'hover:bg-slate-800 hover:text-white' : 'hover:bg-slate-900 hover:text-white',
                isActive('/settings').value
                  ? isDark
                    ? 'bg-slate-800 text-white'
                    : 'bg-slate-900 text-white'
                  : isDark
                    ? 'text-slate-200'
                    : 'text-slate-700'
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

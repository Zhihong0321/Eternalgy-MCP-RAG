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
  <div
    :class="[
      'min-h-screen',
      isDark ? 'bg-[#0e0e10] text-[var(--text)]' : 'bg-[var(--bg)] text-[var(--text)]'
    ]"
  >
    <header
      v-if="showNav"
      :class="[
        'border-b',
        isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-gray-300'
      ]"
    >
      <nav class="mx-auto flex max-w-6xl justify-end px-4">
        <div class="flex">
          <router-link
            to="/"
            :class="[
              'px-6 py-3 text-xs uppercase tracking-[0.16em] -ml-px border transition-colors',
              'first:ml-0',
              isDark ? 'border-slate-700' : 'border-gray-300',
              isActive('/').value
                ? isDark
                  ? 'bg-slate-700 text-white'
                  : 'bg-gray-200 text-gray-900'
                : isDark
                  ? 'bg-slate-900 text-slate-100 hover:bg-slate-800'
                  : 'bg-white text-gray-800 hover:bg-gray-100'
            ]"
          >
            agent
          </router-link>
          <router-link
            to="/mcps"
            :class="[
              'px-6 py-3 text-xs uppercase tracking-[0.16em] -ml-px border transition-colors',
              'first:ml-0',
              isDark ? 'border-slate-700' : 'border-gray-300',
              isActive('/mcps').value
                ? isDark
                  ? 'bg-slate-700 text-white'
                  : 'bg-gray-200 text-gray-900'
                : isDark
                  ? 'bg-slate-900 text-slate-100 hover:bg-slate-800'
                  : 'bg-white text-gray-800 hover:bg-gray-100'
            ]"
          >
            mcp
          </router-link>
          <router-link
            to="/chat"
            :class="[
              'px-6 py-3 text-xs uppercase tracking-[0.16em] -ml-px border transition-colors',
              'first:ml-0',
              isDark ? 'border-slate-700' : 'border-gray-300',
              isActive('/chat').value
                ? isDark
                  ? 'bg-slate-700 text-white'
                  : 'bg-gray-200 text-gray-900'
                : isDark
                  ? 'bg-slate-900 text-slate-100 hover:bg-slate-800'
                  : 'bg-white text-gray-800 hover:bg-gray-100'
            ]"
          >
            chat
          </router-link>
        </div>
      </nav>
    </header>
    <router-view />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import TuiBadge from '../components/ui/TuiBadge.vue'
import TuiButton from '../components/ui/TuiButton.vue'

const API_BASE = `${window.location.origin}/api/v1`

const agents = ref([])
const threads = ref([])
const isLoadingAgents = ref(true)
const isLoadingThreads = ref(true)
const agentError = ref('')
const threadError = ref('')

const statusVariant = (status) => {
  const normalized = (status || '').toLowerCase()
  if (normalized === 'live' || normalized === 'active' || normalized === 'ready') return 'success'
  if (normalized === 'watch' || normalized === 'syncing' || normalized === 'listening' || normalized === 'cooldown') return 'warning'
  return 'muted'
}

const formatTokens = (value) => {
  const num = Number(value)
  if (Number.isNaN(num)) return value || '—'
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`
  return `${num}`
}

const lastActiveThreads = computed(() => threads.value.slice(0, 10))
const totalAgents = computed(() => agents.value.length)
const activeThreadsCount = computed(() => lastActiveThreads.value.length)
const totalTokensToday = computed(() =>
  agents.value.reduce((acc, agent) => acc + (Number(agent.tokenCountToday) || 0), 0)
)

const loadAgents = async () => {
  isLoadingAgents.value = true
  agentError.value = ''
  try {
    const res = await fetch(`${API_BASE}/agents/`)
    if (!res.ok) throw new Error('Failed to fetch agents')
    const data = await res.json()
    agents.value = Array.isArray(data)
      ? data.map((agent, index) => ({
          id: agent.id ?? index,
          name: agent.name ?? 'Unknown Agent',
          model: agent.model ?? 'n/a',
          status: (agent.status ?? 'ready').toLowerCase(),
          lastActive: agent.lastActive ?? agent.last_active ?? '—',
          tokenCountToday: agent.tokenCountToday ?? agent.token_count_today ?? 0
        }))
      : []
  } catch (error) {
    console.error('Failed to load agents', error)
    agentError.value = 'Failed to load agents from API.'
    agents.value = []
  } finally {
    isLoadingAgents.value = false
  }
}

const loadThreads = async () => {
  isLoadingThreads.value = true
  threadError.value = ''
  try {
    const res = await fetch(`${API_BASE}/threads?limit=10&status=active`)
    if (!res.ok) throw new Error('Failed to fetch threads')
    const data = await res.json()
    threads.value = Array.isArray(data)
      ? data.map((thread, index) => ({
          id: thread.id ?? index,
          title: thread.title ?? thread.name ?? 'Thread',
          agent: thread.agent ?? thread.agent_name ?? 'unknown',
          lastActive: thread.lastActive ?? thread.last_active ?? '—',
          tokensUsed: thread.tokensUsed ?? thread.tokens_used ?? 0,
          status: (thread.status ?? 'active').toLowerCase()
        }))
      : []
  } catch (error) {
    console.error('Failed to load threads', error)
    threadError.value = 'Failed to load threads from API.'
    threads.value = []
  } finally {
    isLoadingThreads.value = false
  }
}

onMounted(() => {
  loadAgents()
  loadThreads()
})
</script>

<template>
  <div class="relative min-h-screen">
    <main class="relative z-10 mx-auto w-full max-w-none px-5 lg:px-10 py-10 space-y-8">
      <header class="tui-surface rounded-xl border border-slate-200 p-6">
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div class="space-y-2">
            <p class="text-xs uppercase tracking-[0.32em] text-slate-500">z.ai admin</p>
            <h1 class="text-3xl font-bold text-slate-900">RAG Control Dashboard</h1>
            <p class="text-sm text-slate-600">
              Manage agents, MCP links, and active threads. Home routes to the latest status.
            </p>
            <div class="flex flex-wrap items-center gap-2">
              <TuiBadge variant="info">/api/v1</TuiBadge>
            <TuiBadge variant="muted">base: dynamic (current host)</TuiBadge>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <router-link to="/agents">
              <TuiButton size="sm">Agent management</TuiButton>
            </router-link>
            <router-link to="/mcps">
              <TuiButton size="sm" variant="outline">MCP management</TuiButton>
            </router-link>
            <router-link to="/chat">
              <TuiButton size="sm" variant="outline">Chat tester</TuiButton>
            </router-link>
            <router-link to="/components">
              <TuiButton size="sm" variant="outline">component library</TuiButton>
            </router-link>
          </div>
        </div>
      </header>

      <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div class="tui-surface rounded-lg border border-slate-200 px-4 py-3">
          <p class="text-xs uppercase tracking-[0.26em] text-slate-500">agents online</p>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-3xl font-bold text-slate-900">{{ totalAgents.toString().padStart(2, '0') }}</span>
            <span class="text-sm text-slate-600">managed</span>
          </div>
        </div>
        <div class="tui-surface rounded-lg border border-slate-200 px-4 py-3">
          <p class="text-xs uppercase tracking-[0.26em] text-slate-500">active threads</p>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-3xl font-bold text-slate-900">{{ activeThreadsCount.toString().padStart(2, '0') }}</span>
            <span class="text-sm text-slate-600">last 10</span>
          </div>
        </div>
        <div class="tui-surface rounded-lg border border-slate-200 px-4 py-3">
          <p class="text-xs uppercase tracking-[0.26em] text-slate-500">tokens today</p>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-3xl font-bold text-slate-900">{{ formatTokens(totalTokensToday) }}</span>
            <span class="text-sm text-slate-600">sum</span>
          </div>
        </div>
        <div class="tui-surface rounded-lg border border-slate-200 px-4 py-3">
          <p class="text-xs uppercase tracking-[0.26em] text-slate-500">api base</p>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-3xl font-bold text-slate-900">/api</span>
            <span class="text-sm text-slate-600">v1</span>
          </div>
          <p class="mt-1 text-xs text-slate-600">Uses current host for API calls.</p>
        </div>
      </section>

      <section class="grid gap-6 xl:grid-cols-[2fr_1.1fr]">
        <div class="tui-surface rounded-xl border border-slate-200 p-5">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-slate-500">agents</p>
              <h2 class="text-xl font-semibold text-slate-900">Status & Usage</h2>
            </div>
            <div class="flex items-center gap-2 text-xs text-slate-700">
              <span class="h-2 w-2 rounded-full bg-slate-900"></span>
              live sync
            </div>
          </div>
          <div class="mt-4 space-y-2 text-xs text-slate-600" v-if="agentError">
            {{ agentError }}
          </div>
          <div v-if="isLoadingAgents" class="mt-6 text-sm text-slate-600">Loading agents...</div>
          <div v-else class="mt-4 divide-y divide-slate-200">
            <div
              v-for="agent in agents"
              :key="agent.id"
              class="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div class="flex items-center gap-3">
                <div class="h-10 w-10 rounded-md border border-slate-300 bg-white text-center text-sm font-semibold leading-10 uppercase text-slate-800">
                  {{ agent.name.slice(0, 2) }}
                </div>
                <div>
                  <p class="text-base font-semibold text-slate-900">{{ agent.name }}</p>
                  <p class="text-sm text-slate-600">{{ agent.model }}</p>
                </div>
              </div>
              <div class="grid w-full grid-cols-2 gap-4 text-sm text-slate-700 sm:w-auto sm:grid-cols-3 sm:items-center">
                <div>
                  <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500">tokens today</p>
                  <p class="font-semibold">{{ formatTokens(agent.tokenCountToday) }}</p>
                </div>
                <div>
                  <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500">last active</p>
                  <p class="font-semibold">{{ agent.lastActive || '—' }}</p>
                </div>
                <TuiBadge :variant="statusVariant(agent.status)" class="w-24 justify-center">
                  {{ agent.status || 'ready' }}
                </TuiBadge>
              </div>
            </div>
            <div v-if="!agents.length" class="py-6 text-sm text-slate-600">
              No agents found. Create one from Agent Management.
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="tui-surface rounded-xl border border-slate-200 p-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs uppercase tracking-[0.24em] text-slate-500">threads</p>
                <h2 class="text-xl font-semibold text-slate-900">Last 10 Active</h2>
              </div>
              <router-link to="/threads" class="text-xs uppercase tracking-[0.2em] text-slate-600 hover:text-slate-800">
                manage threads
              </router-link>
            </div>
            <div class="mt-3 space-y-2 text-xs text-slate-600" v-if="threadError">
              {{ threadError }}
            </div>
            <div v-if="isLoadingThreads" class="mt-6 text-sm text-slate-600">Loading threads...</div>
            <div v-else class="mt-4 space-y-3">
              <div
                v-for="thread in lastActiveThreads"
                :key="thread.id"
                class="rounded-lg border border-slate-200 px-4 py-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <p class="text-base font-semibold text-slate-900">{{ thread.title }}</p>
                  <TuiBadge :variant="statusVariant(thread.status)" class="w-24 justify-center">
                    {{ thread.status }}
                  </TuiBadge>
                </div>
                <p class="text-sm text-slate-600">Agent: {{ thread.agent }}</p>
                <div class="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-700">
                  <span>Tokens: {{ formatTokens(thread.tokensUsed) }}</span>
                  <span>Last active: {{ thread.lastActive }}</span>
                </div>
              </div>
              <div v-if="!lastActiveThreads.length" class="rounded-lg border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-600">
                No active threads yet.
              </div>
            </div>
          </div>

          <div class="tui-surface rounded-xl border border-slate-200 p-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs uppercase tracking-[0.24em] text-slate-500">api status</p>
                <h2 class="text-xl font-semibold text-slate-900">Signals</h2>
              </div>
              <TuiBadge variant="muted">/api/v1</TuiBadge>
            </div>
            <div class="mt-4 space-y-3 text-sm text-slate-700">
              <p class="flex items-center gap-2">
                <span class="h-2 w-2 rounded-full bg-slate-900"></span>
                Dashboard is wired to the current host (no localhost hardcoding).
              </p>
              <p class="flex items-center gap-2">
                <span class="h-2 w-2 rounded-full bg-slate-500"></span>
                Agents fetch from `/agents/`; threads fetch from `/threads`.
              </p>
              <p class="flex items-center gap-2">
                <span class="h-2 w-2 rounded-full bg-slate-300"></span>
                Fallback data renders when API is unreachable.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

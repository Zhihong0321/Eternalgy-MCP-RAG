<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TuiBadge from '../components/ui/TuiBadge.vue'
import TuiButton from '../components/ui/TuiButton.vue'
import TuiSelect from '../components/ui/TuiSelect.vue'

const API_BASE = `${window.location.origin}/api/v1`
const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws`

const route = useRoute()
const router = useRouter()

const agents = ref([])
const isLoadingAgents = ref(true)
const agentError = ref('')
const isSending = ref(false)
const composer = ref('')
const status = ref('idle')
const socket = ref(null)
const socketReady = ref(false)
const socketConnecting = ref(false)
const streamStatus = ref('disconnected')
const toolStatus = ref('')
const tokenStats = ref(null)

const conversations = reactive({})
const currentAgentId = ref('')

const statusVariant = (state) => {
  const normalized = (state || '').toLowerCase()
  if (normalized === 'live' || normalized === 'active' || normalized === 'ready') return 'success'
  if (normalized === 'watch' || normalized === 'syncing' || normalized === 'cooldown') return 'warning'
  return 'muted'
}

const agentOptions = computed(() =>
  agents.value.map((agent) => ({
    label: agent.name,
    value: String(agent.id)
  }))
)

const currentAgent = computed(() =>
  agents.value.find((agent) => String(agent.id) === String(currentAgentId.value))
)

const currentConversation = computed(() => ensureConversation(String(currentAgentId.value || '')))

const ensureConversation = (key) => {
  if (!key) return []
  if (!conversations[key]) conversations[key] = []
  return conversations[key]
}

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
          name: agent.name ?? 'Agent',
          model: agent.model ?? 'n/a',
          status: (agent.status ?? 'ready').toLowerCase()
        }))
      : []
  } catch (error) {
    console.error('Failed to load agents', error)
    agentError.value = 'Failed to load agents from API.'
    agents.value = []
  } finally {
    isLoadingAgents.value = false
    if (!currentAgentId.value && agents.value.length) {
      currentAgentId.value = String(agents.value[0].id)
    }
  }
}

const setAgentFromRoute = () => {
  const paramId = route.params.agentId || route.query.agentId
  if (paramId) currentAgentId.value = String(paramId)
}

const handleAgentChange = (agentId) => {
  currentAgentId.value = agentId
  router.replace({ name: 'Chat', params: { agentId } })
  connectSocket()
}

const startNewChat = () => {
  if (!currentAgentId.value) return
  conversations[String(currentAgentId.value)] = []
  tokenStats.value = null
  streamStatus.value = 'ready'
}

const cleanupSocket = () => {
  if (socket.value) {
    socket.value.close()
    socket.value = null
  }
  socketReady.value = false
  socketConnecting.value = false
}

const connectSocket = () => {
  cleanupSocket()
  const agentId = currentAgentId.value
  if (!agentId) return

  socketConnecting.value = true
  streamStatus.value = 'connecting'
  tokenStats.value = null
  toolStatus.value = ''

  const ws = new WebSocket(`${WS_BASE}/chat/${agentId}`)
  socket.value = ws

  ws.onopen = () => {
    socketReady.value = true
    socketConnecting.value = false
    streamStatus.value = 'ready'
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    const convo = ensureConversation(String(agentId))

    switch (data.type) {
      case 'token': {
        let last = convo[convo.length - 1]
        if (!last || last.role !== 'assistant') {
          last = { role: 'assistant', text: '', ts: new Date().toISOString() }
          convo.push(last)
        }
        last.text += data.content || ''
        streamStatus.value = 'streaming'
        break
      }
      case 'tool_start': {
        toolStatus.value = `Using ${data.tool || 'tool'}...`
        streamStatus.value = 'tool'
        break
      }
      case 'tool_end': {
        toolStatus.value = ''
        break
      }
      case 'done': {
        streamStatus.value = 'ready'
        tokenStats.value = data.tokens || null
        break
      }
      case 'error': {
        streamStatus.value = 'error'
        convo.push({
          role: 'assistant',
          text: data.content || 'Error from server.',
          ts: new Date().toISOString()
        })
        break
      }
      default:
        break
    }
  }

  ws.onerror = () => {
    streamStatus.value = 'error'
    socketReady.value = false
    socketConnecting.value = false
  }

  ws.onclose = () => {
    socketReady.value = false
    socketConnecting.value = false
    streamStatus.value = 'disconnected'
  }
}

const sendMessage = async () => {
  if (!currentAgentId.value || !composer.value.trim()) return
  if (!socketReady.value || !socket.value) {
    agentError.value = 'Socket not ready. Reconnecting...'
    connectSocket()
    return
  }

  const agentId = currentAgentId.value
  const messageText = composer.value.trim()
  composer.value = ''

  const convo = currentConversation.value
  convo.push({ role: 'user', text: messageText, ts: new Date().toISOString() })
  status.value = 'sending'
  isSending.value = true

  try {
    socket.value.send(JSON.stringify({ message: messageText }))
    streamStatus.value = 'streaming'
  } catch (error) {
    console.error('Chat send failed', error)
    status.value = 'degraded'
    streamStatus.value = 'error'
    convo.push({
      role: 'assistant',
      text: 'Send failed. Check socket connection.',
      ts: new Date().toISOString()
    })
  } finally {
    isSending.value = false
  }
}

watch(
  () => route.params.agentId,
  () => setAgentFromRoute()
)

onMounted(() => {
  setAgentFromRoute()
  loadAgents()
})

onBeforeUnmount(() => {
  cleanupSocket()
})
</script>

<template>
  <div class="relative min-h-screen">
    <main class="relative z-10 mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-10 space-y-8">
      <header class="tui-surface rounded-xl border border-slate-200 p-6">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div class="space-y-2">
            <p class="text-xs uppercase tracking-[0.32em] text-slate-500">z.ai admin</p>
            <h1 class="text-3xl font-bold text-slate-900">Chat Tester</h1>
            <p class="text-sm text-slate-600">
              Select an agent, review prior messages, and start a new chat session. Mobile-friendly layout for testers.
            </p>
            <div class="flex flex-wrap items-center gap-2">
              <TuiBadge variant="info">ws /api/v1/ws/chat</TuiBadge>
      <TuiBadge variant="muted">base: dynamic (current host)</TuiBadge>
              <TuiBadge :variant="statusVariant(streamStatus)">state: {{ streamStatus }}</TuiBadge>
              <TuiBadge v-if="toolStatus" variant="warning">{{ toolStatus }}</TuiBadge>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <TuiButton size="sm" variant="outline" @click="startNewChat" :disabled="!currentAgentId">Start new chat</TuiButton>
            <TuiButton size="sm" variant="outline" @click="loadAgents">Refresh agents</TuiButton>
          </div>
        </div>
      </header>

      <section class="space-y-4">
        <div class="grid gap-4 sm:grid-cols-[1.4fr_1fr]">
          <TuiSelect
            label="Agent"
            hint="required"
            :options="agentOptions"
            v-model="currentAgentId"
            placeholder="Select agent"
            @update:modelValue="handleAgentChange"
          />
          <div class="flex flex-wrap gap-2">
            <TuiBadge v-if="currentAgent" :variant="statusVariant(currentAgent.status)" class="w-24 justify-center">
              {{ currentAgent.status || 'ready' }}
            </TuiBadge>
            <TuiBadge variant="muted">agents: {{ agents.length }}</TuiBadge>
            <TuiBadge v-if="tokenStats" variant="muted">
              tokens: {{ tokenStats.total || 0 }}
            </TuiBadge>
          </div>
        </div>
        <p v-if="agentError" class="text-xs text-slate-600">{{ agentError }}</p>
      </section>

      <section class="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div class="tui-surface rounded-xl border border-slate-200 p-4 sm:p-5">
          <header class="mb-3 flex items-center justify-between">
            <div>
              <p class="text-[11px] uppercase tracking-[0.2em] text-slate-500">conversation</p>
              <h2 class="text-xl font-semibold text-slate-900">{{ currentAgent?.name || 'Select an agent' }}</h2>
            </div>
            <TuiBadge v-if="currentAgent" variant="muted">{{ currentAgent.model }}</TuiBadge>
          </header>

            <div
              class="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-3 sm:p-4 max-h-[60vh] overflow-y-auto"
            >
              <p v-if="!currentAgentId" class="text-sm text-slate-600">Choose an agent to view chat history.</p>
              <div v-else>
                <div
                  v-for="(message, idx) in currentConversation"
                  :key="idx"
                  :class="[
                    'mb-3 flex',
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  ]"
                >
                  <div
                    :class="[
                      'max-w-full rounded-lg border px-3 py-2 text-sm sm:max-w-[75%]',
                      message.role === 'user'
                        ? 'border-slate-900 bg-slate-900 text-white'
                        : 'border-slate-200 bg-white text-slate-900'
                    ]"
                  >
                    <p class="text-[11px] uppercase tracking-[0.16em] text-slate-500" v-if="message.role === 'assistant'">
                      {{ currentAgent?.name || 'agent' }}
                    </p>
                    <p class="text-[11px] uppercase tracking-[0.16em] text-white/80" v-else>
                      you
                    </p>
                    <p class="whitespace-pre-wrap leading-relaxed">
                      {{ message.text }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div class="mt-4 space-y-3">
            <label class="flex flex-col gap-2 text-sm text-slate-800">
              <div class="flex items-center justify-between">
                <span class="text-[11px] uppercase tracking-[0.2em] text-slate-600">message</span>
                <span class="text-[11px] text-slate-500">agent: {{ currentAgent?.name || 'none' }}</span>
              </div>
              <div class="relative breathing-ring">
                <textarea
                  v-model="composer"
                  rows="3"
                  :disabled="!currentAgentId"
                  placeholder="Type a message to the agent. Press Send to dispatch."
                  class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-[inset_0_1px_1px_rgba(15,23,42,0.06)] focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200 disabled:cursor-not-allowed disabled:bg-slate-100"
                ></textarea>
              </div>
            </label>
            <div class="flex flex-wrap items-center gap-3">
              <TuiButton :loading="isSending" @click="sendMessage" :disabled="!currentAgentId">
                Send
              </TuiButton>
              <TuiButton variant="outline" @click="startNewChat" :disabled="!currentAgentId">New chat</TuiButton>
              <p class="text-xs text-slate-600">POST /chat/ with agent_id + message</p>
            </div>
          </div>
        </div>

        <div class="tui-surface rounded-xl border border-slate-200 p-4 sm:p-5 space-y-4">
          <div>
            <p class="text-[11px] uppercase tracking-[0.2em] text-slate-500">tester notes</p>
            <h3 class="text-lg font-semibold text-slate-900">Session Controls</h3>
            <ul class="mt-2 space-y-2 text-sm text-slate-700">
              <li>- Select an agent to auto-create a tester chat.</li>
              <li>- Start a new chat to reset conversation for that agent.</li>
              <li>- Mobile layout stacks controls for thumb reach.</li>
            </ul>
          </div>
          <div class="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700 space-y-1">
        <p><strong>Base URL</strong>: {window.location.origin}/api/v1</p>
            <p><strong>Send</strong>: POST /chat/</p>
            <p><strong>Agents</strong>: GET /agents/</p>
            <p><strong>Fallback</strong>: local messages if API is down.</p>
          </div>
        </div>
      </section>
    </main>
  </div>
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

.breathing-ring > textarea {
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

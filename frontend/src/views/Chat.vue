<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TuiBadge from '../components/ui/TuiBadge.vue'
import TuiButton from '../components/ui/TuiButton.vue'
import TuiSelect from '../components/ui/TuiSelect.vue'

const API_BASE = `${window.location.origin}/api/v1`

const route = useRoute()
const router = useRouter()

const agents = ref([])
const isLoadingAgents = ref(true)
const agentError = ref('')
const isSending = ref(false)
const composer = ref('')
const status = ref('idle')
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
}

const startNewChat = () => {
  if (!currentAgentId.value) return
  conversations[String(currentAgentId.value)] = []
  tokenStats.value = null
}

const sendMessage = async () => {
  if (!currentAgentId.value || !composer.value.trim()) return

  const agentId = currentAgentId.value
  const messageText = composer.value.trim()
  composer.value = ''

  const convo = currentConversation.value
  convo.push({ role: 'user', text: messageText, ts: new Date().toISOString() })
  status.value = 'sending'
  isSending.value = true
  agentError.value = ''

  try {
    const res = await fetch(`${API_BASE}/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        agent_id: parseInt(agentId),
        message: messageText
      })
    })

    if (!res.ok) {
      throw new Error(`API Error: ${res.statusText}`)
    }

    const data = await res.json()
    
    // Add assistant response to conversation
    convo.push({
      role: 'assistant',
      text: data.response || 'No response text.',
      ts: new Date().toISOString()
    })
    
    status.value = 'idle'
  } catch (error) {
    console.error('Chat send failed', error)
    status.value = 'degraded'
    agentError.value = error.message || 'Failed to send message'
    convo.push({
      role: 'assistant',
      text: 'Send failed. Please try again.',
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
</script>

<template>
  <div class="relative min-h-screen">
    <main class="relative z-10 mx-auto w-full max-w-5xl px-2 py-6 sm:px-4 lg:px-8 space-y-0">
      <header class="tui-surface border border-[var(--border)] px-6 py-5">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div class="space-y-2">
            <p class="text-xs uppercase tracking-[0.32em] text-[var(--muted)]">z.ai admin</p>
            <h1 class="text-3xl font-bold text-[var(--text)]">Chat Tester</h1>
            <p class="text-sm text-[var(--muted)]">
              Select an agent, review prior messages, and start a new chat session. Mobile-friendly layout for testers.
            </p>
            <div class="flex flex-wrap items-center gap-2">
              <TuiBadge variant="info">POST /api/v1/chat</TuiBadge>
              <TuiBadge variant="muted">base: dynamic (current host)</TuiBadge>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-2 text-xs text-[var(--muted)]">
            <TuiButton size="sm" variant="outline" @click="startNewChat" :disabled="!currentAgentId">Start new chat</TuiButton>
            <TuiButton size="sm" variant="outline" @click="loadAgents">Refresh agents</TuiButton>
          </div>
        </div>
      </header>

      <section class="border border-[var(--border)] px-6 py-5">
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
          </div>
        </div>
        <p v-if="agentError" class="mt-2 text-xs text-red-600">{{ agentError }}</p>
      </section>

      <section class="grid lg:grid-cols-[1.4fr_1fr]">
        <div class="tui-surface border border-[var(--border)] px-5 py-5">
          <header class="mb-3 flex items-center justify-between">
            <div>
              <p class="text-[11px] uppercase tracking-[0.2em] text-[var(--muted)]">conversation</p>
              <h2 class="text-xl font-semibold text-[var(--text)]">{{ currentAgent?.name || 'Select an agent' }}</h2>
            </div>
            <TuiBadge v-if="currentAgent" variant="muted">{{ currentAgent.model }}</TuiBadge>
          </header>

            <div
              class="flex flex-col gap-3 border border-[var(--border)] bg-white p-3 sm:p-4 max-h-[60vh] overflow-y-auto"
            >
              <p v-if="!currentAgentId" class="text-sm text-[var(--muted)]">Choose an agent to view chat history.</p>
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
                      'max-w-full border px-3 py-2 text-sm sm:max-w-[75%]',
                      message.role === 'user'
                        ? 'border-[#ff8200] bg-[var(--accent-soft)] text-[var(--text)]'
                        : 'border-[var(--border)] bg-white text-[var(--text)]'
                    ]"
                  >
                    <p class="text-[11px] uppercase tracking-[0.16em] text-[var(--muted)]" v-if="message.role === 'assistant'">
                      {{ currentAgent?.name || 'agent' }}
                    </p>
                    <p class="text-[11px] uppercase tracking-[0.16em] text-[var(--muted)]" v-else>
                      you
                    </p>
                    <p class="whitespace-pre-wrap leading-relaxed">
                      {{ message.text }}
                    </p>
                  </div>
                </div>
                <div v-if="isSending" class="flex justify-start">
                   <div class="max-w-full border border-[var(--border)] bg-white px-3 py-2 text-sm text-[var(--muted)] italic">
                      Thinking...
                   </div>
                </div>
              </div>
            </div>

            <div class="mt-4 space-y-3">
            <label class="flex flex-col gap-2 text-sm text-[var(--text)]">
              <div class="flex items-center justify-between">
                <span class="text-[11px] uppercase tracking-[0.2em] text-[var(--muted)]">message</span>
                <span class="text-[11px] text-[var(--muted)]">agent: {{ currentAgent?.name || 'none' }}</span>
              </div>
              <div class="relative breathing-ring">
                <textarea
                  v-model="composer"
                  rows="3"
                  :disabled="!currentAgentId || isSending"
                  placeholder="Type a message to the agent. Press Send to dispatch."
                  class="w-full rounded-none border border-[var(--border-strong)] bg-white px-3 py-2 text-sm text-[var(--text)] focus:border-[var(--text)] focus:outline-none focus:ring-2 focus:ring-[rgba(31,31,31,0.12)] disabled:cursor-not-allowed disabled:bg-[var(--bg)]"
                ></textarea>
              </div>
            </label>
            <div class="mt-3 flex flex-wrap items-center gap-2">
              <TuiButton size="md" :loading="isSending" @click="sendMessage" :disabled="!currentAgentId || isSending">
                Send
              </TuiButton>
              <TuiButton size="md" variant="outline" @click="startNewChat" :disabled="!currentAgentId">New chat</TuiButton>
              <p class="text-xs text-[var(--muted)]">POST /chat/ with agent_id + message</p>
            </div>
          </div>
        </div>

        <div class="tui-surface border border-[var(--border)] px-5 py-5 space-y-4">
          <div>
            <p class="text-[11px] uppercase tracking-[0.2em] text-[var(--muted)]">tester notes</p>
            <h3 class="text-lg font-semibold text-[var(--text)]">Session Controls</h3>
            <ul class="mt-2 space-y-2 text-sm text-[var(--muted)]">
              <li>- Select an agent to auto-create a tester chat.</li>
              <li>- Start a new chat to reset conversation for that agent.</li>
              <li>- Mobile layout stacks controls for thumb reach.</li>
            </ul>
          </div>
          <div class="border border-[var(--border)] bg-white p-3 text-xs text-[var(--text)] space-y-1">
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

<script setup>
import { onMounted, reactive, ref } from 'vue'
import TuiBadge from '../components/ui/TuiBadge.vue'
import TuiButton from '../components/ui/TuiButton.vue'
import TuiCard from '../components/ui/TuiCard.vue'
import TuiInput from '../components/ui/TuiInput.vue'
import TuiSelect from '../components/ui/TuiSelect.vue'

const API_BASE = `${window.location.origin}/api/v1`

const agents = ref([])
const mcpServers = ref([])
const isLoading = ref(true)
const mcpLoading = ref(true)
const isSaving = ref(false)
const isUploading = ref(false)
const deletingAgentId = ref(null)
const message = ref('')

const modelOptions = [
  { label: 'glm-4.5-flash', value: 'glm-4.5-flash' },
  { label: 'glm-4.6', value: 'glm-4.6' },
  { label: 'claude-3.5', value: 'claude-3.5' },
  { label: 'gpt-4o-mini', value: 'gpt-4o-mini' }
]

const form = reactive({
  id: null,
  name: '',
  model: 'glm-4.5-flash',
  system_prompt: '',
  linkedMcpId: ''
})

const statusVariant = (status) => {
  const normalized = (status || '').toLowerCase()
  if (normalized === 'live' || normalized === 'active' || normalized === 'ready') return 'success'
  if (normalized === 'watch' || normalized === 'syncing' || normalized === 'cooldown') return 'warning'
  return 'muted'
}

const formatTokens = (value) => {
  const num = Number(value)
  if (Number.isNaN(num)) return value || '—'
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`
  return `${num}`
}

const resetForm = (agent) => {
  form.id = agent?.id ?? null
  form.name = agent?.name ?? ''
  form.model = agent?.model ?? 'glm-4.5-flash'
  form.system_prompt = agent?.system_prompt ?? agent?.systemPrompt ?? ''
  form.linkedMcpId = agent?.linkedMcpId ?? agent?.linked_mcp_id ?? ''
}

const loadAgents = async () => {
  isLoading.value = true
  message.value = ''
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
          tokenCountToday: agent.tokenCountToday ?? agent.token_count_today ?? 0,
          linkedMcpId: agent.linkedMcpId ?? agent.linked_mcp_id ?? '',
          system_prompt: agent.system_prompt ?? ''
      }))
      : []
  } catch (error) {
    console.error('Failed to load agents', error)
    message.value = 'Failed to load agents from API.'
    agents.value = []
  } finally {
    isLoading.value = false
  }
}

const loadMcpServers = async () => {
  mcpLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/mcp/servers`)
    if (!res.ok) throw new Error('Failed to fetch mcp servers')
    const data = await res.json()
    mcpServers.value = Array.isArray(data)
      ? data.map((server, index) => ({
          id: server.id ?? index,
          name: server.name ?? 'server',
          status: (server.status ?? 'online').toLowerCase(),
          endpoint: server.endpoint ?? server.script ?? ''
      }))
      : []
  } catch (error) {
    console.error('Failed to load mcp servers', error)
    mcpServers.value = []
  } finally {
    mcpLoading.value = false
  }
}

const saveAgent = async () => {
  isSaving.value = true
  message.value = ''
  try {
    const method = form.id ? 'PUT' : 'POST'
    const url = form.id ? `${API_BASE}/agents/${form.id}` : `${API_BASE}/agents/`
    const payload = {
      name: form.name,
      model: form.model,
      system_prompt: form.system_prompt
    }

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (!res.ok) throw new Error('Failed to save agent')
    message.value = form.id ? 'Agent updated' : 'Agent created'
    await loadAgents()
    if (!form.id) resetForm()
  } catch (error) {
    console.error('Save agent failed', error)
    message.value = 'Save failed. Check API connectivity.'
  } finally {
    isSaving.value = false
  }
}

const deleteAgent = async (agentId) => {
  if (!agentId) return
  const confirmDelete = window.confirm('Delete this agent? This action cannot be undone.')
  if (!confirmDelete) return

  deletingAgentId.value = agentId
  message.value = ''
  try {
    const res = await fetch(`${API_BASE}/agents/${agentId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to delete agent')
    message.value = 'Agent deleted.'
    await loadAgents()
    if (form.id === agentId) resetForm()
  } catch (error) {
    console.error('Delete agent failed', error)
    message.value = 'Delete failed. Confirm backend DELETE /agents/{id} is available.'
  } finally {
    deletingAgentId.value = null
  }
}

const linkMcp = async () => {
  if (!form.id || !form.linkedMcpId) {
    message.value = 'Select an agent and MCP to link.'
    return
  }

  try {
    const res = await fetch(`${API_BASE}/agents/${form.id}/link-mcp/${form.linkedMcpId}`, {
      method: 'POST'
    })
    if (!res.ok) throw new Error('Failed to link MCP')
    message.value = 'MCP linked to agent.'
    await loadAgents()
  } catch (error) {
    console.error('Link MCP failed', error)
    message.value = 'Link failed. Confirm backend endpoint.'
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file || !form.id) {
    message.value = 'Select an agent before uploading.'
    event.target.value = ''
    return
  }

  isUploading.value = true
  message.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API_BASE}/agents/${form.id}/knowledge`, {
      method: 'POST',
      body: formData
    })
    if (!res.ok) throw new Error('Failed to upload file')
    message.value = 'File uploaded to agent knowledge.'
  } catch (error) {
    console.error('Upload failed', error)
    message.value = 'Upload failed. Verify backend handler.'
  } finally {
    isUploading.value = false
    event.target.value = ''
  }
}

const selectAgent = (agent) => {
  resetForm(agent)
}

onMounted(() => {
  loadAgents()
  loadMcpServers()
})
</script>

<template>
  <div class="relative min-h-screen">
    <main class="relative z-10 mx-auto w-full max-w-none px-5 lg:px-10 py-10 space-y-8">
      <header class="tui-surface rounded-xl border border-slate-200 p-6">
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div class="space-y-2">
            <p class="text-xs uppercase tracking-[0.32em] text-slate-500">z.ai admin</p>
            <h1 class="text-3xl font-bold text-slate-900">Agent Management</h1>
            <p class="text-sm text-slate-600">
              Create, edit, and link RAG agents to MCP servers. Attach files to extend knowledge.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <TuiBadge variant="info">/api/v1</TuiBadge>
            <TuiBadge variant="muted">base: dynamic (current host)</TuiBadge>
          </div>
        </div>
      </header>

      <section class="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <TuiCard title="Agents" subtitle="list">
          <div class="mb-4 flex items-center justify-between gap-3 text-xs text-slate-600">
            <span v-if="message">{{ message }}</span>
            <TuiButton size="sm" variant="outline" @click="loadAgents">refresh</TuiButton>
          </div>
          <div v-if="isLoading" class="text-sm text-slate-600">Loading agents...</div>
          <div v-else class="divide-y divide-slate-200">
            <div
              v-for="agent in agents"
              :key="agent.id"
              class="grid gap-3 py-4 sm:grid-cols-[auto_1fr_1fr_130px_auto] sm:items-center"
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
              <div class="flex flex-col gap-1 text-sm text-slate-700">
                <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500">tokens today</p>
                <p class="font-semibold tabular-nums">{{ formatTokens(agent.tokenCountToday) }}</p>
              </div>
              <div class="flex flex-col gap-1 text-sm text-slate-700">
                <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500">last active</p>
                <p class="font-semibold tabular-nums">{{ agent.lastActive || '—' }}</p>
              </div>
              <div class="flex items-center">
                <TuiBadge :variant="statusVariant(agent.status)" class="w-24 justify-center">
                  {{ agent.status || 'ready' }}
                </TuiBadge>
              </div>
              <div class="flex flex-wrap items-center justify-start gap-2 text-xs text-slate-700 sm:justify-end">
                <TuiButton size="sm" variant="outline" @click="selectAgent(agent)">edit</TuiButton>
                <router-link :to="`/chat/${agent.id}`">
                  <TuiButton size="sm" variant="ghost">tester</TuiButton>
                </router-link>
                <TuiButton
                  size="sm"
                  variant="ghost"
                  class="text-red-600"
                  :loading="deletingAgentId === agent.id"
                  @click="deleteAgent(agent.id)"
                >
                  delete
                </TuiButton>
                <TuiBadge variant="muted">mcp: {{ agent.linkedMcpId || 'none' }}</TuiBadge>
              </div>
            </div>
            <div v-if="!agents.length" class="py-6 text-sm text-slate-600">
              No agents yet. Create one using the form.
            </div>
          </div>
        </TuiCard>

        <TuiCard title="Agent Form" subtitle="create / edit">
          <div class="space-y-4">
            <TuiInput label="Agent Name" placeholder="Atlas" v-model="form.name" />
            <TuiSelect label="Model" :options="modelOptions" v-model="form.model" placeholder="Select model" />
            <label class="flex flex-col gap-2 text-sm text-slate-800">
              <div class="flex items-center justify-between">
                <span class="text-[11px] uppercase tracking-[0.2em] text-slate-600">Instruction</span>
                <span class="text-[11px] text-slate-500">system_prompt</span>
              </div>
              <div class="relative breathing-ring">
                <textarea
                  v-model="form.system_prompt"
                  rows="4"
                  placeholder="Set concise operating instructions for the agent."
                  class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-[inset_0_1px_1px_rgba(15,23,42,0.06)] focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200"
                ></textarea>
              </div>
            </label>
            <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
              <TuiSelect
                label="Linked MCP Server"
                :options="mcpServers.map((server) => ({ label: server.name, value: server.id }))"
                v-model="form.linkedMcpId"
                placeholder="Select MCP"
                :hint="mcpLoading ? 'loading...' : 'optional'"
              />
              <div class="flex items-end">
                <TuiButton class="w-full" variant="outline" :loading="false" @click="linkMcp">link mcp</TuiButton>
              </div>
            </div>
            <div class="space-y-2">
              <p class="text-[11px] uppercase tracking-[0.2em] text-slate-600">Attach File</p>
              <input
                type="file"
                class="w-full rounded-md border border-dashed border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
                :disabled="!form.id || isUploading"
                @change="handleFileUpload"
              />
              <p class="text-xs text-slate-600">
                {{ form.id ? 'Uploads will POST to /agents/{id}/knowledge' : 'Save the agent before uploading.' }}
              </p>
            </div>
            <div class="flex flex-wrap gap-3">
              <TuiButton :loading="isSaving" @click="saveAgent">
                {{ form.id ? 'Save changes' : 'Create agent' }}
              </TuiButton>
              <TuiButton variant="outline" @click="resetForm()">Reset</TuiButton>
            </div>
          </div>
        </TuiCard>
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

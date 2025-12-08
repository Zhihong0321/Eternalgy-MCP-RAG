<script setup>
const agents = [
  {
    name: 'Atlas',
    model: 'gpt-4o-mini',
    status: 'Ready',
    tokens: '2.1M',
    latency: '210ms',
    load: 32
  },
  {
    name: 'Vesper',
    model: 'claude-3.5',
    status: 'Live',
    tokens: '1.4M',
    latency: '180ms',
    load: 48
  },
  {
    name: 'Neon',
    model: 'sonnet-3.1',
    status: 'Cooling',
    tokens: '950K',
    latency: '260ms',
    load: 21
  }
]

const mcpServers = [
  { name: 'repo-tools', status: 'Online', tools: 'fs.read, grep, write', env: 'local', usage: 58 },
  { name: 'vector-search', status: 'Syncing', tools: 'search, embed', env: 'cloud', usage: 24 },
  { name: 'analytics', status: 'Online', tools: 'metrics, chart', env: 'local', usage: 41 }
]

const testerSessions = [
  { id: '#42A', agent: 'Atlas', user: 'qa-bot', state: 'Live', tokens: 12, updated: '14s' },
  { id: '#357', agent: 'Vesper', user: 'ops', state: 'Listening', tokens: 7, updated: '38s' },
  { id: '#221', agent: 'Neon', user: 'lab', state: 'Idle', tokens: 0, updated: '2m' }
]

const activityLog = [
  { time: '14:12:09', text: 'Atlas issued mcp.call -> repo-tools:grep' },
  { time: '14:11:44', text: 'Vesper system prompt updated (safety bump)' },
  { time: '14:10:32', text: 'Neon streamed 12 tokens (reasoning log open)' },
  { time: '14:09:51', text: 'MCP analytics heartbeat received (92ms)' }
]
</script>

<template>
  <div class="relative min-h-screen">
    <main class="relative z-10 mx-auto w-full max-w-none px-5 lg:px-10 py-10 space-y-8">
      <header class="tui-surface rounded-xl border border-slate-200 p-6">
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div class="space-y-2">
            <p class="text-xs uppercase tracking-[0.32em] text-slate-500">z.ai console</p>
            <h1 class="text-3xl font-bold text-slate-900">Light TUI Admin</h1>
            <p class="text-sm text-slate-600">
              Minimal, modern surface for agents, MCP, and tester sessions.
            </p>
          </div>
          <div class="flex items-center gap-3">
            <router-link
              to="/components"
              class="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-700 transition hover:bg-slate-50"
            >
              component library
            </router-link>
            <span class="tui-surface rounded-md border border-slate-300 px-3 py-2 text-xs uppercase tracking-widest text-slate-800">
              build / v0.2
            </span>
            <span class="flex items-center gap-2 rounded-md border border-slate-900 bg-slate-900 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-white">
              <span class="h-2 w-2 rounded-full bg-white"></span>
              systems nominal
            </span>
          </div>
        </div>
      </header>

      <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div class="tui-surface rounded-lg border border-slate-200 px-4 py-3">
          <p class="text-xs uppercase tracking-[0.26em] text-slate-500">agents online</p>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-3xl font-bold text-slate-900">03</span>
            <span class="text-sm text-slate-600">ready</span>
          </div>
          <div class="mt-2 h-[1px] w-full bg-gradient-to-r from-slate-900/80 via-slate-400 to-transparent"></div>
        </div>
        <div class="tui-surface rounded-lg border border-slate-200 px-4 py-3">
          <p class="text-xs uppercase tracking-[0.26em] text-slate-500">mcp nodes</p>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-3xl font-bold text-slate-900">03</span>
            <span class="text-sm text-slate-600">linked</span>
          </div>
          <div class="mt-2 h-[1px] w-full bg-gradient-to-r from-slate-900/80 via-slate-400 to-transparent"></div>
        </div>
        <div class="tui-surface rounded-lg border border-slate-200 px-4 py-3">
          <p class="text-xs uppercase tracking-[0.26em] text-slate-500">latency</p>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-3xl font-bold text-slate-900">184</span>
            <span class="text-sm text-slate-600">ms median</span>
          </div>
          <div class="mt-2 flex items-center gap-2 text-xs text-slate-800">
            <span class="h-1.5 w-1.5 rounded-full bg-slate-900"></span>
            stable
          </div>
        </div>
        <div class="tui-surface rounded-lg border border-slate-200 px-4 py-3">
          <p class="text-xs uppercase tracking-[0.26em] text-slate-500">uptime</p>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-3xl font-bold text-slate-900">99.9%</span>
            <span class="text-sm text-slate-600">/ 24h</span>
          </div>
          <div class="mt-2 h-[1px] w-full bg-gradient-to-r from-slate-900/80 via-slate-400 to-transparent"></div>
        </div>
      </section>

      <section class="grid gap-6 lg:grid-cols-3">
        <div class="space-y-6 lg:col-span-2">
          <div class="tui-surface rounded-xl border border-slate-200 p-5">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="text-xs uppercase tracking-[0.24em] text-slate-500">agents</p>
                <h2 class="text-xl font-semibold text-slate-900">Control Plane</h2>
              </div>
              <div class="flex items-center gap-2 text-xs text-slate-700">
                <span class="h-2 w-2 rounded-full bg-slate-900"></span> autoscaler idle
              </div>
            </div>
            <div class="mt-4 divide-y divide-slate-200">
              <div
                v-for="agent in agents"
                :key="agent.name"
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
                    <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500">tokens</p>
                    <p class="font-semibold">{{ agent.tokens }}</p>
                  </div>
                  <div>
                    <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500">latency</p>
                    <p class="font-semibold">{{ agent.latency }}</p>
                  </div>
                  <div class="flex items-center gap-2">
                    <span
                      :class="[
                        'inline-flex items-center rounded px-2 py-1 text-[11px] font-semibold uppercase tracking-wide',
                        agent.status === 'Ready'
                          ? 'border border-slate-900 bg-slate-900 text-white'
                          : agent.status === 'Live'
                            ? 'border border-slate-700 bg-slate-800 text-slate-100'
                            : 'border border-slate-400 bg-slate-100 text-slate-800'
                      ]"
                    >
                      <span class="mr-2 h-1.5 w-1.5 rounded-full bg-current"></span>
                      {{ agent.status }}
                    </span>
                  </div>
                </div>
                <div class="w-full sm:w-48">
                  <div class="flex items-center justify-between text-[11px] uppercase tracking-[0.18em] text-slate-500">
                    <span>load</span>
                    <span>{{ agent.load }}%</span>
                  </div>
                  <div class="mt-2 h-2 w-full overflow-hidden rounded-full border border-slate-200 bg-white">
                    <div
                      class="h-full bg-gradient-to-r from-slate-900 to-slate-500"
                      :style="{ width: `${agent.load}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="tui-surface rounded-xl border border-slate-200 p-5">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="text-xs uppercase tracking-[0.24em] text-slate-500">tester chat</p>
                <h2 class="text-xl font-semibold text-slate-900">Live Stream</h2>
              </div>
              <div class="flex items-center gap-2 text-xs text-slate-700">
                <span class="h-2 w-2 rounded-full bg-slate-900"></span> streaming enabled
              </div>
            </div>
            <div class="mt-4 grid gap-4 md:grid-cols-3">
              <div
                v-for="session in testerSessions"
                :key="session.id"
                class="tui-surface rounded-lg border border-slate-200 px-4 py-3"
              >
                <div class="flex items-center justify-between text-[11px] uppercase tracking-[0.2em] text-slate-500">
                  <span>{{ session.id }}</span>
                  <span>{{ session.state }}</span>
                </div>
                <p class="mt-2 text-base font-semibold text-slate-900">{{ session.agent }}</p>
                <p class="text-sm text-slate-600">user: {{ session.user }}</p>
                <div class="mt-3 flex items-center justify-between text-xs text-slate-600">
                  <span>{{ session.tokens }} messages</span>
                  <span>{{ session.updated }} ago</span>
                </div>
              </div>
            </div>
            <div class="mt-5 grid gap-4 md:grid-cols-2">
              <div class="tui-surface rounded-lg border border-slate-200 p-4">
                <p class="text-xs uppercase tracking-[0.2em] text-slate-500">chat surface</p>
                <div class="mt-3 space-y-2 text-sm text-slate-800">
                  <p>> user: run quick audit on repo-tools</p>
                  <p>> atlas: scanning mcp registry...</p>
                  <p>> atlas: found 3 scripts, ready to execute.</p>
                  <p class="font-semibold text-slate-900">> streaming: awaiting confirmation _</p>
                </div>
              </div>
              <div class="tui-surface rounded-lg border border-slate-200 p-4">
                <p class="text-xs uppercase tracking-[0.2em] text-slate-500">reasoning log</p>
                <div class="mt-3 space-y-2 text-sm text-slate-800">
                  <p>[14:12:07] load agent atlas profile</p>
                  <p>[14:12:09] compose mcp.call(repo-tools:grep)</p>
                  <p>[14:12:10] stream delta tokens (12)</p>
                  <p class="font-semibold text-slate-900">[14:12:11] awaiting tool ack _</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="tui-surface rounded-xl border border-slate-200 p-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs uppercase tracking-[0.24em] text-slate-500">mcp nodes</p>
                <h2 class="text-xl font-semibold text-slate-900">Tooling Mesh</h2>
              </div>
              <span class="rounded-md border border-slate-300 px-2 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-600">
                sync loop: 30s
              </span>
            </div>
            <div class="mt-4 space-y-4">
              <div
                v-for="server in mcpServers"
                :key="server.name"
                class="rounded-lg border border-slate-200 p-4"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-base font-semibold text-slate-900">{{ server.name }}</p>
                    <p class="text-sm text-slate-600">{{ server.tools }}</p>
                  </div>
                  <span
                    :class="[
                      'rounded-md border px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]',
                      server.status === 'Online'
                        ? 'border-slate-900 bg-slate-900 text-white'
                        : 'border-slate-500 bg-slate-100 text-slate-800'
                    ]"
                  >
                    {{ server.status }}
                  </span>
                </div>
                <div class="mt-3 flex items-center justify-between text-xs text-slate-600">
                  <span>env: {{ server.env }}</span>
                  <span>usage: {{ server.usage }}%</span>
                </div>
                <div class="mt-2 h-2 w-full overflow-hidden rounded-full border border-slate-200 bg-white">
                  <div
                    class="h-full bg-gradient-to-r from-slate-900 to-slate-500"
                    :style="{ width: `${server.usage}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div class="tui-surface rounded-xl border border-slate-200 p-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs uppercase tracking-[0.24em] text-slate-500">timeline</p>
                <h2 class="text-xl font-semibold text-slate-900">Activity Log</h2>
              </div>
              <span class="text-xs uppercase tracking-[0.2em] text-slate-600">last 5m</span>
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="entry in activityLog"
                :key="entry.text"
                class="flex items-start gap-3 rounded-lg border border-slate-200 px-3 py-2"
              >
                <span class="mt-0.5 text-xs font-semibold text-slate-500">{{ entry.time }}</span>
                <p class="text-sm text-slate-800">{{ entry.text }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

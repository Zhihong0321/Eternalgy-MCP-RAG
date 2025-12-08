# Frontend Build Plan

## Scope & Assumptions
- UI only; no backend changes. API calls consume existing `/api/v1` endpoints.
- App launches at `/` to the Admin Dashboard (home).
- Core sections: Admin Dashboard, Agent Management, MCP Management, Thread Management.

## Routes & Layout
1) `/` Admin Dashboard (default).  
2) `/agents` Agent Management (list + detail/edit).  
3) `/mcps` MCP Management (list + detail).  
4) `/threads` Thread Management (list + detail).

Shared layout: top nav with section links + global status; responsive grid with TUI theme.

## Data Needs (frontend contract)
- Agents: id, name, instruction, status, lastActive, tokenCountToday, linkedMcpId, files[].  
- MCP servers: id, name, status, endpoint, capabilities.  
- Threads: id, agentId, title/preview, lastActive, tokensUsed, status; need last 10 active for dashboard.  
- Stats: agent status summary, token totals today.

## Dashboard (Home)
- Hero: RAG Agent overview + “Create Agent” CTA.
- Widgets:
  - Last 10 active threads (title, agent, last active, tokens).
  - Agent status summary (per agent: lastActive, tokenCountToday; quick state badge).
  - High-level metrics (total agents, total MCPs, active threads).
  - API hint: surface `/api/v1` base for discoverability.

## Agent Management
- List: searchable/sortable table (name, linked MCP, status, lastActive, tokenCountToday).
- Detail/Edit:
  - Fields: name, instruction (textarea), linked MCP select, file attachments list (mock actions for now), status badge.
  - Actions: save/update, attach file (UI stub), remove attachment.
- “Create Agent” flow can reuse detail form with empty defaults.

## MCP Management
- List: MCP servers with status, endpoint, capabilities.
- Detail: server info + linked agents; controls to refresh status (UI action).

## Thread Management
- List: threads with agent, lastActive, tokensUsed, status; filter by agent/status.
- Detail: show messages/log preview (mock data), thread metadata, actions (archive/end thread UI).

## Components to Build
- Badges for statuses (ready/online/syncing/cooldown/etc.) with fixed width where needed.
- Cards for dashboard widgets; tables/lists for entities.
- Forms: Agent form (name, instruction, MCP select, file list).
- Thread list item component (compact view for dashboard widget).
- Layout components: Nav, PageShell, Section headers.

## API Integration Stubs
- `/api/v1/agents` (list/create/update), `/api/v1/agents/:id/files` (attach/remove).
- `/api/v1/mcps` (list/detail).
- `/api/v1/threads` (list, filter recent/active).
- Keep services modular so real fetch wiring can replace mocks.

## Phased Implementation
1) Routing/layout shell with nav + top-level pages.  
2) Dashboard widgets with mock data (last 10 threads, agent status summary, metrics).  
3) Agent list + detail form (instruction, linked MCP, files UI).  
4) MCP list/detail views.  
5) Thread list/detail views.  
6) Replace mocks with API service layer and wire to `/api/v1`.  
7) Polish: responsiveness, empty/loading states, accessibility pass.

## Testing & Validation
- Component-level checks: forms render, lists handle empty/loading.
- View smoke tests via manual run `npm run dev` / `npm run build` in `frontend`.

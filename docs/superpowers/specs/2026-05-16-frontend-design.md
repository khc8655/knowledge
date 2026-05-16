# Frontend Design Spec — KB Platform v7.5

> **Date:** 2026-05-16
> **Tech Stack:** React 18 + Vite + TypeScript + TailwindCSS + shadcn/ui
> **Design System:** 知识库检索工作台（Stitch project 16421899919665521312）
> **State Management:** Zustand
> **Routing:** React Router v6

---

## 1. Design System Tokens

From Stitch design system "知识库检索工作台设计系统":

**Colors:**
- Primary: `#0052cc` / `#003d9b`
- Success: `#36B37E`
- Warning: `#FFAB00`
- Error: `#FF5630`
- Processing: `#0052CC`
- Background: `#faf8ff`
- Surface: `#ffffff` (cards), `#f3f3fd` (container-low), `#ededf8` (container)
- Text: `#191b23` (primary), `#434654` (secondary), `#737685` (outline)
- Hit Rate: green (>=0.85), blue (0.65-0.84), amber (0.5-0.64)
- Report: purple `#6554C0`, teal `#00B8D9`

**Typography:**
- Headings: Manrope (h1: 24px/600, h2: 18px/600)
- Body: Inter (14px/400), Small (13px/400)
- Meta: Inter (12px/400)
- Code: JetBrains Mono (13px/400)

**Spacing:**
- Sidebar width: 240px (collapsed: 64px)
- Top bar height: 56px
- Container padding: 24px
- Element gap: 16px
- Stack tight: 8px

**Roundness:** 8px default, pill for buttons

---

## 2. Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── router.tsx          # React Router config
│   │   └── layout.tsx          # AppShell with Sidebar + TopBar
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── layout/             # Sidebar, TopBar
│   │   ├── search/             # SearchInput, ResultCard, SourcePill
│   │   ├── upload/             # Dropzone, UploadQueue, JobProgress
│   │   ├── cards/              # CardList, CardDetail, CardFilters
│   │   ├── presales/           # ProjectCard, EvidencePanel, OutputReview
│   │   └── shared/             # StatusBadge, EmptyState, ErrorState
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Search.tsx
│   │   ├── Upload.tsx
│   │   ├── Cards.tsx
│   │   ├── Settings.tsx
│   │   ├── Indexes.tsx
│   │   ├── Workspace.tsx
│   │   ├── ProposalView.tsx
│   │   ├── TenderView.tsx
│   │   ├── BomView.tsx
│   │   ├── ReplyView.tsx
│   │   ├── Templates.tsx
│   │   └── OutputReview.tsx
│   ├── hooks/                  # Custom hooks
│   ├── lib/
│   │   ├── api.ts              # Backend API client
│   │   └── utils.ts            # Utility functions
│   ├── stores/                 # Zustand stores
│   └── styles/
│       └── globals.css         # Tailwind directives + design tokens
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── components.json             # shadcn/ui config
└── package.json
```

---

## 3. Pages

| Page | Route | Priority | Stitch Design |
|------|-------|----------|---------------|
| Dashboard | `/` | P0 | Yes |
| Search | `/search` | P0 | Yes |
| Upload | `/upload` | P0 | Yes |
| Cards | `/cards` | P1 | Yes |
| Indexes | `/indexes` | P1 | Yes |
| Settings | `/settings` | P2 | Yes |
| Workspace | `/workspace` | P1 | New |
| Proposal Detail | `/proposals/:id` | P1 | New |
| Tender Matching | `/tender` | P1 | New |
| BOM Config | `/bom` | P1 | New |
| Customer Reply | `/reply` | P1 | New |
| Templates | `/templates` | P2 | New |
| Output Review | `/outputs/:id/review` | P2 | New |

---

## 4. API Integration

All API calls go to `/api/v1/` prefix. Vite dev server proxies to backend.

Key endpoints:
- `POST /query` — Search
- `GET /health` — System health
- `POST /upload` — File upload
- `GET/POST /cards` — Card CRUD
- `POST /evidence/build` — Evidence pack
- `POST /proposals/generate` — Proposal generation
- `POST /tender/match` — Tender matching
- `POST /bom/generate` — BOM generation
- `POST /reply/generate` — Customer reply
- `GET/POST /templates` — Template CRUD
- `POST /outputs/{id}/review` — Output review
- `POST /exports/{id}` — Export

---

## 5. Implementation Phases

**Phase 1: Foundation + Search**
- Project scaffold (Vite + React + Tailwind + shadcn/ui)
- Design tokens and theme configuration
- AppShell layout (Sidebar + TopBar)
- Search page (core page)
- API client

**Phase 2: Knowledge Management**
- Dashboard
- Upload page with drag-and-drop
- Card management
- Index management
- Settings

**Phase 3: Pre-sales Workbench**
- Workspace (project list)
- Proposal view
- Tender matching
- BOM configuration
- Customer reply
- Template management
- Output review

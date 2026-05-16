# Frontend Phase 1: Foundation + Search Page

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the React frontend with Vite, TailwindCSS, shadcn/ui, configure design tokens from the Stitch design system, build the AppShell layout (Sidebar + TopBar), API client, and the Search page.

**Architecture:** Single-page app with React Router v6 for routing, Zustand for state, shadcn/ui for components, TailwindCSS for styling. The backend API is at `/api/v1/` and the Vite dev server proxies to it.

**Tech Stack:** React 18, Vite 6, TypeScript, TailwindCSS 4, shadcn/ui, Zustand, React Router v6, Lucide icons

---

## File Structure

**New files:**
- `frontend/package.json` — Dependencies and scripts
- `frontend/vite.config.ts` — Vite config with API proxy
- `frontend/tsconfig.json` — TypeScript config
- `frontend/tailwind.config.ts` — Tailwind with design tokens
- `frontend/postcss.config.js` — PostCSS for Tailwind
- `frontend/components.json` — shadcn/ui config
- `frontend/index.html` — Entry HTML
- `frontend/src/main.tsx` — React entry point
- `frontend/src/app.tsx` — App with Router
- `frontend/src/globals.css` — Tailwind directives + custom CSS vars
- `frontend/src/lib/api.ts` — Backend API client
- `frontend/src/lib/utils.ts` — cn() helper
- `frontend/src/stores/app.ts` — Global app store (health, sidebar state)
- `frontend/src/components/layout/sidebar.tsx` — Left sidebar navigation
- `frontend/src/components/layout/topbar.tsx` — Top bar with system status
- `frontend/src/components/layout/app-shell.tsx` — Main layout wrapper
- `frontend/src/components/search/search-input.tsx` — Search input component
- `frontend/src/components/search/result-card.tsx` — Search result card
- `frontend/src/components/search/source-pill.tsx` — Source type badge
- `frontend/src/components/shared/status-badge.tsx` — Status indicator
- `frontend/src/components/shared/empty-state.tsx` — Empty state placeholder
- `frontend/src/pages/search.tsx` — Search page
- `frontend/src/pages/dashboard.tsx` — Dashboard placeholder

---

### Task 1: Project Scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/components.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/globals.css`
- Create: `frontend/src/lib/utils.ts`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "kb-platform-frontend",
  "private": true,
  "version": "7.5.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint ."
  },
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0",
    "react-router-dom": "^7.6.1",
    "@radix-ui/react-slot": "^1.2.3",
    "@radix-ui/react-dialog": "^1.1.14",
    "@radix-ui/react-dropdown-menu": "^2.1.15",
    "@radix-ui/react-tabs": "^1.1.12",
    "@radix-ui/react-toast": "^1.2.14",
    "@radix-ui/react-tooltip": "^1.2.7",
    "@radix-ui/react-select": "^2.1.14",
    "@radix-ui/react-separator": "^1.1.7",
    "@radix-ui/react-progress": "^1.1.7",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.3.1",
    "lucide-react": "^0.511.0",
    "zustand": "^5.0.5"
  },
  "devDependencies": {
    "@types/react": "^19.1.4",
    "@types/react-dom": "^19.1.5",
    "@vitejs/plugin-react": "^4.6.0",
    "autoprefixer": "^10.4.21",
    "postcss": "^8.5.4",
    "tailwindcss": "^4.1.7",
    "@tailwindcss/vite": "^4.1.7",
    "typescript": "^5.8.3",
    "vite": "^6.3.5"
  }
}
```

- [ ] **Step 2: Create vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: Create tsconfig files**

`tsconfig.json`:
```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

`tsconfig.app.json`:
```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true,
    "paths": {
      "@/*": ["./src/*"]
    },
    "baseUrl": "."
  },
  "include": ["src"]
}
```

`tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Create tailwind.config.ts**

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0052cc',
          foreground: '#ffffff',
          50: '#e6f0ff',
          100: '#b3d1ff',
          200: '#80b3ff',
          300: '#4d94ff',
          400: '#1a75ff',
          500: '#0052cc',
          600: '#003d9b',
          700: '#002d73',
          800: '#001e4d',
          900: '#000f26',
        },
        success: '#36B37E',
        warning: '#FFAB00',
        destructive: '#FF5630',
        processing: '#0052CC',
        background: '#faf8ff',
        surface: {
          DEFAULT: '#ffffff',
          dim: '#d9d9e4',
          container: {
            lowest: '#ffffff',
            low: '#f3f3fd',
            DEFAULT: '#ededf8',
            high: '#e7e7f2',
            highest: '#e1e2ec',
          },
        },
        muted: {
          DEFAULT: '#f3f3fd',
          foreground: '#434654',
        },
        accent: {
          DEFAULT: '#f3f3fd',
          foreground: '#191b23',
        },
        border: '#c3c6d6',
        input: '#c3c6d6',
        ring: '#0052cc',
        foreground: '#191b23',
        'hit-high': '#36B37E',
        'hit-medium': '#0052CC',
        'hit-low': '#FFAB00',
        'report-purple': '#6554C0',
        'report-teal': '#00B8D9',
      },
      borderRadius: {
        lg: '0.75rem',
        md: '0.5rem',
        sm: '0.25rem',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Manrope', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'h1': ['24px', { lineHeight: '32px', fontWeight: '600' }],
        'h2': ['18px', { lineHeight: '24px', fontWeight: '600' }],
        'body': ['14px', { lineHeight: '20px' }],
        'body-small': ['13px', { lineHeight: '18px' }],
        'meta': ['12px', { lineHeight: '16px' }],
      },
      spacing: {
        'sidebar': '240px',
        'sidebar-collapsed': '64px',
        'topbar': '56px',
      },
    },
  },
  plugins: [],
}

export default config
```

- [ ] **Step 5: Create postcss.config.js**

```javascript
export default {
  plugins: {
    autoprefixer: {},
  },
}
```

- [ ] **Step 6: Create components.json (shadcn/ui config)**

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/globals.css",
    "baseColor": "blue",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
```

- [ ] **Step 7: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
    <title>知识库平台</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 8: Create globals.css**

```css
@import "tailwindcss";

@custom-variant dark (&:is(.dark *));

:root {
  --background: oklch(0.98 0.005 280);
  --foreground: oklch(0.15 0.01 280);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.15 0.01 280);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.15 0.01 280);
  --primary: oklch(0.45 0.15 260);
  --primary-foreground: oklch(1 0 0);
  --secondary: oklch(0.95 0.01 280);
  --secondary-foreground: oklch(0.25 0.01 280);
  --muted: oklch(0.95 0.01 280);
  --muted-foreground: oklch(0.45 0.01 280);
  --accent: oklch(0.95 0.01 280);
  --accent-foreground: oklch(0.25 0.01 280);
  --destructive: oklch(0.55 0.2 25);
  --destructive-foreground: oklch(1 0 0);
  --border: oklch(0.85 0.01 280);
  --input: oklch(0.85 0.01 280);
  --ring: oklch(0.45 0.15 260);
  --radius: 0.75rem;
  --success: oklch(0.65 0.15 150);
  --warning: oklch(0.75 0.15 85);
  --processing: oklch(0.45 0.15 260);
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground font-sans antialiased;
  }
  h1, h2, h3, h4 {
    font-family: 'Manrope', system-ui, sans-serif;
  }
}
```

- [ ] **Step 9: Create src/lib/utils.ts**

```typescript
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 10: Create src/main.tsx**

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './globals.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <div>KB Platform Loading...</div>
  </StrictMode>,
)
```

- [ ] **Step 11: Install dependencies and verify**

Run: `cd /home/jjb/kb-platform/frontend && npm install`
Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Run: `cd /home/jjb/kb-platform/frontend && npx vite build`
Expected: Build succeeds

- [ ] **Step 12: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/ && git commit -m "feat: scaffold frontend with Vite, React, TailwindCSS, and shadcn/ui config"
```

---

### Task 2: shadcn/ui Base Components

**Files:**
- Create: `frontend/src/components/ui/button.tsx`
- Create: `frontend/src/components/ui/card.tsx`
- Create: `frontend/src/components/ui/badge.tsx`
- Create: `frontend/src/components/ui/input.tsx`
- Create: `frontend/src/components/ui/separator.tsx`
- Create: `frontend/src/components/ui/tooltip.tsx`
- Create: `frontend/src/components/ui/progress.tsx`
- Create: `frontend/src/components/ui/tabs.tsx`
- Create: `frontend/src/components/ui/dropdown-menu.tsx`
- Create: `frontend/src/components/ui/dialog.tsx`
- Create: `frontend/src/components/ui/toast.tsx`

- [ ] **Step 1: Create button.tsx**

```typescript
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 cursor-pointer",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

- [ ] **Step 2: Create card.tsx**

```typescript
import * as React from "react"
import { cn } from "@/lib/utils"

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-lg border bg-card text-card-foreground shadow-sm", className)} {...props} />
  )
)
Card.displayName = "Card"

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />
  )
)
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("font-heading text-2xl font-semibold leading-none tracking-tight", className)} {...props} />
  )
)
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("text-sm text-muted-foreground", className)} {...props} />
  )
)
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
  )
)
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center p-6 pt-0", className)} {...props} />
  )
)
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
```

- [ ] **Step 3: Create badge.tsx**

```typescript
import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground shadow",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground shadow",
        outline: "text-foreground",
        success: "border-transparent bg-success/15 text-success",
        warning: "border-transparent bg-warning/15 text-warning",
        processing: "border-transparent bg-processing/15 text-processing",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
```

- [ ] **Step 4: Create input.tsx**

```typescript
import * as React from "react"
import { cn } from "@/lib/utils"

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
```

- [ ] **Step 5: Create remaining UI components**

Create `separator.tsx`, `tooltip.tsx`, `progress.tsx`, `tabs.tsx`, `dropdown-menu.tsx`, `dialog.tsx`, `toast.tsx` following the shadcn/ui pattern. Use the standard shadcn/ui implementations from https://ui.shadcn.com — each follows the same pattern of wrapping Radix UI primitives with Tailwind styling.

- [ ] **Step 6: Verify build**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Run: `cd /home/jjb/kb-platform/frontend && npx vite build`
Expected: Build succeeds

- [ ] **Step 7: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/src/components/ui/ && git commit -m "feat: add shadcn/ui base components"
```

---

### Task 3: API Client and App Store

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/stores/app.ts`
- Create: `frontend/src/vite-env.d.ts`

- [ ] **Step 1: Create vite-env.d.ts**

```typescript
/// <reference types="vite/client" />
```

- [ ] **Step 2: Create api.ts**

```typescript
const BASE = '/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// Types
export interface SearchResult {
  rank: number
  card_id: string
  title: string
  body: string
  source_type: string
  source_file: string
  path: string
  hit_rate: number
  intent_tags: string[]
  quality_tier: string
  doc_file: string
}

export interface QueryResponse {
  query: string
  route: string
  cache_hit: boolean
  latency_ms: number
  results: SearchResult[]
  total: number
}

export interface HealthResponse {
  status: string
  version: string
  checks: Record<string, unknown>
  latency_ms: number
}

export interface UploadedFile {
  id: string
  filename: string
  file_type: string
  file_size: number
  cards_count: number
  pipeline_status: string
  created_at: string
}

export interface Card {
  id: string
  title: string
  body: string
  path: string
  source_type: string
  doc_file: string
  quality_tier: string
  intent_tags: string[]
  updated_at: string
}

// API functions
export const api = {
  health: () => request<HealthResponse>('/health'),

  query: (q: string, opts?: { page?: number; page_size?: number; include_low_quality?: boolean }) =>
    request<QueryResponse>('/query', {
      method: 'POST',
      body: JSON.stringify({ query: q, ...opts }),
    }),

  feedback: (card_id: string, rating: 'positive' | 'negative', reason?: string) =>
    request('/feedback', {
      method: 'POST',
      body: JSON.stringify({ card_id, rating, reason }),
    }),

  upload: async (file: File): Promise<UploadedFile> => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${BASE}/upload`, { method: 'POST', body: formData })
    if (!res.ok) throw new Error('Upload failed')
    return res.json()
  },

  listFiles: () => request<{ files: UploadedFile[] }>('/files'),

  listCards: (params?: { page?: number; page_size?: number; source_type?: string }) => {
    const qs = new URLSearchParams()
    if (params?.page) qs.set('page', String(params.page))
    if (params?.page_size) qs.set('page_size', String(params.page_size))
    if (params?.source_type) qs.set('source_type', params.source_type)
    return request<{ total: number; items: Card[] }>(`/cards?${qs}`)
  },
}
```

- [ ] **Step 3: Create stores/app.ts**

```typescript
import { create } from 'zustand'
import { api, type HealthResponse } from '@/lib/api'

interface AppState {
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  health: HealthResponse | null
  fetchHealth: () => Promise<void>
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  health: null,
  fetchHealth: async () => {
    try {
      const health = await api.health()
      set({ health })
    } catch {
      set({ health: { status: 'error', version: '0', checks: {}, latency_ms: 0 } })
    }
  },
}))
```

- [ ] **Step 4: Verify build**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/src/lib/ frontend/src/stores/ frontend/src/vite-env.d.ts && git commit -m "feat: add API client and app store"
```

---

### Task 4: Layout Components (Sidebar + TopBar + AppShell)

**Files:**
- Create: `frontend/src/components/layout/sidebar.tsx`
- Create: `frontend/src/components/layout/topbar.tsx`
- Create: `frontend/src/components/layout/app-shell.tsx`
- Create: `frontend/src/app.tsx`

- [ ] **Step 1: Create sidebar.tsx**

```typescript
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/stores/app'
import {
  Search, Upload, LayoutDashboard, Layers,
  Settings, ListOrdered, Briefcase,
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘' },
  { to: '/search', icon: Search, label: '查询' },
  { to: '/upload', icon: Upload, label: '上传' },
  { to: '/cards', icon: Layers, label: '卡片' },
  { to: '/workspace', icon: Briefcase, label: '售前工作台' },
  { to: '/indexes', icon: ListOrdered, label: '索引' },
  { to: '/settings', icon: Settings, label: '配置' },
]

export function Sidebar() {
  const collapsed = useAppStore((s) => s.sidebarCollapsed)

  return (
    <aside
      className={cn(
        'fixed left-0 top-[56px] bottom-0 z-40 flex flex-col border-r bg-surface-container-lowest transition-[width] duration-200',
        collapsed ? 'w-[64px]' : 'w-[240px]'
      )}
    >
      <nav className="flex flex-col gap-1 p-3 flex-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )
            }
          >
            <Icon className="h-5 w-5 shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
```

- [ ] **Step 2: Create topbar.tsx**

```typescript
import { useAppStore } from '@/stores/app'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { PanelLeftClose, PanelLeftOpen, Upload, RefreshCw } from 'lucide-react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export function TopBar() {
  const { health, fetchHealth, sidebarCollapsed, toggleSidebar } = useAppStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  const statusColor = health?.status === 'healthy' ? 'success' : 'destructive'

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-[56px] flex items-center justify-between border-b bg-surface-container-lowest px-4">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={toggleSidebar}>
          {sidebarCollapsed ? <PanelLeftOpen className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
        </Button>
        <h1 className="font-heading text-lg font-semibold">知识库平台</h1>
        {health && (
          <Badge variant={statusColor} className="ml-2">
            {health.status === 'healthy' ? '正常' : '异常'}
          </Badge>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => navigate('/upload')}>
          <Upload className="h-4 w-4" />
          上传
        </Button>
        <Button variant="ghost" size="icon" onClick={fetchHealth}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
```

- [ ] **Step 3: Create app-shell.tsx**

```typescript
import { Outlet } from 'react-router-dom'
import { Sidebar } from './sidebar'
import { TopBar } from './topbar'
import { useAppStore } from '@/stores/app'
import { cn } from '@/lib/utils'

export function AppShell() {
  const collapsed = useAppStore((s) => s.sidebarCollapsed)

  return (
    <div className="min-h-screen bg-background">
      <TopBar />
      <Sidebar />
      <main
        className={cn(
          'pt-[56px] transition-[margin-left] duration-200',
          collapsed ? 'ml-[64px]' : 'ml-[240px]'
        )}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 4: Create app.tsx with Router**

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from '@/components/layout/app-shell'
import SearchPage from '@/pages/search'
import DashboardPage from '@/pages/dashboard'

function Placeholder({ title }: { title: string }) {
  return (
    <div>
      <h1 className="font-heading text-h1">{title}</h1>
      <p className="text-muted-foreground mt-2">页面开发中...</p>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/upload" element={<Placeholder title="上传文档" />} />
          <Route path="/cards" element={<Placeholder title="卡片管理" />} />
          <Route path="/indexes" element={<Placeholder title="索引管理" />} />
          <Route path="/settings" element={<Placeholder title="系统配置" />} />
          <Route path="/workspace" element={<Placeholder title="售前工作台" />} />
          <Route path="/templates" element={<Placeholder title="模板管理" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 5: Update main.tsx**

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './globals.css'
import App from './app'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 6: Verify build**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Run: `cd /home/jjb/kb-platform/frontend && npx vite build`
Expected: Build succeeds

- [ ] **Step 7: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/src/components/layout/ frontend/src/app.tsx frontend/src/main.tsx && git commit -m "feat: add AppShell layout with Sidebar and TopBar"
```

---

### Task 5: Search Components

**Files:**
- Create: `frontend/src/components/search/search-input.tsx`
- Create: `frontend/src/components/search/result-card.tsx`
- Create: `frontend/src/components/search/source-pill.tsx`
- Create: `frontend/src/components/shared/status-badge.tsx`
- Create: `frontend/src/components/shared/empty-state.tsx`

- [ ] **Step 1: Create search-input.tsx**

```typescript
import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, Loader2 } from 'lucide-react'

interface SearchInputProps {
  onSearch: (query: string) => void
  loading?: boolean
  placeholder?: string
}

export function SearchInput({ onSearch, loading, placeholder = '输入问题，例如：AE800 的价格是多少' }: SearchInputProps) {
  const [value, setValue] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (value.trim()) onSearch(value.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="h-12 text-base flex-1"
      />
      <Button type="submit" size="lg" disabled={loading || !value.trim()}>
        {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Search className="h-5 w-5" />}
        查询
      </Button>
    </form>
  )
}
```

- [ ] **Step 2: Create source-pill.tsx**

```typescript
import { Badge } from '@/components/ui/badge'
import { FileSpreadsheet, FileText, FileImage, File, FileCheck } from 'lucide-react'

const sourceConfig: Record<string, { label: string; variant: string; icon: React.ElementType }> = {
  excel: { label: 'Excel', variant: 'success', icon: FileSpreadsheet },
  word: { label: 'Word', variant: 'default', icon: FileText },
  markdown: { label: 'Markdown', variant: 'secondary', icon: FileText },
  txt: { label: 'TXT', variant: 'secondary', icon: File },
  ppt: { label: 'PPT', variant: 'warning', icon: FileImage },
  report: { label: '检测报告', variant: 'processing', icon: FileCheck },
}

interface SourcePillProps {
  sourceType: string
  fileName?: string
  path?: string
  className?: string
}

export function SourcePill({ sourceType, fileName, path, className }: SourcePillProps) {
  const config = sourceConfig[sourceType] || { label: sourceType, variant: 'secondary', icon: File }
  const Icon = config.icon

  return (
    <Badge variant={config.variant as any} className={className}>
      <Icon className="h-3 w-3 mr-1" />
      {config.label}
      {fileName && <span className="ml-1 opacity-70">· {fileName}</span>}
      {path && <span className="ml-1 opacity-70">· {path}</span>}
    </Badge>
  )
}
```

- [ ] **Step 3: Create result-card.tsx**

```typescript
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SourcePill } from './source-pill'
import { Copy, ExternalLink, ThumbsUp, ThumbsDown } from 'lucide-react'
import type { SearchResult } from '@/lib/api'
import { cn } from '@/lib/utils'

function hitRateColor(rate: number): string {
  if (rate >= 0.85) return 'text-hit-high'
  if (rate >= 0.65) return 'text-hit-medium'
  if (rate >= 0.5) return 'text-hit-low'
  return 'text-muted-foreground'
}

function hitRateLabel(rate: number): string {
  if (rate >= 0.85) return '强命中'
  if (rate >= 0.65) return '较相关'
  if (rate >= 0.5) return '可能相关'
  return '低质量'
}

interface ResultCardProps {
  result: SearchResult
  onCopy: (text: string) => void
  onFeedback: (cardId: string, rating: 'positive' | 'negative') => void
}

export function ResultCard({ result, onCopy, onFeedback }: ResultCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-lg font-heading font-semibold text-muted-foreground">
              #{result.rank}
            </span>
            <div>
              <span className={cn('text-lg font-semibold font-heading', hitRateColor(result.hit_rate))}>
                {Math.round(result.hit_rate * 100)}%
              </span>
              <span className="text-meta text-muted-foreground ml-2">
                {hitRateLabel(result.hit_rate)}
              </span>
            </div>
            <SourcePill
              sourceType={result.source_type}
              fileName={result.source_file}
              path={result.path}
            />
          </div>
        </div>

        <h3 className="font-heading text-h2 mt-3">{result.title}</h3>

        <div className="mt-2 rounded-md bg-surface-container p-3 font-mono text-body-small leading-relaxed whitespace-pre-wrap max-h-[200px] overflow-y-auto">
          {result.body}
        </div>

        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center gap-1">
            {result.intent_tags?.map((tag) => (
              <Badge key={tag} variant="outline" className="text-meta">
                {tag}
              </Badge>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={() => onCopy(result.body)}>
              <Copy className="h-4 w-4" />
              复制原文
            </Button>
            <Button variant="ghost" size="sm">
              <ExternalLink className="h-4 w-4" />
              查看出处
            </Button>
            <Button variant="ghost" size="icon" onClick={() => onFeedback(result.card_id, 'positive')}>
              <ThumbsUp className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => onFeedback(result.card_id, 'negative')}>
              <ThumbsDown className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 4: Create status-badge.tsx**

```typescript
import { cn } from '@/lib/utils'

interface StatusBadgeProps {
  status: 'healthy' | 'processing' | 'warning' | 'failed' | 'stale'
  label?: string
  className?: string
}

const statusStyles: Record<string, { dot: string; text: string }> = {
  healthy: { dot: 'bg-success', text: 'text-success' },
  processing: { dot: 'bg-processing animate-pulse', text: 'text-processing' },
  warning: { dot: 'bg-warning', text: 'text-warning' },
  failed: { dot: 'bg-destructive', text: 'text-destructive' },
  stale: { dot: 'bg-muted-foreground', text: 'text-muted-foreground' },
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const style = statusStyles[status] || statusStyles.stale
  return (
    <span className={cn('inline-flex items-center gap-1.5 text-meta', className)}>
      <span className={cn('h-2 w-2 rounded-full', style.dot)} />
      {label && <span className={style.text}>{label}</span>}
    </span>
  )
}
```

- [ ] **Step 5: Create empty-state.tsx**

```typescript
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  icon?: React.ElementType
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
  className?: string
}

export function EmptyState({ icon: Icon = Inbox, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      <Icon className="h-12 w-12 text-muted-foreground/50 mb-4" />
      <h3 className="font-heading text-h2 text-foreground">{title}</h3>
      {description && <p className="text-body-small text-muted-foreground mt-1 max-w-md">{description}</p>}
      {action && (
        <Button className="mt-4" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  )
}
```

- [ ] **Step 6: Verify build**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/src/components/search/ frontend/src/components/shared/ && git commit -m "feat: add search and shared components"
```

---

### Task 6: Search Page and Dashboard

**Files:**
- Create: `frontend/src/pages/search.tsx`
- Create: `frontend/src/pages/dashboard.tsx`
- Modify: `frontend/src/app.tsx`

- [ ] **Step 1: Create search.tsx**

```typescript
import { useState } from 'react'
import { SearchInput } from '@/components/search/search-input'
import { ResultCard } from '@/components/search/result-card'
import { EmptyState } from '@/components/shared/empty-state'
import { Badge } from '@/components/ui/badge'
import { api, type QueryResponse } from '@/lib/api'
import { Search, AlertCircle } from 'lucide-react'

const exampleQueries = [
  'AE800 的价格是多少',
  'PE8000 什么时候停产',
  '公安行业怎么推',
  'XE800 与 AE800 接口对比',
  '软件端和硬件端的区别',
]

export default function SearchPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (query: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.query(query)
      setResult(data)
    } catch (e: any) {
      setError(e.message || '查询失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const handleFeedback = async (cardId: string, rating: 'positive' | 'negative') => {
    try {
      await api.feedback(cardId, rating)
    } catch {
      // silent
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="font-heading text-h1">查询</h1>
        <p className="text-muted-foreground text-body-small mt-1">
          输入问题，从知识库中查找原文和出处
        </p>
      </div>

      <SearchInput onSearch={handleSearch} loading={loading} />

      {!result && !loading && !error && (
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((q) => (
            <Badge
              key={q}
              variant="outline"
              className="cursor-pointer hover:bg-accent"
              onClick={() => handleSearch(q)}
            >
              {q}
            </Badge>
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-md bg-destructive/10 text-destructive">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 text-meta text-muted-foreground">
            <span>路由：{result.route}</span>
            {result.cache_hit && <Badge variant="secondary">缓存命中</Badge>}
            <span>{result.latency_ms}ms</span>
            <span>共 {result.total} 条结果</span>
          </div>

          {result.results.length === 0 ? (
            <EmptyState
              icon={Search}
              title="没有找到匹配结果"
              description="可以尝试换关键词、开启低质量结果，或确认文档是否已上传"
            />
          ) : (
            <div className="space-y-3">
              {result.results.map((r) => (
                <ResultCard
                  key={r.card_id}
                  result={r}
                  onCopy={handleCopy}
                  onFeedback={handleFeedback}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Create dashboard.tsx**

```typescript
import { useEffect } from 'react'
import { useAppStore } from '@/stores/app'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { StatusBadge } from '@/components/shared/status-badge'
import { useNavigate } from 'react-router-dom'
import { Search, Layers, FileText, Activity } from 'lucide-react'

export default function DashboardPage() {
  const { health, fetchHealth } = useAppStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchHealth()
  }, [fetchHealth])

  const checks = health?.checks || {}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-h1">仪表盘</h1>
          <p className="text-muted-foreground text-body-small mt-1">
            系统状态总览
          </p>
        </div>
        <StatusBadge
          status={health?.status === 'healthy' ? 'healthy' : 'failed'}
          label={health?.status === 'healthy' ? '系统正常' : '系统异常'}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('/cards')}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">卡片总数</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-heading font-bold">{(checks as any).cards_count ?? '—'}</div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('/search')}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">查询</CardTitle>
            <Search className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-heading font-bold">—</div>
            <p className="text-meta text-muted-foreground">点击开始查询</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">待处理任务</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-heading font-bold">
              {((checks as any).jobs_pending ?? 0) + ((checks as any).jobs_running ?? 0)}
            </div>
            <p className="text-meta text-muted-foreground">
              失败: {(checks as any).jobs_failed ?? 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">证据包</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-heading font-bold">{(checks as any).evidence_count ?? '—'}</div>
            <p className="text-meta text-muted-foreground">
              检测报告: {(checks as any).report_evidence_count ?? 0}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Update app.tsx to use real pages**

Replace the placeholder routes for Dashboard and Search with the actual page imports. Keep other routes as placeholders.

- [ ] **Step 4: Verify build**

Run: `cd /home/jjb/kb-platform/frontend && npx tsc --noEmit`
Run: `cd /home/jjb/kb-platform/frontend && npx vite build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
cd /home/jjb/kb-platform && git add frontend/src/pages/ frontend/src/app.tsx && git commit -m "feat: add search page and dashboard"
```

---

### Task 7: End-to-End Verification

- [ ] **Step 1: Start backend**

Run: `cd /home/jjb/kb-platform/backend && python3 -m uvicorn main:app --port 8000`

- [ ] **Step 2: Start frontend dev server**

Run: `cd /home/jjb/kb-platform/frontend && npm run dev`

- [ ] **Step 3: Verify in browser**

Open http://localhost:3000
- Dashboard should show system health stats
- Click "查询" in sidebar
- Search input should be visible
- Type a query and see results (or empty state if no data)

- [ ] **Step 4: Final commit**

```bash
cd /home/jjb/kb-platform && git add frontend/ && git commit -m "feat: frontend phase 1 complete - foundation, layout, search page"
```

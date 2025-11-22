# Frontend Architecture Blueprint - Vue.js 3 + Vite

**Framework:** Vue.js 3 (Composition API)  
**Build Tool:** Vite  
**State Management:** Pinia  
**Routing:** Vue Router 4  
**Type System:** TypeScript  
**Date:** 2025-01-XX  

---

## 1. Project Structure

```
frontend/
├── public/                     # Static assets
│   ├── favicon.ico
│   └── logo.png
│
├── src/
│   ├── assets/                 # Compiled assets (images, styles)
│   │   ├── images/
│   │   └── styles/
│   │       └── main.css
│   │
│   ├── components/             # Reusable Vue components
│   │   ├── common/            # Common UI components
│   │   │   ├── Button.vue
│   │   │   ├── Input.vue
│   │   │   ├── Select.vue
│   │   │   ├── Card.vue
│   │   │   ├── Badge.vue
│   │   │   ├── Loading.vue
│   │   │   ├── ErrorBoundary.vue
│   │   │   └── StatusIndicator.vue
│   │   │
│   │   ├── research/          # Research-specific components
│   │   │   ├── QueryInput.vue
│   │   │   ├── ModeSelector.vue
│   │   │   ├── ConversationInterface.vue
│   │   │   ├── LogViewer.vue
│   │   │   ├── ProgressTracker.vue
│   │   │   ├── ResultVisualization.vue
│   │   │   └── PaperViewer.vue
│   │   │
│   │   └── layout/            # Layout components
│   │       ├── AppHeader.vue
│   │       ├── AppSidebar.vue
│   │       └── AppFooter.vue
│   │
│   ├── composables/           # Composition API composables
│   │   ├── useApiClient.ts
│   │   ├── useJobManagement.ts
│   │   ├── useLogStreaming.ts
│   │   ├── useEnvironment.ts
│   │   ├── usePolling.ts
│   │   ├── useErrorHandler.ts
│   │   └── useSessionPersistence.ts
│   │
│   ├── stores/                # Pinia stores
│   │   ├── index.ts
│   │   ├── job.ts             # Job state management
│   │   ├── environment.ts     # Environment variables
│   │   ├── session.ts         # Session/UI state
│   │   └── logs.ts            # Log state management
│   │
│   ├── services/              # API services
│   │   ├── api/
│   │   │   ├── client.ts      # Axios instance
│   │   │   ├── types.ts       # TypeScript types
│   │   │   ├── jobs.ts        # Job endpoints
│   │   │   ├── logs.ts        # Log endpoints
│   │   │   ├── environment.ts # Environment endpoints
│   │   │   └── health.ts      # Health endpoints
│   │   │
│   │   └── storage/
│   │       ├── localStorage.ts
│   │       └── sessionStorage.ts
│   │
│   ├── views/                 # Route views
│   │   ├── Home.vue           # Main research interface
│   │   ├── Jobs.vue           # Job list/management
│   │   ├── JobDetail.vue      # Job detail view
│   │   ├── Environment.vue    # Environment configuration
│   │   ├── Settings.vue       # Application settings
│   │   └── NotFound.vue       # 404 page
│   │
│   ├── router/                # Vue Router configuration
│   │   └── index.ts
│   │
│   ├── types/                 # TypeScript type definitions
│   │   ├── api.ts
│   │   ├── job.ts
│   │   ├── environment.ts
│   │   └── index.ts
│   │
│   ├── utils/                 # Utility functions
│   │   ├── formatting.ts
│   │   ├── validation.ts
│   │   ├── polling.ts
│   │   └── constants.ts
│   │
│   ├── plugins/               # Vue plugins
│   │   └── pinia.ts
│   │
│   ├── App.vue                # Root component
│   ├── main.ts                # Application entry point
│   └── env.d.ts               # Environment type declarations
│
├── tests/                     # Test files
│   ├── unit/
│   │   ├── components/
│   │   ├── composables/
│   │   └── stores/
│   │
│   └── integration/
│       └── api/
│
├── .env                       # Environment variables
├── .env.local                 # Local environment overrides
├── .eslintrc.cjs              # ESLint configuration
├── .prettierrc                # Prettier configuration
├── .gitignore
├── index.html
├── package.json
├── pnpm-lock.yaml             # Package lock (or yarn/npm)
├── tsconfig.json              # TypeScript configuration
├── vite.config.ts             # Vite configuration
└── vitest.config.ts           # Vitest configuration
```

---

## 2. Technology Stack

### Core Framework
- **Vue.js 3.4+** - Progressive JavaScript framework
  - Composition API (primary)
  - `<script setup>` syntax
  - TypeScript support

### Build Tooling
- **Vite 5+** - Next-generation frontend build tool
  - Fast HMR (Hot Module Replacement)
  - Optimized production builds
  - Plugin ecosystem

### State Management
- **Pinia 2+** - Vue state management
  - TypeScript-first
  - Devtools support
  - Modular stores

### Routing
- **Vue Router 4+** - Official Vue.js router
  - Route-based code splitting
  - Navigation guards
  - History mode support

### HTTP Client
- **Axios 1.6+** - Promise-based HTTP client
  - Request/response interceptors
  - Automatic JSON parsing
  - Request cancellation

### Type System
- **TypeScript 5+** - Static type checking
  - Strict mode enabled
  - Full type inference

### UI Framework (Optional)
- **Tailwind CSS 3+** - Utility-first CSS framework
  - Or **Vuetify 3** / **Quasar** for component library
  - Or custom CSS modules

### Testing
- **Vitest** - Vite-native test runner
- **@vue/test-utils** - Vue component testing
- **Testing Library** - User-centric testing

### Code Quality
- **ESLint** - JavaScript/TypeScript linter
  - Vue 3 recommended rules
  - TypeScript ESLint plugin
- **Prettier** - Code formatter
- **Husky** - Git hooks (pre-commit linting)

---

## 3. Component Hierarchy

### 3.1 Root Component Structure

```
App.vue
├── AppHeader
│   ├── Logo
│   ├── Navigation
│   └── UserMenu
│
├── AppSidebar (optional)
│   ├── NavigationMenu
│   └── QuickActions
│
├── RouterView (main content)
│   ├── Home (default route)
│   │   ├── QueryInput
│   │   ├── ModeSelector
│   │   ├── ConversationInterface
│   │   │   ├── LogViewer
│   │   │   └── ProgressTracker
│   │   └── ResultVisualization
│   │
│   ├── Jobs
│   │   ├── JobList
│   │   │   └── JobCard[]
│   │   └── JobFilters
│   │
│   ├── JobDetail
│   │   ├── JobHeader
│   │   ├── LogViewer
│   │   ├── ProgressTracker
│   │   └── ResultViewer
│   │
│   └── Environment
│       ├── EnvVarTable
│       └── EnvVarForm
│
└── AppFooter
```

### 3.2 Key Components

#### QueryInput.vue
- **Purpose:** Research query input
- **Features:**
  - Multi-line text input
  - Character counter
  - Validation
  - Reference input (optional)
- **Props:**
  - `modelValue: string`
  - `placeholder?: string`
  - `required?: boolean`
- **Emits:**
  - `update:modelValue`
  - `submit`

#### ModeSelector.vue
- **Purpose:** Select research mode
- **Features:**
  - Dropdown/radio selection
  - Mode descriptions
  - Required env vars display
- **Props:**
  - `modelValue: string`
  - `modes: Mode[]`
- **Emits:**
  - `update:modelValue`
  - `mode-change`

#### ConversationInterface.vue
- **Purpose:** Display agent conversations
- **Features:**
  - Scrollable log viewer
  - Markdown rendering
  - Syntax highlighting
  - Auto-scroll to bottom
- **Props:**
  - `conversations: Conversation[]`
  - `isLoading?: boolean`
- **Composables:**
  - `useLogStreaming`

#### ProgressTracker.vue
- **Purpose:** Visualize job progress
- **Features:**
  - Progress bar
  - Agent status indicators
  - Subtask list
  - Time estimates
- **Props:**
  - `progress: JobProgress`
  - `status: JobStatus`

#### ResultVisualization.vue
- **Purpose:** Display research results
- **Features:**
  - Structured result display
  - Paper viewer (PDF)
  - Download buttons
  - Token usage display
- **Props:**
  - `result: JobResult`
  - `jobId: string`

---

## 4. State Management (Pinia Stores)

### 4.1 Job Store (`stores/job.ts`)

```typescript
interface JobState {
  jobs: Map<string, JobInfo>
  currentJobId: string | null
  jobList: JobInfo[]
  filters: JobFilters
  pagination: Pagination
}

interface JobActions {
  submitJob(payload: RunRequest): Promise<string> // Returns job_id
  fetchJob(jobId: string): Promise<void>
  fetchJobList(params?: ListJobsParams): Promise<void>
  cancelJob(jobId: string): Promise<void>
  pollJobStatus(jobId: string): Promise<void>
  clearJobs(): void
}

interface JobGetters {
  currentJob: JobInfo | null
  filteredJobs: JobInfo[]
  activeJobs: JobInfo[]
  completedJobs: JobInfo[]
}
```

**Usage:**
```typescript
const jobStore = useJobStore()
const jobId = await jobStore.submitJob({ question, reference, mode })
await jobStore.pollJobStatus(jobId)
```

### 4.2 Environment Store (`stores/environment.ts`)

```typescript
interface EnvironmentState {
  envVars: Record<string, EnvVarInfo>
  validation: EnvValidation | null
  isLoading: boolean
}

interface EnvironmentActions {
  fetchEnvVars(): Promise<void>
  updateEnvVar(key: string, value: string): Promise<void>
  updateEnvVars(vars: EnvItem[]): Promise<void>
  deleteEnvVar(key: string): Promise<void>
  validateEnv(mode: string): Promise<void>
  fetchModes(): Promise<Mode[]>
}

interface EnvironmentGetters {
  requiredVarsForMode: (mode: string) => string[]
  isEnvValidForMode: (mode: string) => boolean
}
```

### 4.3 Session Store (`stores/session.ts`)

```typescript
interface SessionState {
  activeJobIds: string[]
  viewMode: 'compact' | 'detailed'
  autoRefresh: boolean
  refreshInterval: number
  theme: 'light' | 'dark'
}

interface SessionActions {
  addActiveJob(jobId: string): void
  removeActiveJob(jobId: string): void
  restoreFromStorage(): void
  saveToStorage(): void
}

interface SessionGetters {
  hasActiveJobs: boolean
}
```

### 4.4 Logs Store (`stores/logs.ts`)

```typescript
interface LogsState {
  jobLogs: Map<string, Conversation[]>
  globalLogs: Conversation[]
  lastIndex: Map<string, number>
  globalLastIndex: number
}

interface LogsActions {
  fetchJobLogs(jobId: string, lastIndex?: number): Promise<void>
  fetchGlobalLogs(lastIndex?: number): Promise<void>
  clearJobLogs(jobId: string): void
  clearGlobalLogs(): void
}

interface LogsGetters {
  getJobLogs: (jobId: string) => Conversation[]
}
```

---

## 5. Composables

### 5.1 useApiClient.ts
- **Purpose:** Axios instance with interceptors
- **Features:**
  - Base URL configuration
  - Request/response interceptors
  - Error handling
  - Request cancellation

```typescript
export function useApiClient() {
  const client = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 30000,
  })

  // Request interceptor
  client.interceptors.request.use(/* ... */)
  
  // Response interceptor
  client.interceptors.response.use(/* ... */)

  return client
}
```

### 5.2 useJobManagement.ts
- **Purpose:** Job lifecycle management
- **Features:**
  - Submit job
  - Poll job status
  - Cancel job
  - Handle job completion

```typescript
export function useJobManagement() {
  const jobStore = useJobStore()
  const { poll, stopPolling } = usePolling()

  async function submitAndPoll(payload: RunRequest) {
    const jobId = await jobStore.submitJob(payload)
    
    poll(
      async () => {
        await jobStore.fetchJob(jobId)
        return jobStore.jobs.get(jobId)
      },
      {
        interval: 2000,
        until: (job) => !['pending', 'running'].includes(job?.status),
      }
    )

    return jobId
  }

  return {
    submitAndPoll,
    cancelJob: jobStore.cancelJob,
  }
}
```

### 5.3 useLogStreaming.ts
- **Purpose:** Incremental log fetching
- **Features:**
  - Polling-based log updates
  - Incremental fetching (last_index)
  - Auto-scroll
  - Format conversion

```typescript
export function useLogStreaming(jobId?: string) {
  const logsStore = useLogsStore()
  const { poll, stopPolling } = usePolling()

  function startStreaming() {
    poll(
      async () => {
        if (jobId) {
          await logsStore.fetchJobLogs(
            jobId,
            logsStore.lastIndex.get(jobId)
          )
        } else {
          await logsStore.fetchGlobalLogs(logsStore.globalLastIndex)
        }
      },
      {
        interval: 2000,
        immediate: true,
      }
    )
  }

  function stopStreaming() {
    stopPolling()
  }

  return {
    startStreaming,
    stopStreaming,
    logs: computed(() => 
      jobId 
        ? logsStore.getJobLogs(jobId)
        : logsStore.globalLogs
    ),
  }
}
```

### 5.4 usePolling.ts
- **Purpose:** Generic polling utility
- **Features:**
  - Configurable interval
  - Exponential backoff
  - Stop condition
  - Automatic cleanup

```typescript
export function usePolling() {
  const pollIds = new Set<number>()

  function poll<T>(
    fn: () => Promise<T>,
    options: {
      interval: number
      maxInterval?: number
      immediate?: boolean
      until?: (result: T) => boolean
    }
  ) {
    let interval = options.interval
    let timeoutId: number

    const execute = async () => {
      const result = await fn()
      
      if (options.until?.(result)) {
        pollIds.delete(timeoutId)
        return
      }

      // Exponential backoff (capped)
      if (options.maxInterval) {
        interval = Math.min(interval * 1.2, options.maxInterval)
      }

      timeoutId = window.setTimeout(execute, interval)
      pollIds.add(timeoutId)
    }

    if (options.immediate) {
      execute()
    } else {
      timeoutId = window.setTimeout(execute, interval)
      pollIds.add(timeoutId)
    }

    return () => {
      clearTimeout(timeoutId)
      pollIds.delete(timeoutId)
    }
  }

  function stopPolling() {
    pollIds.forEach(clearTimeout)
    pollIds.clear()
  }

  return { poll, stopPolling }
}
```

---

## 6. Routing Structure

### 6.1 Route Configuration

```typescript
const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: 'AI Researcher' },
  },
  {
    path: '/jobs',
    name: 'Jobs',
    component: () => import('@/views/Jobs.vue'),
    meta: { title: 'Jobs' },
  },
  {
    path: '/jobs/:id',
    name: 'JobDetail',
    component: () => import('@/views/JobDetail.vue'),
    meta: { title: 'Job Details' },
    props: true,
  },
  {
    path: '/environment',
    name: 'Environment',
    component: () => import('@/views/Environment.vue'),
    meta: { title: 'Environment Configuration' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: 'Settings' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
  },
]
```

### 6.2 Navigation Guards

```typescript
router.beforeEach((to, from, next) => {
  // Set document title
  document.title = to.meta.title || 'AI Researcher'

  // Check for active jobs (optional)
  const sessionStore = useSessionStore()
  if (sessionStore.hasActiveJobs && to.name !== 'JobDetail') {
    // Could show notification or save state
  }

  next()
})
```

---

## 7. Error Boundary Strategy

### 7.1 Error Boundary Component

```vue
<template>
  <div v-if="error" class="error-boundary">
    <h2>Something went wrong</h2>
    <p>{{ error.message }}</p>
    <button @click="handleReset">Try Again</button>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { onErrorCaptured, ref } from 'vue'

const error = ref<Error | null>(null)

onErrorCaptured((err) => {
  error.value = err
  // Log to error tracking service
  console.error('Error caught:', err)
  return false // Prevent error from propagating
})

function handleReset() {
  error.value = null
}
</script>
```

### 7.2 Global Error Handler

```typescript
// main.ts
app.config.errorHandler = (err, instance, info) => {
  console.error('Global error:', err, info)
  // Send to error tracking service
}
```

---

## 8. Environment Variable Management

### 8.1 Environment Variables

```typescript
// .env
VITE_API_BASE_URL=http://localhost:8080
VITE_APP_TITLE=AI Researcher
VITE_LOG_POLL_INTERVAL=2000
VITE_MAX_LOG_LINES=500
```

### 8.2 Type Declarations

```typescript
// env.d.ts
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_LOG_POLL_INTERVAL: string
  readonly VITE_MAX_LOG_LINES: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

---

## 9. Styling Strategy

### Option 1: Tailwind CSS (Recommended)
- Utility-first approach
- Fast development
- Small bundle size (with purging)

### Option 2: CSS Modules
- Scoped styles per component
- Type-safe (with TypeScript)
- No runtime overhead

### Option 3: Component Library
- **Vuetify 3** - Material Design
- **Quasar** - Full-featured framework
- **Ant Design Vue** - Enterprise components

**Recommendation:** Tailwind CSS for rapid development and flexibility.

---

## 10. Performance Optimizations

### 10.1 Code Splitting
- Route-based code splitting (automatic with Vite)
- Component lazy loading
- Dynamic imports for heavy libraries

### 10.2 State Management
- Store only necessary data
- Use computed properties for derived state
- Avoid unnecessary reactivity

### 10.3 Polling Optimization
- Exponential backoff
- Stop polling when not visible (Page Visibility API)
- Debounce rapid updates

### 10.4 Log Rendering
- Virtual scrolling for large log lists
- Memoization of parsed log entries
- Lazy rendering of off-screen content

---

## 11. Testing Strategy

### 11.1 Unit Tests
- Component testing with Vue Test Utils
- Composables testing
- Store testing
- Utility function testing

### 11.2 Integration Tests
- API client testing (with MSW)
- End-to-end workflows
- User interaction flows

### 11.3 Test Structure
```
tests/
├── unit/
│   ├── components/
│   │   └── QueryInput.spec.ts
│   ├── composables/
│   │   └── useJobManagement.spec.ts
│   └── stores/
│       └── job.spec.ts
└── integration/
    └── jobWorkflow.spec.ts
```

---

## 12. CI/CD Structure

### 12.1 GitHub Actions Workflow

```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v3
      - run: pnpm install
      - run: pnpm lint
      - run: pnpm test

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v3
      - run: pnpm install
      - run: pnpm build
      - uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist
```

---

## 13. Accessibility Considerations

1. **ARIA Labels:** All interactive elements
2. **Keyboard Navigation:** Full keyboard support
3. **Screen Reader Support:** Semantic HTML
4. **Color Contrast:** WCAG AA compliance
5. **Focus Management:** Visible focus indicators

---

## 14. Browser Support

- **Modern Browsers:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Features Used:** ES2020+, CSS Grid, Flexbox
- **Polyfills:** Handled by Vite/browserslist

---

## 15. Security Considerations

1. **Input Validation:** Validate all user inputs
2. **XSS Prevention:** Vue's automatic escaping + sanitization
3. **CSRF Protection:** Configure CORS properly
4. **Environment Variables:** Never expose secrets in frontend
5. **API Keys:** Manage via backend (env management API)

---

## 16. Development Workflow

### 16.1 Local Development
```bash
# Install dependencies
pnpm install

# Start dev server
pnpm dev

# Run linter
pnpm lint

# Run tests
pnpm test

# Build for production
pnpm build
```

### 16.2 Code Standards
- **TypeScript:** Strict mode enabled
- **ESLint:** Vue 3 recommended rules
- **Prettier:** Auto-format on save
- **Git Hooks:** Pre-commit linting (Husky)

---

## 17. Deployment Considerations

### 17.1 Build Output
- Static files (HTML, JS, CSS)
- Can be served by any static file server
- Environment variables baked in at build time

### 17.2 Recommended Hosting
- **Vercel** - Automatic deployments
- **Netlify** - Static hosting + forms
- **GitHub Pages** - Free hosting
- **Nginx/Apache** - Self-hosted

### 17.3 Build Configuration
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable in production
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'axios': ['axios'],
        },
      },
    },
  },
})
```

---

## Conclusion

This architecture provides:

1. **Modularity:** Clear separation of concerns
2. **Scalability:** Easy to extend and maintain
3. **Type Safety:** Full TypeScript support
4. **Performance:** Optimized for fast load times
5. **Developer Experience:** Excellent tooling and DX
6. **Production Ready:** CI/CD, testing, error handling

The architecture is designed to be zero-coupled to backend implementation details, relying purely on the API contract defined in `B_API_CONTRACT.md`.

---

**End of Architecture Blueprint**


/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_LOG_POLL_INTERVAL: string
  readonly VITE_MAX_LOG_LINES: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}


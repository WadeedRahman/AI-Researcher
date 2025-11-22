<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const appTitle = computed(() => import.meta.env.VITE_APP_TITLE || 'AI Researcher')

import logo from '@/assets/images/logo.png'
</script>

<template>
  <header class="app-header">
    <div class="container">
      <div class="header-content">
        <div class="logo">
          <RouterLink to="/" class="logo-link">
            <img :src="logo" alt="Logo">
          </RouterLink>
        </div>
      </div>
    </div>
  </header>
</template>
<style scoped>
.app-header {
  background-color: #ffffff;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  padding: var(--spacing-md) 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-lg);
}

.logo-link {
  text-decoration: none;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  transition: transform var(--transition);
}

.logo-link:hover {
  transform: translateY(-1px);
}

.logo-main {
  font-size: 1.75rem;
  font-weight: 800;
  color: #1a1a2e;
  letter-spacing: -0.03em;
  line-height: 1;
}

.logo-subtitle {
  font-size: 0.875rem;
  font-weight: 500;
  color: #06b6d4;
  letter-spacing: 0.02em;
  line-height: 1;
}

@media (max-width: 768px) {
  .logo-main {
    font-size: 1.5rem;
  }
  
  .logo-subtitle {
    font-size: 0.75rem;
  }
}
</style>


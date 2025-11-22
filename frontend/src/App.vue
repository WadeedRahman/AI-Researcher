<template>
  <div id="app" :data-theme="theme">
    <AppHeader />
    <main class="main-content">
      <RouterView />
    </main>
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'

const sessionStore = useSessionStore()
const theme = computed(() => sessionStore.theme)

onMounted(() => {
  // Apply theme on mount (default to dark if not set)
  const currentTheme = sessionStore.theme || 'dark'
  document.documentElement.setAttribute('data-theme', currentTheme)
  if (!sessionStore.theme) {
    sessionStore.setTheme('dark')
  }
})
</script>

<style scoped>
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>


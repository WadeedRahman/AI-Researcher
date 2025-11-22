<template>
  <footer class="app-footer">
    <div class="container">
      <div class="footer-bottom">
        <p>&copy; {{ currentYear }} AI-Researcher. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>

<style scoped>
.app-footer {
  background-color: var(--color-background);
  border-top: 1px solid var(--color-border);
  padding: var(--spacing-lg) 0;
  margin-top: auto;
  color: var(--color-text-secondary);
}

.footer-bottom {
  text-align: center;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}
</style>


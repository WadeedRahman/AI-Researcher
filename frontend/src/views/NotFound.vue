<template>
  <div class="not-found-view">
    <div class="container">
      <h1>404</h1>
      <p>Page not found</p>
      <RouterLink to="/" class="button button-primary">Go Home</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.not-found-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

h1 {
  font-size: 6rem;
  color: var(--color-primary);
  margin-bottom: 1rem;
}

p {
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  margin-bottom: 2rem;
}
</style>


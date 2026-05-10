<template>
  <div class="shell">
    <AppHeader />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import AppHeader from './components/AppHeader.vue'
import { useGraphStore } from './stores/graphStore.js'
import { useUIStore } from './stores/uiStore.js'

const graphStore = useGraphStore()
const uiStore = useUIStore()

onMounted(async () => {
  uiStore.initTheme()
  await graphStore.loadData()
})
</script>

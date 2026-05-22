<template>
  <div class="shell">
    <AppHeader />
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
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

<style>
.shell {
  position: relative;
  min-height: 100vh;
}

.app-main {
  position: relative;
  z-index: 1;
}

.page-enter-active, .page-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>

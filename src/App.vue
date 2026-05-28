<template>
  <div class="shell" :class="{ 'shell-landing': isLanding }">
    <AppHeader v-if="!isLanding" />
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
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import { useGraphStore } from './stores/graphStore.js'
import { useUIStore } from './stores/uiStore.js'

const route = useRoute()
const graphStore = useGraphStore()
const uiStore = useUIStore()

const isLanding = computed(() => route.name === 'Landing')

onMounted(async () => {
  uiStore.initTheme()
  await graphStore.loadData()
})
</script>

<style>
.shell {
  position: relative;
  isolation: isolate;
  min-height: 100vh;
  padding: 20px 24px;
  overflow-x: hidden;
}

.shell::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    linear-gradient(135deg, rgba(15, 143, 125, 0.08) 0 12%, transparent 12.2% 100%),
    linear-gradient(24deg, transparent 0 58%, rgba(14, 165, 233, 0.08) 58.2% 58.9%, transparent 59.2% 100%);
  mask-image: linear-gradient(180deg, #000 0, transparent 72%);
}

.shell::after {
  content: "";
  position: fixed;
  left: max(24px, 4vw);
  bottom: max(18px, 4vw);
  z-index: 0;
  width: clamp(210px, 28vw, 420px);
  height: clamp(110px, 13vw, 190px);
  pointer-events: none;
  opacity: 0.12;
  color: var(--accent);
  border: 2px solid currentColor;
  border-left-color: transparent;
  border-bottom-color: transparent;
  border-radius: 62% 80% 48% 72%;
  transform: rotate(-18deg);
}

.shell-landing {
  padding: 0;
}

.shell-landing::before,
.shell-landing::after {
  display: none;
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

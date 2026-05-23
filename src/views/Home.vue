<template>
  <div class="home-page">
    <div class="home-hero">
      <div class="search-section">
        <div class="search-wrapper">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="搜索鸟类中文名、英文名或学名…"
            @input="handleSearch"
          />
        </div>
        <div v-if="searchResults.length" class="search-dropdown">
          <button
            v-for="item in searchResults"
            :key="item.id"
            type="button"
            class="search-result-item"
            @click="selectSearchResult(item)"
          >
            <div class="result-name">{{ item.name }}</div>
            <div class="result-meta">{{ item.englishName || '暂无英文名' }} · {{ item.latinName || '暂无学名' }}</div>
          </button>
        </div>
      </div>
    </div>

    <div class="home-layout">
      <aside class="home-sidebar">
        <section class="panel insight-panel">
          <h3 class="panel-title">数据加载状态</h3>
          <div class="metric-grid">
            <div class="metric-card">
              <span class="metric-value">{{ store.totalBirdCount }}</span>
              <span class="metric-label">鸟类索引</span>
            </div>
            <div class="metric-card">
              <span class="metric-value">{{ store.loadedBirdCount }}</span>
              <span class="metric-label">已进图物种</span>
            </div>
            <div class="metric-card">
              <span class="metric-value">{{ store.nodeCount }}</span>
              <span class="metric-label">当前节点</span>
            </div>
            <div class="metric-card">
              <span class="metric-value">{{ store.linkCount }}</span>
              <span class="metric-label">当前关系</span>
            </div>
          </div>
        </section>

        <section class="panel export-panel">
          <h3 class="panel-title">导出当前子图</h3>
          <div class="export-btns">
            <button type="button" class="export-btn" @click="exportPNG(containerRef)">PNG 截图</button>
            <button type="button" class="export-btn" @click="exportJSON(store.nodes, store.links)">JSON 数据</button>
            <button type="button" class="export-btn" @click="exportGraphML(store.nodes, store.links)">GraphML</button>
          </div>
        </section>
      </aside>

      <section class="graph-panel">
        <div class="graph-header">
          <div>
            <h2>鸟类知识图谱</h2>
            <p class="graph-summary">{{ graphSummary }}</p>
          </div>
          <div class="legend">
            <span v-for="item in legendItems" :key="item.label">
              <i :style="{ backgroundColor: item.color }"></i>{{ item.label }}
            </span>
          </div>
        </div>

        <div class="graph-toolbar">
          <div class="toolbar-group wide">
            <span class="toolbar-label">上下文实体</span>
            <div class="pill-group">
              <button
                v-for="item in filterableTypeItems"
                :key="item.type"
                type="button"
                class="pill"
                :class="{ active: activeContextTypes.includes(item.type) }"
                @click="toggleContextType(item.type)"
              >
                {{ item.label }}
              </button>
            </div>
          </div>
          <div class="toolbar-group compact">
            <span class="toolbar-label">标签策略</span>
            <p class="toolbar-copy">悬停节点可查看名称与分类。</p>
          </div>
          <div class="toolbar-actions">
            <button type="button" class="pill reset-btn" @click="resetContextFilters">重置视图</button>
          </div>
        </div>

        <div ref="containerRef" class="graph-canvas">
          <div v-if="showInitialLoading" class="graph-loading">
            <div class="loading-spinner"></div>
            <p>正在加载…</p>
          </div>
          <SigmaCanvas
            v-else
            :active-types="activeContextTypes"
            :dark-mode="uiStore.darkMode"
            @node-click="handleNodeClick"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import SigmaCanvas from '../graph/SigmaCanvas.vue'
import { useGraphExport } from '../composables/useGraphExport.js'
import { useGraphStore } from '../stores/graphStore.js'
import { useUIStore } from '../stores/uiStore.js'

const router = useRouter()
const store = useGraphStore()
const uiStore = useUIStore()
const { exportPNG, exportJSON, exportGraphML } = useGraphExport()

const containerRef = ref(null)
const searchQuery = ref('')
const searchResults = ref([])
const activeContextTypes = ref(['location', 'habitat', 'status', 'threat'])

const legendItems = [
  { label: '鸟类', color: '#eaf3ff' },
  { label: '关联实体', color: '#9fc0ff' }
]

const filterableTypeItems = [
  { type: 'location', label: '地点' },
  { type: 'habitat', label: '栖息地' },
  { type: 'status', label: '保护等级' },
  { type: 'threat', label: '威胁因素' }
]

const showInitialLoading = computed(() => !store.loaded || (store.previewLoading && store.nodeCount === 0))

const graphSummary = computed(() => {
  if (!store.loaded || (store.previewLoading && store.nodeCount === 0)) {
    return '正在加载图谱…'
  }
  if (store.previewLoading) {
    return `已载入 ${store.loadedBirdCount}/${store.totalBirdCount} 种鸟类`
  }
  if (store.previewLoaded) {
    return `共 ${store.totalBirdCount} 种鸟类 · ${store.nodeCount} 个节点 · ${store.linkCount} 条关系`
  }
  return `${store.nodeCount} 个节点 · ${store.linkCount} 条关系`
})

const handleSearch = useDebounceFn(() => {
  const query = searchQuery.value.trim()
  searchResults.value = query ? store.findBirdMatches(query, 8) : []
}, 120)

async function selectSearchResult(item) {
  searchQuery.value = item.name
  searchResults.value = []
  await store.loadNodeChunk(item.id)
  router.push(`/bird/${item.id}`)
}

async function handleNodeClick(node) {
  store.setActiveNode(node.id)

  if (node.type === 'bird') {
    await store.loadNodeChunk(node.id)
    router.push(`/bird/${node.id}`)
    return
  }

  if (node.expandable) {
    await store.loadNodeChunk(node.id)
    return
  }

  store.requestNodeFocus(node.id)
}

function toggleContextType(type) {
  if (activeContextTypes.value.includes(type)) {
    activeContextTypes.value = activeContextTypes.value.filter(item => item !== type)
    return
  }
  activeContextTypes.value = [...activeContextTypes.value, type]
}

function resetContextFilters() {
  activeContextTypes.value = ['location', 'habitat', 'status', 'threat']
  store.requestGraphFit()
}

onMounted(async () => {
  await store.loadInitialData()
  void store.loadGraphPreview()
})
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  animation: pageIn 0.4s ease-out;
}

.home-hero {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: center;
  padding: 28px 18px 0;
}

.search-section {
  position: relative;
  z-index: 12;
  width: 100%;
  max-width: 720px;
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 20px;
  width: 22px;
  height: 22px;
  color: rgba(18, 48, 59, 0.4);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 18px 24px 18px 56px;
  border: 2px solid rgba(15, 118, 110, 0.2);
  border-radius: 999px;
  background: var(--card-bg);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(31, 64, 76, 0.08);
  color: var(--text-color);
  font-size: 17px;
  outline: none;
  transition: all 0.28s ease;
}

.search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 8px 32px rgba(15, 118, 110, 0.14);
}

.search-dropdown {
  position: absolute;
  inset: auto 0 0 0;
  top: calc(100% + 8px);
  border-radius: 20px;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  box-shadow: var(--shadow);
  overflow: hidden;
  z-index: 20;
}

.search-result-item {
  width: 100%;
  padding: 14px 20px;
  border: none;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
}

.search-result-item:hover {
  background: var(--accent-soft);
}

.result-name {
  font-weight: 700;
  color: var(--heading-color);
}

.result-meta {
  margin-top: 2px;
  font-size: 12px;
  color: var(--text-secondary);
}

.home-layout {
  display: flex;
  gap: 18px;
}

.home-sidebar {
  position: relative;
  z-index: 10;
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.graph-panel {
  position: relative;
  z-index: 10;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 720px;
  padding: 20px;
  border-radius: 24px;
  border: 1px solid var(--graph-border);
  background: var(--graph-bg);
  box-shadow: var(--graph-shadow);
  animation: panelIn 0.5s ease-out;
}

.panel {
  padding: 16px;
}

.panel-title {
  margin: 0 0 12px;
  font-size: 15px;
  color: var(--heading-color);
}

.panel-note {
  margin: 12px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.metric-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.metric-card {
  padding: 12px;
  border-radius: 16px;
  background: var(--accent-soft);
  border: 1px solid var(--panel-border);
}

.metric-value {
  display: block;
  font-size: 24px;
  font-weight: 800;
  color: var(--accent);
}

.metric-label {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.export-btn {
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: var(--nav-bg);
  color: var(--text-color);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.export-btn:hover {
  background: var(--accent-soft);
  border-color: var(--accent);
}

.export-btns {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.graph-header {
  position: relative;
  z-index: 12;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.graph-header h2 {
  margin: 0;
  font-size: 19px;
  color: var(--graph-heading);
}

.graph-summary {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--graph-muted);
  line-height: 1.6;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--graph-muted);
}

.legend i {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.32);
}

.graph-toolbar {
  position: relative;
  z-index: 12;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 14px;
  border-radius: 16px;
  background: var(--graph-toolbar-bg);
  border: 1px solid var(--graph-toolbar-border);
}

.toolbar-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 120px;
}

.toolbar-group.wide {
  flex: 1 1 280px;
}

.toolbar-group.compact {
  max-width: 240px;
}

.toolbar-label {
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--graph-muted);
}

.toolbar-copy {
  margin: 0;
  font-size: 12px;
  color: var(--graph-muted);
  line-height: 1.5;
}

.toolbar-actions {
  margin-left: auto;
}

.pill-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pill {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--graph-pill-border);
  background: var(--graph-pill-bg);
  color: var(--graph-pill-text);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s ease;
}

.pill:hover {
  border-color: var(--graph-pill-hover-border);
}

.pill.active {
  border-color: var(--graph-pill-active-border);
  background: var(--graph-pill-active-bg);
  color: var(--graph-pill-active-text);
  font-weight: 600;
}

.reset-btn {
  background: var(--graph-pill-bg);
}

.graph-canvas {
  position: relative;
  width: 100%;
  flex: 1;
  min-height: 620px;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--graph-canvas-border);
  background: #1a1a1a;
}

.graph-loading {
  position: relative;
  z-index: 12;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 420px;
  height: 100%;
  gap: 16px;
  color: var(--graph-muted);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 3px solid var(--panel-border);
  border-top-color: var(--accent);
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes pageIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes panelIn {
  from {
    opacity: 0;
    transform: scale(0.98);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 1080px) {
  .home-layout {
    flex-direction: column;
  }

  .home-sidebar {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
  }
}

@media (max-width: 860px) {
  .home-sidebar {
    grid-template-columns: 1fr;
  }

  .graph-header {
    flex-direction: column;
  }

  .graph-canvas {
    min-height: 520px;
  }
}
</style>

<template>
  <div class="home-page">
    <div class="home-hero">
      <div class="search-section">
        <div class="search-wrapper">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input v-model="searchQuery" type="text" class="search-input" placeholder="搜索鸟类名称、学名或关系关键词…" @input="handleSearch" />
        </div>
        <div v-if="searchResults.length" class="search-dropdown">
          <div v-for="item in searchResults" :key="item.id" class="search-result-item" @click="goToBird(item)">
            <div class="result-name">{{ item.name }}</div>
            <div class="result-meta">{{ item.englishName }} · {{ typeLabelMap[item.type] }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="home-layout">
      <div class="home-sidebar">
        <!-- 探索模式下的路径查询 -->
        <template v-if="graphMode === 'explore'">
          <GraphAnalyzer @path-found="onPathFound" @clear-path="onClearPath" />
        </template>
        <!-- 导出面板：两种模式显示不同按钮 -->
        <div class="panel export-panel">
          <h3 class="analyzer-title">导出</h3>
          <div class="export-btns">
            <button v-if="graphMode === 'academic'" class="export-btn highlight-btn" @click="exportAcademicPNG">
              下载高清图 (PNG)
            </button>
            <button v-if="graphMode === 'explore'" class="export-btn" @click="exportPNG(containerRef)">PNG 截图</button>
            <button class="export-btn" @click="exportJSON(store.nodes, store.links)">JSON 数据</button>
            <button class="export-btn" @click="exportGraphML(store.nodes, store.links)">GraphML</button>
          </div>
        </div>
      </div>

      <section class="graph-panel">
        <div class="graph-header">
          <div>
            <h2>
              <template v-if="graphMode === 'academic'">发表级学术网络图</template>
              <template v-else>鸟类知识图谱</template>
            </h2>
            <p class="graph-summary">{{ graphMode === 'academic' ? academicSummary : graphSummary }}</p>
          </div>
          <div class="legend">
            <span v-for="item in legendItems" :key="item.label">
              <i :style="{ backgroundColor: item.color }"></i>{{ item.label }}
            </span>
          </div>
        </div>

        <div class="graph-toolbar">
          <!-- 视图模式切换 -->
          <div class="toolbar-group">
            <span class="toolbar-label">视图</span>
            <div class="pill-group">
              <button class="pill" :class="{ active: graphMode === 'explore' }" @click="graphMode = 'explore'">探索模式</button>
              <button class="pill" :class="{ active: graphMode === 'academic' }" @click="graphMode = 'academic'">学术模式</button>
            </div>
          </div>

          <!-- 探索模式下的控制项 -->
          <template v-if="graphMode === 'explore'">
            <div class="toolbar-group">
              <span class="toolbar-label">鸟类密度</span>
              <div class="pill-group">
                <button v-for="opt in graphLimitOptions" :key="opt.value" type="button"
                  class="pill" :class="{ active: graphBirdLimit === opt.value }"
                  @click="graphBirdLimit = opt.value">{{ opt.label }}</button>
              </div>
            </div>
            <div class="toolbar-group">
              <span class="toolbar-label">标签</span>
              <div class="pill-group">
                <button v-for="opt in labelModeOptions" :key="opt.value" type="button"
                  class="pill" :class="{ active: labelMode === opt.value }"
                  @click="labelMode = opt.value">{{ opt.label }}</button>
              </div>
            </div>
            <div class="toolbar-group wide">
              <span class="toolbar-label">显示实体</span>
              <div class="pill-group">
                <button v-for="item in filterableTypeItems" :key="item.type" type="button"
                  class="pill" :class="{ active: activeContextTypes.includes(item.type) }"
                  @click="toggleContextType(item.type)">{{ item.label }}</button>
              </div>
            </div>
          </template>

          <div class="toolbar-actions">
            <button v-if="graphMode === 'explore'" class="pill reset-btn" @click="resetGraphControls">重置</button>
          </div>
        </div>

        <div ref="containerRef" class="graph-canvas">
          <!-- 探索模式：Sigma.js 画布 -->
          <SigmaCanvas v-if="graphMode === 'explore'"
            :bird-limit="graphBirdLimit"
            :label-mode="labelMode"
            :focus-entity-id="focusEntityId"
            :active-types="activeContextTypes"
            :highlight-path="highlightPath"
            :dark-mode="uiStore.darkMode"
            @node-click="handleNodeClick"
          />
          <!-- 学术模式：D3 发表级学术网络图 -->
          <AcademicGraph v-if="graphMode === 'academic'" ref="academicGraphRef" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGraphStore } from '../stores/graphStore.js'
import { useUIStore } from '../stores/uiStore.js'
import SigmaCanvas from '../graph/SigmaCanvas.vue'
import AcademicGraph from '../graph/AcademicGraph.vue'
import GraphAnalyzer from '../graph/GraphAnalyzer.vue'
import { useGraphExport } from '../composables/useGraphExport.js'

const router = useRouter()
const store = useGraphStore()
const uiStore = useUIStore()
const { exportPNG, exportJSON, exportGraphML } = useGraphExport()

const containerRef = ref(null)
const academicGraphRef = ref(null)
const searchQuery = ref('')
const searchResults = ref([])

// 模式切换
const graphMode = ref('explore')

// 探索模式控制项
const graphBirdLimit = ref(80)
const labelMode = ref('smart')
const activeContextTypes = ref(['location', 'habitat', 'status', 'threat'])
const focusEntityId = ref('')
const highlightPath = ref([])

const typeLabelMap = { bird: '鸟类', location: '地点', habitat: '栖息地', status: '保护等级', threat: '威胁因素', taxonomy: '分类单元' }

const legendItems = [
  { type: 'bird', label: '鸟类', color: '#7f8fa6' }, { type: 'location', label: '地点', color: '#6f9e98' },
  { type: 'habitat', label: '栖息地', color: '#8da56b' }, { type: 'status', label: '保护等级', color: '#b59a62' },
  { type: 'threat', label: '威胁因素', color: '#9f727a' }, { type: 'taxonomy', label: '分类单元', color: '#8b84ab' }
]

const graphLimitOptions = [
  { value: 40, label: '40' }, { value: 80, label: '80' },
  { value: 160, label: '160' }, { value: 0, label: '全部' }
]

const labelModeOptions = [
  { value: 'smart', label: '智能' }, { value: 'birds', label: '仅鸟类' }, { value: 'all', label: '全部' }
]

const filterableTypeItems = legendItems.filter(item => item.type !== 'bird')

const graphSummary = computed(() => {
  if (!store.nodes.length) return '正在加载图谱数据。'
  return `${store.nodeCount} 个节点 · ${store.linkCount} 条关系`
})

const academicSummary = computed(() => {
  const birds = store.nodes.filter(n => n.type === 'bird').length
  return `${birds} 种鸟类 · IUCN 保护等级着色 · 力导向布局`
})

function handleSearch() {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) { searchResults.value = []; return }
  searchResults.value = store.nodes.filter(n => n.type === 'bird').filter(n => {
    const fields = [n.name, n.englishName, n.latinName].filter(Boolean)
    return fields.some(f => f.toLowerCase().includes(q))
  }).slice(0, 8)
}

function goToBird(item) {
  if (item.type === 'bird') router.push(`/bird/${item.id}`)
  searchQuery.value = item.name
  searchResults.value = []
}

function handleNodeClick(node) {
  if (node.type === 'bird') router.push(`/bird/${node.id}`)
  else focusEntityId.value = node.id
}

function toggleContextType(type) {
  if (activeContextTypes.value.includes(type))
    activeContextTypes.value = activeContextTypes.value.filter(t => t !== type)
  else activeContextTypes.value = [...activeContextTypes.value, type]
}

function resetGraphControls() {
  graphBirdLimit.value = 80; labelMode.value = 'smart'
  activeContextTypes.value = ['location', 'habitat', 'status', 'threat']
  focusEntityId.value = ''; highlightPath.value = []
}

function onPathFound(path) { highlightPath.value = path }
function onClearPath() { highlightPath.value = [] }

// 学术模式高清导出
function exportAcademicPNG() {
  academicGraphRef.value?.exportHighResPNG()
}

onMounted(async () => {
  if (!store.loaded) await store.loadData()
})
</script>

<style scoped>
.home-page { display: flex; flex-direction: column; gap: 18px; }
.home-hero { display: flex; justify-content: center; padding: 28px 18px 0; }
.search-section { position: relative; width: 100%; max-width: 680px; }
.search-wrapper { position: relative; display: flex; align-items: center; }
.search-icon { position: absolute; left: 20px; width: 22px; height: 22px; color: rgba(18, 48, 59, 0.4); pointer-events: none; }
.search-input { width: 100%; padding: 18px 24px 18px 56px; border: 2px solid rgba(15, 118, 110, 0.2); border-radius: 999px; background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px); font-size: 17px; outline: none; transition: all 0.3s ease; box-shadow: 0 4px 20px rgba(31, 64, 76, 0.08); }
.search-input:focus { border-color: #0f766e; box-shadow: 0 8px 32px rgba(15, 118, 110, 0.15); }
.search-dropdown { position: absolute; top: 100%; left: 0; right: 0; margin-top: 8px; border-radius: 20px; background: rgba(255, 255, 255, 0.96); backdrop-filter: blur(20px); border: 1px solid rgba(18, 48, 59, 0.1); box-shadow: 0 20px 45px rgba(31, 64, 76, 0.15); overflow: hidden; z-index: 100; }
.search-result-item { padding: 14px 20px; cursor: pointer; transition: background 0.15s ease; }
.search-result-item:hover { background: rgba(15, 118, 110, 0.08); }
.result-name { font-weight: 600; color: #12303b; }
.result-meta { font-size: 12px; color: rgba(18, 48, 59, 0.55); margin-top: 2px; }

.home-layout { display: flex; gap: 18px; }
.home-sidebar { width: 280px; flex-shrink: 0; display: flex; flex-direction: column; gap: 14px; }

.graph-panel {
  flex: 1; display: flex; flex-direction: column; gap: 14px;
  padding: 20px; border-radius: 24px;
  border: 1px solid var(--graph-border);
  background: var(--graph-bg);
  box-shadow: var(--graph-shadow);
}

.graph-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.graph-header h2 { margin: 0; font-size: 19px; color: var(--graph-heading); }
.graph-summary { margin: 4px 0 0; font-size: 13px; color: var(--graph-muted); }
.legend { display: flex; flex-wrap: wrap; gap: 10px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--graph-muted); }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 999px; border: 1px solid rgba(255,255,255,0.32); }

.graph-toolbar {
  display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-start;
  padding: 12px 14px; border-radius: 16px;
  background: var(--graph-toolbar-bg);
  border: 1px solid var(--graph-toolbar-border);
}
.toolbar-group { display: flex; flex-direction: column; gap: 6px; min-width: 90px; }
.toolbar-group.wide { flex: 1 1 240px; }
.toolbar-label { font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--graph-muted); }
.toolbar-actions { display: flex; gap: 6px; align-items: flex-end; margin-left: auto; }
.pill-group { display: flex; flex-wrap: wrap; gap: 6px; }
.pill {
  padding: 6px 12px; border-radius: 999px; border: 1px solid var(--graph-pill-border);
  background: var(--graph-pill-bg); color: var(--graph-pill-text); cursor: pointer;
  font-size: 12px; transition: all 0.15s ease;
}
.pill:hover { border-color: var(--graph-pill-hover-border); }
.pill.active {
  border-color: var(--graph-pill-active-border);
  background: var(--graph-pill-active-bg);
  color: var(--graph-pill-active-text);
  font-weight: 600;
}
.reset-btn { margin-left: 4px; background: var(--graph-pill-bg); border-color: var(--graph-pill-border); }

.graph-canvas { width: 100%; flex: 1; min-height: 520px; border-radius: 16px; overflow: hidden; border: 1px solid var(--graph-canvas-border); position: relative; }

.export-panel { padding: 16px; }
.analyzer-title { margin: 0 0 12px; font-size: 15px; color: var(--heading-color); }
.export-btns { display: flex; flex-direction: column; gap: 8px; }
.export-btn { padding: 10px 14px; border-radius: 12px; border: 1px solid var(--panel-border); background: var(--nav-bg); color: var(--text-color); font-size: 13px; cursor: pointer; text-align: left; transition: all 0.2s; }
.export-btn:hover { background: var(--accent-soft); border-color: var(--accent); }
.highlight-btn { background: var(--accent); color: #fff; border-color: var(--accent); font-weight: 700; }
.highlight-btn:hover { opacity: 0.9; }

@media (max-width: 960px) {
  .home-layout { flex-direction: column; }
  .home-sidebar { width: 100%; flex-direction: row; flex-wrap: wrap; }
  .home-sidebar > * { flex: 1; min-width: 200px; }
}
</style>

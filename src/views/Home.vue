<template>
  <div class="home-page" :class="{ 'home-page--migration': isMigrationMode }">
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
            <div v-for="card in homeMetricCards" :key="card.label" class="metric-card">
              <span class="metric-value">{{ card.value }}</span>
              <span class="metric-label">{{ card.label }}</span>
            </div>
          </div>
          <p class="panel-note">{{ loadSummary }}</p>
        </section>

        <section v-if="focusedDisplayNode" class="panel node-detail-panel">
          <h3 class="panel-title">数据点信息</h3>
          <div class="node-detail-head">
            <span>{{ focusedNodeType }}</span>
            <strong>{{ focusedNodeName }}</strong>
            <small v-if="focusedNodeSubtitle">{{ focusedNodeSubtitle }}</small>
          </div>
          <div class="node-detail-grid">
            <span>坐标</span>
            <strong>{{ focusedCoordinateLabel }}</strong>
            <span>连接</span>
            <strong>{{ focusedNeighborCount }} 条</strong>
          </div>
          <p v-if="focusedNodeSummary" class="panel-note">{{ focusedNodeSummary }}</p>
          <p v-if="focusedLocationList" class="panel-note highlight">关联栖息地：{{ focusedLocationList }}</p>
          <button
            v-if="canOpenFocusedDetail"
            type="button"
            class="detail-link-btn"
            @click="openFocusedDetail"
          >
            查看详情
          </button>
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
            <h2>{{ isMigrationMode ? '全球鸟类迁徙图' : '3D 分片异步鸟类知识图谱' }}</h2>
            <p class="graph-summary">{{ graphSummary }}</p>
          </div>
          <div class="legend">
            <span v-for="item in legendItems" :key="item.label">
              <i :style="{ backgroundColor: item.color }"></i>{{ item.label }}
            </span>
          </div>
        </div>

        <div v-if="!isMigrationMode" class="graph-toolbar">
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
          <div class="toolbar-group taxonomy-toolbar">
            <span class="toolbar-label">分类层级</span>
            <div class="pill-group">
              <button
                v-for="item in taxonomyLevelItems"
                :key="item.level"
                type="button"
                class="pill"
                :class="{ active: activeTaxonomyLevels.includes(item.level) }"
                @click="toggleTaxonomyLevel(item.level)"
              >
                {{ item.label }}
              </button>
            </div>
          </div>
          <div class="toolbar-group compact">
            <span class="toolbar-label">颜色分类</span>
            <p class="toolbar-copy">原实体筛选保留；目/科/属/种为新增分类层级筛选。</p>
          </div>
          <div class="toolbar-actions">
            <button type="button" class="pill reset-btn" @click="resetContextFilters">重置视图</button>
          </div>
        </div>

        <div ref="containerRef" class="graph-canvas">
          <div v-if="showInitialLoading" class="graph-loading">
            <div class="loading-spinner"></div>
            <p>{{ isMigrationMode ? '正在加载全球观测点与栖息地连接…' : '正在加载搜索索引与轻量总览图…' }}</p>
          </div>
          <template v-else>
            <button
              v-if="focusedNodeId"
              class="focus-back-btn"
              @click="clearFocus"
            >
              ← 返回全图
            </button>
            <div v-if="focusedNodeId" class="focus-info">
              {{ focusedNodeName }} {{ focusedNodeType }} · {{ focusedNeighborCount }} 个关联
            </div>
            <MigrationGlobe
              v-if="isMigrationMode"
              :center-node-id="centerNodeId"
              @node-click="handleNodeClick"
            />
            <SigmaCanvas
              v-else
              :active-types="activeContextTypes"
              :active-taxonomy-levels="activeTaxonomyLevels"
              :dark-mode="uiStore.darkMode"
              :center-node-id="centerNodeId"
              :focused-node-id="focusedNodeId"
              @node-click="handleNodeClick"
            />
          </template>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import MigrationGlobe from '../graph/MigrationGlobe.vue'
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
const activeContextTypes = ref(['taxonomy', 'location', 'habitat', 'status', 'threat'])
const activeTaxonomyLevels = ref(['order', 'family'])
const centerNodeId = ref('')
const focusedNodeId = ref('')
const selectedGlobeNode = ref(null)
const isMigrationMode = computed(() => uiStore.darkMode)
const maxMigrationRoutes = 320
const maxMigrationLocationNodes = 160
const maxLocationsPerBird = 4

const focusedNode = computed(() => store.getNodeById(focusedNodeId.value))
const focusedDisplayNode = computed(() => focusedNode.value || selectedGlobeNode.value)
const focusedNodeName = computed(() => focusedDisplayNode.value?.name || focusedDisplayNode.value?.id || '')
const focusedNodeType = computed(() => {
  const typeLabels = { bird: '鸟类', location: '地点', habitat: '栖息地', status: '保护等级', threat: '威胁因素', taxonomy: '分类' }
  return typeLabels[focusedDisplayNode.value?.type] || ''
})
const focusedNeighborCount = computed(() => store.getIncidentLinks(focusedNodeId.value).length)
const focusedNodeSubtitle = computed(() => {
  const node = focusedDisplayNode.value
  if (!node) return ''
  return [node.englishName, node.latinName].filter(Boolean).join(' · ')
})
const focusedCoordinateLabel = computed(() => {
  const node = focusedDisplayNode.value
  if (!node || node.lat == null || node.lng == null) return '暂无坐标'
  return `${Number(node.lat).toFixed(2)}, ${Number(node.lng).toFixed(2)}`
})
const focusedNodeSummary = computed(() => {
  const node = focusedDisplayNode.value
  return node?.shortSummary || node?.summary || ''
})
const focusedLocationList = computed(() => {
  const locations = focusedDisplayNode.value?.locations || []
  return locations.slice(0, 4).join('、')
})
const canOpenFocusedDetail = computed(() => {
  const node = focusedDisplayNode.value
  if (!node) return false
  if (node.type === 'bird') return Boolean(node.id)
  if (node.type === 'location') return Boolean(store.getNodeById(node.id))
  return false
})

const loadedGeoBirdCount = computed(() => store.birdNodes.filter(node => node.lat != null && node.lng != null).length)
const graphObservationPointCount = computed(() => {
  const points = new Set()
  store.nodes.forEach(node => {
    if ((node.type === 'bird' || node.type === 'location') && node.lat != null && node.lng != null) {
      points.add(`${Number(node.lat).toFixed(2)},${Number(node.lng).toFixed(2)}`)
    }
  })
  return points.size
})

const locationByName = computed(() => {
  const locationByName = new Map(store.summaryLocations
    .filter(location => location.lat != null && location.lng != null)
    .map(location => [location.name, location]))
  store.locationNodes
    .filter(location => location.lat != null && location.lng != null)
    .forEach(location => locationByName.set(location.name, location))
  return locationByName
})

const migrationObservationPointCount = computed(() => {
  const points = new Set()
  let routeCount = 0

  for (const bird of store.birdNodes) {
    if (bird.lat == null || bird.lng == null) continue
    points.add(`${Number(bird.lat).toFixed(2)},${Number(bird.lng).toFixed(2)}`)
    if (routeCount >= maxMigrationRoutes) continue
    const locationNames = Array.isArray(bird.locations) ? bird.locations : []
    for (const locationName of locationNames.slice(0, maxLocationsPerBird)) {
      if (routeCount >= maxMigrationRoutes) break
      const location = locationByName.value.get(locationName)
      if (!location) continue
      const latDelta = Math.abs(Number(bird.lat) - Number(location.lat))
      const lngDelta = Math.abs(Number(bird.lng) - Number(location.lng))
      if (latDelta + lngDelta <= 2) continue
      points.add(`${Number(location.lat).toFixed(2)},${Number(location.lng).toFixed(2)}`)
      routeCount += 1
    }
  }

  Array.from(locationByName.value.values())
    .sort((left, right) => String(left.name || left.id).localeCompare(String(right.name || right.id), 'zh-Hans-CN'))
    .slice(0, maxMigrationLocationNodes)
    .forEach(location => {
      points.add(`${Number(location.lat).toFixed(2)},${Number(location.lng).toFixed(2)}`)
    })

  return Math.max(graphObservationPointCount.value, points.size)
})

const observationPointCount = computed(() => {
  return isMigrationMode.value ? migrationObservationPointCount.value : graphObservationPointCount.value
})

const migrationRouteCount = computed(() => {
  const actualRouteCount = store.links.filter(link => {
    const source = store.getNodeById(link.source)
    const target = store.getNodeById(link.target)
    const isBirdToPlace = (
      (source?.type === 'bird' && target?.type === 'location') ||
      (source?.type === 'location' && target?.type === 'bird')
    )
    return isBirdToPlace && ['distributed_in', 'lives_in'].includes(link.relation)
  }).length

  let summaryRouteCount = 0
  for (const bird of store.birdNodes) {
    const locationNames = Array.isArray(bird.locations) ? bird.locations : []
    for (const locationName of locationNames.slice(0, maxLocationsPerBird)) {
      const location = locationByName.value.get(locationName)
      if (!location) continue
      const latDelta = Math.abs(Number(bird.lat) - Number(location.lat))
      const lngDelta = Math.abs(Number(bird.lng) - Number(location.lng))
      if (latDelta + lngDelta <= 2) continue
      summaryRouteCount += 1
      if (summaryRouteCount >= maxMigrationRoutes) return Math.max(actualRouteCount, summaryRouteCount)
    }
  }
  return Math.max(actualRouteCount, summaryRouteCount)
})

const nonTaxonomyRelationCount = computed(() => {
  const types = store.meta?.counts?.relationTypes || {}
  let count = 0
  for (const [key, val] of Object.entries(types)) {
    if (!key.startsWith('belongs_to_')) count += val
  }
  return count || 0
})

const topRelationMetrics = computed(() => {
  const labels = {
    distributed_in: '分布关系',
    belongs_to_species: '种分类',
    belongs_to_family: '科分类',
    belongs_to_genus: '属分类',
    belongs_to_order: '目分类',
    lives_in: '栖息关系',
    has_status: '保护等级',
    threatened_by: '威胁关系'
  }
  return Object.entries(store.meta?.counts?.relationTypes || {})
    .filter(([, value]) => Number(value) >= 1000)
    .map(([key, value]) => ({ label: labels[key] || key, value: Number(value) }))
    .sort((left, right) => right.value - left.value)
    .slice(0, 4)
})

const homeMetricCards = computed(() => {
  if (isMigrationMode.value) {
    return [
      { label: '观测点', value: observationPointCount.value },
      { label: '栖息连接', value: migrationRouteCount.value },
      { label: '鸟类物种', value: store.totalBirdCount },
      { label: '数据总关系', value: store.totalRelationCount }
    ].map(card => ({ ...card, value: Number(card.value || 0).toLocaleString() }))
  }

  return topRelationMetrics.value.map(card => ({
    label: card.label,
    value: card.value.toLocaleString()
  }))
})

const legendItems = computed(() => [
  { label: '鸟类', color: '#4FC3F7', mode: 'graph' },
  { label: '地点', color: '#81C784', mode: 'graph' },
  { label: '栖息地', color: '#FFB74D', mode: 'graph' },
  { label: '保护等级', color: '#E57373', mode: 'graph' },
  { label: '威胁因素', color: '#BA68C8', mode: 'graph' },
  { label: '目', color: '#38bdf8', mode: 'graph' },
  { label: '科', color: '#22c55e', mode: 'graph' },
  { label: '属', color: '#f59e0b', mode: 'graph' },
  { label: '种', color: '#ef4444', mode: 'graph' },
  { label: '鸟类观测点', color: '#22d3ee', mode: 'migration' },
  { label: '地点节点', color: '#7cff6b', mode: 'migration' },
  { label: '栖息连接', color: '#7cff6b', mode: 'migration' }
].filter(item => isMigrationMode.value ? item.mode === 'migration' : item.mode === 'graph'))

const taxonomyLevelItems = [
  { level: 'order', label: '目' },
  { level: 'family', label: '科' },
  { level: 'genus', label: '属' },
  { level: 'species', label: '种' }
]

const filterableTypeItems = [
  { type: 'taxonomy', label: '分类' },
  { type: 'location', label: '地点' },
  { type: 'habitat', label: '栖息地' },
  { type: 'status', label: '保护等级' },
  { type: 'threat', label: '威胁因素' }
]

const showInitialLoading = computed(() => !store.loaded || (store.previewLoading && store.nodeCount === 0))

const graphSummary = computed(() => {
  if (!store.loaded) return '首屏正在加载 summary.json 与轻量总览图入口。'
  if (!isMigrationMode.value) {
    if (store.previewLoading && store.nodeCount === 0) {
      return '正在请求 graph_preview.json，并把鸟类与高层分类节点铺到 3D 画布上。'
    }
    if (store.previewLoading) {
      return `轻量总览图正在继续织入，当前已入图 ${store.loadedBirdCount}/${store.totalBirdCount} 种，节点 ${store.nodeCount} 个，关系 ${store.linkCount} 条。`
    }
    if (store.previewLoaded) {
      return `首页轻量总览图已载入全部 ${store.totalBirdCount} 种鸟类和高层分类；点击节点时再按需请求对应分片详情。`
    }
    return `当前画布中已织入 ${store.nodeCount} 个节点、${store.linkCount} 条关系；其中 ${store.loadedBirdCount}/${store.totalBirdCount} 种鸟类已按需载入。`
  }
  if (store.previewLoading && store.nodeCount === 0) {
    return '正在请求 graph_preview.json，并把带坐标的鸟类观测点投射到正交地球仪。'
  }
  if (store.previewLoading) {
    return `迁徙地球仪正在继续织入，当前已定位 ${loadedGeoBirdCount.value}/${store.totalBirdCount} 种，观测点 ${observationPointCount.value} 个。`
  }
  if (store.previewLoaded) {
    return `全球鸟类迁徙图已载入 ${observationPointCount.value} 个观测点与 ${migrationRouteCount.value} 条鸟类-地点连接；点击节点可继续展开分布地点。`
  }
  return `当前画布中已织入 ${observationPointCount.value} 个观测点、${migrationRouteCount.value} 条栖息地连接。`
})

const loadSummary = computed(() => {
  if (!store.loaded) return '首屏只加载轻量搜索索引，不把全量详情属性一次性塞进浏览器内存。'
  if (store.previewLoading && store.nodeCount === 0) {
    return `正在后台加载 graph_preview.json：${store.previewLoadProgress.loaded}/${store.previewLoadProgress.total}，失败 ${store.previewLoadProgress.failed}。`
  }
  if (store.previewLoading) {
    return `正在后台加载 graph_preview.json：${store.previewLoadProgress.loaded}/${store.previewLoadProgress.total}，失败 ${store.previewLoadProgress.failed}。`
  }
  if (store.previewLoaded) {
    return isMigrationMode.value
      ? '首页已经完成全球鸟类迁徙图加载。点击鸟类节点会继续织入局部分布地与关联路径。'
      : '首页已经完成轻量总览加载。点击分类或鸟类节点会继续分层织入邻域。'
  }
  const expandedChunks = Math.max(0, store.loadedChunkCount - 1)
  return isMigrationMode.value
    ? `当前已展开 ${expandedChunks} 个局部邻域。新增地点会变成地球表面的荧光观测点。`
    : `当前已展开 ${expandedChunks} 个局部邻域。重复点击同一节点会继续加深，不需要一次性渲染全量图。`
})

const handleSearch = useDebounceFn(() => {
  const query = searchQuery.value.trim()
  searchResults.value = query ? store.findBirdMatches(query, 8) : []
}, 120)

async function selectSearchResult(item) {
  searchQuery.value = item.name
  searchResults.value = []
  selectedGlobeNode.value = item
  await store.loadNodeChunk(item.id)
  centerNodeId.value = item.id
}

async function handleNodeClick(node, isCenter) {
  selectedGlobeNode.value = node
  store.setActiveNode(node.id)

  if (node.type === 'bird') {
    await store.loadNodeChunk(node.id)
    if (isCenter && node.id === centerNodeId.value) {
      router.push(`/bird/${node.id}`)
      return
    }
    centerNodeId.value = node.id
    focusedNodeId.value = node.id
    return
  }

  if (node.type === 'location') {
    if (store.getNodeById(node.id) || node.expandable) await store.loadNodeChunk(node.id)
    if (isCenter && node.id === centerNodeId.value && store.getNodeById(node.id)) {
      router.push(`/location/${node.id}`)
      return
    }
    centerNodeId.value = node.id
    focusedNodeId.value = node.id
    return
  }

  if (node.type === 'taxonomy') {
    await store.loadNodeChunk(node.id)
    if (isCenter && node.id === centerNodeId.value) {
      centerNodeId.value = ''
      focusedNodeId.value = ''
      store.setActiveNode('')
      return
    }
    centerNodeId.value = node.id
    focusedNodeId.value = node.id
    return
  }

  if (node.expandable) {
    await store.loadNodeChunk(node.id)
    focusedNodeId.value = node.id
    return
  }

  store.requestNodeFocus(node.id)
  focusedNodeId.value = node.id
}

function openFocusedDetail() {
  const node = focusedDisplayNode.value
  if (!node) return
  if (node.type === 'bird') {
    router.push(`/bird/${node.id}`)
    return
  }
  if (node.type === 'location' && store.getNodeById(node.id)) {
    router.push(`/location/${node.id}`)
  }
}

function toggleContextType(type) {
  if (activeContextTypes.value.includes(type)) {
    activeContextTypes.value = activeContextTypes.value.filter(item => item !== type)
    return
  }
  activeContextTypes.value = [...activeContextTypes.value, type]
}

function toggleTaxonomyLevel(level) {
  if (activeTaxonomyLevels.value.includes(level)) {
    const next = activeTaxonomyLevels.value.filter(item => item !== level)
    activeTaxonomyLevels.value = next.length ? next : [level]
    return
  }
  activeTaxonomyLevels.value = [...activeTaxonomyLevels.value, level]
}

function resetContextFilters() {
  activeContextTypes.value = ['taxonomy', 'location', 'habitat', 'status', 'threat']
  activeTaxonomyLevels.value = ['order', 'family']
  centerNodeId.value = ''
  focusedNodeId.value = ''
  selectedGlobeNode.value = null
  store.setActiveNode('')
  store.requestGraphFit()
}

function clearFocus() {
  focusedNodeId.value = ''
  selectedGlobeNode.value = null
}

onMounted(async () => {
  await store.loadInitialData()
  void store.loadGraphPreview()
})
</script>

<style scoped>
.home-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: calc(100vh - 40px);
  padding: 0 0 14px;
  animation: pageIn 0.4s ease-out;
}

.home-page--migration::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 68% 35%, rgba(34, 211, 238, 0.2), transparent 32%),
    radial-gradient(circle at 16% 30%, rgba(124, 255, 107, 0.08), transparent 28%),
    linear-gradient(135deg, #020617 0%, #07111f 46%, #02040a 100%);
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
  color: var(--text-secondary);
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

.search-input::placeholder {
  color: var(--text-secondary);
}

.home-page--migration .search-input {
  border: 1px solid rgba(38, 255, 230, 0.34);
  background: rgba(2, 8, 23, 0.78);
  box-shadow: 0 0 22px rgba(34, 211, 238, 0.16), inset 0 0 18px rgba(38, 255, 230, 0.06);
  color: #d9fff8;
}

.home-page--migration .search-input:focus {
  border-color: #7cff6b;
  box-shadow: 0 0 32px rgba(124, 255, 107, 0.2), inset 0 0 18px rgba(38, 255, 230, 0.08);
}

.home-page--migration .search-input::placeholder {
  color: rgba(217, 255, 248, 0.48);
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

.home-page--migration .search-dropdown {
  background: rgba(2, 8, 23, 0.94);
  border: 1px solid rgba(38, 255, 230, 0.24);
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.42), 0 0 24px rgba(34, 211, 238, 0.14);
}

.home-page--migration .search-result-item:hover {
  background: rgba(38, 255, 230, 0.1);
}

.home-page--migration .result-name {
  color: #d9fff8;
}

.home-page--migration .result-meta {
  color: rgba(217, 255, 248, 0.6);
}

.home-layout {
  position: relative;
  z-index: 1;
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

.home-page--migration .graph-panel {
  padding: 18px;
  border-radius: 8px;
  border: 1px solid rgba(38, 255, 230, 0.18);
  background: linear-gradient(135deg, rgba(2, 6, 23, 0.88), rgba(8, 18, 33, 0.78));
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.48), 0 0 42px rgba(34, 211, 238, 0.1);
}

.home-page--migration .panel {
  border-radius: 8px;
  border: 1px solid rgba(38, 255, 230, 0.18);
  background: linear-gradient(180deg, rgba(2, 8, 23, 0.9), rgba(8, 20, 35, 0.76));
  box-shadow: inset 0 0 22px rgba(38, 255, 230, 0.05), 0 0 24px rgba(34, 211, 238, 0.08);
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

.panel-note.highlight {
  color: var(--accent);
  font-weight: 600;
  padding: 8px 12px;
  border-radius: 10px;
  background: var(--accent-soft);
  border: 1px solid rgba(15, 118, 110, 0.2);
}

.home-page--migration .panel-title {
  color: #d9fff8;
  letter-spacing: 0.04em;
}

.home-page--migration .panel-note {
  color: rgba(217, 255, 248, 0.66);
}

.home-page--migration .panel-note.highlight {
  color: #7cff6b;
  background: rgba(124, 255, 107, 0.08);
  border: 1px solid rgba(124, 255, 107, 0.24);
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

.home-page--migration .metric-card {
  border-radius: 8px;
  background: rgba(2, 8, 23, 0.66);
  border: 1px solid rgba(38, 255, 230, 0.16);
  box-shadow: inset 0 0 16px rgba(34, 211, 238, 0.06);
}

.home-page--migration .metric-value {
  color: #7cff6b;
  text-shadow: 0 0 16px rgba(124, 255, 107, 0.48);
}

.home-page--migration .metric-label {
  color: rgba(217, 255, 248, 0.58);
}

.node-detail-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.node-detail-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.node-detail-head span,
.node-detail-head small,
.node-detail-grid span {
  color: var(--text-secondary);
  font-size: 12px;
}

.node-detail-head strong {
  color: var(--text-color);
  font-size: 18px;
  line-height: 1.35;
}

.node-detail-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 12px;
  padding: 12px;
  border-radius: 8px;
  background: rgba(15, 118, 110, 0.08);
}

.node-detail-grid strong {
  min-width: 0;
  color: var(--text-color);
  font-size: 13px;
  text-align: right;
}

.home-page--migration .node-detail-head strong,
.home-page--migration .node-detail-grid strong {
  color: #d9fff8;
}

.home-page--migration .node-detail-head span,
.home-page--migration .node-detail-head small,
.home-page--migration .node-detail-grid span {
  color: rgba(217, 255, 248, 0.58);
}

.home-page--migration .node-detail-grid {
  border: 1px solid rgba(38, 255, 230, 0.14);
  background: rgba(2, 8, 23, 0.58);
}

.detail-link-btn {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(15, 118, 110, 0.24);
  border-radius: 8px;
  background: rgba(15, 118, 110, 0.12);
  color: var(--accent);
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.detail-link-btn:hover {
  background: rgba(15, 118, 110, 0.2);
  border-color: var(--accent);
}

.home-page--migration .detail-link-btn {
  border-color: rgba(124, 255, 107, 0.28);
  background: rgba(124, 255, 107, 0.08);
  color: #7cff6b;
  box-shadow: inset 0 0 16px rgba(124, 255, 107, 0.04);
}

.home-page--migration .detail-link-btn:hover {
  background: rgba(124, 255, 107, 0.14);
  border-color: #7cff6b;
  box-shadow: 0 0 18px rgba(124, 255, 107, 0.14);
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

.home-page--migration .export-btn {
  border-radius: 8px;
  border: 1px solid rgba(38, 255, 230, 0.2);
  background: rgba(2, 8, 23, 0.7);
  color: #d9fff8;
}

.home-page--migration .export-btn:hover {
  background: rgba(38, 255, 230, 0.1);
  border-color: #26ffe6;
  box-shadow: 0 0 18px rgba(38, 255, 230, 0.16);
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

.home-page--migration .graph-header h2 {
  color: #d9fff8;
  text-shadow: 0 0 18px rgba(34, 211, 238, 0.32);
}

.home-page--migration .graph-summary,
.home-page--migration .legend span {
  color: rgba(217, 255, 248, 0.66);
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

.toolbar-group.taxonomy-toolbar {
  flex: 0 1 250px;
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

.home-page--migration .graph-canvas {
  min-height: 560px;
  border-radius: 8px;
  border: 1px solid rgba(38, 255, 230, 0.2);
  background: #020617;
  box-shadow: inset 0 0 24px rgba(34, 211, 238, 0.08), 0 0 34px rgba(0, 0, 0, 0.34);
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

.focus-back-btn {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 20;
  padding: 10px 20px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: rgba(15, 118, 110, 0.85);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  backdrop-filter: blur(8px);
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.focus-back-btn:hover {
  background: rgba(15, 118, 110, 0.95);
  border-color: rgba(255, 255, 255, 0.4);
}

.focus-info {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  padding: 8px 20px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.65);
  color: #e2e8f0;
  font-size: 13px;
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  pointer-events: none;
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

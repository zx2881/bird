<template>
  <div class="home-page">
    <button class="help-float-btn" @click="helpGuide.open('home')" title="使用说明">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    </button>

    <HelpModal subtitle="3D 知识图谱 · 操作说明">
      <div class="help-section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="7" cy="6" r="3.5"/><circle cx="17" cy="5" r="3"/><circle cx="12" cy="16" r="3.5"/><line x1="7" y1="6" x2="12" y2="16"/><line x1="17" y1="5" x2="12" y2="16"/></svg>
          3D 知识图谱操作
        </h3>
        <ul>
          <li><strong>旋转/缩放：</strong>鼠标拖拽旋转视角，滚轮缩放，右键平移。画布展示了鸟类与分类、地点、栖息地、保护等级等实体的 3D 关联网络。</li>
          <li><strong>点击节点：</strong>点击任意节点织入该实体的一度邻域关系；再次点击中心节点可跳转至详情页查看完整信息。</li>
          <li><strong>搜索鸟类：</strong>顶部搜索框支持中文名、英文名和学名检索，选择匹配结果后自动在画布中心展开该物种。</li>
          <li><strong>上下文过滤：</strong>工具栏可选显示/隐藏分类、地点、栖息地、保护等级、威胁因素等不同类型的节点。</li>
          <li><strong>聚焦模式：</strong>点击节点后进入聚焦视图，显示当前节点的所有关联；点击「返回全图」退出聚焦。</li>
        </ul>
      </div>
      <div class="help-section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
          导出功能
        </h3>
        <ul>
          <li>左侧边栏支持导出当前可见子图：<strong>PNG 截图</strong>保存当前画布视图，<strong>JSON 数据</strong>导出节点与关系，<strong>GraphML</strong>导出为图分析工具可读格式。</li>
        </ul>
      </div>
      <div class="help-section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          加载机制
        </h3>
        <ul>
          <li>首屏仅加载鸟类与界门纲目科的分类骨架，属和种在点击节点后按需织入，避免一次性加载全部数据。</li>
          <li>左侧面板显示当前数据加载状态，包括已入图物种数、节点数和关系数。</li>
        </ul>
      </div>
    </HelpModal>

    <div class="home-hero">
      <div class="home-hero-copy">
        <span class="home-kicker">Avian graph observatory</span>
        <h2>{{ isMigrationMode ? '夜间迁徙观测台' : '鸟类知识图谱控制台' }}</h2>
        <p>{{ isMigrationMode ? '用暗色模式观察地点、物种与迁徙连接的夜间分布。' : '从物种出发，沿着分布地点、栖息地、保护等级和分类层级展开全球鸟类关系。' }}</p>
      </div>
      <div class="search-section">
        <div class="search-shell">
          <span class="search-chip">Search</span>
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
          <span class="search-chip muted">{{ store.totalBirdCount.toLocaleString() }} species</span>
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
        <section class="field-panel">
          <span class="field-label">Current field lens</span>
          <strong>{{ isMigrationMode ? 'Migration atlas' : 'Knowledge network' }}</strong>
          <p>{{ isMigrationMode ? '地球视角用于观察夜间迁徙连接。' : '图谱视角用于展开实体关系与分类层级。' }}</p>
        </section>
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
              <span class="metric-value">{{ nonTaxonomyRelationCount }}</span>
              <span class="metric-label">实体关系</span>
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
            <span class="view-kicker">{{ isMigrationMode ? 'Night migration atlas' : 'Daylight knowledge network' }}</span>
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
import { useHelpGuide } from '../composables/useHelpGuide.js'
import HelpModal from '../components/HelpModal.vue'

const router = useRouter()
const store = useGraphStore()
const uiStore = useUIStore()
const helpGuide = useHelpGuide()
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
const maxMigrationRoutes = 860
const maxMigrationLocationNodes = 560
const maxLocationsPerBird = 3

const focusedNode = computed(() => store.getNodeById(focusedNodeId.value))
const focusedDisplayNode = computed(() => focusedNode.value || selectedGlobeNode.value)
const focusedNodeName = computed(() => focusedDisplayNode.value?.name || focusedDisplayNode.value?.id || '')
const focusedNodeType = computed(() => {
  const typeLabels = { bird: '鸟类', location: '地点', habitat: '栖息地', status: '保护等级', threat: '威胁因素', taxonomy: '分类' }
  return typeLabels[focusedDisplayNode.value?.type] || ''
})
const focusedNeighborCount = computed(() => {
  const node = focusedDisplayNode.value
  if (!node) return 0
  const loadedCount = store.getIncidentLinks(node.id).length
  if (loadedCount) return loadedCount
  if (Array.isArray(node.locations)) return node.locations.length
  if (node.type === 'location') {
    return store.birdNodes.filter(bird => Array.isArray(bird.locations) && bird.locations.includes(node.name)).length
  }
  return 0
})
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
  if (node.type === 'location') return Boolean(node.id)
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
  if (isMigrationMode.value) {
    selectedGlobeNode.value = node
    store.setActiveNode(node.id)
    if (node.type === 'bird') {
      router.push(`/bird/${node.id}`)
      return
    }
    if (node.type === 'location') {
      router.push(`/location/${node.id}`)
      return
    }
  }

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
    return
  }
  if (node.type === 'location') {
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
  setTimeout(() => helpGuide.checkFirstVisit('home'), 800)
})
</script>

<style scoped>
.home-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 24px;
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
  display: grid;
  grid-template-columns: minmax(260px, 0.85fr) minmax(420px, 1.15fr);
  align-items: end;
  gap: 24px;
  padding: 32px 0 0;
}

.home-hero::before {
  content: "";
  position: absolute;
  left: 8%;
  top: 24px;
  width: 180px;
  height: 70px;
  opacity: 0.22;
  pointer-events: none;
  color: var(--accent);
  background:
    radial-gradient(circle at 10% 58%, currentColor 0 2px, transparent 2.5px),
    radial-gradient(circle at 38% 32%, currentColor 0 2px, transparent 2.5px),
    radial-gradient(circle at 68% 50%, currentColor 0 2px, transparent 2.5px),
    linear-gradient(16deg, transparent 0 18%, currentColor 18.3% 19.2%, transparent 19.5% 100%),
    linear-gradient(-10deg, transparent 0 45%, currentColor 45.3% 46.2%, transparent 46.5% 100%);
}

.home-hero-copy {
  position: relative;
  padding: 30px 30px 28px;
  border: 1px solid var(--panel-border);
  border-radius: 24px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--accent) 14%, transparent), transparent 44%),
    var(--card-bg);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.home-hero-copy::after {
  content: "";
  position: absolute;
  right: -42px;
  bottom: -62px;
  width: 190px;
  height: 150px;
  border: 2px solid color-mix(in srgb, var(--accent) 42%, transparent);
  border-left-color: transparent;
  border-bottom-color: transparent;
  border-radius: 60% 82% 42% 76%;
  transform: rotate(-18deg);
  opacity: 0.32;
}

.home-kicker {
  display: inline-flex;
  margin-bottom: 12px;
  color: var(--accent);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.home-hero-copy h2 {
  position: relative;
  z-index: 1;
  margin: 0;
  color: var(--heading-color);
  font-size: clamp(30px, 3.4vw, 52px);
  font-weight: 900;
  line-height: 1.02;
}

.home-hero-copy p {
  position: relative;
  z-index: 1;
  max-width: 58ch;
  margin: 14px 0 0;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.72;
}

.search-section {
  position: relative;
  z-index: 12;
  width: 100%;
  max-width: none;
}

.search-section::before {
  content: "";
  display: none;
}

.search-shell {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--panel-border);
  border-radius: 24px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--accent-2) 12%, transparent), transparent 46%),
    var(--surface-strong);
  box-shadow: var(--shadow);
}

.search-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 16px;
  border-radius: 14px;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid color-mix(in srgb, var(--accent) 18%, transparent);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.11em;
  text-transform: uppercase;
  white-space: nowrap;
}

.search-chip.muted {
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--card-bg) 82%, transparent);
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
  padding: 18px 22px 18px 58px;
  border: 1px solid color-mix(in srgb, var(--accent) 22%, var(--panel-border));
  border-radius: 16px;
  background: color-mix(in srgb, var(--card-bg) 92%, transparent);
  backdrop-filter: blur(8px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
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
  display: grid;
  grid-template-columns: minmax(300px, 360px) minmax(0, 1fr);
  gap: 22px;
}

.home-sidebar {
  position: relative;
  z-index: 10;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field-panel {
  position: relative;
  overflow: hidden;
  padding: 22px;
  border-radius: 24px;
  color: oklch(0.96 0.018 170);
  background:
    radial-gradient(circle at 85% 18%, rgba(250, 204, 21, 0.18), transparent 28%),
    linear-gradient(135deg, #0a2f35, #0f766e 54%, #12303b);
  box-shadow: 0 22px 58px rgba(15, 118, 110, 0.24);
}

.field-panel::after {
  content: "";
  position: absolute;
  right: -30px;
  bottom: -36px;
  width: 132px;
  height: 92px;
  border: 2px solid rgba(255, 255, 255, 0.28);
  border-left-color: transparent;
  border-bottom-color: transparent;
  border-radius: 62% 82% 48% 72%;
  transform: rotate(-18deg);
}

.field-label {
  display: block;
  margin-bottom: 12px;
  color: rgba(236, 253, 245, 0.68);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.field-panel strong {
  display: block;
  font-size: 25px;
  line-height: 1.08;
}

.field-panel p {
  position: relative;
  z-index: 1;
  margin: 12px 0 0;
  color: rgba(236, 253, 245, 0.75);
  font-size: 13px;
  line-height: 1.7;
}

.graph-panel {
  position: relative;
  z-index: 10;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 720px;
  padding: 18px;
  border-radius: 24px;
  border: 1px solid var(--graph-border);
  background:
    radial-gradient(circle at 12% 10%, color-mix(in srgb, var(--accent) 16%, transparent), transparent 24%),
    linear-gradient(180deg, rgba(255,255,255,0.62), rgba(255,255,255,0.1)),
    var(--graph-bg);
  box-shadow: var(--graph-shadow);
  animation: panelIn 0.5s ease-out;
}

.panel {
  position: relative;
  padding: 18px;
  overflow: hidden;
}

.panel::after {
  content: "";
  position: absolute;
  inset: 12px 12px auto auto;
  width: 62px;
  height: 22px;
  border-radius: 999px;
  background:
    radial-gradient(circle at 15% 50%, var(--accent) 0 2px, transparent 2.5px),
    radial-gradient(circle at 50% 50%, var(--accent-2) 0 2px, transparent 2.5px),
    radial-gradient(circle at 85% 50%, var(--accent) 0 2px, transparent 2.5px);
  opacity: 0.16;
}

.home-page--migration .graph-panel {
  padding: 18px;
  border-radius: 14px;
  border: 1px solid rgba(38, 255, 230, 0.18);
  background: linear-gradient(135deg, rgba(2, 6, 23, 0.88), rgba(8, 18, 33, 0.78));
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.48), 0 0 42px rgba(34, 211, 238, 0.1);
}

.home-page--migration .panel {
  border-radius: 14px;
  border: 1px solid rgba(38, 255, 230, 0.18);
  background: linear-gradient(180deg, rgba(2, 8, 23, 0.9), rgba(8, 20, 35, 0.76));
  box-shadow: inset 0 0 22px rgba(38, 255, 230, 0.05), 0 0 24px rgba(34, 211, 238, 0.08);
}

.panel-title {
  margin: 0 0 12px;
  font-size: 15px;
  color: var(--heading-color);
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-title::before {
  content: "";
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-soft);
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
  gap: 12px;
}

.metric-card {
  position: relative;
  padding: 16px 14px;
  border-radius: 18px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.32), transparent),
    var(--accent-soft);
  border: 1px solid var(--panel-border);
  overflow: hidden;
}

.metric-card::after {
  content: "";
  position: absolute;
  right: -18px;
  top: -24px;
  width: 72px;
  height: 72px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--accent) 22%, transparent);
}

.metric-value {
  display: block;
  font-size: 30px;
  font-weight: 950;
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
  gap: 18px;
  padding: 18px;
  border-radius: 18px;
  background:
    linear-gradient(120deg, color-mix(in srgb, var(--accent) 12%, transparent), transparent 54%),
    color-mix(in srgb, var(--card-bg) 76%, transparent);
  border: 1px solid var(--panel-border);
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
  border-radius: 14px;
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
  border-radius: 10px;
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
  border-radius: 18px;
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
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: rgba(15, 118, 110, 0.85);
  color: oklch(0.99 0.01 170);
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
  border-radius: 10px;
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
  .home-hero {
    grid-template-columns: 1fr;
  }

  .home-layout {
    grid-template-columns: 1fr;
  }

  .home-sidebar {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
  }
}

@media (max-width: 860px) {
  .search-shell {
    grid-template-columns: 1fr;
  }

  .search-chip {
    justify-content: flex-start;
  }

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

.help-float-btn {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 100;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.9), rgba(124, 58, 237, 0.9));
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.35);
  backdrop-filter: blur(8px);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.help-float-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 24px rgba(139, 92, 246, 0.5);
  border-color: rgba(139, 92, 246, 0.5);
}
.help-float-btn svg {
  width: 22px;
  height: 22px;
}
</style>

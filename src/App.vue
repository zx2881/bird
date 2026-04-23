<template>
  <div class="shell">
    <header class="app-header">
      <div>
        <p class="eyebrow">Global Avian Biodiversity Graph</p>
        <h1>全球鸟类多样性知识探索平台</h1>
        <p class="subtitle">
          以静态知识图谱与地图浏览为前端核心，快速探索全球鸟类分布与保护知识框架。
        </p>
      </div>
    </header>

    <main class="app-main">
      <aside class="sidebar panel">
        <section class="sidebar-section">
          <div class="section-heading">
            <h2>概览</h2>
            <p>{{ overviewCaption }}</p>
          </div>
          <div class="summary-grid">
            <article class="metric-card">
              <span>鸟类</span>
              <strong>{{ metrics.bird }}</strong>
            </article>
            <article class="metric-card">
              <span>地点</span>
              <strong>{{ metrics.location }}</strong>
            </article>
            <article class="metric-card">
              <span>栖息地</span>
              <strong>{{ metrics.habitat }}</strong>
            </article>
            <article class="metric-card">
              <span>关系</span>
              <strong>{{ knowledge.links.length }}</strong>
            </article>
          </div>
        </section>

        <section class="sidebar-section">
          <div class="section-heading">
            <h2>实体搜索</h2>
            <p>支持鸟类或地点</p>
          </div>
          <el-autocomplete
            v-model="searchKeyword"
            class="search-box"
            :fetch-suggestions="querySuggestions"
            value-key="name"
            placeholder="输入鸟类或地点名称"
            clearable
            @select="handleSearchSelect"
          />
          <div class="quick-tags">
            <button
              v-for="item in quickBirds"
              :key="item.id"
              class="quick-tag"
              type="button"
              @click="selectEntity(item)"
            >
              {{ item.name }}
            </button>
          </div>
        </section>

        <section class="sidebar-section">
          <div class="section-heading">
            <h2>实体详情</h2>
            <p>点击图谱节点后同步更新</p>
          </div>
          <div v-if="selectedEntity" class="detail-card">
            <div class="detail-top">
              <div>
                <h3>{{ selectedEntity.name }}</h3>
                <p class="detail-type">{{ typeLabelMap[selectedEntity.type] ?? selectedEntity.type }}</p>
              </div>
              <span
                v-if="selectedEntity.type === 'bird' && selectedEntity.status"
                class="status-chip"
                :class="statusClassMap[selectedEntity.status] ?? 'is-neutral'"
              >
                {{ selectedEntity.status }}
              </span>
            </div>

            <p v-if="selectedEntity.summary" class="detail-summary">
              {{ selectedEntity.summary }}
            </p>

            <dl class="detail-list">
              <template v-if="selectedEntity.type === 'bird'">
                <div class="detail-row">
                  <dt>英文名</dt>
                  <dd>{{ selectedEntity.englishName }}</dd>
                </div>
                <div class="detail-row">
                  <dt>学名</dt>
                  <dd>{{ selectedEntity.latinName }}</dd>
                </div>
                <div class="detail-row">
                  <dt>主要分布</dt>
                  <dd>{{ formatList(selectedEntity.locations) }}</dd>
                </div>
                <div class="detail-row">
                  <dt>栖息地</dt>
                  <dd>{{ formatList(selectedEntity.habitats) }}</dd>
                </div>
                <div class="detail-row">
                  <dt>威胁因素</dt>
                  <dd>{{ formatList(selectedEntity.threats) }}</dd>
                </div>
              </template>
              <template v-else>
                <div class="detail-row">
                  <dt>坐标</dt>
                  <dd>{{ formatCoordinates(selectedEntity) }}</dd>
                </div>
                <div class="detail-row">
                  <dt>关联关系</dt>
                  <dd>{{ relatedFacts.join('；') || '暂无' }}</dd>
                </div>
              </template>
            </dl>
          </div>
          <div v-else class="empty-card">
            请选择图谱中的鸟类或地点节点。
          </div>
        </section>

      </aside>

      <section class="workspace">
        <section class="panel graph-panel">
          <div class="section-heading compact">
            <div>
              <h2>鸟类知识图谱</h2>
              <p>{{ graphSummary }}</p>
            </div>
            <div class="legend">
              <span v-for="item in legendItems" :key="item.label">
                <i :style="{ backgroundColor: item.color }"></i>{{ item.label }}
              </span>
            </div>
          </div>
          <div class="graph-toolbar">
            <div class="graph-toolbar-group">
              <span class="control-label">视图模式</span>
              <div class="pill-group">
                <button
                  v-for="option in graphModeOptions"
                  :key="option.value"
                  type="button"
                  class="control-pill"
                  :class="{ 'is-active': graphMode === option.value }"
                  @click="graphMode = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>

            <div class="graph-toolbar-group">
              <span class="control-label">鸟类密度</span>
              <div class="pill-group">
                <button
                  v-for="option in graphLimitOptions"
                  :key="option.value"
                  type="button"
                  class="control-pill"
                  :class="{ 'is-active': graphBirdLimit === option.value }"
                  @click="graphBirdLimit = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>

            <div class="graph-toolbar-group">
              <span class="control-label">标签策略</span>
              <div class="pill-group">
                <button
                  v-for="option in labelModeOptions"
                  :key="option.value"
                  type="button"
                  class="control-pill"
                  :class="{ 'is-active': labelMode === option.value }"
                  @click="labelMode = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>

            <div class="graph-toolbar-group wide">
              <span class="control-label">外圈实体</span>
              <div class="pill-group">
                <button
                  v-for="item in filterableTypeItems"
                  :key="item.type"
                  type="button"
                  class="control-pill"
                  :class="{ 'is-active': activeContextTypes.includes(item.type) }"
                  @click="toggleContextType(item.type)"
                >
                  {{ item.label }}
                </button>
              </div>
            </div>
          </div>
          <div class="graph-stat-strip">
            <span class="graph-stat-chip">显示 {{ graphSnapshot.nodes.length }} / {{ knowledge.nodes.length }} 个节点</span>
            <span class="graph-stat-chip">显示 {{ graphSnapshot.links.length }} / {{ knowledge.links.length }} 条关系</span>
            <span class="graph-stat-chip">{{ graphModeHint }}</span>
            <button type="button" class="graph-reset" @click="resetGraphControls">重置图谱视图</button>
          </div>
          <div ref="graphRef" class="graph-canvas"></div>
        </section>

        <section class="panel map-panel">
          <div class="section-heading compact">
            <div>
              <h2>分布地图</h2>
              <p>{{ activeLocationText }}</p>
            </div>
            <div class="map-coord">{{ activeCoordinateText }}</div>
          </div>
          <div ref="mapRef" class="map-canvas"></div>
        </section>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import L from 'leaflet'

const graphRef = ref(null)
const mapRef = ref(null)

const knowledge = ref({ meta: null, nodes: [], links: [] })
const selectedEntity = ref(null)
const searchKeyword = ref('')
const activeLocation = ref(null)
const graphMode = ref('overview')
const graphBirdLimit = ref(80)
const labelMode = ref('smart')
const activeContextTypes = ref(['location', 'habitat', 'status', 'threat'])

const typeLabelMap = {
  bird: '鸟类',
  location: '地点',
  habitat: '栖息地',
  status: '保护等级',
  threat: '威胁因素',
  taxonomy: '分类单元'
}

const statusClassMap = {
  CR: 'is-danger',
  EN: 'is-warning',
  VU: 'is-caution',
  NT: 'is-neutral'
}

const graphTheme = {
  background: 'rgba(6, 19, 31, 0.76)',
  label: '#e2e8f0',
  labelMuted: 'rgba(226, 232, 240, 0.76)',
  labelChip: 'rgba(8, 20, 35, 0.78)',
  tooltipBackground: 'rgba(8, 20, 35, 0.96)',
  tooltipBorder: 'rgba(125, 211, 252, 0.24)',
  textBorder: 'rgba(5, 15, 26, 0.92)',
  linkMuted: 'rgba(148, 163, 184, 0.16)'
}

const nodeVisualMap = {
  bird: {
    color: 'rgba(125, 211, 252, 0.72)',
    border: 'rgba(224, 242, 254, 0.52)'
  },
  location: {
    color: 'rgba(110, 231, 183, 0.72)',
    border: 'rgba(220, 252, 231, 0.52)'
  },
  habitat: {
    color: 'rgba(249, 168, 212, 0.72)',
    border: 'rgba(253, 242, 248, 0.5)'
  },
  status: {
    color: 'rgba(252, 211, 77, 0.72)',
    border: 'rgba(254, 249, 195, 0.5)'
  },
  threat: {
    color: 'rgba(251, 113, 133, 0.72)',
    border: 'rgba(255, 228, 230, 0.52)'
  },
  taxonomy: {
    color: 'rgba(196, 181, 253, 0.72)',
    border: 'rgba(237, 233, 254, 0.52)'
  }
}

const legendItems = [
  { type: 'bird', label: '鸟类', color: nodeVisualMap.bird.color },
  { type: 'location', label: '地点', color: nodeVisualMap.location.color },
  { type: 'habitat', label: '栖息地', color: nodeVisualMap.habitat.color },
  { type: 'status', label: '保护等级', color: nodeVisualMap.status.color },
  { type: 'threat', label: '威胁因素', color: nodeVisualMap.threat.color },
  { type: 'taxonomy', label: '分类单元', color: nodeVisualMap.taxonomy.color }
]

const graphModeOptions = [
  { value: 'overview', label: '全局概览' },
  { value: 'focus', label: '实体聚焦' }
]

const graphLimitOptions = [
  { value: 40, label: '40' },
  { value: 80, label: '80' },
  { value: 160, label: '160' },
  { value: 0, label: '全部' }
]

const labelModeOptions = [
  { value: 'smart', label: '智能标签' },
  { value: 'birds', label: '仅鸟类' },
  { value: 'all', label: '全部显示' }
]

const filterableTypeItems = legendItems.filter((item) => item.type !== 'bird')
const categoryIndex = legendItems.reduce((memo, item, index) => {
  memo[item.type] = index
  return memo
}, {})
const graphColors = ['#a3d2ca', '#056676', '#ea2c62', '#16a596', '#03c4a1', '#f5a25d', '#8cd282', '#32e0c4']

let chartInstance
let mapInstance
let mapMarker

const graphIndexes = computed(() => {
  const nodeMap = new Map()
  const linksByNode = new Map()
  const degreeMap = new Map()

  knowledge.value.nodes.forEach((node) => {
    nodeMap.set(node.id, node)
    linksByNode.set(node.id, [])
    degreeMap.set(node.id, 0)
  })

  knowledge.value.links.forEach((link, index) => {
    const enrichedLink = {
      ...link,
      key: `${link.source}__${link.relation}__${link.target}__${index}`
    }

    if (!linksByNode.has(link.source)) {
      linksByNode.set(link.source, [])
      degreeMap.set(link.source, 0)
    }
    if (!linksByNode.has(link.target)) {
      linksByNode.set(link.target, [])
      degreeMap.set(link.target, 0)
    }

    linksByNode.get(link.source).push(enrichedLink)
    linksByNode.get(link.target).push(enrichedLink)
    degreeMap.set(link.source, (degreeMap.get(link.source) ?? 0) + 1)
    degreeMap.set(link.target, (degreeMap.get(link.target) ?? 0) + 1)
  })

  return { nodeMap, linksByNode, degreeMap }
})

const birdNodes = computed(() => knowledge.value.nodes.filter((item) => item.type === 'bird'))
const searchableNodes = computed(() =>
  knowledge.value.nodes.filter((item) => item.type === 'bird' || item.type === 'location')
)

const rankedBirds = computed(() =>
  [...birdNodes.value].sort((left, right) => {
    const degreeDiff = getNodeDegree(right.id) - getNodeDegree(left.id)
    if (degreeDiff !== 0) {
      return degreeDiff
    }
    return left.name.localeCompare(right.name, 'zh-Hans-CN')
  })
)

const quickBirds = computed(() => rankedBirds.value.slice(0, 6))

const metrics = computed(() => {
  const counts = {
    bird: 0,
    location: 0,
    habitat: 0,
    status: 0,
    threat: 0,
    taxonomy: 0
  }

  knowledge.value.nodes.forEach((node) => {
    if (counts[node.type] !== undefined) {
      counts[node.type] += 1
    }
  })

  return counts
})

const overviewCaption = computed(() => {
  if (!knowledge.value.nodes.length) {
    return '正在载入静态知识图谱'
  }

  return `${metrics.value.bird} 种鸟类 · ${metrics.value.location} 个地点 · ${knowledge.value.links.length} 条关系`
})

const relatedFacts = computed(() => {
  if (!selectedEntity.value) {
    return []
  }

  return knowledge.value.links
    .filter((link) => link.source === selectedEntity.value.id || link.target === selectedEntity.value.id)
    .slice(0, 12)
    .map((link) => {
      const source = getNodeById(link.source)
      const target = getNodeById(link.target)
      return `${source?.name ?? link.source} ${link.relation} ${target?.name ?? link.target}`
    })
})

const activeLocationText = computed(() => {
  if (!activeLocation.value) {
    return '点击地点节点后，地图会自动跳转到对应区域。'
  }

  return `当前定位：${activeLocation.value.name}`
})

const activeCoordinateText = computed(() => {
  if (!activeLocation.value) {
    return '坐标未锁定'
  }

  return formatCoordinates(activeLocation.value)
})

const graphSnapshot = computed(() => {
  const enabledContextTypes = new Set(activeContextTypes.value)
  const selectedId = selectedEntity.value?.id ?? ''

  let visibleNodeIds =
    graphMode.value === 'focus'
      ? buildFocusNodeIds(enabledContextTypes)
      : buildOverviewNodeIds(enabledContextTypes)

  if (!visibleNodeIds.size && rankedBirds.value.length) {
    visibleNodeIds = buildFallbackNodeIds(enabledContextTypes)
  }

  const visibleLinks = knowledge.value.links.filter((link) => {
    if (!visibleNodeIds.has(link.source) || !visibleNodeIds.has(link.target)) {
      return false
    }

    const source = getNodeById(link.source)
    const target = getNodeById(link.target)
    if (!source || !target) {
      return false
    }

    const sourceEnabled = source.type === 'bird' || enabledContextTypes.has(source.type) || source.id === selectedId
    const targetEnabled = target.type === 'bird' || enabledContextTypes.has(target.type) || target.id === selectedId
    return sourceEnabled && targetEnabled
  })

  const visibleNodes = knowledge.value.nodes.filter((node) => visibleNodeIds.has(node.id))

  const visibleNodeIdSet = new Set(visibleNodes.map((node) => node.id))
  const filteredLinks = visibleLinks.filter(
    (link) => visibleNodeIdSet.has(link.source) && visibleNodeIdSet.has(link.target)
  )

  const focusNeighborIds = new Set()
  if (selectedId && visibleNodeIdSet.has(selectedId)) {
    focusNeighborIds.add(selectedId)
    filteredLinks.forEach((link) => {
      if (link.source === selectedId) {
        focusNeighborIds.add(link.target)
      }
      if (link.target === selectedId) {
        focusNeighborIds.add(link.source)
      }
    })
  }

  return {
    nodes: visibleNodes,
    links: filteredLinks,
    selectedId,
    focusNeighborIds
  }
})

const graphSummary = computed(() => {
  if (!knowledge.value.nodes.length) {
    return '正在加载图谱数据。'
  }

  const scopeText =
    graphMode.value === 'focus'
      ? `聚焦 ${selectedEntity.value?.name ?? '当前实体'} 的局部关系`
      : `按关联度展示 ${graphBirdLimit.value === 0 ? '全部' : `前 ${graphBirdLimit.value}`} 个鸟类簇`

  return `${scopeText} · ${graphSnapshot.value.nodes.length}/${knowledge.value.nodes.length} 节点 · ${graphSnapshot.value.links.length}/${knowledge.value.links.length} 关系`
})

const graphModeHint = computed(() => {
  if (graphMode.value === 'focus') {
    return '参考示例图谱，聚焦当前实体及其一跳关系'
  }

  if (graphBirdLimit.value === 0) {
    return '已展示全部鸟类簇，适合高性能设备'
  }

  return '概览模式按关联度筛选高价值节点，避免全量拥挤'
})

function getNodeById(id) {
  return graphIndexes.value.nodeMap.get(id)
}

function getNodeDegree(id) {
  return graphIndexes.value.degreeMap.get(id) ?? 0
}

function formatList(values) {
  return Array.isArray(values) && values.length ? values.join('、') : '暂无'
}

function formatCoordinates(entity) {
  if (entity?.lat === null || entity?.lat === undefined || entity?.lng === null || entity?.lng === undefined) {
    return '无空间坐标'
  }

  return `${Number(entity.lat).toFixed(2)}, ${Number(entity.lng).toFixed(2)}`
}

function truncateLabel(text, maxLength = 12) {
  if (!text) {
    return ''
  }

  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text
}

function getNodeVisual(type) {
  return nodeVisualMap[type] ?? nodeVisualMap.taxonomy
}

function getLabelMaxLength(visibleCount, isSelected) {
  if (isSelected) {
    return visibleCount > 180 ? 12 : 16
  }

  if (visibleCount > 220) {
    return 7
  }

  if (visibleCount > 120) {
    return 9
  }

  return 12
}

function querySuggestions(queryString, callback) {
  const keyword = queryString.trim().toLowerCase()
  const matches = !keyword
    ? searchableNodes.value
    : searchableNodes.value.filter((item) => {
        const fields = [item.name, item.englishName, item.latinName].filter(Boolean)
        return fields.some((field) => field.toLowerCase().includes(keyword))
      })

  callback(matches.slice(0, 8))
}

function handleSearchSelect(item) {
  selectEntity(item)
}

function selectEntity(entity) {
  selectedEntity.value = entity
  searchKeyword.value = entity.name

  if (entity.lat !== null && entity.lat !== undefined && entity.lng !== null && entity.lng !== undefined) {
    moveMap(entity)
  }
}

function handleNodeClick(nodeId) {
  const node = getNodeById(nodeId)
  if (!node) {
    return
  }
  selectEntity(node)
}

function toggleContextType(type) {
  if (activeContextTypes.value.includes(type)) {
    activeContextTypes.value = activeContextTypes.value.filter((item) => item !== type)
    return
  }

  activeContextTypes.value = [...activeContextTypes.value, type]
}

function resetGraphControls() {
  graphMode.value = 'overview'
  graphBirdLimit.value = 80
  labelMode.value = 'smart'
  activeContextTypes.value = ['location', 'habitat', 'status', 'threat']
}

function moveMap(entity) {
  if (!mapInstance || entity.lat === null || entity.lat === undefined || entity.lng === null || entity.lng === undefined) {
    return
  }

  activeLocation.value = entity
  mapInstance.flyTo([entity.lat, entity.lng], entity.type === 'bird' ? 5 : 6, {
    animate: true,
    duration: 1.2
  })

  if (!mapMarker) {
    mapMarker = L.marker([entity.lat, entity.lng]).addTo(mapInstance)
  } else {
    mapMarker.setLatLng([entity.lat, entity.lng])
  }

  mapMarker.bindPopup(`<strong>${entity.name}</strong><br/>${typeLabelMap[entity.type] ?? entity.type}`).openPopup()
}

function getIncidentLinks(nodeId) {
  return graphIndexes.value.linksByNode.get(nodeId) ?? []
}

function getLinkOtherNodeId(link, nodeId) {
  return link.source === nodeId ? link.target : link.source
}

function collectBirdContext(nodeId, visibleNodeIds, enabledContextTypes) {
  if (!getNodeById(nodeId)) {
    return
  }

  visibleNodeIds.add(nodeId)

  getIncidentLinks(nodeId).forEach((link) => {
    const otherId = getLinkOtherNodeId(link, nodeId)
    const otherNode = getNodeById(otherId)
    if (!otherNode) {
      return
    }

    if (otherNode.type === 'bird' || enabledContextTypes.has(otherNode.type) || otherNode.id === selectedEntity.value?.id) {
      visibleNodeIds.add(otherId)
    }
  })
}

function buildFallbackNodeIds(enabledContextTypes) {
  const visibleNodeIds = new Set()
  const fallbackBird = rankedBirds.value[0]
  if (!fallbackBird) {
    return visibleNodeIds
  }

  collectBirdContext(fallbackBird.id, visibleNodeIds, enabledContextTypes)
  return visibleNodeIds
}

function buildOverviewNodeIds(enabledContextTypes) {
  const visibleNodeIds = new Set()
  const selected = selectedEntity.value
  const birdLimit = graphBirdLimit.value === 0 ? rankedBirds.value.length : graphBirdLimit.value
  const seedBirdIds = new Set(rankedBirds.value.slice(0, birdLimit).map((bird) => bird.id))

  if (selected) {
    visibleNodeIds.add(selected.id)
    if (selected.type === 'bird') {
      seedBirdIds.add(selected.id)
    } else {
      getIncidentLinks(selected.id).forEach((link) => {
        const otherNode = getNodeById(getLinkOtherNodeId(link, selected.id))
        if (otherNode?.type === 'bird') {
          seedBirdIds.add(otherNode.id)
        }
      })
    }
  }

  seedBirdIds.forEach((birdId) => collectBirdContext(birdId, visibleNodeIds, enabledContextTypes))
  return visibleNodeIds
}

function buildFocusNodeIds(enabledContextTypes) {
  const visibleNodeIds = new Set()
  const seedNode = selectedEntity.value ?? rankedBirds.value[0]

  if (!seedNode) {
    return visibleNodeIds
  }

  visibleNodeIds.add(seedNode.id)

  if (seedNode.type === 'bird') {
    collectBirdContext(seedNode.id, visibleNodeIds, enabledContextTypes)
    return visibleNodeIds
  }

  const linkedBirdIds = new Set()
  getIncidentLinks(seedNode.id).forEach((link) => {
    const otherId = getLinkOtherNodeId(link, seedNode.id)
    const otherNode = getNodeById(otherId)
    if (!otherNode) {
      return
    }

    if (otherNode.type === 'bird' || enabledContextTypes.has(otherNode.type)) {
      visibleNodeIds.add(otherNode.id)
    }

    if (otherNode.type === 'bird') {
      linkedBirdIds.add(otherNode.id)
    }
  })

  linkedBirdIds.forEach((birdId) => collectBirdContext(birdId, visibleNodeIds, enabledContextTypes))
  return visibleNodeIds
}

function shouldShowNodeLabel(node, visibleCount, focusNeighborIds) {
  if (focusNeighborIds.has(node.id)) {
    return true
  }

  if (labelMode.value === 'all') {
    return true
  }

  if (labelMode.value === 'birds') {
    return node.type === 'bird' && (visibleCount <= 160 || getNodeDegree(node.id) >= 5)
  }

  const degree = getNodeDegree(node.id)
  if (node.type === 'bird') {
    if (visibleCount <= 54) {
      return true
    }
    return degree >= 6
  }

  if (node.type === 'location') {
    return visibleCount <= 42 && degree >= 4
  }

  return visibleCount <= 28 && degree >= 5
}

function getNodeSymbolSize(node, visibleCount) {
  const densityScale = visibleCount > 260 ? 0.56 : visibleCount > 170 ? 0.68 : visibleCount > 90 ? 0.82 : 1
  const base = {
    bird: 50,
    location: 30,
    habitat: 25,
    status: 23,
    threat: 23,
    taxonomy: 21
  }[node.type] ?? 26
  const degreeBoost = Math.min(node.type === 'bird' ? 16 : 9, getNodeDegree(node.id) * (node.type === 'bird' ? 1.35 : 0.75))
  return Math.max(16, Math.round((base + degreeBoost) * densityScale))
}

async function loadKnowledge() {
  const response = await fetch('/knowledge.json')
  const data = await response.json()
  knowledge.value = data

  if (rankedBirds.value.length) {
    const featuredBird = rankedBirds.value[0]
    selectedEntity.value = featuredBird
    activeLocation.value = featuredBird
  }
}

function formatGraphData(snapshot) {
  const visibleCount = snapshot.nodes.length
  const categoryColorMap = new Map(
    legendItems.map((item, index) => [
      item.type,
      graphColors[index % graphColors.length] ?? item.color
    ])
  )

  const seriesData = snapshot.nodes.map((node) => {
    const visual = getNodeVisual(node.type)
    const isSelected = node.id === snapshot.selectedId
    const isNeighbor = snapshot.focusNeighborIds.has(node.id) && !isSelected
    const muted = snapshot.selectedId && !snapshot.focusNeighborIds.has(node.id)
    const labelMaxLength = getLabelMaxLength(visibleCount, isSelected)

    return {
      ...node,
      id: String(node.id),
      value: getNodeDegree(node.id),
      category: categoryIndex[node.type] ?? 0,
      symbolSize: getNodeSymbolSize(node, visibleCount),
      draggable: true,
      itemStyle: {
        color: categoryColorMap.get(node.type) ?? visual.color,
        borderColor: isSelected ? '#ffffff' : isNeighbor ? visual.border : 'rgba(255, 255, 255, 0.42)',
        borderWidth: isSelected ? 2.4 : isNeighbor ? 1.8 : 1,
        opacity: muted ? 0.22 : 0.94
      },
      label: {
        show: shouldShowNodeLabel(node, visibleCount, snapshot.focusNeighborIds),
        position: 'right',
        formatter: truncateLabel(node.name, labelMaxLength),
        fontSize: isSelected ? 14 : 11,
        fontWeight: isSelected ? 700 : 500,
        color: graphTheme.label
      }
    }
  })

  const seriesLinks = snapshot.links.map((link) => {
    const isFocusEdge =
      snapshot.focusNeighborIds.has(link.source) && snapshot.focusNeighborIds.has(link.target)

    return {
      source: String(link.source),
      target: String(link.target),
      name: link.label ?? link.relation ?? '',
      relationLabel: link.label ?? link.relation,
      sourceName: getNodeById(link.source)?.name ?? link.source,
      targetName: getNodeById(link.target)?.name ?? link.target,
      lineStyle: {
        width: isFocusEdge ? 2 : 1.2,
        opacity: snapshot.selectedId ? (isFocusEdge ? 0.82 : 0.16) : 0.4
      }
    }
  })

  const categories = legendItems.map((item, index) => ({
    name: item.label,
    itemStyle: {
      color: graphColors[index % graphColors.length] ?? item.color
    }
  }))

  return {
    seriesData,
    seriesLinks,
    categories
  }
}

function buildGraphOption() {
  const snapshot = graphSnapshot.value
  const visibleCount = snapshot.nodes.length
  const { seriesData, seriesLinks, categories } = formatGraphData(snapshot)
  const repulsion = visibleCount > 240 ? 240 : visibleCount > 140 ? 320 : 420
  const edgeLength = visibleCount > 240 ? 40 : visibleCount > 140 ? 55 : 72

  return {
    backgroundColor: graphTheme.background,
    animationDurationUpdate: 500,
    animationEasingUpdate: 'quinticInOut',
    tooltip: {
      trigger: 'item',
      confine: true,
      backgroundColor: graphTheme.tooltipBackground,
      borderColor: graphTheme.tooltipBorder,
      borderWidth: 1,
      textStyle: {
        color: '#f8fafc',
        fontSize: 12,
        lineHeight: 18
      },
      formatter: (params) => {
        if (params.dataType === 'edge') {
          return `${params.data.sourceName} → ${params.data.relationLabel} → ${params.data.targetName}`
        }

        const node = params.data
        return [
          `<strong>${node.name}</strong>`,
          `${typeLabelMap[node.type] ?? node.type} · 关联 ${getNodeDegree(node.id)} 条`,
          node.latinName ? `学名：${node.latinName}` : '',
          node.summary ?? ''
        ]
          .filter(Boolean)
          .join('<br/>')
      }
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        legendHoverLink: true,
        hoverAnimation: true,
        focusNodeAdjacency: true,
        roam: true,
        draggable: true,
        progressive: 200,
        progressiveThreshold: 500,
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 8],
        force: {
          edgeLength,
          repulsion,
          gravity: 0.08
        },
        edgeLabel: {
          show: visibleCount <= 80,
          position: 'middle',
          fontSize: 11,
          color: graphTheme.labelMuted,
          formatter: ({ data }) => data?.name ?? ''
        },
        itemStyle: {
          color: '#00FAE1',
          cursor: 'pointer'
        },
        lineStyle: {
          color: 'rgba(148, 163, 184, 0.38)',
          width: 1.2,
          opacity: 0.45
        },
        label: {
          show: visibleCount <= 160,
          fontSize: 12,
          color: graphTheme.label,
          position: 'right'
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 2.2,
            opacity: 0.9
          },
          itemStyle: {
            borderWidth: 2.6
          }
        },
        symbolSize: 24,
        links: seriesLinks,
        data: seriesData,
        categories,
        cursor: 'pointer'
      }
    ]
  }
}

function refreshGraph() {
  if (!chartInstance) {
    return
  }

  chartInstance.setOption(buildGraphOption(), {
    notMerge: true,
    lazyUpdate: true
  })
}

function initChart() {
  if (!graphRef.value) {
    return
  }

  chartInstance?.dispose()
  chartInstance = echarts.init(graphRef.value)
  chartInstance.on('click', (params) => {
    if (params.dataType !== 'node' || !params.data?.id) {
      return
    }
    handleNodeClick(params.data.id)
  })
  refreshGraph()
}

function initMap() {
  if (!mapRef.value || mapInstance) {
    return
  }

  mapInstance = L.map(mapRef.value, {
    zoomControl: true,
    worldCopyJump: true
  }).setView([20, 110], 2)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(mapInstance)
}

function handleResize() {
  chartInstance?.resize()
  mapInstance?.invalidateSize()
}

watch(
  [
    () => knowledge.value.nodes.length,
    () => knowledge.value.links.length,
    () => selectedEntity.value?.id ?? '',
    graphMode,
    graphBirdLimit,
    labelMode,
    () => activeContextTypes.value.join('|')
  ],
  () => {
    refreshGraph()
  }
)

onMounted(async () => {
  await loadKnowledge()
  await nextTick()
  initMap()
  initChart()

  if (selectedEntity.value) {
    moveMap(selectedEntity.value)
  }

  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  mapInstance?.remove()
})
</script>

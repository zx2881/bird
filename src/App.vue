<template>
  <div class="shell">
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
let graphRefreshFrame = 0
let selectionRefreshFrame = 0
let lastRenderedGraphSignature = ''

const MAX_OVERVIEW_LOCATION_NODES = 140
const OVERVIEW_LOCATION_MIN_DEGREE = 2

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

  const visibleNodeIds =
    graphMode.value === 'focus'
      ? buildFocusNodeIds(enabledContextTypes)
      : buildOverviewNodeIds(enabledContextTypes)

  if (!visibleNodeIds.size && rankedBirds.value.length) {
    const fallbackNodeIds = buildFallbackNodeIds(enabledContextTypes)
    fallbackNodeIds.forEach((nodeId) => visibleNodeIds.add(nodeId))
  }

  const visibleLinks = collectVisibleLinks(visibleNodeIds, enabledContextTypes, selectedId)
  const finalNodeIds =
    graphMode.value === 'overview'
      ? pruneOverviewNodeIds(visibleNodeIds, visibleLinks, selectedId)
      : visibleNodeIds
  const filteredLinks = visibleLinks.filter((link) => finalNodeIds.has(link.source) && finalNodeIds.has(link.target))
  const visibleNodes = [...finalNodeIds].map((nodeId) => getNodeById(nodeId)).filter(Boolean)
  const visibleNodeIdSet = new Set(visibleNodes.map((node) => node.id))

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
    return '已展示全部鸟类簇，概览模式会自动折叠低频地点节点'
  }

  return '概览模式按关联度筛选高价值节点，并自动裁剪低频地点节点'
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
  graphMode.value = 'focus'
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

function isGraphNodeEnabled(node, enabledContextTypes, selectedId) {
  return !!node && (node.type === 'bird' || enabledContextTypes.has(node.type) || node.id === selectedId)
}

function collectVisibleLinks(visibleNodeIds, enabledContextTypes, selectedId) {
  const visibleLinkMap = new Map()

  visibleNodeIds.forEach((nodeId) => {
    getIncidentLinks(nodeId).forEach((link) => {
      if (visibleLinkMap.has(link.key)) {
        return
      }

      if (!visibleNodeIds.has(link.source) || !visibleNodeIds.has(link.target)) {
        return
      }

      const sourceNode = getNodeById(link.source)
      const targetNode = getNodeById(link.target)
      if (!isGraphNodeEnabled(sourceNode, enabledContextTypes, selectedId)) {
        return
      }
      if (!isGraphNodeEnabled(targetNode, enabledContextTypes, selectedId)) {
        return
      }

      visibleLinkMap.set(link.key, link)
    })
  })

  return [...visibleLinkMap.values()]
}

function pruneOverviewNodeIds(visibleNodeIds, visibleLinks, selectedId) {
  const finalNodeIds = new Set()
  const selectedNeighborIds = new Set()
  const preservedTypeLimits = {
    location: MAX_OVERVIEW_LOCATION_NODES,
    habitat: 90,
    status: 70,
    threat: 90,
    taxonomy: 70
  }
  const rankedNodeIdsByType = new Map()

  if (selectedId) {
    visibleLinks.forEach((link) => {
      if (link.source === selectedId) {
        selectedNeighborIds.add(link.target)
      }
      if (link.target === selectedId) {
        selectedNeighborIds.add(link.source)
      }
    })
  }

  visibleNodeIds.forEach((nodeId) => {
    const node = getNodeById(nodeId)
    if (!node) {
      return
    }

    if (!preservedTypeLimits[node.type]) {
      finalNodeIds.add(nodeId)
      return
    }

    if (nodeId === selectedId || selectedNeighborIds.has(nodeId)) {
      finalNodeIds.add(nodeId)
      return
    }

    if (getNodeDegree(nodeId) < OVERVIEW_LOCATION_MIN_DEGREE) {
      return
    }

    if (!rankedNodeIdsByType.has(node.type)) {
      rankedNodeIdsByType.set(node.type, [])
    }
    rankedNodeIdsByType.get(node.type).push(nodeId)
  })

  rankedNodeIdsByType.forEach((nodeIds, type) => {
    nodeIds
      .sort((leftId, rightId) => {
        const degreeDiff = getNodeDegree(rightId) - getNodeDegree(leftId)
        if (degreeDiff !== 0) {
          return degreeDiff
        }

        const leftNode = getNodeById(leftId)
        const rightNode = getNodeById(rightId)
        return (leftNode?.name ?? '').localeCompare(rightNode?.name ?? '', 'zh-Hans-CN')
      })
      .slice(0, preservedTypeLimits[type] ?? nodeIds.length)
      .forEach((nodeId) => finalNodeIds.add(nodeId))
  })

  return finalNodeIds
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

  getIncidentLinks(seedNode.id).forEach((link) => {
    const otherId = getLinkOtherNodeId(link, seedNode.id)
    const otherNode = getNodeById(otherId)
    if (!otherNode) {
      return
    }

    if (otherNode.type === 'bird' || enabledContextTypes.has(otherNode.type)) {
      visibleNodeIds.add(otherNode.id)
    }
  })

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
  const densityScale = visibleCount > 260 ? 0.88 : visibleCount > 170 ? 0.93 : 1
  const base = {
    bird: 17,
    location: 14,
    habitat: 13,
    status: 12,
    threat: 12,
    taxonomy: 12
  }[node.type] ?? 12
  const degreeBoost =
    node.type === 'bird'
      ? Math.min(2.2, getNodeDegree(node.id) * 0.12)
      : Math.min(1.4, getNodeDegree(node.id) * 0.08)

  return Math.max(10, Math.min(20, Math.round((base + degreeBoost) * densityScale)))
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

function getGraphStructureSignature(snapshot) {
  const nodePart = snapshot.nodes.map((node) => String(node.id)).join('|')
  const linkPart = snapshot.links.map((link) => `${link.source}->${link.target}:${link.relation}`).join('|')
  return `${graphMode.value}::${nodePart}::${linkPart}`
}

function getNodeLayoutPosition({
  nodeId,
  typeIndex,
  typeCount,
  typeRank,
  typeSize,
  globalIndex,
  totalNodes
}) {
  const goldenAngle = 2.399963229728653
  const seed = String(nodeId).split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  const globalRatio = Math.sqrt((globalIndex + 0.5) / Math.max(totalNodes, 1))
  const typeRatio = Math.sqrt((typeRank + 0.5) / Math.max(typeSize, 1))
  const sectorOffset = ((typeIndex + 0.5) / Math.max(typeCount, 1)) * Math.PI * 2
  const jitter = ((seed % 97) / 96 - 0.5) * (Math.PI / Math.max(18, typeCount * 6))
  const angle = goldenAngle * globalIndex + sectorOffset + jitter
  const radius = 90 + (globalRatio * 0.55 + typeRatio * 0.45) * 340

  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius
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

  const nodeGroups = new Map()
  snapshot.nodes.forEach((node) => {
    if (!nodeGroups.has(node.type)) {
      nodeGroups.set(node.type, [])
    }
    nodeGroups.get(node.type).push(node)
  })
  const orderedTypes = [...nodeGroups.keys()].sort((left, right) => left.localeCompare(right))
  const typeCount = orderedTypes.length || 1
  const typeMetaByNodeId = new Map()

  orderedTypes.forEach((type, typeIndex) => {
    const group = nodeGroups.get(type) ?? []
    group.forEach((node, typeRank) => {
      typeMetaByNodeId.set(node.id, {
        typeIndex,
        typeCount,
        typeRank,
        typeSize: group.length
      })
    })
  })

  const symbolSizeById = new Map()
  const seriesData = snapshot.nodes.map((node, globalIndex) => {
    const visual = getNodeVisual(node.type)
    const isSelected = node.id === snapshot.selectedId
    const isNeighbor = snapshot.focusNeighborIds.has(node.id) && !isSelected
    const muted = snapshot.selectedId && !snapshot.focusNeighborIds.has(node.id)
    const labelMaxLength = getLabelMaxLength(visibleCount, isSelected)
    const typeMeta = typeMetaByNodeId.get(node.id) ?? {
      typeIndex: 0,
      typeCount: 1,
      typeRank: globalIndex,
      typeSize: snapshot.nodes.length || 1
    }
    const position = getNodeLayoutPosition({
      nodeId: node.id,
      ...typeMeta,
      globalIndex,
      totalNodes: snapshot.nodes.length
    })
    const symbolSize = getNodeSymbolSize(node, visibleCount)
    symbolSizeById.set(node.id, symbolSize)

    return {
      ...node,
      id: String(node.id),
      x: position.x,
      y: position.y,
      fixed: false,
      value: getNodeDegree(node.id),
      category: categoryIndex[node.type] ?? 0,
      symbolSize,
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
    const sourceSize = symbolSizeById.get(link.source) ?? 12
    const targetSize = symbolSizeById.get(link.target) ?? 12
    const baseWidth = Math.max(0.7, Math.min(1.25, 0.055 * Math.sqrt(sourceSize * targetSize)))

    return {
      source: String(link.source),
      target: String(link.target),
      name: link.label ?? link.relation ?? '',
      relationLabel: link.label ?? link.relation,
      sourceName: getNodeById(link.source)?.name ?? link.source,
      targetName: getNodeById(link.target)?.name ?? link.target,
      lineStyle: {
        width: isFocusEdge ? Math.min(1.6, baseWidth + 0.35) : baseWidth,
        opacity: snapshot.selectedId ? (isFocusEdge ? 0.85 : 0.14) : 0.34
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
  const isLargeGraph = visibleCount > 260

  const obsidianNodeColorMap = {
    bird: '#7f8fa6',
    location: '#6f9e98',
    habitat: '#8da56b',
    status: '#b59a62',
    threat: '#9f727a',
    taxonomy: '#8b84ab'
  }

  const obsidianNodes = seriesData.map((node) => {
    return {
      ...node,
      symbol: 'circle',
      symbolSize: node.symbolSize,
      draggable: true,
      itemStyle: {
        color: obsidianNodeColorMap[node.type] ?? '#8b949e',
        borderWidth: 0,
        borderColor: 'transparent',
        shadowBlur: 0,
        shadowOffsetX: 0,
        shadowOffsetY: 0,
        opacity: 1
      },
      label: {
        show: true,
        formatter: node.name,
        color: 'rgba(255, 255, 255, 0.9)',
        fontSize: 10,
        fontWeight: 400,
        position: 'bottom',
        distance: 8,
        align: 'center'
      }
    }
  })

  const obsidianLinks = seriesLinks.map((link) => {
    return {
      ...link,
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.08)',
        width: link.lineStyle?.width ?? 1,
        opacity: link.lineStyle?.opacity ?? 1,
        curveness: 0
      },
      label: {
        show: false
      }
    }
  })

  return {
    backgroundColor: '#1a1a1a',
    animation: !isLargeGraph,
    animationDuration: isLargeGraph ? 0 : 600,
    animationDurationUpdate: isLargeGraph ? 0 : 280,
    animationEasingUpdate: 'cubicOut',
    tooltip: {
      show: false
    },
    series: [
      {
        id: 'knowledge-graph',
        type: 'graph',
        layout: 'force',
        legendHoverLink: false,
        hoverAnimation: false,
        focusNodeAdjacency: 'allEdges',
        roam: true,
        draggable: true,
        progressive: 200,
        progressiveThreshold: 500,
        edgeSymbol: ['none', 'none'],
        layoutAnimation: true,
        force: {
          repulsion: [1400, 2600],
          edgeLength: [140, 280],
          gravity: 0.01,
          friction: 0.78,
          layoutAnimation: true,
          preventOverlap: true
        },
        itemStyle: {
          shadowBlur: 0,
          opacity: 1,
          cursor: 'pointer',
          borderWidth: 0,
          borderColor: 'transparent'
        },
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.08)',
          width: 1,
          opacity: 1,
          curveness: 0
        },
        label: {
          show: false
        },
        edgeLabel: {
          show: false
        },
        emphasis: {
          focus: 'none',
          scale: false,
          itemStyle: {
            opacity: 1,
            shadowBlur: 0,
            borderWidth: 0,
            borderColor: 'transparent'
          },
          lineStyle: {
            opacity: 1,
            width: 1.15
          },
          label: {
            show: true,
            color: '#ffffff',
            fontSize: 10,
            fontWeight: 500,
            position: 'bottom',
            distance: 8
          }
        },
        blur: {
          itemStyle: {
            opacity: 1
          },
          lineStyle: {
            opacity: 1
          },
          label: {
            color: 'rgba(255, 255, 255, 0.9)'
          }
        },
        labelLayout: {
          hideOverlap: true
        },
        data: obsidianNodes,
        links: obsidianLinks,
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

  const snapshot = graphSnapshot.value
  lastRenderedGraphSignature = getGraphStructureSignature(snapshot)

  chartInstance.setOption(buildGraphOption(), {
    notMerge: true,
    lazyUpdate: true
  })
}

function refreshGraphSelectionVisual() {
  if (!chartInstance) {
    return
  }

  const snapshot = graphSnapshot.value
  const nextSignature = getGraphStructureSignature(snapshot)
  if (nextSignature !== lastRenderedGraphSignature) {
    scheduleGraphRefresh()
    return
  }

  const visibleCount = snapshot.nodes.length
  const { seriesData, seriesLinks } = formatGraphData(snapshot)

  const obsidianNodeColorMap = {
    bird: '#7f8fa6',
    location: '#6f9e98',
    habitat: '#8da56b',
    status: '#b59a62',
    threat: '#9f727a',
    taxonomy: '#8b84ab'
  }

  const currentSeries = chartInstance.getOption()?.series?.find((series) => series.id === 'knowledge-graph')
  const currentNodePositions = new Map(
    (currentSeries?.data ?? [])
      .filter((node) => node?.id !== undefined && Number.isFinite(node?.x) && Number.isFinite(node?.y))
      .map((node) => [String(node.id), { x: node.x, y: node.y }])
  )

  const nodes = seriesData.map((node) => {
    const currentPosition = currentNodePositions.get(String(node.id))

    return {
      ...node,
      symbol: 'circle',
      symbolSize: node.symbolSize,
      itemStyle: {
        color: obsidianNodeColorMap[node.type] ?? '#8b949e',
        borderWidth: 0,
        borderColor: 'transparent',
        shadowBlur: 0,
        shadowOffsetX: 0,
        shadowOffsetY: 0,
        opacity: 1
      },
      label: {
        show: true,
        formatter: node.name,
        color: 'rgba(255, 255, 255, 0.9)',
        fontSize: 10,
        fontWeight: 400,
        position: 'bottom',
        distance: 8,
        align: 'center'
      },
      ...(currentPosition
        ? {
            x: currentPosition.x,
            y: currentPosition.y,
            fixed: false
          }
        : {})
    }
  })

  const links = seriesLinks.map((link) => {
    return {
      ...link,
      lineStyle: {
        color: 'rgba(255, 255, 255, 0.08)',
        width: link.lineStyle?.width ?? 1,
        opacity: link.lineStyle?.opacity ?? 1,
        curveness: 0
      },
      label: {
        show: false
      }
    }
  })

  chartInstance.setOption(
    {
      animation: false,
      animationDuration: 0,
      animationDurationUpdate: 0,
      animationEasingUpdate: 'linear',
      series: [
        {
          id: 'knowledge-graph',
          layoutAnimation: false,
          data: nodes,
          links
        }
      ]
    },
    {
      notMerge: false,
      lazyUpdate: true
    }
  )
}

function scheduleGraphRefresh() {
  if (!chartInstance) {
    return
  }

  if (graphRefreshFrame) {
    window.cancelAnimationFrame(graphRefreshFrame)
  }

  graphRefreshFrame = window.requestAnimationFrame(() => {
    graphRefreshFrame = 0
    refreshGraph()
  })
}

function scheduleSelectionRefresh() {
  if (!chartInstance) {
    return
  }

  if (selectionRefreshFrame) {
    window.cancelAnimationFrame(selectionRefreshFrame)
  }

  selectionRefreshFrame = window.requestAnimationFrame(() => {
    selectionRefreshFrame = 0
    refreshGraphSelectionVisual()
  })
}

function initChart() {
  if (!graphRef.value) {
    return
  }

  chartInstance?.dispose()
  chartInstance = echarts.init(graphRef.value, null, {
    renderer: 'canvas',
    useDirtyRect: false,
    devicePixelRatio: Math.min(window.devicePixelRatio || 1, 1.5)
  })
  chartInstance.on('click', (params) => {
    if (params.dataType !== 'node' || !params.data?.id) {
      return
    }
    handleNodeClick(params.data.id)
  })
  chartInstance.on('globalout', () => {
    if (!chartInstance) {
      return
    }
    chartInstance.dispatchAction({
      type: 'downplay',
      seriesIndex: 0
    })
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
    graphMode,
    graphBirdLimit,
    labelMode,
    () => activeContextTypes.value.join('|')
  ],
  () => {
    scheduleGraphRefresh()
  }
)

watch(
  () => selectedEntity.value?.id ?? '',
  () => {
    if (graphMode.value === 'focus') {
      scheduleGraphRefresh()
      return
    }

    scheduleSelectionRefresh()
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
  if (graphRefreshFrame) {
    window.cancelAnimationFrame(graphRefreshFrame)
  }
  if (selectionRefreshFrame) {
    window.cancelAnimationFrame(selectionRefreshFrame)
  }
  chartInstance?.dispose()
  mapInstance?.remove()
})
</script>

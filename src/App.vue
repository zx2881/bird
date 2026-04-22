<template>
  <div class="shell">
    <header class="app-header">
      <div>
        <p class="eyebrow">Global Avian Biodiversity Graph</p>
        <h1>全球鸟类多样性知识探索平台</h1>
        <p class="subtitle">
          以静态知识图谱为前端核心，结合地图浏览与三元组抽取测试，快速验证全球鸟类分布与保护知识框架。
        </p>
      </div>
      <div class="header-badge">
        <span>模式</span>
        <strong>static-data + triple-test</strong>
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

        <section class="sidebar-section">
          <div class="section-heading">
            <h2>后端测试</h2>
            <p>按 `三元组提取.md` 的关系模式返回 JSON</p>
          </div>

          <div class="test-toolbar">
            <el-button type="primary" @click="runTripleTest" :loading="tripleState.loading">
              运行三元组抽取测试
            </el-button>
            <span class="test-hint">{{ tripleState.message }}</span>
          </div>

          <el-alert
            v-if="tripleState.error"
            type="warning"
            :closable="false"
            show-icon
            :title="tripleState.error"
          />

          <div v-if="tripleState.documents.length" class="doc-list">
            <article v-for="doc in tripleState.documents" :key="doc.id" class="doc-card">
              <h3>{{ doc.title }}</h3>
              <p>{{ doc.text }}</p>
              <a :href="doc.source_url" target="_blank" rel="noreferrer">来源链接</a>
            </article>
          </div>

          <el-table
            v-if="tripleState.triples.length"
            :data="tripleState.triples"
            height="280"
            stripe
            class="triple-table"
          >
            <el-table-column prop="subject" label="主语" min-width="110" />
            <el-table-column prop="predicate" label="关系" min-width="120" />
            <el-table-column prop="object" label="宾语" min-width="110" />
            <el-table-column prop="evidence" label="证据" min-width="240" show-overflow-tooltip />
          </el-table>
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
const tripleState = ref({
  loading: false,
  error: '',
  message: '点击按钮调用本地后端测试接口。',
  triples: [],
  documents: []
})

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

const legendItems = [
  { type: 'bird', label: '鸟类', color: '#f97316' },
  { type: 'location', label: '地点', color: '#0f766e' },
  { type: 'habitat', label: '栖息地', color: '#1d4ed8' },
  { type: 'status', label: '保护等级', color: '#7c3aed' },
  { type: 'threat', label: '威胁因素', color: '#dc2626' },
  { type: 'taxonomy', label: '分类单元', color: '#475569' }
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

let chartInstance
let mapInstance
let mapMarker
let graphRefreshFrame = 0

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

  const focusNeighborIds = new Set()
  if (selectedId) {
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
    return '当前模式会突出选中实体及其一跳上下文'
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
  const rankedLocationIds = []

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

    if (node.type !== 'location') {
      finalNodeIds.add(nodeId)
      return
    }

    if (nodeId === selectedId || selectedNeighborIds.has(nodeId)) {
      finalNodeIds.add(nodeId)
      return
    }

    if (getNodeDegree(nodeId) >= OVERVIEW_LOCATION_MIN_DEGREE) {
      rankedLocationIds.push(nodeId)
    }
  })

  rankedLocationIds
    .sort((leftId, rightId) => {
      const degreeDiff = getNodeDegree(rightId) - getNodeDegree(leftId)
      if (degreeDiff !== 0) {
        return degreeDiff
      }

      const leftNode = getNodeById(leftId)
      const rightNode = getNodeById(rightId)
      return (leftNode?.name ?? '').localeCompare(rightNode?.name ?? '', 'zh-Hans-CN')
    })
    .slice(0, MAX_OVERVIEW_LOCATION_NODES)
    .forEach((nodeId) => finalNodeIds.add(nodeId))

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
  if (labelMode.value === 'all') {
    return true
  }

  if (labelMode.value === 'birds') {
    return node.type === 'bird'
  }

  if (focusNeighborIds.has(node.id)) {
    return true
  }

  const degree = getNodeDegree(node.id)
  if (node.type === 'bird') {
    if (visibleCount <= 70) {
      return true
    }
    return degree >= 4
  }

  if (node.type === 'location') {
    return visibleCount <= 60 && degree >= 3
  }

  return visibleCount <= 32 && degree >= 4
}

function getNodeSymbolSize(node, visibleCount) {
  const densityScale = visibleCount > 260 ? 0.62 : visibleCount > 170 ? 0.74 : visibleCount > 90 ? 0.86 : 1
  const base = {
    bird: 52,
    location: 34,
    habitat: 28,
    status: 24,
    threat: 24,
    taxonomy: 22
  }[node.type] ?? 26
  const degreeBoost = Math.min(node.type === 'bird' ? 20 : 12, getNodeDegree(node.id) * (node.type === 'bird' ? 1.6 : 0.9))
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

function buildGraphOption() {
  const snapshot = graphSnapshot.value
  const visibleCount = snapshot.nodes.length
  const selectedId = snapshot.selectedId
  const isLargeGraph = visibleCount > 260
  const repulsion = visibleCount > 240 ? 150 : visibleCount > 140 ? 210 : 280
  const edgeLength = visibleCount > 240 ? [45, 90] : visibleCount > 140 ? [60, 120] : [90, 170]
  const gravity = visibleCount > 220 ? 0.2 : visibleCount > 120 ? 0.14 : 0.08

  return {
    backgroundColor: 'transparent',
    animation: !isLargeGraph,
    animationDuration: isLargeGraph ? 0 : visibleCount > 220 ? 320 : 820,
    animationDurationUpdate: visibleCount > 220 ? 0 : 420,
    animationEasingUpdate: 'quinticInOut',
    tooltip: {
      trigger: 'item',
      confine: true,
      enterable: false,
      transitionDuration: 0,
      formatter: (params) => {
        if (params.dataType === 'edge') {
          return `${params.data.sourceName} → ${params.data.relationLabel} → ${params.data.targetName}`
        }

        const node = params.data
        const degree = getNodeDegree(node.id)
        return [
          `<strong>${node.name}</strong>`,
          `${typeLabelMap[node.type] ?? node.type} · 关联 ${degree} 条`,
          node.latinName ? `学名：${node.latinName}` : '',
          node.summary ? node.summary : ''
        ]
          .filter(Boolean)
          .join('<br/>')
      }
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        layoutAnimation: visibleCount < 160,
        force: {
          repulsion,
          edgeLength,
          gravity,
          friction: 0.12
        },
        emphasis: {
          focus: 'adjacency',
          scale: true,
          lineStyle: {
            width: 3,
            opacity: 1
          }
        },
        blur: {
          itemStyle: {
            opacity: 0.12
          },
          lineStyle: {
            opacity: 0.04
          },
          label: {
            show: false
          }
        },
        labelLayout: {
          hideOverlap: true
        },
        lineStyle: {
          color: 'source',
          width: 1,
          curveness: isLargeGraph ? 0.02 : visibleCount > 180 ? 0.08 : 0.13,
          opacity: 0.18
        },
        categories: legendItems.map((item) => ({ name: item.label })),
        data: snapshot.nodes.map((node) => {
          const color = legendItems[categoryIndex[node.type] ?? 0].color
          const isSelected = node.id === selectedId
          const isNeighbor = snapshot.focusNeighborIds.has(node.id) && !isSelected
          const muted = graphMode.value === 'focus' && selectedId && !snapshot.focusNeighborIds.has(node.id)
          const showLabel = shouldShowNodeLabel(node, visibleCount, snapshot.focusNeighborIds)

          return {
            ...node,
            value: getNodeDegree(node.id),
            category: categoryIndex[node.type] ?? 0,
            symbolSize: getNodeSymbolSize(node, visibleCount),
            label: {
              show: showLabel,
              position: 'right',
              formatter: truncateLabel(node.name, visibleCount > 180 ? 9 : 12),
              fontSize: isSelected ? 14 : visibleCount > 170 ? 10 : 11,
              fontWeight: isSelected ? 700 : 500,
              color: '#12303b',
              backgroundColor: isSelected ? 'rgba(255, 248, 240, 0.94)' : isNeighbor ? 'rgba(255, 255, 255, 0.78)' : 'transparent',
              padding: isSelected || isNeighbor ? [4, 6] : 0,
              borderRadius: 8
            },
            itemStyle: {
              color,
              opacity: muted ? 0.22 : node.type === 'bird' ? 0.95 : 0.84,
              borderColor: isSelected ? '#fff7ed' : isNeighbor ? '#ffffff' : 'rgba(255, 255, 255, 0.76)',
              borderWidth: isSelected ? 4 : isNeighbor ? 3 : 1.5,
              shadowBlur: isLargeGraph ? 0 : isSelected ? 24 : isNeighbor ? 12 : 0,
              shadowColor: isSelected ? 'rgba(15, 118, 110, 0.3)' : 'transparent'
            }
          }
        }),
        links: snapshot.links.map((link) => {
          const isSelectedEdge = link.source === selectedId || link.target === selectedId
          const isFocusEdge =
            snapshot.focusNeighborIds.has(link.source) && snapshot.focusNeighborIds.has(link.target)

          return {
            source: link.source,
            target: link.target,
            relationLabel: link.label ?? link.relation,
            sourceName: getNodeById(link.source)?.name ?? link.source,
            targetName: getNodeById(link.target)?.name ?? link.target,
            lineStyle: {
              color: isSelectedEdge ? '#0f766e' : 'rgba(18, 48, 59, 0.22)',
              width: isSelectedEdge ? 2.8 : isFocusEdge ? 1.3 : 0.9,
              opacity: isSelectedEdge ? 0.92 : graphMode.value === 'focus' ? 0.26 : visibleCount > 180 ? 0.12 : 0.22,
              curveness: isLargeGraph ? 0.02 : visibleCount > 180 ? 0.08 : 0.13
            }
          }
        })
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

function initChart() {
  if (!graphRef.value) {
    return
  }

  chartInstance?.dispose()
  chartInstance = echarts.init(graphRef.value, null, {
    renderer: 'canvas',
    useDirtyRect: true,
    devicePixelRatio: Math.min(window.devicePixelRatio || 1, 1.5)
  })
  refreshGraph()
  chartInstance.on('click', (params) => {
    if (params.dataType !== 'node') {
      return
    }

    const node = getNodeById(params.data.id)
    if (node) {
      selectEntity(node)
    }
  })
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

async function runTripleTest() {
  tripleState.value.loading = true
  tripleState.value.error = ''
  tripleState.value.message = '正在请求本地后端...'

  try {
    const response = await fetch('/api/triples/test')
    if (!response.ok) {
      throw new Error(`接口返回 ${response.status}`)
    }

    const payload = await response.json()
    tripleState.value.documents = payload.documents ?? []
    tripleState.value.triples = payload.triples ?? []
    tripleState.value.message = `已完成 ${payload.documents?.length ?? 0} 段文本抽取，共返回 ${payload.triples?.length ?? 0} 条三元组。`
  } catch (error) {
    tripleState.value.error = '未连接到本地后端。请先执行 npm run server，再重新测试。'
    tripleState.value.message = '当前仅前端静态图谱可用。'
  } finally {
    tripleState.value.loading = false
  }
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
    scheduleGraphRefresh()
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
  chartInstance?.dispose()
  mapInstance?.remove()
})
</script>

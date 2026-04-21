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
            <p>10 种鸟类静态样例</p>
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
              <p>点击鸟类查看详情，点击地点联动地图</p>
            </div>
            <div class="legend">
              <span v-for="item in legendItems" :key="item.label">
                <i :style="{ backgroundColor: item.color }"></i>{{ item.label }}
              </span>
            </div>
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import L from 'leaflet'

const graphRef = ref(null)
const mapRef = ref(null)

const knowledge = ref({ nodes: [], links: [] })
const selectedEntity = ref(null)
const searchKeyword = ref('')
const activeLocation = ref(null)
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
  { label: '鸟类', color: '#f97316' },
  { label: '地点', color: '#0f766e' },
  { label: '栖息地', color: '#1d4ed8' },
  { label: '保护等级', color: '#7c3aed' },
  { label: '威胁因素', color: '#dc2626' },
  { label: '分类单元', color: '#475569' }
]

const categoryIndex = {
  bird: 0,
  location: 1,
  habitat: 2,
  status: 3,
  threat: 4,
  taxonomy: 5
}

let chartInstance
let mapInstance
let mapMarker

const birdNodes = computed(() => knowledge.value.nodes.filter((item) => item.type === 'bird'))
const searchableNodes = computed(() =>
  knowledge.value.nodes.filter((item) => item.type === 'bird' || item.type === 'location')
)
const quickBirds = computed(() => birdNodes.value.slice(0, 4))

const metrics = computed(() => {
  const counts = {
    bird: 0,
    location: 0,
    habitat: 0,
    status: 0,
    threat: 0
  }

  knowledge.value.nodes.forEach((node) => {
    if (counts[node.type] !== undefined) {
      counts[node.type] += 1
    }
  })

  return counts
})

const relatedFacts = computed(() => {
  if (!selectedEntity.value) {
    return []
  }

  return knowledge.value.links
    .filter((link) => link.source === selectedEntity.value.id || link.target === selectedEntity.value.id)
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

function getNodeById(id) {
  return knowledge.value.nodes.find((node) => node.id === id)
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

  if (entity.type === 'location') {
    moveMap(entity)
    return
  }

  if (entity.lat !== null && entity.lat !== undefined && entity.lng !== null && entity.lng !== undefined) {
    moveMap(entity)
  }
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

async function loadKnowledge() {
  const response = await fetch('/knowledge.json')
  const data = await response.json()
  knowledge.value = data

  if (birdNodes.value.length) {
    selectedEntity.value = birdNodes.value[0]
    activeLocation.value = birdNodes.value[0]
  }
}

function buildGraphOption() {
  return {
    backgroundColor: 'transparent',
    animationDuration: 900,
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'edge') {
          return `${params.data.sourceName} → ${params.data.relationLabel} → ${params.data.targetName}`
        }

        const node = params.data
        return [
          `<strong>${node.name}</strong>`,
          `${typeLabelMap[node.type] ?? node.type}`,
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
        force: {
          repulsion: 260,
          edgeLength: [90, 170],
          gravity: 0.08
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 3
          }
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{b}',
          fontSize: 12,
          color: '#12303b'
        },
        lineStyle: {
          color: 'source',
          width: 1.8,
          curveness: 0.14,
          opacity: 0.75
        },
        categories: legendItems.map((item) => ({ name: item.label })),
        data: knowledge.value.nodes.map((node) => ({
          ...node,
          category: categoryIndex[node.type] ?? 0,
          symbolSize:
            {
              bird: 58,
              location: 42,
              habitat: 36,
              status: 32,
              threat: 34
            }[node.type] ?? 36,
          itemStyle: {
            color: legendItems[categoryIndex[node.type] ?? 0].color,
            borderColor: '#f7f5ef',
            borderWidth: 2
          }
        })),
        links: knowledge.value.links.map((link) => ({
          source: link.source,
          target: link.target,
          relationLabel: link.label ?? link.relation,
          sourceName: getNodeById(link.source)?.name ?? link.source,
          targetName: getNodeById(link.target)?.name ?? link.target
        }))
      }
    ]
  }
}

function initChart() {
  if (!graphRef.value) {
    return
  }

  chartInstance?.dispose()
  chartInstance = echarts.init(graphRef.value)
  chartInstance.setOption(buildGraphOption())
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

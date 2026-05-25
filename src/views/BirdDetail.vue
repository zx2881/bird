<template>
  <div class="detail-page">
    <aside class="detail-sidebar panel">
      <h3 class="sidebar-title">切换物种</h3>
      <input
        v-model="switchQuery"
        type="text"
        class="switch-input"
        placeholder="搜索中文名、英文名或学名…"
      />
      <div class="switch-list">
        <button
          v-for="item in switchResults"
          :key="item.id"
          type="button"
          class="switch-item"
          :class="{ active: item.id === birdId }"
          @click="switchBird(item.id)"
        >
          <span class="switch-name">{{ item.name }}</span>
          <span class="switch-meta">{{ item.englishName || '暂无英文名' }}</span>
        </button>
      </div>
    </aside>

    <section class="detail-content-area">
      <button class="back-btn" @click="router.back()">← 返回图谱</button>

      <div v-if="bird" class="detail-card-inner">
        <div class="detail-top-bar">
          <div class="detail-header">
            <h2 class="detail-bird-name">{{ bird.name }}</h2>
            <span v-if="bird.status" class="detail-status" :class="statusClass(bird.status)">
              {{ endangermentLabels[bird.status] || bird.status }}
            </span>
          </div>
        </div>

        <div class="detail-image-wrap">
          <div class="detail-image-bg" :style="{ background: statusGradient(bird.status) }"></div>
          <img
            v-if="bird.imageUrl"
            :src="bird.imageUrl"
            :alt="bird.name"
            class="detail-image"
            @error="onDetailImgError"
          />
          <div v-else class="detail-image-placeholder">
            <span>{{ bird.name }}</span>
          </div>
          <div v-if="bird.status" class="detail-image-status" :class="statusClass(bird.status)">
            {{ statusLabel(bird.status) }}
          </div>
        </div>

        <div class="detail-summary-section">
          <p class="detail-summary-text">{{ displaySummary }}</p>
          <button
            v-if="bird.summary && bird.summary.length > 100"
            class="expand-btn"
            @click="summaryExpanded = !summaryExpanded"
          >
            {{ summaryExpanded ? '收起' : '展开全文' }}
          </button>
        </div>

        <div class="detail-stats-row">
          <div class="stat-card">
            <span class="stat-number">{{ bird.locations?.length || 0 }}</span>
            <span class="stat-label">分布地点</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ bird.habitats?.length || 0 }}</span>
            <span class="stat-label">栖息地类型</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ bird.threats?.length || 0 }}</span>
            <span class="stat-label">威胁因素</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ store.getNodeDegree(birdId) }}</span>
            <span class="stat-label">当前关联</span>
          </div>
        </div>

        <div class="detail-info-grid">
          <div
            v-for="item in taxonomyItems"
            :key="item.label"
            class="info-item"
          >
            <span class="info-label">{{ item.label }}</span>
            <span class="info-value">{{ item.value }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">英文名</span>
            <span class="info-value">{{ bird.englishName || '暂无' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">学名</span>
            <span class="info-value"><em>{{ bird.latinName || '暂无' }}</em></span>
          </div>
          <div class="info-item">
            <span class="info-label">主要分布</span>
            <span class="info-value">{{ formatList(bird.locations) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">栖息地</span>
            <span class="info-value">{{ formatList(bird.habitats) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">威胁因素</span>
            <span class="info-value">{{ formatList(bird.threats) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">所属洲别</span>
            <span class="info-value">{{ store.getBirdContinent(birdId) }}</span>
          </div>
        </div>

        <div class="detail-map-section">
          <h3 class="section-title">分布位置</h3>
          <div v-if="bird.lat != null && bird.lng != null" ref="detailMapRef" class="detail-map"></div>
          <p v-else class="empty-tip">当前切片中暂无可用坐标。</p>
        </div>

        <div class="detail-relations-section">
          <h3 class="section-title">当前已加载关系</h3>
          <div class="relation-chip-row">
            <span v-for="link in incidentLinks" :key="link.key" class="relation-chip">
              {{ relationText(link) }}
            </span>
          </div>
          <p v-if="!incidentLinks.length" class="empty-tip">当前没有已载入的相邻关系。</p>
        </div>
      </div>

      <div v-else class="loading-state">正在加载物种详情…</div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import L from 'leaflet'
import { useGraphStore } from '../stores/graphStore.js'

const route = useRoute()
const router = useRouter()
const store = useGraphStore()

const birdId = ref(route.params.id)
const switchQuery = ref('')
const summaryExpanded = ref(false)
const detailMapRef = ref(null)
let detailMapInstance = null

const endangermentLabels = {
  CR: '极危 (CR)',
  EN: '濒危 (EN)',
  VU: '易危 (VU)',
  NT: '近危 (NT)',
  LC: '无危 (LC)'
}

function statusClass(status) {
  return {
    CR: 'status-cr',
    EN: 'status-en',
    VU: 'status-vu',
    NT: 'status-nt',
    LC: 'status-lc'
  }[status] || 'status-lc'
}

function statusLabel(status) {
  return {
    CR: '极危',
    EN: '濒危',
    VU: '易危',
    NT: '近危',
    LC: '无危'
  }[status] || status
}

function statusGradient(status) {
  const gradients = {
    CR: 'linear-gradient(135deg, #fecaca, #ef4444)',
    EN: 'linear-gradient(135deg, #fed7aa, #f97316)',
    VU: 'linear-gradient(135deg, #fef08a, #eab308)',
    NT: 'linear-gradient(135deg, #bbf7d0, #22c55e)',
    LC: 'linear-gradient(135deg, #bbf7d0, #16a34a)'
  }
  return gradients[status] || 'linear-gradient(135deg, #e2e8f0, #94a3b8)'
}

function onDetailImgError(event) {
  event.target.style.display = 'none'
}

const bird = computed(() => store.getNodeById(birdId.value))

const displaySummary = computed(() => {
  if (!bird.value?.summary) return '暂无简介'
  if (summaryExpanded.value) return bird.value.summary
  if (bird.value.summary.length > 100) return `${bird.value.summary.slice(0, 100)}…`
  return bird.value.summary
})

const switchResults = computed(() => {
  const query = switchQuery.value.trim()
  if (!query) {
    return store.summaryBirds.slice(0, 20)
  }
  return store.findBirdMatches(query, 20)
})

const incidentLinks = computed(() => store.getIncidentLinks(birdId.value))

const taxonomyItems = computed(() => {
  const node = bird.value || {}
  return [
    ['界', node.kingdomCn || node.kingdom || '动物界'],
    ['门', node.phylumCn || node.phylum || '脊索动物门'],
    ['纲', node.classCn || node.class || '鸟纲'],
    ['目', node.orderCn || node.order],
    ['科', node.familyCn || node.family],
    ['属', node.genusCn || node.genus],
    ['种', node.speciesCn || node.species || node.name]
  ].map(([label, value]) => ({ label, value: value || '暂无' }))
})

function formatList(values) {
  return Array.isArray(values) && values.length ? values.join('、') : '暂无'
}

function relationText(link) {
  const otherId = link.source === birdId.value ? link.target : link.source
  const other = store.getNodeById(otherId)
  const otherName = other?.name || otherId
  return `${link.label || link.relation} · ${otherName}`
}

function switchBird(id) {
  if (!id || id === birdId.value) return
  router.push(`/bird/${id}`)
}

async function ensureCurrentBirdLoaded(id) {
  await store.loadInitialData()
  await store.ensureBirdLoaded(id)
  store.setActiveNode(id)
}

function destroyDetailMap() {
  if (detailMapInstance) {
    detailMapInstance.remove()
    detailMapInstance = null
  }
}

function initDetailMap() {
  destroyDetailMap()
  if (!detailMapRef.value || !bird.value || bird.value.lat == null || bird.value.lng == null) return

  detailMapInstance = L.map(detailMapRef.value, {
    zoomControl: true,
    scrollWheelZoom: true,
    worldCopyJump: false,
    maxBounds: [[-85, -180], [85, 180]],
    maxBoundsViscosity: 1
  }).setView([bird.value.lat, bird.value.lng], 5)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    noWrap: true,
    bounds: [[-85, -180], [85, 180]],
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(detailMapInstance)

  L.marker([bird.value.lat, bird.value.lng])
    .addTo(detailMapInstance)
    .bindPopup(`<strong>${bird.value.name}</strong>`)
    .openPopup()
}

watch(() => route.params.id, async newId => {
  birdId.value = newId
  summaryExpanded.value = false
  await ensureCurrentBirdLoaded(newId)
  await nextTick()
  initDetailMap()
})

watch(bird, async () => {
  await nextTick()
  initDetailMap()
})

onMounted(async () => {
  await ensureCurrentBirdLoaded(birdId.value)
  await nextTick()
  initDetailMap()
})

onBeforeUnmount(() => {
  destroyDetailMap()
})
</script>

<style scoped>
.detail-page {
  display: flex;
  gap: 18px;
  min-height: 60vh;
}

.detail-sidebar {
  width: 280px;
  flex-shrink: 0;
  padding: 16px;
}

.sidebar-title {
  margin: 0 0 12px;
  font-size: 15px;
  color: var(--heading-color);
}

.switch-input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: var(--nav-bg);
  color: var(--text-color);
  font-size: 13px;
  outline: none;
}

.switch-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 72vh;
  margin-top: 12px;
  overflow-y: auto;
}

.switch-item {
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--card-bg);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.switch-item:hover,
.switch-item.active {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.switch-name {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: var(--heading-color);
}

.switch-meta {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.detail-content-area {
  flex: 1;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  margin-bottom: 12px;
  border: 1px solid var(--panel-border);
  border-radius: 999px;
  background: var(--nav-bg);
  color: var(--text-color);
  font-size: 13px;
  cursor: pointer;
}

.detail-card-inner {
  padding: 24px;
  border-radius: 24px;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  box-shadow: var(--shadow);
}

.detail-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 18px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.detail-bird-name {
  margin: 0;
  font-size: 28px;
  font-family: "Alegreya", "Source Han Serif SC", "Noto Serif SC", serif;
  color: var(--heading-color);
}

.detail-status {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.status-cr { background: #dc2626; }
.status-en { background: #b45309; }
.status-vu { background: #ea580c; }
.status-nt { background: #ca8a04; }
.status-lc { background: #16a34a; }

.detail-image-wrap {
  position: relative;
  width: 100%;
  height: 300px;
  margin-bottom: 20px;
  border-radius: 18px;
  overflow: hidden;
  background: #e2e8f0;
}

.detail-image-bg {
  position: absolute;
  inset: 0;
  opacity: 0.2;
}

.detail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-image-placeholder {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 28px;
  font-weight: 700;
  color: rgba(15, 23, 42, 0.72);
}

.detail-image-status {
  position: absolute;
  top: 16px;
  right: 16px;
  padding: 6px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
}

.detail-summary-section {
  margin-bottom: 20px;
}

.detail-summary-text {
  margin: 0 0 10px;
  color: var(--text-color);
  line-height: 1.7;
  font-size: 15px;
}

.expand-btn {
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: var(--nav-bg);
  color: var(--accent);
  cursor: pointer;
}

.detail-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  padding: 16px;
  border-radius: 14px;
  background: var(--accent-soft);
  text-align: center;
  border: 1px solid var(--panel-border);
}

.stat-number {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: var(--accent);
  line-height: 1.1;
}

.stat-label {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.detail-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.info-item {
  padding: 14px 16px;
  border-radius: 14px;
  background: var(--accent-soft);
  border: 1px solid var(--panel-border);
}

.info-label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 14px;
  color: var(--text-color);
  font-weight: 500;
}

.detail-map-section,
.detail-relations-section {
  margin-bottom: 18px;
}

.section-title {
  margin: 0 0 12px;
  font-size: 16px;
  color: var(--heading-color);
}

.detail-map {
  width: 100%;
  height: 260px;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--panel-border);
}

.relation-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.relation-chip {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 999px;
  background: var(--accent-soft);
  border: 1px solid var(--panel-border);
  font-size: 13px;
  color: var(--text-color);
}

.empty-tip,
.loading-state {
  color: var(--text-secondary);
  font-size: 14px;
}

.loading-state {
  padding: 60px;
  text-align: center;
}

@media (max-width: 980px) {
  .detail-page {
    flex-direction: column;
  }

  .detail-sidebar {
    width: 100%;
  }

  .switch-list {
    max-height: 240px;
  }
}

@media (max-width: 760px) {
  .detail-stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .detail-info-grid {
    grid-template-columns: 1fr;
  }

  .detail-image-wrap {
    height: 220px;
  }
}
</style>

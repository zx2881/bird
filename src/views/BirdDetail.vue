<template>
  <div class="detail-page">
    <button class="help-float-btn" @click="helpGuide.open('bird-detail')" title="使用说明">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    </button>

    <HelpModal subtitle="鸟类详情页 · 功能介绍">
      <div class="help-section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="7" cy="6" r="3.5"/><circle cx="17" cy="5" r="3"/><circle cx="12" cy="16" r="3.5"/></svg>
          鸟类详情页功能
        </h3>
        <ul>
          <li><strong>物种信息：</strong>顶部展示鸟类中文名、英文名和学名，以及 IUCN 保护等级、分布地点数、栖息地数和关联实体数统计。</li>
          <li><strong>分类路径：</strong>显示从界到种的完整七级分类层级，点击任意层级可跳转对应详情。</li>
          <li><strong>分布地图：</strong>若该物种有坐标数据，展示 Leaflet 地图标注分布位置。</li>
          <li><strong>关联关系：</strong>展示该物种与地点、栖息地、威胁因素等实体的所有关系，点击可跳转。</li>
          <li><strong>摘要信息：</strong>从 Wikipedia 抓取或 CSV 导入的物种描述文本。</li>
        </ul>
      </div>
      <div class="help-section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h12M4 10h12M4 16h12"/></svg>
          侧边栏导航
        </h3>
        <ul>
          <li>左侧边栏支持搜索和快速切换到其他鸟类物种，搜索结果实时显示中文名和英文名。</li>
        </ul>
      </div>
    </HelpModal>

    <aside class="detail-sidebar panel">
      <h3 class="sidebar-title">
        <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h12M4 10h12M4 16h12"/></svg>
        切换物种
      </h3>
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
        <p v-if="!switchResults.length" class="switch-empty">未找到匹配物种</p>
      </div>
    </aside>

    <section class="detail-content-area">
      <button class="back-btn" @click="router.back()">
        <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="12 4 6 10 12 16"/></svg>
        返回图谱
      </button>

      <Transition name="detail-enter" mode="out-in">
        <div v-if="bird" :key="birdId" class="detail-card-inner">
          <div class="detail-hero" :class="`hero-${bird.status || 'lc'}`">
            <div class="detail-hero-bg" :style="{ background: statusGradient(bird.status) }"></div>
            <img
              v-if="bird.imageUrl"
              :src="bird.imageUrl"
              :alt="bird.name"
              class="detail-hero-img"
              @error="onDetailImgError"
            />
            <div class="detail-hero-placeholder" v-else>
              <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1" opacity="0.5">
                <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
              </svg>
              <span>{{ bird.name }}</span>
            </div>
            <div class="detail-hero-overlay"></div>
            <div class="detail-hero-content">
              <div class="detail-header">
                <h2 class="detail-bird-name">{{ bird.name }}</h2>
                <div class="detail-header-row">
                  <span v-if="bird.status" class="detail-status" :class="`hero-status-${bird.status || 'lc'}`">
                    {{ endangermentLabels[bird.status] || bird.status }}
                  </span>
                  <span v-if="bird.englishName" class="detail-english-inline">{{ bird.englishName }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="detail-taxonomy-path">
            <div
              v-for="(item, i) in taxonomyItems"
              :key="item.label"
              class="taxonomy-node"
              :class="{ 'taxonomy-node-last': i === taxonomyItems.length - 1, 'taxonomy-node-missing': !item.value || item.value === '暂无' }"
            >
              <div class="taxonomy-dot" :class="{ 'taxonomy-dot-active': i === taxonomyItems.length - 1 }">
                <span class="taxonomy-dot-label">{{ item.label }}</span>
              </div>
              <span class="taxonomy-node-value">{{ item.value || '暂无' }}</span>
              <svg v-if="i < taxonomyItems.length - 1" class="taxonomy-connector" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            </div>
          </div>

          <div class="detail-summary-section">
            <p class="detail-summary-text">{{ displaySummary }}</p>
            <button
              v-if="bird.summary && bird.summary.length > 100"
              class="expand-btn"
              @click="summaryExpanded = !summaryExpanded"
            >
              {{ summaryExpanded ? '收起 ▲' : '展开全文 ▼' }}
            </button>
          </div>

          <div class="detail-stats-row">
            <div class="stat-card" :style="{ animationDelay: '0.05s' }">
              <span class="stat-number">{{ bird.locations?.length || 0 }}</span>
              <span class="stat-label">分布地点</span>
            </div>
            <div class="stat-card" :style="{ animationDelay: '0.1s' }">
              <span class="stat-number">{{ bird.habitats?.length || 0 }}</span>
              <span class="stat-label">栖息地类型</span>
            </div>
            <div class="stat-card" :style="{ animationDelay: '0.15s' }">
              <span class="stat-number">{{ bird.threats?.length || 0 }}</span>
              <span class="stat-label">威胁因素</span>
            </div>
            <div class="stat-card" :style="{ animationDelay: '0.2s' }">
              <span class="stat-number">{{ store.getNodeDegree(birdId) }}</span>
              <span class="stat-label">当前关联</span>
            </div>
          </div>

          <div class="detail-info-grid">
            <div class="info-item">
              <span class="info-label">英文名</span>
              <span class="info-value">{{ bird.englishName || '暂无' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">学名</span>
              <span class="info-value"><em>{{ bird.latinName || '暂无' }}</em></span>
            </div>
            <div class="info-item">
              <span class="info-label">所属洲别</span>
              <span class="info-value">{{ store.getBirdContinent(birdId) }}</span>
            </div>
            <div class="info-item info-item-full">
              <span class="info-label">主要分布</span>
              <span class="info-value">{{ formatList(bird.locations) }}</span>
            </div>
            <div class="info-item info-item-full">
              <span class="info-label">栖息地</span>
              <span class="info-value">{{ formatList(bird.habitats) }}</span>
            </div>
            <div class="info-item info-item-full">
              <span class="info-label">威胁因素</span>
              <span class="info-value">{{ formatList(bird.threats) }}</span>
            </div>
          </div>

          <div class="detail-map-section">
            <h3 class="section-title">
              <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
              分布位置
            </h3>
            <div v-if="bird.lat != null && bird.lng != null" ref="detailMapRef" class="detail-map"></div>
            <p v-else class="empty-tip">当前切片中暂无可用坐标。</p>
          </div>

          <div class="detail-relations-section">
            <h3 class="section-title">
              <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="10" cy="5" r="3"/><path d="M3 16c0-3.5 3.13-6 7-6s7 2.5 7 6"/></svg>
              当前已加载关系
            </h3>
            <div v-if="incidentLinks.length" class="relation-chip-row">
              <span
                v-for="link in incidentLinks"
                :key="link.key"
                class="relation-chip"
                :class="`chip-${relationChipType(link.relation)}`"
              >
                <span class="chip-type">{{ link.label || link.relation }}</span>
                <span class="chip-sep"></span>
                <span class="chip-target">{{ relationOtherName(link) }}</span>
              </span>
            </div>
            <p v-else class="empty-tip">当前没有已载入的相邻关系。</p>
          </div>
        </div>

        <div v-else key="loading" class="loading-state">
          <span class="loading-spinner"></span>
          正在加载物种详情…
        </div>
      </Transition>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import L from 'leaflet'
import { useGraphStore } from '../stores/graphStore.js'
import { useHelpGuide } from '../composables/useHelpGuide.js'
import HelpModal from '../components/HelpModal.vue'

const route = useRoute()
const router = useRouter()
const store = useGraphStore()
const helpGuide = useHelpGuide()

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
    CR: 'linear-gradient(135deg, #7f1d1d 0%, #dc2626 40%, #fca5a5 100%)',
    EN: 'linear-gradient(135deg, #7c2d12 0%, #ea580c 40%, #fdba74 100%)',
    VU: 'linear-gradient(135deg, #713f12 0%, #ca8a04 40%, #fde047 100%)',
    NT: 'linear-gradient(135deg, #14532d 0%, #16a34a 40%, #86efac 100%)',
    LC: 'linear-gradient(135deg, #0f2b33 0%, #0f766e 60%, #5eead4 100%)'
  }
  return gradients[status] || 'linear-gradient(135deg, #1e293b 0%, #475569 60%, #94a3b8 100%)'
}

function relationChipType(relation) {
  const map = {
    'lives_in': 'lives',
    'has_habitat': 'habitat',
    'faces_threat': 'threat',
    'belongs_to_order': 'taxonomy',
    'belongs_to_family': 'taxonomy',
    'belongs_to_genus': 'taxonomy',
    'located_in': 'lives'
  }
  return map[relation] || 'default'
}

function relationOtherName(link) {
  const otherId = link.source === birdId.value ? link.target : link.source
  const other = store.getNodeById(otherId)
  return other?.name || otherId
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

  const statusColor = {
    CR: '#dc2626', EN: '#ea580c', VU: '#ca8a04', NT: '#16a34a', LC: '#0f766e'
  }[bird.value.status] || '#0f766e'

  const markerIcon = L.divIcon({
    className: 'detail-marker-icon',
    html: `<div style="width:18px;height:18px;border-radius:50%;background:${statusColor};border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.3);"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    popupAnchor: [0, -9]
  })

  L.marker([bird.value.lat, bird.value.lng], { icon: markerIcon })
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
  setTimeout(() => helpGuide.checkFirstVisit('bird-detail'), 800)
})

onBeforeUnmount(() => {
  destroyDetailMap()
})
</script>

<style scoped>
.detail-page {
  display: flex;
  gap: 20px;
  min-height: 60vh;
}

.detail-sidebar {
  width: 280px;
  flex-shrink: 0;
  padding: 18px;
}

.sidebar-title {
  margin: 0 0 14px;
  font-size: 14px;
  font-weight: 700;
  color: var(--heading-color);
  display: flex;
  align-items: center;
  gap: 8px;
}

.switch-input {
  width: 100%;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: var(--nav-bg);
  color: var(--text-color);
  font-size: 13px;
  outline: none;
  transition: all 0.25s ease;
}
.switch-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(15,118,110,0.08); }
.switch-input::placeholder { color: var(--text-secondary); opacity: 0.6; }

.switch-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 68vh;
  margin-top: 14px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--panel-border) transparent;
}

.switch-item {
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--card-bg);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}
.switch-item:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
  transform: translateX(4px);
}
.switch-item.active {
  border-color: var(--accent);
  background: var(--accent-soft);
  box-shadow: 0 0 0 3px rgba(15,118,110,0.1);
}
.switch-name { display: block; font-size: 14px; font-weight: 700; color: var(--heading-color); }
.switch-meta { display: block; margin-top: 4px; font-size: 11px; color: var(--text-secondary); }
.switch-empty { padding: 20px; text-align: center; font-size: 13px; color: var(--text-secondary); }

.detail-content-area { flex: 1; min-width: 0; }

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  margin-bottom: 14px;
  border: 1px solid var(--panel-border);
  border-radius: 999px;
  background: var(--nav-bg);
  color: var(--text-color);
  font-size: 13px; font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
}
.back-btn:hover { border-color: var(--accent); background: var(--accent-soft); color: var(--accent); }

.detail-enter-enter-active { transition: opacity 0.3s ease, transform 0.3s cubic-bezier(0.16,1,0.3,1); }
.detail-enter-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.detail-enter-enter-from { opacity: 0; transform: translateY(16px); }
.detail-enter-leave-to { opacity: 0; transform: translateY(-8px); }

.detail-card-inner {
  border-radius: var(--radius-xl);
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.detail-hero {
  position: relative;
  width: 100%;
  height: 340px;
  overflow: hidden;
}
.detail-hero-bg { position: absolute; inset: 0; }
.detail-hero-img { width: 100%; height: 100%; object-fit: cover; position: relative; z-index: 1; }
.detail-hero-placeholder {
  position: relative; z-index: 1;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  width: 100%; height: 100%;
  font-size: 22px; font-weight: 700; color: rgba(255,255,255,0.8);
  gap: 12px;
}
.detail-hero-overlay {
  position: absolute; inset: 0; z-index: 2;
  background: linear-gradient(180deg, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.5) 60%, rgba(0,0,0,0.75) 100%);
}
.detail-hero-content {
  position: absolute; bottom: 0; left: 0; right: 0; z-index: 3;
  padding: 32px 28px 28px;
}
.detail-header { display: flex; flex-direction: column; gap: 10px; }
.detail-bird-name {
  margin: 0; font-size: 34px; font-weight: 800;
  font-family: "Alegreya","Source Han Serif SC","Noto Serif SC",serif;
  color: #fff; text-shadow: 0 2px 12px rgba(0,0,0,0.4);
  line-height: 1.15;
}
.detail-header-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.detail-status {
  padding: 5px 16px; border-radius: 999px;
  font-size: 12px; font-weight: 700; color: #fff;
  backdrop-filter: blur(6px);
}
.hero-status-CR { background: rgba(220,38,38,0.85); }
.hero-status-EN { background: rgba(234,88,12,0.85); }
.hero-status-VU { background: rgba(202,138,4,0.85); }
.hero-status-NT { background: rgba(22,163,74,0.85); }
.hero-status-LC { background: rgba(15,118,110,0.85); }
.detail-english-inline {
  font-size: 15px; color: rgba(255,255,255,0.85); font-style: italic;
  text-shadow: 0 1px 6px rgba(0,0,0,0.3);
}

.detail-taxonomy-path {
  display: flex; align-items: flex-start; gap: 0;
  padding: 20px 24px; overflow-x: auto;
  background: var(--nav-bg);
  border-bottom: 1px solid var(--panel-border);
  scrollbar-width: thin; scrollbar-color: var(--panel-border) transparent;
}
.taxonomy-node {
  display: flex; flex-direction: column; align-items: center;
  gap: 8px; flex-shrink: 0; position: relative;
}
.taxonomy-dot {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--card-bg); border: 2px solid var(--panel-border);
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; color: var(--text-secondary);
  transition: all 0.3s ease;
}
.taxonomy-dot-active {
  background: var(--accent); border-color: var(--accent);
  color: #fff; box-shadow: 0 0 0 4px var(--accent-soft);
  width: 42px; height: 42px;
}
.taxonomy-node-missing .taxonomy-dot { opacity: 0.4; }
.taxonomy-dot-label { font-size: 11px; }
.taxonomy-node-value {
  font-size: 12px; color: var(--text-color); font-weight: 500;
  max-width: 72px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.taxonomy-node-missing .taxonomy-node-value { color: var(--text-secondary); }
.taxonomy-connector {
  position: absolute; top: 14px; left: calc(100% - 4px);
  color: var(--text-secondary); opacity: 0.5;
}

.detail-summary-section { padding: 20px 28px 12px; }
.detail-summary-text { margin: 0 0 10px; color: var(--text-color); line-height: 1.78; font-size: 15px; }
.expand-btn {
  padding: 7px 16px; border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: var(--nav-bg); color: var(--accent);
  font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.2s ease;
}
.expand-btn:hover { border-color: var(--accent); background: var(--accent-soft); }

.detail-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  padding: 8px 28px 20px;
}
.stat-card {
  padding: 20px 16px; border-radius: var(--radius-lg);
  background: var(--accent-soft); text-align: center;
  border: 1px solid var(--panel-border);
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  animation: stat-pop-in 0.45s cubic-bezier(0.16,1,0.3,1) backwards;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  border-color: var(--accent);
}
@keyframes stat-pop-in {
  from { opacity: 0; transform: scale(0.9) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.stat-number { display: block; font-size: 32px; font-weight: 800; color: var(--accent); line-height: 1.1; font-variant-numeric: tabular-nums; }
.stat-label { display: block; margin-top: 6px; font-size: 12px; color: var(--text-secondary); font-weight: 500; }

.detail-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding: 0 28px 20px;
}
.info-item {
  padding: 16px 18px; border-radius: var(--radius-lg);
  background: var(--accent-soft); border: 1px solid var(--panel-border);
  transition: all 0.25s ease;
}
.info-item:hover { border-color: var(--accent); }
.info-item-full { grid-column: 1 / -1; }
.info-label { display: block; margin-bottom: 6px; font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em; }
.info-value { font-size: 14px; color: var(--text-color); font-weight: 500; line-height: 1.6; }

.detail-map-section,
.detail-relations-section {
  padding: 0 28px 24px;
}
.section-title {
  margin: 0 0 14px; font-size: 16px; font-weight: 700;
  color: var(--heading-color);
  display: flex; align-items: center; gap: 8px;
}

.detail-map {
  width: 100%;
  height: 280px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--panel-border);
}

.relation-chip-row { display: flex; flex-wrap: wrap; gap: 10px; }
.relation-chip {
  display: inline-flex; align-items: center; gap: 0;
  border-radius: 999px; font-size: 13px; color: var(--text-color);
  border: 1px solid var(--panel-border);
  background: var(--card-bg);
  overflow: hidden;
  transition: all 0.25s ease;
}
.relation-chip:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.chip-type {
  padding: 8px 12px; font-size: 11px; font-weight: 600;
  color: #fff; letter-spacing: 0.02em;
}
.chip-sep { width: 1px; align-self: stretch; background: var(--panel-border); }
.chip-target { padding: 8px 14px; font-weight: 500; }

.chip-lives .chip-type { background: var(--success); }
.chip-habitat .chip-type { background: #0284c7; }
.chip-threat .chip-type { background: var(--danger); }
.chip-taxonomy .chip-type { background: #7c3aed; }
.chip-default .chip-type { background: var(--accent); }
.chip-lives { border-color: rgba(22,163,74,0.3); }
.chip-habitat { border-color: rgba(2,132,199,0.3); }
.chip-threat { border-color: rgba(220,38,38,0.3); }
.chip-taxonomy { border-color: rgba(124,58,237,0.3); }

.empty-tip { color: var(--text-secondary); font-size: 14px; }
.loading-state {
  padding: 80px 40px; text-align: center; color: var(--text-secondary);
  display: flex; flex-direction: column; align-items: center; gap: 14px; font-size: 15px;
}
.loading-spinner {
  width: 32px; height: 32px; border-radius: 50%;
  border: 3px solid var(--panel-border);
  border-top-color: var(--accent);
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 980px) {
  .detail-page { flex-direction: column; }
  .detail-sidebar { width: 100%; }
  .switch-list { max-height: 240px; }
}

@media (max-width: 760px) {
  .detail-hero { height: 240px; }
  .detail-hero-content { padding: 24px 20px; }
  .detail-bird-name { font-size: 26px; }
  .detail-stats-row { grid-template-columns: repeat(2, 1fr); padding: 8px 20px 16px; }
  .detail-info-grid { grid-template-columns: 1fr; padding: 0 20px 16px; }
  .detail-taxonomy-path { padding: 14px 16px; }
  .detail-summary-section { padding: 16px 20px 8px; }
  .detail-map-section, .detail-relations-section { padding: 0 20px 20px; }
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

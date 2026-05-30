<template>
  <div class="detail-page">
    <button class="help-float-btn" @click="helpGuide.open('location-detail')" title="使用说明">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    </button>

    <HelpModal subtitle="地点详情页 · 功能介绍">
      <div class="help-section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
          地点详情页功能
        </h3>
        <ul>
          <li><strong>位置信息：</strong>顶部展示地点名称、所属大洲、经纬度坐标和关联的鸟类数量统计。</li>
          <li><strong>分布地图：</strong>Leaflet 地图标注该地点的位置，支持缩放和拖拽查看周边区域。</li>
          <li><strong>该地鸟类：</strong>列出分布于该地点的所有鸟类物种卡片，包含照片、名称和保护等级标签。点击卡片跳转鸟类详情页。</li>
          <li><strong>关联关系：</strong>若该地点关联了栖息地类型或威胁因素，展示对应的关系列表。</li>
        </ul>
      </div>
      <div class="help-section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h12M4 10h12M4 16h12"/></svg>
          侧边栏导航
        </h3>
        <ul>
          <li>左侧边栏支持搜索和快速切换到其他分布地点。</li>
        </ul>
      </div>
    </HelpModal>

    <aside class="detail-sidebar panel">
      <h3 class="sidebar-title">
        <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
        切换地点
      </h3>
      <input
        v-model="switchQuery"
        type="text"
        class="switch-input"
        placeholder="搜索地点名称…"
      />
      <div class="switch-list">
        <button
          v-for="item in switchResults"
          :key="item.id"
          type="button"
          class="switch-item"
          :class="{ active: item.id === locId }"
          @click="switchLoc(item.id)"
        >
          <span class="switch-name">{{ item.name }}</span>
          <span class="switch-meta">{{ item.type === 'location' ? '地点' : '' }}</span>
        </button>
        <p v-if="!switchResults.length" class="switch-empty">未找到匹配地点</p>
      </div>
    </aside>

    <section class="detail-content-area">
      <button class="back-btn" @click="router.back()">
        <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="12 4 6 10 12 16"/></svg>
        返回图谱
      </button>

      <Transition name="detail-enter" mode="out-in">
        <div v-if="node" :key="locId" class="detail-card-inner">
          <div class="detail-hero loc-hero">
            <div class="detail-hero-bg"></div>
            <div class="detail-hero-overlay"></div>
            <div class="detail-hero-content">
              <div class="loc-hero-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                  <circle cx="12" cy="9" r="2.5"/>
                </svg>
              </div>
              <div class="detail-header">
                <h2 class="detail-loc-name">{{ node.name }}</h2>
                <div class="detail-header-row">
                  <span class="detail-type-badge">地点</span>
                  <span v-if="node.lat != null" class="loc-coords-badge">{{ node.lat.toFixed(4) }}, {{ node.lng.toFixed(4) }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="detail-summary-section">
            <p class="detail-summary-text">{{ displaySummary }}</p>
            <button
              v-if="node.summary && node.summary.length > 100"
              class="expand-btn"
              @click="summaryExpanded = !summaryExpanded"
            >
              {{ summaryExpanded ? '收起 ▲' : '展开全文 ▼' }}
            </button>
          </div>

          <div class="detail-stats-row">
            <div class="stat-card" :style="{ animationDelay: '0.05s' }">
              <span class="stat-number">{{ relatedBirds.length }}</span>
              <span class="stat-label">关联鸟类</span>
            </div>
            <div class="stat-card" :style="{ animationDelay: '0.15s' }">
              <span class="stat-number">{{ store.getNodeDegree(locId) }}</span>
              <span class="stat-label">总关联数</span>
            </div>
          </div>

          <div class="detail-info-grid">
            <div class="info-item">
              <span class="info-label">所属洲别</span>
              <span class="info-value">{{ store.getContinent(node.lat, node.lng) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">关联鸟类数</span>
              <span class="info-value">{{ relatedBirds.length }} 种</span>
            </div>
            <div class="info-item info-item-full">
              <span class="info-label">ID</span>
              <span class="info-value mono">{{ node.id }}</span>
            </div>
          </div>

          <div class="detail-map-section" v-if="node.lat != null && node.lng != null">
            <h3 class="section-title">
              <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
              地理位置
            </h3>
            <div ref="detailMapRef" class="detail-map"></div>
          </div>

          <div class="detail-relations-section">
            <h3 class="section-title">
              <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="10" cy="5" r="3"/><path d="M3 16c0-3.5 3.13-6 7-6s7 2.5 7 6"/></svg>
              关联鸟类 ({{ relatedBirds.length }})
            </h3>
            <div v-if="relatedBirds.length" class="relation-bird-grid">
              <div
                v-for="(bird, idx) in relatedBirds"
                :key="bird.id"
                class="relation-bird-card"
                :style="{ animationDelay: `${idx * 0.04}s` }"
                @click="router.push(`/bird/${bird.id}`)"
              >
                <div class="rb-card-top">
                  <div class="rb-avatar" :style="{ background: birdAvatarGradient(bird.status) }">
                    <span class="rb-avatar-text">{{ bird.name.charAt(0) }}</span>
                  </div>
                  <div class="rb-card-header">
                    <span class="rb-card-name">{{ bird.name }}</span>
                    <span class="rb-card-meta">{{ bird.englishName || bird.latinName || '' }}</span>
                  </div>
                </div>
                <svg class="rb-arrow" viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="7 4 13 10 7 16"/></svg>
              </div>
            </div>
            <p v-else class="empty-tip">当前没有已载入的关联鸟类。</p>
          </div>
        </div>

        <div v-else key="loading" class="loading-state">
          <span class="loading-spinner"></span>
          正在加载地点详情…
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

const locId = ref(route.params.id)
const switchQuery = ref('')
const summaryExpanded = ref(false)
const detailMapRef = ref(null)
let detailMapInstance = null

const node = computed(() => store.getNodeById(locId.value))

const displaySummary = computed(() => {
  if (!node.value?.summary) return '暂无简介'
  if (summaryExpanded.value) return node.value.summary
  if (node.value.summary.length > 100) return `${node.value.summary.slice(0, 100)}…`
  return node.value.summary
})

const relatedBirds = computed(() => {
  const links = store.getIncidentLinks(locId.value)
  const birds = []
  const seen = new Set()
  for (const link of links) {
    const otherId = link.source === locId.value ? link.target : link.source
    if (seen.has(otherId)) continue
    seen.add(otherId)
    const birdNode = store.getNodeById(otherId)
    if (birdNode && birdNode.type === 'bird') {
      birds.push(birdNode)
    }
  }
  return birds
})

function birdAvatarGradient(status) {
  const gradients = {
    CR: 'linear-gradient(135deg, #dc2626, #fca5a5)',
    EN: 'linear-gradient(135deg, #ea580c, #fdba74)',
    VU: 'linear-gradient(135deg, #ca8a04, #fde047)',
    NT: 'linear-gradient(135deg, #16a34a, #86efac)',
    LC: 'linear-gradient(135deg, #0f766e, #5eead4)'
  }
  return gradients[status] || 'linear-gradient(135deg, #475569, #94a3b8)'
}

const switchResults = computed(() => {
  const q = switchQuery.value.trim().toLowerCase()
  const locs = store.locationNodes.length ? store.locationNodes.filter(n => n.type === 'location') : store.summaryLocations
  if (!q) return locs.slice(0, 20)
  return locs.filter(n => n.name.toLowerCase().includes(q)).slice(0, 20)
})

function switchLoc(id) {
  if (!id || id === locId.value) return
  router.push(`/location/${id}`)
}

async function ensureCurrentLoaded(id) {
  await store.loadInitialData()
  await store.loadNodeChunk(id).catch(() => {})
  store.setActiveNode(id)
}

function destroyMap() {
  if (detailMapInstance) {
    detailMapInstance.remove()
    detailMapInstance = null
  }
}

function initMap() {
  destroyMap()
  if (!detailMapRef.value || !node.value || node.value.lat == null || node.value.lng == null) return
  detailMapInstance = L.map(detailMapRef.value, {
    zoomControl: true,
    scrollWheelZoom: true,
    worldCopyJump: false,
    maxBounds: [[-85, -180], [85, 180]],
    maxBoundsViscosity: 1
  }).setView([node.value.lat, node.value.lng], 6)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    noWrap: true,
    bounds: [[-85, -180], [85, 180]],
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(detailMapInstance)

  const locMarkerIcon = L.divIcon({
    className: 'detail-marker-icon',
    html: `<div style="width:22px;height:22px;border-radius:50%;background:#16a34a;border:3px solid #fff;box-shadow:0 2px 10px rgba(0,0,0,0.35);"></div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -11]
  })

  L.marker([node.value.lat, node.value.lng], { icon: locMarkerIcon })
    .addTo(detailMapInstance)
    .bindPopup(`<strong>${node.value.name}</strong>`)
    .openPopup()
}

watch(() => route.params.id, async newId => {
  locId.value = newId
  summaryExpanded.value = false
  await ensureCurrentLoaded(newId)
  await nextTick()
  initMap()
})

watch(node, async () => {
  await nextTick()
  initMap()
})

onMounted(async () => {
  await ensureCurrentLoaded(locId.value)
  await nextTick()
  initMap()
  setTimeout(() => helpGuide.checkFirstVisit('location-detail'), 800)
})

onBeforeUnmount(() => {
  destroyMap()
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
  height: 260px;
  overflow: hidden;
}
.loc-hero .detail-hero-bg {
  position: absolute; inset: 0;
  background: linear-gradient(135deg, #064e3b 0%, #16a34a 50%, #86efac 100%);
}
.loc-hero .detail-hero-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.45) 100%);
}
.detail-hero-content {
  position: absolute; bottom: 0; left: 0; right: 0; z-index: 3;
  padding: 28px 28px 24px;
  display: flex; flex-direction: column; align-items: center; gap: 14px;
}
.loc-hero-icon {
  width: 56px; height: 56px; border-radius: 16px;
  background: rgba(255,255,255,0.18);
  backdrop-filter: blur(8px);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}
.loc-hero-icon svg { width: 28px; height: 28px; }
.detail-header { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.detail-loc-name {
  margin: 0; font-size: 30px; font-weight: 800;
  font-family: "Alegreya","Source Han Serif SC","Noto Serif SC",serif;
  color: #fff; text-shadow: 0 2px 10px rgba(0,0,0,0.35);
  line-height: 1.15; text-align: center;
}
.detail-header-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: center; }
.detail-type-badge {
  padding: 4px 14px; border-radius: 999px;
  font-size: 11px; font-weight: 700; color: #fff;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(6px);
}
.loc-coords-badge {
  padding: 4px 14px; border-radius: 999px;
  font-size: 11px; font-weight: 500; color: rgba(255,255,255,0.85);
  background: rgba(0,0,0,0.25);
  backdrop-filter: blur(6px);
  font-family: monospace;
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
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  padding: 8px 28px 20px;
}
.stat-card {
  padding: 22px 18px; border-radius: var(--radius-lg);
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
.stat-number { display: block; font-size: 36px; font-weight: 800; color: var(--accent); line-height: 1.1; font-variant-numeric: tabular-nums; }
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
.info-value.mono { font-size: 12px; word-break: break-all; font-family: monospace; }

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
  height: 300px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--panel-border);
}

.relation-bird-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}
.relation-bird-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; border-radius: var(--radius-lg);
  border: 1px solid var(--panel-border);
  background: var(--card-bg);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  animation: bird-card-slide 0.4s cubic-bezier(0.16,1,0.3,1) backwards;
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.relation-bird-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 28px rgba(0,0,0,0.1);
  border-color: var(--accent);
}
.relation-bird-card:active { transform: translateY(-1px) scale(0.98); }
@keyframes bird-card-slide {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.rb-card-top {
  display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;
}
.rb-avatar {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
.rb-avatar-text {
  font-size: 16px; font-weight: 700; color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}
.rb-card-header {
  display: flex; flex-direction: column; gap: 3px; min-width: 0;
}
.rb-card-name {
  font-size: 14px; font-weight: 700; color: var(--heading-color);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.rb-card-meta {
  font-size: 11px; color: var(--text-secondary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  font-style: italic;
}
.rb-arrow {
  color: var(--text-secondary); opacity: 0; flex-shrink: 0;
  transition: all 0.25s ease; transform: translateX(-4px);
}
.relation-bird-card:hover .rb-arrow {
  opacity: 1; color: var(--accent);
  transform: translateX(0);
}

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
  .detail-hero { height: 200px; }
  .detail-hero-content { padding: 20px 18px; }
  .detail-loc-name { font-size: 24px; }
  .loc-hero-icon { width: 44px; height: 44px; border-radius: 12px; }
  .loc-hero-icon svg { width: 22px; height: 22px; }
  .detail-stats-row { grid-template-columns: 1fr 1fr; padding: 8px 20px 16px; }
  .detail-info-grid { grid-template-columns: 1fr; padding: 0 20px 16px; }
  .detail-summary-section { padding: 16px 20px 8px; }
  .detail-map-section, .detail-relations-section { padding: 0 20px 20px; }
  .relation-bird-grid { grid-template-columns: 1fr; }
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

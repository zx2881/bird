<template>
  <div class="detail-page" :class="layoutMode">
    <div v-if="layoutMode === 'panel'" class="panel-left">
      <div class="panel-thumb-list">
        <div v-for="bird in allBirds" :key="bird.id" class="thumb-card" :class="{ 'thumb-active': bird.id === birdId }" @click="switchBird(bird.id)">
          <img :src="bird.imageUrl || `https://picsum.photos/seed/${bird.id}/80/60`" :alt="bird.name" />
          <span>{{ bird.name }}</span>
        </div>
      </div>
    </div>
    <div class="detail-content-area" :class="{ 'detail-modal': layoutMode === 'modal' }">
      <button class="back-btn" @click="router.back()">← 返回</button>
      <div v-if="bird" class="detail-card-inner">
        <div class="detail-top-bar">
          <div v-if="layoutMode === 'modal'" class="modal-backdrop-bg"></div>
          <div class="detail-header">
            <h2 class="detail-bird-name">{{ bird.name }}</h2>
            <span v-if="bird.status" class="detail-status" :class="statusClass(bird.status)">{{ endangermentLabels[bird.status] || bird.status }}</span>
          </div>
          <div class="layout-toggle">
            <button class="toggle-btn" :class="{ 'toggle-active': layoutMode === 'modal' }" @click="layoutMode = 'modal'" title="居中卡片模式">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="3"/><line x1="3" y1="9" x2="21" y2="9"/></svg>
            </button>
            <button class="toggle-btn" :class="{ 'toggle-active': layoutMode === 'panel' }" @click="layoutMode = 'panel'" title="右侧面板模式">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="3"/><line x1="15" y1="3" x2="15" y2="21"/></svg>
            </button>
          </div>
        </div>
        <div class="detail-image-wrap">
          <div class="detail-image-bg" :style="{ background: statusGradient(bird.status) }"></div>
          <img :src="bird.imageUrl || `https://picsum.photos/seed/${bird.id}/800/400`" :alt="bird.name" class="detail-image" @error="onDetailImgError" />
          <div v-if="bird.status" class="detail-image-status" :class="statusClass(bird.status)">{{ statusLabel(bird.status) }}</div>
        </div>
        <div class="detail-summary-section">
          <p class="detail-summary-text">{{ displaySummary }}</p>
          <button v-if="bird.summary && bird.summary.length > 80" class="expand-btn" @click="summaryExpanded = !summaryExpanded">
            {{ summaryExpanded ? '收起' : '展开全文' }}
            <svg :class="{ 'rotated': summaryExpanded }" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
        </div>
        <div class="detail-stats-row">
          <div class="stat-card"><span class="stat-number">{{ bird.locations?.length || 0 }}</span><span class="stat-label">分布地点</span></div>
          <div class="stat-card"><span class="stat-number">{{ bird.habitats?.length || 0 }}</span><span class="stat-label">栖息地类型</span></div>
          <div class="stat-card"><span class="stat-number">{{ bird.threats?.length || 0 }}</span><span class="stat-label">威胁因素</span></div>
          <div class="stat-card"><span class="stat-number">{{ relatedBirds.length }}</span><span class="stat-label">相关鸟类</span></div>
        </div>
        <div class="detail-info-grid">
          <div class="info-item"><span class="info-label">📖 英文名</span><span class="info-value">{{ bird.englishName || '暂无' }}</span></div>
          <div class="info-item"><span class="info-label">🔬 学名</span><span class="info-value"><em>{{ bird.latinName || '暂无' }}</em></span></div>
          <div class="info-item"><span class="info-label">📍 主要分布</span><span class="info-value">{{ formatList(bird.locations) }}</span></div>
          <div class="info-item"><span class="info-label">🌿 栖息地</span><span class="info-value">{{ formatList(bird.habitats) }}</span></div>
          <div class="info-item"><span class="info-label">⚠️ 威胁因素</span><span class="info-value">{{ formatList(bird.threats) }}</span></div>
        </div>
        <div class="detail-map-section">
          <h3 class="section-title">分布位置</h3>
          <div ref="detailMapRef" class="detail-map"></div>
        </div>
        <div class="detail-relations-section">
          <h3 class="section-title">🕊️ 相关关系</h3>
          <div v-if="relatedBirds.length" class="relation-list">
            <div v-for="rel in relatedBirds" :key="rel.link.key" class="relation-chip" @click="goToBird(rel.bird.id)">
              <span class="rel-emoji">{{ relationEmoji(rel.link.relation) }}</span>
              <div class="rel-content">
                <span class="rel-bird">{{ rel.bird.name }}</span>
                <span class="rel-label">{{ rel.link.label || rel.link.relation }}</span>
              </div>
            </div>
          </div>
          <p v-else class="no-relations">暂无相关关系数据</p>
        </div>
      </div>
      <div v-else class="loading-state">正在加载鸟类信息…</div>
    </div>
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
const summaryExpanded = ref(false)
const layoutMode = ref('modal')
const detailMapRef = ref(null)
let detailMapInstance = null

watch(() => route.params.id, (newId) => { birdId.value = newId })

const endangermentLabels = { CR: '极危 (CR)', EN: '濒危 (EN)', VU: '易危 (VU)', NT: '近危 (NT)', LC: '无危 (LC)' }
function statusClass(status) { return { CR: 'status-cr', EN: 'status-en', VU: 'status-vu', NT: 'status-nt', LC: 'status-lc' }[status] || 'status-lc' }
function statusLabel(status) { return { CR: '极危', EN: '濒危', VU: '易危', NT: '近危', LC: '无危' }[status] || status }
function statusGradient(status) {
  const g = { CR: 'linear-gradient(135deg, #fecaca, #ef4444)', EN: 'linear-gradient(135deg, #fed7aa, #f97316)', VU: 'linear-gradient(135deg, #fef08a, #eab308)', NT: 'linear-gradient(135deg, #bbf7d0, #22c55e)', LC: 'linear-gradient(135deg, #bbf7d0, #16a34a)' }
  return g[status] || 'linear-gradient(135deg, #e2e8f0, #94a3b8)'
}
function onDetailImgError(e) { e.target.style.display = 'none' }

const bird = computed(() => store.getNodeById(birdId.value))

const displaySummary = computed(() => {
  if (!bird.value?.summary) return '暂无简介'
  if (summaryExpanded.value) return bird.value.summary
  if (bird.value.summary.length > 80) return bird.value.summary.slice(0, 80) + '…'
  return bird.value.summary
})

const relatedBirds = computed(() => {
  const results = []; const seen = new Set()
  store.getIncidentLinks(birdId.value).forEach(link => {
    const otherId = link.source === birdId.value ? link.target : link.source
    const other = store.getNodeById(otherId)
    if (other && other.type === 'bird') {
      const key = `${other.id}-${link.relation}`
      if (seen.has(key)) return
      seen.add(key)
      results.push({ bird: other, link })
    }
  })
  return results
})

const allBirds = computed(() => store.birdNodes)

function formatList(arr) { return Array.isArray(arr) && arr.length ? arr.join('、') : '暂无' }
function relationEmoji(r) {
  const map = { distributed_in: '📍', lives_in: '🌿', has_status: '🔴', threatened_by: '⚠️', belongs_to: '🏷️' }
  return map[r] || '🔗'
}
function switchBird(id) { router.push(`/bird/${id}`) }
function goToBird(id) { router.push(`/bird/${id}`) }

function initDetailMap() {
  if (!detailMapRef.value || !bird.value || bird.value.lat == null || bird.value.lng == null) return
  if (detailMapInstance) { detailMapInstance.remove(); detailMapInstance = null }
  detailMapInstance = L.map(detailMapRef.value, { zoomControl: true, scrollWheelZoom: false }).setView([bird.value.lat, bird.value.lng], 5)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '&copy; OpenStreetMap contributors' }).addTo(detailMapInstance)
  L.marker([bird.value.lat, bird.value.lng]).addTo(detailMapInstance).bindPopup(`<strong>${bird.value.name}</strong>`).openPopup()
}

watch(bird, async () => { summaryExpanded.value = false; await nextTick(); initDetailMap() })

onMounted(async () => {
  if (!store.loaded) await store.loadData()
  await nextTick()
  setTimeout(() => { initDetailMap() }, 200)
})

onBeforeUnmount(() => { detailMapInstance?.remove() })
</script>

<style scoped>
.detail-page { display: flex; gap: 18px; min-height: 60vh; }
.detail-page.panel { position: relative; }
.panel-left { width: 280px; flex-shrink: 0; }
.panel-thumb-list { display: flex; flex-direction: column; gap: 8px; max-height: 70vh; overflow-y: auto; padding-right: 4px; }
.thumb-card { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 14px; background: var(--card-bg); border: 1px solid var(--panel-border); cursor: pointer; transition: all 0.2s ease; }
.thumb-card:hover { background: var(--card-bg); transform: translateX(2px); }
.thumb-active { border-color: var(--accent); background: var(--accent-soft); }
.thumb-card img { width: 48px; height: 36px; border-radius: 8px; object-fit: cover; }
.thumb-card span { font-size: 13px; color: var(--text-color); font-weight: 500; }
.detail-content-area { flex: 1; transition: all 0.35s ease; }
.detail-content-area.detail-modal { max-width: 800px; margin: 0 auto; }
.detail-card-inner { padding: 24px; border-radius: 24px; background: var(--card-bg); border: 1px solid var(--panel-border); box-shadow: var(--shadow); transition: all 0.35s ease; }
.detail-modal .detail-card-inner { position: relative; border: 2px solid rgba(255, 255, 255, 0.6); box-shadow: 0 24px 60px rgba(2, 8, 23, 0.25); backdrop-filter: blur(20px); }
.detail-top-bar { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; }
.detail-header { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.detail-bird-name { margin: 0; font-size: 28px; font-family: "Alegreya", "Source Han Serif SC", "Noto Serif SC", serif; color: var(--heading-color); }
.detail-status { padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; color: #fff; }
.status-cr { background: #dc2626; } .status-en { background: #b45309; } .status-vu { background: #ea580c; } .status-nt { background: #ca8a04; } .status-lc { background: #16a34a; }
.layout-toggle { display: flex; gap: 4px; padding: 3px; border-radius: 999px; background: rgba(18, 48, 59, 0.06); flex-shrink: 0; }
.toggle-btn { padding: 8px; border: none; border-radius: 999px; background: transparent; color: var(--text-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease; }
.toggle-btn:hover { background: rgba(18, 48, 59, 0.08); }
.toggle-active { background: #fff !important; color: #0f766e !important; box-shadow: 0 2px 8px rgba(31, 64, 76, 0.12); }
.detail-image-wrap { position: relative; width: 100%; height: 300px; border-radius: 18px; overflow: hidden; margin-bottom: 20px; background: #e2e8f0; }
.detail-image-bg { position: absolute; inset: 0; opacity: 0.2; }
.detail-image { width: 100%; height: 100%; object-fit: cover; }
.detail-image-status { position: absolute; top: 16px; right: 16px; padding: 6px 16px; border-radius: 999px; font-size: 13px; font-weight: 700; color: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.2); backdrop-filter: blur(4px); letter-spacing: 0.03em; }
.detail-stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { padding: 16px; border-radius: 14px; background: var(--accent-soft); text-align: center; border: 1px solid var(--panel-border); }
.stat-number { display: block; font-size: 28px; font-weight: 800; color: var(--accent); line-height: 1.1; }
.stat-label { display: block; font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
.detail-summary-section { margin-bottom: 20px; }
.detail-summary-text { margin: 0 0 8px; color: var(--text-color); line-height: 1.7; font-size: 15px; }
.expand-btn { display: inline-flex; align-items: center; gap: 4px; padding: 6px 14px; border: 1px solid var(--panel-border); border-radius: 999px; background: rgba(255, 255, 255, 0.7); color: var(--accent); font-size: 13px; cursor: pointer; transition: all 0.2s ease; }
.expand-btn:hover { background: var(--accent-soft); }
.expand-btn svg { transition: transform 0.25s ease; }
.expand-btn svg.rotated { transform: rotate(180deg); }
.detail-info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
.info-item { padding: 14px 16px; border-radius: 14px; background: var(--accent-soft); border: 1px solid var(--panel-border); }
.info-label { display: block; font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; }
.info-value { font-size: 14px; color: var(--text-color); font-weight: 500; }
.detail-map-section { margin-bottom: 18px; }
.section-title { margin: 0 0 12px; font-size: 16px; color: var(--heading-color); }
.detail-map { width: 100%; height: 260px; border-radius: 16px; overflow: hidden; border: 1px solid var(--panel-border); }
.detail-relations-section { margin-bottom: 0; }
.relation-list { display: flex; flex-wrap: wrap; gap: 10px; }
.relation-chip { display: inline-flex; align-items: center; gap: 10px; padding: 12px 18px; border-radius: 16px; background: var(--accent-soft); border: 1px solid var(--panel-border); cursor: pointer; transition: all 0.25s ease; min-width: 140px; }
.relation-chip:hover { transform: translateY(-2px); border-color: var(--accent); box-shadow: 0 6px 16px rgba(31, 64, 76, 0.1); }
.rel-emoji { font-size: 18px; }
.rel-content { display: flex; flex-direction: column; gap: 2px; }
.rel-bird { font-weight: 700; font-size: 14px; color: var(--heading-color); }
.rel-label { font-size: 11px; color: var(--text-secondary); }
.no-relations { color: var(--text-secondary); font-size: 14px; }
.back-btn { display: inline-flex; align-items: center; gap: 4px; padding: 8px 16px; margin-bottom: 12px; border: 1px solid var(--panel-border); border-radius: 999px; background: var(--nav-bg); color: var(--text-color); font-size: 13px; cursor: pointer; transition: all 0.2s; font-family: inherit; }
.back-btn:hover { background: var(--accent-soft); border-color: var(--accent); }
.loading-state { padding: 60px; text-align: center; color: var(--text-secondary); }
@media (max-width: 860px) {
  .detail-page.panel { flex-direction: column; }
  .panel-left { width: 100%; }
  .panel-thumb-list { flex-direction: row; overflow-x: auto; max-height: none; padding-bottom: 4px; }
  .thumb-card { flex-shrink: 0; flex-direction: column; width: 100px; text-align: center; }
  .thumb-card img { width: 64px; height: 48px; }
  .detail-info-grid { grid-template-columns: 1fr; }
  .detail-stats-row { grid-template-columns: repeat(2, 1fr); }
  .detail-image-wrap { height: 200px; }
}
</style>

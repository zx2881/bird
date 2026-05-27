<template>
  <div class="overview-page">
    <div class="hero-section">
      <div class="hero-intro">
        <h1 class="hero-title">鸟类生物多样性知识图谱</h1>
        <p class="hero-subtitle">全球 {{ store.totalBirdCount.toLocaleString() }} 个鸟类物种，{{ store.totalRelationCount.toLocaleString() }} 条知识关系的结构化概览</p>
      </div>
    </div>

    <div class="stats-bento">
      <div class="stat-card" v-for="(card, idx) in statCards" :key="card.id"
           :style="{ animationDelay: `${idx * 0.08}s` }">
        <div class="stat-card-glow" :style="{ background: card.glow }"></div>
        <div class="stat-card-inner">
          <div class="stat-icon-wrap" :style="{ background: card.iconBg, color: card.iconColor }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                 v-html="card.iconPaths"></svg>
          </div>
          <div class="stat-body">
            <span class="stat-value" :style="{ color: card.accent }">{{ card.value }}</span>
            <span class="stat-label">{{ card.label }}</span>
          </div>
          <div class="stat-spark"></div>
        </div>
      </div>
    </div>

    <div class="charts-bento">
      <div class="chart-card reveal-card" ref="continentCardEl">
        <div class="chart-card-header">
          <div class="chart-card-dot" style="background: #0f766e"></div>
          <h3 class="chart-card-title">按大洲统计</h3>
          <span class="chart-card-badge">{{ continentData.length }} 大洲</span>
        </div>
        <div ref="continentChartRef" class="chart-canvas"></div>
      </div>
      <div class="chart-card reveal-card" ref="endangermentCardEl">
        <div class="chart-card-header">
          <div class="chart-card-dot" style="background: #dc2626"></div>
          <h3 class="chart-card-title">IUCN 濒危等级</h3>
          <span class="chart-card-badge danger">{{ threatenedCount }} 受威胁</span>
        </div>
        <div ref="endangermentChartRef" class="chart-canvas"></div>
      </div>
    </div>

    <div class="charts-bento">
      <div class="chart-card reveal-card" ref="habitatCardEl">
        <div class="chart-card-header">
          <div class="chart-card-dot" style="background: #14b8a6"></div>
          <h3 class="chart-card-title">栖息地类型分布</h3>
          <span class="chart-card-badge">前 {{ Math.min(15, habitatData.length) }} 项</span>
        </div>
        <div ref="habitatChartRef" class="chart-canvas"></div>
      </div>
      <div class="chart-card reveal-card" ref="relationCardEl">
        <div class="chart-card-header">
          <div class="chart-card-dot" style="background: #7c3aed"></div>
          <h3 class="chart-card-title">关系类型分布</h3>
          <span class="chart-card-badge">{{ relationData.length }} 类型</span>
        </div>
        <div ref="relationChartRef" class="chart-canvas"></div>
      </div>
    </div>

    <section class="map-section reveal-card">
      <div class="map-header">
        <div class="map-header-left">
          <div class="chart-card-dot" style="background: #2563eb"></div>
          <div>
            <h3>全球鸟类分布地图</h3>
            <p>点击 Marker 查看鸟类详情，缩放查看集群分布</p>
          </div>
        </div>
        <span class="chart-card-badge map-badge">{{ store.birdNodes.filter(b => b.lat != null && b.lng != null).length }} 有坐标</span>
      </div>
      <div ref="overviewMapRef" class="map-canvas"></div>
    </section>

    <div class="quick-links">
      <router-link to="/categories" class="quick-link">
        <div class="quick-link-icon" style="background: rgba(15,118,110,0.1); color: #0f766e">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
        </div>
        <div class="quick-link-text">
          <h4>浏览类别</h4>
          <p>按鸟类卡片或关系一览浏览知识图谱数据</p>
        </div>
        <svg class="quick-link-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </router-link>
      <router-link to="/semantic-search" class="quick-link">
        <div class="quick-link-icon" style="background: rgba(124,58,237,0.1); color: #7c3aed">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/></svg>
        </div>
        <div class="quick-link-text">
          <h4>语义搜索</h4>
          <p>用自然语言查询鸟类分布、栖息地与保护等级</p>
        </div>
        <svg class="quick-link-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </router-link>
      <router-link to="/" class="quick-link">
        <div class="quick-link-icon" style="background: rgba(37,99,235,0.1); color: #2563eb">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>
        </div>
        <div class="quick-link-text">
          <h4>3D 知识图谱</h4>
          <p>在交互式三维图谱中探索物种与地点关联</p>
        </div>
        <svg class="quick-link-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import L from 'leaflet'
import { useGraphStore } from '../stores/graphStore.js'

const router = useRouter()
const store = useGraphStore()

const continentChartRef = ref(null)
const habitatChartRef = ref(null)
const endangermentChartRef = ref(null)
const relationChartRef = ref(null)
const overviewMapRef = ref(null)
const continentCardEl = ref(null)
const endangermentCardEl = ref(null)
const habitatCardEl = ref(null)
const relationCardEl = ref(null)

let continentChart = null, habitatChart = null, endangermentChart = null, relationChart = null
let mapInstance = null

const endangermentLabels = { CR: '极危 (CR)', EN: '濒危 (EN)', VU: '易危 (VU)', NT: '近危 (NT)', LC: '无危 (LC)', '未知': '未加载' }
const CONTINENT_COLORS = {
  '亚洲': '#0f766e', '非洲': '#d97706', '北美洲': '#2563eb', '南美洲': '#16a34a',
  '欧洲': '#7c3aed', '大洋洲': '#0891b2', '南极洲': '#94a3b8'
}

const statCards = computed(() => [
  { id: 'birds', value: store.totalBirdCount.toLocaleString(), label: '鸟类物种',
    glow: 'radial-gradient(circle at 50% 0%, rgba(15,118,110,0.15), transparent 70%)',
    iconBg: 'rgba(15,118,110,0.1)', iconColor: '#0f766e', accent: '#0f766e',
    iconPaths: '<path d="M12 3c-4 0-7 3-7 7 0 3 1 5 3 7l-3 4h14l-3-4c2-2 3-4 3-7 0-4-3-7-7-7z"/><circle cx="12" cy="10" r="2"/>' },
  { id: 'locations', value: locationCount.value.toLocaleString(), label: '分布地点',
    glow: 'radial-gradient(circle at 50% 0%, rgba(37,99,235,0.15), transparent 70%)',
    iconBg: 'rgba(37,99,235,0.1)', iconColor: '#2563eb', accent: '#2563eb',
    iconPaths: '<path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/>' },
  { id: 'relations', value: store.totalRelationCount.toLocaleString(), label: '知识关系',
    glow: 'radial-gradient(circle at 50% 0%, rgba(124,58,237,0.15), transparent 70%)',
    iconBg: 'rgba(124,58,237,0.1)', iconColor: '#7c3aed', accent: '#7c3aed',
    iconPaths: '<path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/>' },
  { id: 'threatened', value: threatenedCount.value.toLocaleString(), label: '受威胁物种',
    glow: 'radial-gradient(circle at 50% 0%, rgba(220,38,38,0.15), transparent 70%)',
    iconBg: 'rgba(220,38,38,0.1)', iconColor: '#dc2626', accent: '#dc2626',
    iconPaths: '<path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>' },
  { id: 'taxonomy', value: taxonomySummary.value, label: '目 / 科分类',
    glow: 'radial-gradient(circle at 50% 0%, rgba(217,119,6,0.15), transparent 70%)',
    iconBg: 'rgba(217,119,6,0.1)', iconColor: '#d97706', accent: '#d97706',
    iconPaths: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>' }
])

const locationCount = computed(() => store.meta?.counts?.relationTypes?.distributed_in
  ? new Set(store.birdNodes.flatMap(b => b.locations || [])).size
  : store.summaryLocations?.length || 0)

const threatenedCount = computed(() => {
  const counts = {}
  store.birdNodes.forEach(b => { if (b.status) counts[b.status] = (counts[b.status] || 0) + 1 })
  return (counts.CR || 0) + (counts.EN || 0) + (counts.VU || 0)
})

const taxonomySummary = computed(() => {
  const m = store.meta?.counts || {}
  return `${m.orders || 0}目 / ${m.families || 0}科`
})

const continentData = computed(() => {
  const counts = {}
  store.birdNodes.forEach(bird => {
    const c = store.getBirdContinent(bird.id)
    counts[c] = (counts[c] || 0) + 1
  })
  return Object.entries(counts).filter(([k]) => k !== '未知').sort((a, b) => b[1] - a[1])
})

const habitatData = computed(() => {
  const counts = {}
  store.birdNodes.forEach(bird => {
    if (bird.habitats) bird.habitats.forEach(h => { counts[h] = (counts[h] || 0) + 1 })
  })
  return Object.entries(counts).sort((a, b) => b[1] - a[1])
})

const endangermentData = computed(() => {
  const counts = {}
  store.birdNodes.forEach(bird => {
    const s = bird.status || '未知'
    counts[s] = (counts[s] || 0) + 1
  })
  return Object.entries(counts).sort((a, b) => {
    const order = ['CR', 'EN', 'VU', 'NT', 'LC', '未知']
    return order.indexOf(a[0]) - order.indexOf(b[0])
  })
})

const relationData = computed(() => {
  const types = store.meta?.counts?.relationTypes || {}
  const labels = { distributed_in: '分布于', lives_in: '栖息于', has_status: '保护等级', threatened_by: '受威胁于', belongs_to: '属于' }
  return Object.entries(types)
    .filter(([k]) => labels[k] && !k.startsWith('belongs_to_'))
    .map(([k, v]) => ({ name: labels[k] || k, value: v }))
    .sort((a, b) => b.value - a.value)
})

function initContinentChart() {
  if (!continentChartRef.value || !continentData.value.length) return
  continentChart?.dispose()
  continentChart = echarts.init(continentChartRef.value)
  continentChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['35%', '72%'], center: ['50%', '52%'],
      animationType: 'scale', animationEasing: 'elasticOut', animationDelay: 0,
      data: continentData.value.map(([name, value]) => ({ name, value, itemStyle: { color: CONTINENT_COLORS[name] || '#90A4AE' } })),
      label: { color: 'var(--text-secondary, #64748b)', fontSize: 12, formatter: '{b}\n{d}%' },
      itemStyle: { borderRadius: 8, borderColor: 'var(--card-bg, #fff)', borderWidth: 3 },
      emphasis: { label: { fontSize: 16, fontWeight: 'bold' }, scaleSize: 12 }
    }]
  })
}

function initHabitatChart() {
  if (!habitatChartRef.value) return
  habitatChart?.dispose()
  habitatChart = echarts.init(habitatChartRef.value)
  const top = habitatData.value.slice(0, 15)
  const colors = ['#0f766e', '#14b8a6', '#2dd4bf', '#5eead4', '#99f6e4', '#ccfbf1',
    '#0891b2', '#06b6d4', '#22d3ee', '#67e8f9', '#a5f3fc', '#cffafe',
    '#6366f1', '#818cf8', '#a5b4fc']
  habitatChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['30%', '70%'], center: ['50%', '52%'], roseType: 'area',
      animationType: 'scale', animationEasing: 'elasticOut',
      data: top.map(([n, v], i) => ({ name: n, value: v, itemStyle: { color: colors[i % colors.length] } })),
      label: { color: 'var(--text-secondary, #64748b)', fontSize: 11, formatter: '{b}' },
      itemStyle: { borderRadius: 6, borderColor: 'var(--card-bg, #fff)', borderWidth: 2 },
      emphasis: { label: { fontSize: 14, fontWeight: 'bold' } }
    }]
  })
}

function initEndangermentChart() {
  if (!endangermentChartRef.value || !endangermentData.value.length) return
  endangermentChart?.dispose()
  endangermentChart = echarts.init(endangermentChartRef.value)
  const colors = { CR: '#dc2626', EN: '#b45309', VU: '#ea580c', NT: '#ca8a04', LC: '#16a34a', '未知': '#94a3b8' }
  endangermentChart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}: {c} 种' },
    xAxis: { type: 'category', data: endangermentData.value.filter(([k]) => k !== '未知').map(([k]) => endangermentLabels[k] || k),
      axisLabel: { color: 'var(--text-secondary, #64748b)', fontSize: 12 },
      axisLine: { lineStyle: { color: 'var(--panel-border, #e2e8f0)' } },
      axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { color: 'var(--text-secondary, #64748b)' },
      splitLine: { lineStyle: { color: 'var(--panel-border, #e2e8f0)', type: 'dashed' } } },
    grid: { left: '3%', right: '6%', bottom: '3%', top: '8%', containLabel: true },
    series: [{
      type: 'bar', animationDelay: function (idx) { return idx * 80 },
      data: endangermentData.value.filter(([k]) => k !== '未知').map(([k, v]) => ({
        value: v, itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: colors[k] || '#16a34a' }, { offset: 1, color: (colors[k] || '#16a34a') + '88' }
          ]), borderRadius: [8, 8, 0, 0]
        }
      })), barMaxWidth: 56, label: { show: true, position: 'top', color: 'var(--text-color, #12303b)', fontSize: 12, fontWeight: 600 }
    }]
  })
}

function initRelationChart() {
  if (!relationChartRef.value || !relationData.value.length) return
  relationChart?.dispose()
  relationChart = echarts.init(relationChartRef.value)
  const colors = { '分布于': '#0f766e', '栖息于': '#16a34a', '保护等级': '#d97706', '受威胁于': '#dc2626', '属于': '#7c3aed' }
  relationChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 条' },
    series: [{
      type: 'pie', radius: ['35%', '72%'], center: ['50%', '52%'],
      animationType: 'scale', animationEasing: 'elasticOut',
      data: relationData.value.map(r => ({ name: r.name, value: r.value, itemStyle: { color: colors[r.name] || '#90A4AE' } })),
      label: { color: 'var(--text-secondary, #64748b)', fontSize: 12, formatter: '{b}\n{d}%' },
      itemStyle: { borderRadius: 8, borderColor: 'var(--card-bg, #fff)', borderWidth: 3 },
      emphasis: { label: { fontSize: 16, fontWeight: 'bold' }, scaleSize: 12 }
    }]
  })
}

function initOverviewMap() {
  const el = overviewMapRef.value
  if (!el || mapInstance) return
  if (el.clientWidth === 0 || el.clientHeight === 0) {
    setTimeout(initOverviewMap, 200)
    return
  }
  mapInstance = L.map(el, {
    zoomControl: true, scrollWheelZoom: true, worldCopyJump: false,
    maxBounds: [[-85, -180], [85, 180]], maxBoundsViscosity: 1
  }).setView([20, 110], 2)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18, noWrap: true, bounds: [[-85, -180], [85, 180]],
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(mapInstance)

  const birdsWithCoords = store.birdNodes.filter(b => b.lat != null && b.lng != null)

  if (birdsWithCoords.length > 800) {
    const clusterLayer = L.layerGroup().addTo(mapInstance)
    const gridSize = 20
    const grid = {}
    birdsWithCoords.forEach(b => {
      const gx = Math.floor(b.lng / gridSize) * gridSize
      const gy = Math.floor(b.lat / gridSize) * gridSize
      const key = `${gx},${gy}`
      if (!grid[key]) grid[key] = { lat: gy + gridSize / 2, lng: gx + gridSize / 2, count: 0, birds: [] }
      grid[key].count++
      grid[key].birds.push(b)
    })

    Object.values(grid).forEach(cell => {
      const size = Math.min(40, Math.max(16, Math.sqrt(cell.count) * 8))
      const marker = L.circleMarker([cell.lat, cell.lng], {
        radius: size, fillColor: '#0f766e', color: '#fff', weight: 1.5,
        fillOpacity: 0.7
      }).addTo(clusterLayer)
      marker.bindPopup(`<strong>${cell.count} 种鸟类</strong><br/>此区域`)
      marker.on('click', () => mapInstance.setView([cell.lat, cell.lng], Math.min(8, mapInstance.getZoom() + 3)))
    })
  } else {
    birdsWithCoords.forEach(bird => {
      const marker = L.circleMarker([bird.lat, bird.lng], {
        radius: 4, fillColor: '#0f766e', color: '#fff', weight: 1, fillOpacity: 0.6
      }).addTo(mapInstance)
      marker.bindPopup(`<strong>${bird.name}</strong><br/><em>${bird.englishName || ''}</em><br/>` +
        (bird.status ? `<span style="color:#b45309">${endangermentLabels[bird.status] || bird.status}</span><br/>` : '') +
        `<a href="/bird/${bird.id}" style="color:#0f766e;font-weight:600;">查看详情 →</a>`)
      marker.on('click', () => router.push(`/bird/${bird.id}`))
    })
  }

  setTimeout(() => mapInstance?.invalidateSize(), 300)
}

function handleResize() {
  continentChart?.resize(); habitatChart?.resize(); endangermentChart?.resize(); relationChart?.resize()
  mapInstance?.invalidateSize()
}

function observeRevealCards() {
  if (typeof IntersectionObserver === 'undefined') return
  const cards = document.querySelectorAll('.reveal-card')
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed')
        observer.unobserve(entry.target)
      }
    })
  }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' })
  cards.forEach(card => observer.observe(card))
}

onMounted(async () => {
  if (!store.loaded) await store.loadData()
  if (!store.previewLoaded) await store.loadGraphPreview()
  await nextTick()
  setTimeout(() => {
    initContinentChart(); initHabitatChart(); initEndangermentChart(); initRelationChart(); initOverviewMap()
    window.addEventListener('resize', handleResize)
    observeRevealCards()
  }, 300)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  continentChart?.dispose(); habitatChart?.dispose(); endangermentChart?.dispose(); relationChart?.dispose()
  mapInstance?.remove()
})
</script>

<style scoped>
.overview-page { display: flex; flex-direction: column; gap: 28px; padding-bottom: 48px; }

.hero-section { text-align: center; padding: 8px 0 6px; }
.hero-title {
  margin: 0 0 8px;
  font-size: 32px; font-weight: 800;
  background: linear-gradient(135deg, var(--heading-color) 0%, var(--accent) 100%);
  background-clip: text; -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
}
.hero-subtitle { margin: 0; font-size: 15px; color: var(--text-secondary); max-width: 520px; margin: 0 auto; line-height: 1.6; }

.stats-bento { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.stat-card {
  position: relative; overflow: hidden;
  border-radius: 20px;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  box-shadow: 0 1px 3px rgba(0,0,0,0.03), 0 4px 16px rgba(0,0,0,0.04);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease;
  animation: statSlideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
  cursor: default;
}
.stat-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.08); border-color: var(--accent); }
.stat-card:hover .stat-spark { opacity: 1; }
.stat-card-glow {
  position: absolute; top: 0; left: 0; right: 0; height: 120px;
  pointer-events: none; opacity: 0.6;
}
.stat-card-inner { position: relative; z-index: 1; padding: 22px 18px 20px; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.stat-icon-wrap {
  width: 48px; height: 48px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.3s ease;
}
.stat-icon-wrap svg { width: 24px; height: 24px; }
.stat-card:hover .stat-icon-wrap { transform: scale(1.08); }
.stat-body { text-align: center; }
.stat-value { display: block; font-size: 30px; font-weight: 800; line-height: 1.15; letter-spacing: -0.02em; transition: transform 0.3s ease; }
.stat-card:hover .stat-value { transform: scale(1.04); }
.stat-label { display: block; margin-top: 4px; font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.stat-spark {
  position: absolute; inset: 0; opacity: 0; pointer-events: none;
  background: radial-gradient(ellipse at 50% 30%, var(--accent-soft, rgba(15,118,110,0.12)), transparent 70%);
  transition: opacity 0.4s ease;
}

@keyframes statSlideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

.charts-bento { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }

.chart-card {
  padding: 22px;
  border: 1px solid var(--panel-border);
  border-radius: 24px;
  background: var(--card-bg);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 6px 20px rgba(0,0,0,0.04);
  transition: box-shadow 0.3s ease, border-color 0.3s ease, transform 0.25s ease;
  display: flex; flex-direction: column;
}
.chart-card:hover { border-color: var(--accent); box-shadow: 0 8px 28px rgba(0,0,0,0.08); transform: translateY(-1px); }
.chart-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.chart-card-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.chart-card-title { margin: 0; font-size: 16px; font-weight: 700; color: var(--heading-color); }
.chart-card-badge {
  margin-left: auto;
  padding: 3px 10px; border-radius: 100px;
  font-size: 12px; font-weight: 600;
  background: var(--accent-soft, rgba(15,118,110,0.1));
  color: var(--accent);
}
.chart-card-badge.danger { background: rgba(220,38,38,0.1); color: #dc2626; }
.chart-canvas { width: 100%; height: 360px; flex: 1; }

.reveal-card { opacity: 0; transform: translateY(28px); transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1), transform 0.6s cubic-bezier(0.16, 1, 0.3, 1); }
.reveal-card.revealed { opacity: 1; transform: translateY(0); }

.map-section {
  padding: 22px;
  border: 1px solid var(--panel-border);
  border-radius: 24px;
  background: var(--card-bg);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 6px 20px rgba(0,0,0,0.04);
}
.map-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.map-header-left { display: flex; align-items: center; gap: 10px; }
.map-header-left h3 { margin: 0; font-size: 16px; font-weight: 700; color: var(--heading-color); }
.map-header-left p { margin: 4px 0 0; font-size: 13px; color: var(--text-secondary); }
.map-badge { flex-shrink: 0; }
.map-canvas { width: 100%; height: 460px; border-radius: 18px; overflow: hidden; border: 1px solid var(--panel-border); }

.quick-links { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }

.quick-link {
  display: flex; align-items: center; gap: 14px;
  padding: 20px 18px;
  border-radius: 20px;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  text-decoration: none; color: inherit;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: pointer;
  position: relative; overflow: hidden;
}
.quick-link::before {
  content: ''; position: absolute; inset: 0; opacity: 0;
  background: linear-gradient(135deg, var(--accent-soft, rgba(15,118,110,0.08)), transparent);
  transition: opacity 0.3s ease;
}
.quick-link:hover { transform: translateY(-3px); box-shadow: 0 12px 28px rgba(0,0,0,0.08); border-color: var(--accent); }
.quick-link:hover::before { opacity: 1; }
.quick-link:hover .quick-link-arrow { opacity: 1; transform: translateX(0); }
.quick-link-icon {
  position: relative; z-index: 1;
  width: 44px; height: 44px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}
.quick-link-icon svg { width: 22px; height: 22px; }
.quick-link:hover .quick-link-icon { transform: scale(1.08); }
.quick-link-text { position: relative; z-index: 1; flex: 1; min-width: 0; }
.quick-link-text h4 { margin: 0 0 4px; font-size: 15px; font-weight: 700; color: var(--heading-color); }
.quick-link-text p { margin: 0; font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.quick-link-arrow {
  position: relative; z-index: 1;
  width: 20px; height: 20px; flex-shrink: 0;
  color: var(--text-secondary);
  opacity: 0; transform: translateX(-6px);
  transition: all 0.3s ease;
}

@media (max-width: 1080px) {
  .stats-bento { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .hero-title { font-size: 26px; }
  .stats-bento { grid-template-columns: repeat(2, 1fr); }
  .charts-bento { grid-template-columns: 1fr; }
  .quick-links { grid-template-columns: 1fr; }
  .chart-canvas { height: 290px; }
  .map-canvas { height: 340px; }
}
@media (max-width: 480px) {
  .stats-bento { grid-template-columns: 1fr 1fr; }
  .stat-value { font-size: 24px; }
  .hero-title { font-size: 22px; }
}
</style>

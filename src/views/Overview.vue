<template>
  <div class="overview-page">
    <h2 class="page-title">数据概览</h2>
    <div class="charts-row">
      <div class="panel chart-panel">
        <h3 class="chart-title">按大洲统计</h3>
        <div ref="continentChartRef" class="chart-canvas"></div>
      </div>
      <div class="panel chart-panel">
        <h3 class="chart-title">按栖息地统计</h3>
        <div ref="habitatChartRef" class="chart-canvas"></div>
      </div>
    </div>
    <section class="panel map-panel">
      <div class="section-heading">
        <h3>全球鸟类分布地图</h3>
        <p>点击 Marker 查看鸟类详情</p>
      </div>
      <div ref="overviewMapRef" class="map-canvas"></div>
    </section>
    <div class="panel chart-panel full">
      <h3 class="chart-title">按濒危等级统计</h3>
      <div ref="endangermentChartRef" class="chart-canvas tall"></div>
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
const overviewMapRef = ref(null)

let continentChart = null, habitatChart = null, endangermentChart = null
let mapInstance = null, markersLayer = null

const endangermentLabels = { CR: '极危 (CR)', EN: '濒危 (EN)', VU: '易危 (VU)', NT: '近危 (NT)', LC: '无危 (LC)' }

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
  store.birdNodes.forEach(bird => { const s = bird.status || 'LC'; counts[s] = (counts[s] || 0) + 1 })
  return Object.entries(counts).sort((a, b) => {
    const order = ['CR', 'EN', 'VU', 'NT', 'LC']
    return order.indexOf(a[0]) - order.indexOf(b[0])
  })
})

function initContinentChart() {
  if (!continentChartRef.value) return
  continentChart?.dispose()
  continentChart = echarts.init(continentChartRef.value)
  continentChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{ type: 'pie', radius: ['30%', '70%'], center: ['50%', '55%'],
      data: continentData.value.map(([name, value]) => ({ name, value })),
      label: { color: 'var(--text-color, #12303b)', fontSize: 12 },
      itemStyle: { borderRadius: 6, borderColor: 'var(--panel-bg, #fff)', borderWidth: 2 },
      emphasis: { label: { fontSize: 14, fontWeight: 'bold' } } }]
  })
}

function initHabitatChart() {
  if (!habitatChartRef.value) return
  habitatChart?.dispose()
  habitatChart = echarts.init(habitatChartRef.value)
  const top = habitatData.value.slice(0, 12)
  habitatChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{ type: 'pie', radius: ['30%', '70%'], center: ['50%', '55%'],
      data: top.map(([n, v]) => ({ name: n, value: v })),
      label: { color: 'var(--text-color, #12303b)', fontSize: 12 },
      itemStyle: { borderRadius: 6, borderColor: 'var(--panel-bg, #fff)', borderWidth: 2 } }]
  })
}

function initEndangermentChart() {
  if (!endangermentChartRef.value) return
  endangermentChart?.dispose()
  endangermentChart = echarts.init(endangermentChartRef.value)
  const colors = { CR: '#dc2626', EN: '#b45309', VU: '#ea580c', NT: '#ca8a04', LC: '#16a34a' }
  endangermentChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: endangermentData.value.map(([k]) => endangermentLabels[k] || k),
      axisLabel: { color: 'var(--text-color, #12303b)' } },
    yAxis: { type: 'value', axisLabel: { color: 'var(--text-color, #12303b)' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    series: [{ type: 'bar', data: endangermentData.value.map(([k, v]) => ({
      value: v, itemStyle: { color: colors[k] || '#16a34a', borderRadius: [6, 6, 0, 0] } })),
      barMaxWidth: 60, label: { show: true, position: 'top', color: 'var(--text-color, #12303b)' } }]
  })
}

function initOverviewMap() {
  const el = overviewMapRef.value
  if (!el || mapInstance) return
  // 确保容器有尺寸后再初始化
  if (el.clientWidth === 0 || el.clientHeight === 0) {
    setTimeout(initOverviewMap, 200)
    return
  }
  mapInstance = L.map(el, {
    zoomControl: true,
    scrollWheelZoom: true,
    worldCopyJump: false,
    maxBounds: [[-85, -180], [85, 180]],
    maxBoundsViscosity: 1
  }).setView([20, 110], 2)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18,
    noWrap: true,
    bounds: [[-85, -180], [85, 180]],
    attribution: '&copy; OpenStreetMap contributors' }).addTo(mapInstance)
  markersLayer = L.layerGroup().addTo(mapInstance)
  store.birdNodes.forEach(bird => {
    if (bird.lat == null || bird.lng == null) return
    const marker = L.marker([bird.lat, bird.lng])
    marker.bindPopup(`<strong>${bird.name}</strong><br/><em>${bird.englishName || ''}</em><br/>` +
      (bird.status ? `<span style="color:#b45309">${endangermentLabels[bird.status] || bird.status}</span><br/>` : '') +
      `<a href="/bird/${bird.id}" style="color:#0f766e;font-weight:600;" target="_self">查看详情 →</a>`)
    marker.on('click', () => router.push(`/bird/${bird.id}`))
    markersLayer.addLayer(marker)
  })
  // 首次加载后通知地图重算尺寸
  setTimeout(() => mapInstance?.invalidateSize(), 300)
}

function handleResize() {
  continentChart?.resize(); habitatChart?.resize(); endangermentChart?.resize(); mapInstance?.invalidateSize()
}

onMounted(async () => {
  if (!store.loaded) await store.loadData()
  await nextTick()
  setTimeout(() => {
    initContinentChart(); initHabitatChart(); initEndangermentChart(); initOverviewMap()
    window.addEventListener('resize', handleResize)
  }, 100)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  continentChart?.dispose(); habitatChart?.dispose(); endangermentChart?.dispose(); mapInstance?.remove()
})
</script>

<style scoped>
.overview-page { display: flex; flex-direction: column; gap: 18px; }
.page-title { margin: 0; font-size: 24px; font-family: "Alegreya", "Source Han Serif SC", "Noto Serif SC", serif; color: var(--heading-color); }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.chart-panel { padding: 18px; border: 1px solid var(--panel-border); border-radius: 24px; background: var(--panel-bg); box-shadow: var(--shadow); backdrop-filter: blur(14px); }
.chart-panel.full { grid-column: 1 / -1; }
.chart-title { margin: 0 0 12px; font-size: 16px; color: var(--heading-color); }
.chart-canvas { width: 100%; height: 340px; }
.chart-canvas.tall { height: 380px; }
.map-panel { padding: 18px; border: 1px solid var(--panel-border); border-radius: 24px; background: var(--panel-bg); box-shadow: var(--shadow); backdrop-filter: blur(14px); display: flex; flex-direction: column; gap: 14px; }
.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.section-heading h3 { margin: 0; font-size: 16px; color: var(--heading-color); }
.section-heading p { margin: 0; font-size: 13px; color: var(--text-secondary); }
.map-canvas { width: 100%; height: 420px; border-radius: 18px; overflow: hidden; border: 1px solid var(--panel-border); }
@media (max-width: 860px) {
  .charts-row { grid-template-columns: 1fr; }
  .chart-canvas { height: 280px; }
  .map-canvas { height: 320px; }
}
</style>

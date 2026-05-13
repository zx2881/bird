<template>
  <div class="academic-root">
    <div ref="svgContainer" class="academic-svg-container"></div>

    <div v-show="tooltip.show" class="academic-tooltip" :style="tooltip.style">
      <div class="tooltip-title">{{ tooltip.name }}</div>
      <div class="tooltip-latin">{{ tooltip.latin }}</div>
      <div class="tooltip-row">
        <span class="tooltip-badge" :style="{ background: tooltip.color }">{{ tooltip.status || 'LC' }}</span>
        <span class="tooltip-stat">关联 {{ tooltip.degree }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, reactive, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { useGraphStore } from '../stores/graphStore.js'

const props = defineProps({
  searchQuery: { type: String, default: '' }
})

const store = useGraphStore()
const svgContainer = ref(null)

const tooltip = reactive({ show: false, name: '', latin: '', status: '', color: '#006400', degree: 0, style: {} })

const IUCN_COLOR = { CR: '#FF0000', EN: '#FFA500', VU: '#FFD700', NT: '#90EE90', LC: '#006400' }

let svg, gMain, zoomBehavior, simNodes, simEdges, nodeGroup, edgeGroup, labelGroup

function render() {
  if (!svgContainer.value || !store.loaded) return
  svgContainer.value.innerHTML = ''

  // ── 1. 只保留鸟类节点 ──
  const birdNodes = store.nodes.filter(n => n.type === 'bird')
  if (!birdNodes.length) return

  // 从 latinName 提取属名
  birdNodes.forEach(b => {
    b.genus = b.latinName ? (b.latinName.split(' ')[0] || 'Unknown') : 'Unknown'
  })

  // ── 2. 推导鸟-鸟边（共享地点/栖息地/威胁）──
  const locBirds = new Map(), habBirds = new Map(), thrBirds = new Map()
  birdNodes.forEach(b => {
    ;(b.locations || []).forEach(l => { if (!locBirds.has(l)) locBirds.set(l, []); locBirds.get(l).push(b.id) })
    ;(b.habitats || []).forEach(h => { if (!habBirds.has(h)) habBirds.set(h, []); habBirds.get(h).push(b.id) })
    ;(b.threats || []).forEach(t => { if (!thrBirds.has(t)) thrBirds.set(t, []); thrBirds.get(t).push(b.id) })
  })

  const edgeSet = new Map()
  function addEdge(a, b) {
    if (a === b) return
    const key = a < b ? `${a}|${b}` : `${b}|${a}`
    edgeSet.set(key, (edgeSet.get(key) || 0) + 1)
  }
  for (const [, ids] of locBirds) for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) addEdge(ids[i], ids[j])
  for (const [, ids] of habBirds) for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) addEdge(ids[i], ids[j])
  for (const [, ids] of thrBirds) for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) addEdge(ids[i], ids[j])

  let derivedEdges = Array.from(edgeSet.entries()).map(([k, w]) => {
    const [source, target] = k.split('|')
    return { source, target, weight: w }
  })
  derivedEdges.sort((a, b) => b.weight - a.weight)
  if (derivedEdges.length > 300) derivedEdges = d3.shuffle(derivedEdges).slice(0, 300)

  // ── 3. 节点大小：按度数对数缩放 ──
  const MIN_SIZE = 5, MAX_SIZE = 30
  const degrees = birdNodes.map(b => store.getNodeDegree(b.id))
  const maxDeg = Math.max(...degrees, 1)
  birdNodes.forEach(b => {
    const deg = store.getNodeDegree(b.id)
    b.nodeSize = MIN_SIZE + (Math.log2(deg + 1) / Math.log2(maxDeg + 1)) * (MAX_SIZE - MIN_SIZE)
    b.nodeColor = IUCN_COLOR[b.status] || IUCN_COLOR.LC
    b.displayDegree = deg
  })

  // ── 4. 按属名分组，计算簇中心 ──
  const genusGroups = d3.group(birdNodes, d => d.genus)
  const genusList = Array.from(genusGroups.keys())
  const LAYOUT_RADIUS = Math.max(200, Math.sqrt(genusList.length) * 80)
  const genusCenters = new Map()
  genusList.forEach((g, i) => {
    const angle = (2 * Math.PI * i) / genusList.length - Math.PI / 2
    genusCenters.set(g, { x: Math.cos(angle) * LAYOUT_RADIUS, y: Math.sin(angle) * LAYOUT_RADIUS })
  })

  // ── 5. 力导向布局 ──
  const scatter = Math.max(20, LAYOUT_RADIUS / genusList.length * 3)
  simNodes = birdNodes.map(b => ({
    id: b.id, name: b.name, latinName: b.latinName, status: b.status,
    genus: b.genus, nodeSize: b.nodeSize, nodeColor: b.nodeColor, degree: b.displayDegree,
    x: (genusCenters.get(b.genus)?.x || 0) + (Math.random() - 0.5) * scatter,
    y: (genusCenters.get(b.genus)?.y || 0) + (Math.random() - 0.5) * scatter
  }))

  const nodeMap = new Map(simNodes.map(n => [n.id, n]))
  simEdges = derivedEdges.map(e => ({
    source: nodeMap.get(e.source), target: nodeMap.get(e.target), weight: e.weight
  })).filter(e => e.source && e.target)

  function clusterForce(alpha) {
    for (const node of simNodes) {
      const center = genusCenters.get(node.genus)
      if (center) { node.vx += (center.x - node.x) * 0.08 * alpha; node.vy += (center.y - node.y) * 0.08 * alpha }
    }
  }

  d3.forceSimulation(simNodes)
    .force('link', d3.forceLink(simEdges).id(d => d.id).distance(d => 120 - d.weight * 10).strength(0.3))
    .force('charge', d3.forceManyBody().strength(-120))
    .force('center', d3.forceCenter(0, 0).strength(0.05))
    .force('collide', d3.forceCollide().radius(d => d.nodeSize + 3))
    .alphaDecay(0.02).stop()
    .tick(300)

  // ── 6. SVG 画布 ──
  const W = svgContainer.value.clientWidth || 900
  const H = svgContainer.value.clientHeight || 600

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  const bgColor = isDark ? '#1a1a2e' : '#FAFAFA'
  const textColor = isDark ? '#e0e0e0' : '#444'
  const edgeColor = isDark ? '#888' : '#808080'
  const edgeOpacity = isDark ? 0.25 : 0.3
  const edgeWidth = 0.5
  const labelColor = isDark ? '#ccc' : '#444'

  svg = d3.select(svgContainer.value)
    .append('svg')
    .attr('width', W).attr('height', H)
    .attr('viewBox', `0 0 ${W} ${H}`)
    .style('background', bgColor).style('cursor', 'grab')
    .attr('opacity', 0)
    .transition().duration(600).attr('opacity', 1)

  gMain = svg.append('g').attr('class', 'main-group')

  zoomBehavior = d3.zoom().scaleExtent([0.3, 10])
    .on('zoom', (event) => { gMain.attr('transform', event.transform) })
  svg.call(zoomBehavior)

  const initialScale = Math.min(W, H) / (LAYOUT_RADIUS * 2.5)
  svg.call(zoomBehavior.transform, d3.zoomIdentity.translate(W / 2, H / 2).scale(initialScale))

  // ── 7. 绘制边 ──
  edgeGroup = gMain.append('g').attr('class', 'edges')
  edgeGroup.selectAll('line').data(simEdges).join('line')
    .attr('stroke', edgeColor).attr('stroke-opacity', edgeOpacity).attr('stroke-width', edgeWidth)
    .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
    // 入场合：边从透明渐入
    .attr('opacity', 0).transition().delay((d, i) => i * 0.5).duration(300).attr('opacity', 1)

  // ── 8. 绘制节点 ──
  nodeGroup = gMain.append('g').attr('class', 'nodes')
  const circles = nodeGroup.selectAll('circle').data(simNodes).join('circle')
    .attr('r', d => d.nodeSize).attr('fill', d => d.nodeColor)
    .attr('stroke', '#FFFFFF').attr('stroke-width', 1.2)
    .attr('cx', d => d.x).attr('cy', d => d.y)
    .attr('opacity', 1).style('cursor', 'pointer')
    .style('transition', 'opacity 0.2s')

  // ── 9. 节点名称标签（在所有节点旁显示） ──
  labelGroup = gMain.append('g').attr('class', 'labels')
  labelGroup.selectAll('text').data(simNodes).join('text')
    .text(d => d.name)
    .attr('x', d => d.x).attr('y', d => d.y + d.nodeSize + 10)
    .attr('text-anchor', 'middle').attr('font-size', '8px')
    .attr('fill', labelColor).attr('font-family', 'Arial, sans-serif')
    .attr('pointer-events', 'none').attr('opacity', 0)
    // 入场合：标签淡入
    .transition().delay((d, i) => 200 + i * 1.5).duration(300).attr('opacity', 0.85)
    // 给每个标签加白色描边，黑色模式下也清晰可见
    .attr('stroke', isDark ? '#333' : '#fff').attr('stroke-width', 0.3)
    .attr('paint-order', 'stroke')

  // ── 10. 悬停 tooltip ──
  circles.on('mouseover', function (event, d) {
    tooltip.show = true; tooltip.name = d.name; tooltip.latin = d.latinName || ''
    tooltip.status = d.status || 'LC'; tooltip.color = IUCN_COLOR[d.status] || IUCN_COLOR.LC
    tooltip.degree = d.degree; positionTooltip(event)
  }).on('mousemove', positionTooltip)
    .on('mouseout', () => { if (!currentHighlightId) tooltip.show = false })

  // ── 11. 点击高亮邻居 ──
  let currentHighlightId = null

  circles.on('click', function (event, d) {
    event.stopPropagation()
    if (currentHighlightId === d.id) {
      currentHighlightId = null; resetHighlight(); tooltip.show = false; return
    }
    currentHighlightId = d.id

    const neighbors = new Set([d.id])
    for (const e of simEdges) {
      if (e.source.id === d.id) neighbors.add(e.target.id)
      if (e.target.id === d.id) neighbors.add(e.source.id)
    }

    circles.transition().duration(200)
      .attr('opacity', n => neighbors.has(n.id) ? 1 : 0.12)
      .attr('stroke-width', n => n.id === d.id ? 3 : 1.2)
      .attr('stroke', n => n.id === d.id ? '#333' : '#FFF')

    labelGroup.selectAll('text').transition().duration(200)
      .attr('opacity', n => neighbors.has(n.id) ? 1 : 0.08)

    edgeGroup.selectAll('line').transition().duration(200)
      .attr('stroke-opacity', e =>
        (e.source.id === d.id || e.target.id === d.id ||
         (neighbors.has(e.source.id) && neighbors.has(e.target.id))) ? 0.5 : 0.03)
      .attr('stroke-width', e => (e.source.id === d.id || e.target.id === d.id) ? 1.5 : 0.3)
  })

  svg.on('click', () => { if (currentHighlightId) { currentHighlightId = null; resetHighlight(); tooltip.show = false } })

  // ── 12. 图例（带半透明白色背景卡片） ──
  const leg = [
    { label: 'CR（极危）', color: '#FF0000' }, { label: 'EN（濒危）', color: '#FFA500' },
    { label: 'VU（易危）', color: '#FFD700' }, { label: 'NT（近危）', color: '#90EE90' },
    { label: 'LC（无危）', color: '#006400' }
  ]
  const legW = 155, legH = 20 + leg.length * 22 + 10
  svg.append('rect').attr('class', 'legend-bg')
    .attr('x', W - legW - 8).attr('y', 8).attr('width', legW).attr('height', legH)
    .attr('rx', 8).attr('fill', isDark ? 'rgba(30,30,50,0.85)' : 'rgba(255,255,255,0.85)')
    .attr('stroke', isDark ? '#444' : '#ddd').attr('stroke-width', 0.5)

  const lg = svg.append('g').attr('class', 'legend').attr('transform', `translate(${W - legW + 8}, 20)`)
  lg.append('text').attr('x', 0).attr('y', 0).attr('font-size', 12).attr('font-weight', 'bold')
    .attr('fill', isDark ? '#ddd' : '#333').attr('font-family', 'Arial, sans-serif').text('IUCN 保护等级')
  leg.forEach((item, i) => {
    const y = 20 + i * 22
    lg.append('circle').attr('cx', 6).attr('cy', y).attr('r', 5).attr('fill', item.color).attr('stroke', isDark ? '#666' : '#ccc').attr('stroke-width', 0.5)
    lg.append('text').attr('x', 18).attr('y', y + 4).attr('font-size', 11).attr('fill', isDark ? '#ccc' : '#555').attr('font-family', 'Arial, sans-serif').text(item.label)
  })

  // ── 13. 聚类标注 ──
  const topGenera = Array.from(genusGroups.entries())
    .map(([g, sp]) => ({ genus: g, count: sp.length })).filter(d => d.count >= 3)
    .sort((a, b) => b.count - a.count).slice(0, 3)

  if (topGenera.length) {
    const ag = gMain.append('g').attr('class', 'annotations')
    topGenera.forEach(({ genus, count }) => {
      const species = simNodes.filter(n => n.genus === genus)
      if (!species.length) return
      const cx = d3.mean(species, d => d.x), cy = d3.mean(species, d => d.y)
      const angle = Math.atan2(cy, cx), lr = LAYOUT_RADIUS * 0.75
      const lx = Math.cos(angle) * lr, ly = Math.sin(angle) * lr
      ag.append('line').attr('x1', cx).attr('y1', cy).attr('x2', lx).attr('y2', ly)
        .attr('stroke', isDark ? '#777' : '#999').attr('stroke-width', 0.5).attr('stroke-dasharray', '2,2').attr('opacity', 0.6)
      const off = 10
      ag.append('text').attr('x', lx + (lx > 0 ? off : -off)).attr('y', ly)
        .attr('text-anchor', lx > 0 ? 'start' : 'end').attr('font-size', 11).attr('fill', isDark ? '#bbb' : '#444')
        .attr('font-family', 'Arial, sans-serif').attr('font-weight', '600')
        .text(`${genus} (${count}种)`)
    })
  }

  // ── 节点入场动画 ──
  circles.attr('opacity', 0).attr('r', 0)
    .transition().delay((d, i) => 100 + i * 2).duration(400)
    .attr('r', d => d.nodeSize).attr('opacity', 1)

  // ── 保存引用用于搜索高亮 ──
  applySearchHighlight()
}

function resetHighlight() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  nodeGroup.selectAll('circle').transition().duration(200)
    .attr('opacity', 1).attr('stroke-width', 1.2).attr('stroke', '#FFF')
  labelGroup.selectAll('text').transition().duration(200).attr('opacity', 0.85)
  edgeGroup.selectAll('line').transition().duration(200)
    .attr('stroke-opacity', isDark ? 0.25 : 0.3).attr('stroke-width', 0.5)
}

function applySearchHighlight() {
  if (!nodeGroup || !labelGroup || !edgeGroup) return
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  const defEdgeOpacity = isDark ? 0.25 : 0.3
  const q = (props.searchQuery || '').trim().toLowerCase()
  if (!q) {
    nodeGroup.selectAll('circle').attr('opacity', 1)
    labelGroup.selectAll('text').attr('opacity', 0.85)
    edgeGroup.selectAll('line').attr('stroke-opacity', defEdgeOpacity).attr('stroke-width', 0.5)
    return
  }
  const matchIds = new Set()
  simNodes.forEach(n => {
    const fields = [n.name, n.latinName].filter(Boolean)
    if (fields.some(f => f.toLowerCase().includes(q))) matchIds.add(n.id)
  })
  if (!matchIds.size) return

  nodeGroup.selectAll('circle')
    .attr('opacity', n => matchIds.has(n.id) ? 1 : 0.08)
    .attr('stroke-width', n => matchIds.has(n.id) ? 2.5 : 0.5)
    .attr('stroke', n => matchIds.has(n.id) ? '#FF6600' : '#FFF')

  labelGroup.selectAll('text')
    .attr('opacity', n => matchIds.has(n.id) ? 1 : 0.04)
    .attr('font-weight', n => matchIds.has(n.id) ? 'bold' : 'normal')

  edgeGroup.selectAll('line')
    .attr('stroke-opacity', e =>
      (matchIds.has(e.source.id) && matchIds.has(e.target.id)) ? 0.35 : 0.03)
    .attr('stroke-width', e =>
      (matchIds.has(e.source.id) && matchIds.has(e.target.id)) ? 1 : 0.2)
}

function positionTooltip(event) {
  const rect = svgContainer.value?.getBoundingClientRect()
  if (!rect) return
  tooltip.style = {
    left: (event.clientX - rect.left + 16) + 'px',
    top: (event.clientY - rect.top - 10) + 'px'
  }
}

// ── 高清 PNG 导出（重写，修复空白问题）──
function exportHighResPNG() {
  const container = svgContainer.value
  if (!container) return
  const svgEl = container.querySelector('svg')
  if (!svgEl) return

  try {
    // 读取 viewBox 获取实际尺寸
    const vb = svgEl.getAttribute('viewBox') || '0 0 900 600'
    const parts = vb.split(/\s+/).map(Number)
    const vbW = parts[2] || 900, vbH = parts[3] || 600

    // 直接用 innerHTML 取 SVG 内容（避免命名空间问题）
    const content = svgEl.innerHTML

    // 构建完整 SVG 文档字符串（带上命名空间）
    const scale = Math.max(2, 1600 / vbW)
    const svgStr = [
      '<?xml version="1.0" encoding="UTF-8"?>',
      `<svg xmlns="http://www.w3.org/2000/svg" width="${vbW * scale}" height="${vbH * scale}" viewBox="${vb}" style="background:#FFFFFF">`,
      content,
      '</svg>'
    ].join('\n')

    const blob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(blob)

    const img = new Image()
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas')
        canvas.width = vbW * scale
        canvas.height = vbH * scale
        const ctx = canvas.getContext('2d')
        ctx.fillStyle = '#FFFFFF'
        ctx.fillRect(0, 0, canvas.width, canvas.height)
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

        canvas.toBlob(outBlob => {
          const link = document.createElement('a')
          link.download = `bird-graph-academic-${Date.now()}.png`
          link.href = URL.createObjectURL(outBlob)
          link.click()
          URL.revokeObjectURL(url)
        }, 'image/png', 0.95)
      } catch (e) { console.error('Export draw error:', e) }
    }
    img.onerror = (e) => { console.error('Export image load error:', e) }
    img.src = url
  } catch (e) { console.error('Export error:', e) }
}

defineExpose({ exportHighResPNG })

watch(() => props.searchQuery, () => {
  if (nodeGroup) applySearchHighlight()
})

onMounted(async () => {
  if (!store.loaded) await store.loadData()
  await nextTick()
  render()
})

onBeforeUnmount(() => {
  if (svg) { svg.on('.zoom', null); svg.on('click', null); svgContainer.value.innerHTML = '' }
})
</script>

<style scoped>
.academic-root { width: 100%; height: 100%; position: relative; }
.academic-svg-container { width: 100%; height: 100%; min-height: 520px; }
.academic-tooltip {
  position: absolute; z-index: 20; pointer-events: none; padding: 10px 14px;
  border-radius: 10px; background: rgba(255, 255, 255, 0.95);
  border: 1px solid #ddd; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  font-family: Arial, sans-serif; white-space: nowrap;
}
.tooltip-title { font-weight: 700; font-size: 14px; color: #222; }
.tooltip-latin { font-size: 12px; font-style: italic; color: #666; margin-top: 2px; }
.tooltip-row { display: flex; align-items: center; gap: 10px; margin-top: 6px; }
.tooltip-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; color: #fff; }
.tooltip-stat { font-size: 11px; color: #888; }
</style>

<template>
  <div class="academic-root">
    <!-- D3 将在 svgContainer 内创建 SVG -->
    <div ref="svgContainer" class="academic-svg-container"></div>

    <!-- 图例：由 D3 在 SVG 内绘制，此注释放保留 -->

    <!-- 工具提示：Vue 管理的浮动层，跟随鼠标 -->
    <div
      v-show="tooltip.show"
      class="academic-tooltip"
      :style="tooltip.style"
    >
      <div class="tooltip-title">{{ tooltip.name }}</div>
      <div class="tooltip-latin">{{ tooltip.latin }}</div>
      <div class="tooltip-row">
        <span class="tooltip-badge" :style="{ background: tooltip.color }">
          {{ tooltip.status || 'LC' }}
        </span>
        <span class="tooltip-stat">关联度 {{ tooltip.degree }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, reactive, nextTick } from 'vue'
import * as d3 from 'd3'
import { useGraphStore } from '../stores/graphStore.js'

const store = useGraphStore()

// ── DOM refs ──
const svgContainer = ref(null)

// ── Tooltip state ──
const tooltip = reactive({
  show: false, name: '', latin: '', status: '', color: '#006400', degree: 0, style: {}
})

// ── IUCN 颜色映射 ──
const IUCN_COLOR = {
  CR: '#FF0000', EN: '#FFA500', VU: '#FFD700', NT: '#90EE90', LC: '#006400'
}

// ── 主渲染入口 ──
let svg, gMain, zoomBehavior
let currentHighlightId = null

function render() {
  if (!svgContainer.value || !store.loaded) return

  // 清空容器
  svgContainer.value.innerHTML = ''

  // ────────────────────────────
  // 1. 数据准备：只保留鸟类节点
  // ────────────────────────────
  const birdNodes = store.nodes.filter(n => n.type === 'bird')
  if (!birdNodes.length) return

  // 从 latinName 提取属名，无 latinName 的归为 "Unknown"
  birdNodes.forEach(b => {
    b.genus = b.latinName
      ? (b.latinName.split(' ')[0] || 'Unknown')
      : 'Unknown'
  })

  // ────────────────────────────
  // 2. 推导鸟-鸟关系边
  // ────────────────────────────
  // 建立 地点/栖息地/威胁 → 鸟类ID列表 的倒排索引
  const locBirds = new Map()   // 地点名 → [birdId, ...]
  const habBirds = new Map()   // 栖息地名 → [birdId, ...]
  const thrBirds = new Map()   // 威胁名 → [birdId, ...]

  birdNodes.forEach(b => {
    ;(b.locations || []).forEach(loc => {
      if (!locBirds.has(loc)) locBirds.set(loc, [])
      locBirds.get(loc).push(b.id)
    })
    ;(b.habitats || []).forEach(hab => {
      if (!habBirds.has(hab)) habBirds.set(hab, [])
      habBirds.get(hab).push(b.id)
    })
    ;(b.threats || []).forEach(thr => {
      if (!thrBirds.has(thr)) thrBirds.set(thr, [])
      thrBirds.get(thr).push(b.id)
    })
  })

  // 从共享属性生成边，用 Set 去重
  const edgeSet = new Map() // "src|tgt" → weight
  function addEdge(a, b) {
    if (a === b) return
    const key = a < b ? `${a}|${b}` : `${b}|${a}`
    edgeSet.set(key, (edgeSet.get(key) || 0) + 1)
  }

  for (const [, ids] of locBirds) {
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) addEdge(ids[i], ids[j])
    }
  }
  for (const [, ids] of habBirds) {
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) addEdge(ids[i], ids[j])
    }
  }
  for (const [, ids] of thrBirds) {
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) addEdge(ids[i], ids[j])
    }
  }

  // 转换为边数组，按权重排序，最多保留 300 条
  let derivedEdges = Array.from(edgeSet.entries()).map(([key, weight]) => {
    const [source, target] = key.split('|')
    return { source, target, weight }
  })
  derivedEdges.sort((a, b) => b.weight - a.weight)

  // 如果超过 300 条，随机下采样
  if (derivedEdges.length > 300) {
    derivedEdges = d3.shuffle(derivedEdges).slice(0, 300)
  }

  // ────────────────────────────
  // 3. 节点大小：用度数（原始数据中的连接数）作为广布度代理，对数缩放
  // ────────────────────────────
  const MIN_SIZE = 5, MAX_SIZE = 30
  const degrees = birdNodes.map(b => store.getNodeDegree(b.id))
  const maxDeg = Math.max(...degrees, 1)

  birdNodes.forEach(b => {
    const deg = store.getNodeDegree(b.id)
    b.nodeSize = MIN_SIZE + (Math.log2(deg + 1) / Math.log2(maxDeg + 1)) * (MAX_SIZE - MIN_SIZE)
    b.nodeColor = IUCN_COLOR[b.status] || IUCN_COLOR.LC
    b.displayDegree = deg
  })

  // ────────────────────────────
  // 4. 按属分组，计算簇中心位置
  // ────────────────────────────
  const genusGroups = d3.group(birdNodes, d => d.genus)
  const genusList = Array.from(genusGroups.keys())
  const genusCount = genusList.length
  const LAYOUT_RADIUS = Math.max(200, Math.sqrt(genusCount) * 80)

  const genusCenters = new Map()
  genusList.forEach((genus, i) => {
    const angle = (2 * Math.PI * i) / genusCount - Math.PI / 2
    genusCenters.set(genus, {
      x: Math.cos(angle) * LAYOUT_RADIUS,
      y: Math.sin(angle) * LAYOUT_RADIUS
    })
  })

  // ────────────────────────────
  // 5. 创建 D3 力导向布局
  // ────────────────────────────
  const scatter = Math.max(20, LAYOUT_RADIUS / genusCount * 3)

  const simNodes = birdNodes.map(b => ({
    id: b.id,
    name: b.name,
    latinName: b.latinName,
    status: b.status,
    genus: b.genus,
    nodeSize: b.nodeSize,
    nodeColor: b.nodeColor,
    degree: b.displayDegree,
    x: (genusCenters.get(b.genus)?.x || 0) + (Math.random() - 0.5) * scatter,
    y: (genusCenters.get(b.genus)?.y || 0) + (Math.random() - 0.5) * scatter
  }))

  const nodeMap = new Map(simNodes.map(n => [n.id, n]))

  const simEdges = derivedEdges.map(e => ({
    source: nodeMap.get(e.source),
    target: nodeMap.get(e.target),
    weight: e.weight
  })).filter(e => e.source && e.target)

  // ── 自定义簇力：将节点拉向其属的中心 ──
  function clusterForce(alpha) {
    const strength = 0.08
    for (const node of simNodes) {
      const center = genusCenters.get(node.genus)
      if (center) {
        node.vx += (center.x - node.x) * strength * alpha
        node.vy += (center.y - node.y) * strength * alpha
      }
    }
  }

  const simulation = d3.forceSimulation(simNodes)
    .force('link', d3.forceLink(simEdges)
      .id(d => d.id)
      .distance(d => 120 - d.weight * 10)
      .strength(0.3))
    .force('charge', d3.forceManyBody().strength(-120))
    .force('center', d3.forceCenter(0, 0).strength(0.05))
    .force('collide', d3.forceCollide().radius(d => d.nodeSize + 3))
    .alphaDecay(0.02)
    .stop()

  // 手动运行 300 个 tick 使布局收敛
  for (let i = 0; i < 300; i++) simulation.tick()

  // ────────────────────────────
  // 6. 创建 SVG 画布
  // ────────────────────────────
  const W = svgContainer.value.clientWidth || 900
  const H = svgContainer.value.clientHeight || 600

  svg = d3.select(svgContainer.value)
    .append('svg')
    .attr('width', W)
    .attr('height', H)
    .attr('viewBox', `0 0 ${W} ${H}`)
    .style('background', '#FFFFFF')
    .style('cursor', 'grab')

  // 主容器 g，用于 zoom/pan
  gMain = svg.append('g').attr('class', 'main-group')

  // ── 平移缩放 ──
  zoomBehavior = d3.zoom()
    .scaleExtent([0.3, 10])
    .on('zoom', (event) => {
      gMain.attr('transform', event.transform)
    })
  svg.call(zoomBehavior)

  // 初始居中
  const initialScale = Math.min(W, H) / (LAYOUT_RADIUS * 2.5)
  svg.call(zoomBehavior.transform, d3.zoomIdentity
    .translate(W / 2, H / 2)
    .scale(initialScale)
  )

  // ────────────────────────────
  // 7. 绘制边
  // ────────────────────────────
  gMain.append('g')
    .attr('class', 'edges')
    .selectAll('line')
    .data(simEdges)
    .join('line')
    .attr('stroke', '#808080')
    .attr('stroke-opacity', 0.15)
    .attr('stroke-width', 0.3)
    .attr('x1', d => d.source.x)
    .attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x)
    .attr('y2', d => d.target.y)

  // ────────────────────────────
  // 8. 绘制节点
  // ────────────────────────────
  const nodeGroup = gMain.append('g').attr('class', 'nodes')

  const nodeCircles = nodeGroup.selectAll('circle')
    .data(simNodes)
    .join('circle')
    .attr('r', d => d.nodeSize)
    .attr('fill', d => d.nodeColor)
    .attr('stroke', '#FFFFFF')
    .attr('stroke-width', 1.2)
    .attr('cx', d => d.x)
    .attr('cy', d => d.y)
    .attr('opacity', 1)
    .style('cursor', 'pointer')
    .style('transition', 'opacity 0.2s')

  // ────────────────────────────
  // 9. 交互：悬停 tooltip
  // ────────────────────────────
  nodeCircles
    .on('mouseover', function (event, d) {
      tooltip.show = true
      tooltip.name = d.name
      tooltip.latin = d.latinName || ''
      tooltip.status = d.status || 'LC'
      tooltip.color = IUCN_COLOR[d.status] || IUCN_COLOR.LC
      tooltip.degree = d.degree
      positionTooltip(event)
    })
    .on('mousemove', positionTooltip)
    .on('mouseout', () => {
      if (!currentHighlightId) tooltip.show = false
    })

  // ────────────────────────────
  // 10. 交互：点击高亮邻居
  // ────────────────────────────
  nodeCircles.on('click', function (event, d) {
    event.stopPropagation()

    if (currentHighlightId === d.id) {
      // 再次点击取消高亮
      currentHighlightId = null
      resetHighlight(nodeCircles, simEdges)
      tooltip.show = false
      return
    }

    currentHighlightId = d.id

    // 找到 d 的所有直接邻居
    const neighborIds = new Set()
    neighborIds.add(d.id)
    for (const e of simEdges) {
      if (e.source.id === d.id) neighborIds.add(e.target.id)
      if (e.target.id === d.id) neighborIds.add(e.source.id)
    }

    // 高亮节点
    nodeCircles
      .transition().duration(200)
      .attr('opacity', n => neighborIds.has(n.id) ? 1 : 0.15)
      .attr('stroke-width', n => n.id === d.id ? 3 : 1.2)
      .attr('stroke', n => n.id === d.id ? '#333' : '#FFF')

    // 高亮边
    gMain.select('.edges').selectAll('line')
      .transition().duration(200)
      .attr('stroke-opacity', e =>
        (e.source.id === d.id || e.target.id === d.id ||
         (neighborIds.has(e.source.id) && neighborIds.has(e.target.id)))
          ? 0.4 : 0.04
      )
      .attr('stroke-width', e =>
        (e.source.id === d.id || e.target.id === d.id) ? 1.5 : 0.3
      )
  })

  // 点击画布空白取消高亮
  svg.on('click', () => {
    if (currentHighlightId) {
      currentHighlightId = null
      resetHighlight(nodeCircles, simEdges)
      tooltip.show = false
    }
  })

  // ────────────────────────────
  // 11. 图例（右上角固定，不随 zoom 移动）
  // ────────────────────────────
  const legendData = [
    { label: 'CR（极危）', color: '#FF0000' },
    { label: 'EN（濒危）', color: '#FFA500' },
    { label: 'VU（易危）', color: '#FFD700' },
    { label: 'NT（近危）', color: '#90EE90' },
    { label: 'LC（无危）', color: '#006400' }
  ]

  const legendG = svg.append('g')
    .attr('class', 'legend')
    .attr('transform', `translate(${W - 160}, 20)`)

  legendG.append('text')
    .attr('x', 0).attr('y', 0)
    .attr('font-size', 12).attr('font-weight', 'bold')
    .attr('fill', '#333').attr('font-family', 'Arial, sans-serif')
    .text('IUCN 保护等级')

  legendData.forEach((item, i) => {
    const y = 20 + i * 22
    legendG.append('circle')
      .attr('cx', 6).attr('cy', y).attr('r', 5)
      .attr('fill', item.color).attr('stroke', '#ccc').attr('stroke-width', 0.5)
    legendG.append('text')
      .attr('x', 18).attr('y', y + 4)
      .attr('font-size', 11).attr('fill', '#555')
      .attr('font-family', 'Arial, sans-serif')
      .text(item.label)
  })

  // ────────────────────────────
  // 12. 聚类标注：找出最多物种的 3 个属
  // ────────────────────────────
  const genusSizeRank = Array.from(genusGroups.entries())
    .map(([g, species]) => ({ genus: g, count: species.length }))
    .filter(d => d.count >= 3)
    .sort((a, b) => b.count - a.count)
    .slice(0, 3)

  if (genusSizeRank.length) {
    const annotateG = gMain.append('g').attr('class', 'annotations')

    genusSizeRank.forEach(({ genus, count }) => {
      // 计算该属所有节点的中心
      const species = simNodes.filter(n => n.genus === genus)
      if (!species.length) return
      const cx = d3.mean(species, d => d.x)
      const cy = d3.mean(species, d => d.y)

      // 引线末端位置（偏移）
      const angle = Math.atan2(cy, cx)
      const labelRadius = LAYOUT_RADIUS * 0.75
      const lx = Math.cos(angle) * labelRadius
      const ly = Math.sin(angle) * labelRadius

      // 引线
      annotateG.append('line')
        .attr('x1', cx).attr('y1', cy)
        .attr('x2', lx).attr('y2', ly)
        .attr('stroke', '#999').attr('stroke-width', 0.5)
        .attr('stroke-dasharray', '2,2')
        .attr('opacity', 0.6)

      // 文本标注
      const textOffset = 10
      const tx = lx + (lx > 0 ? textOffset : -textOffset)
      const ty = ly

      annotateG.append('text')
        .attr('x', tx).attr('y', ty)
        .attr('text-anchor', lx > 0 ? 'start' : 'end')
        .attr('font-size', 11).attr('fill', '#444')
        .attr('font-family', 'Arial, sans-serif')
        .attr('font-weight', '600')
        .text(`${genus} (${count}种)`)
    })
  }
}

// ── 工具函数 ──

function positionTooltip(event) {
  const container = svgContainer.value
  if (!container) return
  const rect = container.getBoundingClientRect()
  tooltip.style = {
    left: (event.clientX - rect.left + 16) + 'px',
    top: (event.clientY - rect.top - 10) + 'px'
  }
}

function resetHighlight(circles, edges) {
  circles
    .transition().duration(200)
    .attr('opacity', 1)
    .attr('stroke-width', 1.2)
    .attr('stroke', '#FFF')

  d3.select(svgContainer.value).select('.edges').selectAll('line')
    .transition().duration(200)
    .attr('stroke-opacity', 0.15)
    .attr('stroke-width', 0.3)
}

// ── 暴露给父组件的导出方法 ──
function exportHighResPNG() {
  const container = svgContainer.value
  if (!container) return
  const svgEl = container.querySelector('svg')
  if (!svgEl) return

  const W = svgEl.clientWidth || 900
  const H = svgEl.clientHeight || 600
  const scale = 1600 / W

  // 克隆 SVG，设置高清尺寸
  const clone = svgEl.cloneNode(true)
  clone.setAttribute('width', W * scale)
  clone.setAttribute('height', H * scale)
  clone.setAttribute('viewBox', `0 0 ${W} ${H}`)
  clone.style.background = '#FFFFFF'

  const svgData = new XMLSerializer().serializeToString(clone)
  const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)

  const img = new Image()
  img.onload = () => {
    const canvas = document.createElement('canvas')
    canvas.width = W * scale
    canvas.height = H * scale
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
    }, 'image/png')
  }
  img.src = url
}

defineExpose({ exportHighResPNG })

onMounted(async () => {
  if (!store.loaded) await store.loadData()
  await nextTick()
  render()
})

onBeforeUnmount(() => {
  if (svg) {
    svg.on('.zoom', null)
    svg.on('click', null)
    svg.selectAll('*').interrupt()
    svgContainer.value.innerHTML = ''
  }
})
</script>

<style scoped>
.academic-root {
  width: 100%;
  height: 100%;
  position: relative;
}

.academic-svg-container {
  width: 100%;
  height: 100%;
  min-height: 520px;
}

.academic-tooltip {
  position: absolute;
  z-index: 20;
  pointer-events: none;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #ddd;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  font-family: Arial, sans-serif;
  white-space: nowrap;
}

.tooltip-title {
  font-weight: 700;
  font-size: 14px;
  color: #222;
}

.tooltip-latin {
  font-size: 12px;
  font-style: italic;
  color: #666;
  margin-top: 2px;
}

.tooltip-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}

.tooltip-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}

.tooltip-stat {
  font-size: 11px;
  color: #888;
}
</style>

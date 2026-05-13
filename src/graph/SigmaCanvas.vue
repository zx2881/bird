<template>
  <div ref="containerRef" class="sigma-wrapper">
    <div v-if="tooltip.visible" class="sigma-tooltip" :style="tooltip.style">
      <div class="tooltip-name">{{ tooltip.name }}</div>
      <div class="tooltip-type">{{ tooltip.type }}</div>
      <div v-if="tooltip.latin" class="tooltip-latin">{{ tooltip.latin }}</div>
      <div class="tooltip-footer">
        <span v-if="tooltip.degree != null" class="tooltip-degree">{{ tooltip.degree }} 条关联</span>
        <span v-if="tooltip.status" class="tooltip-badge" :class="'badge-' + tooltip.status.toLowerCase()">{{ tooltip.status }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, reactive } from 'vue'
import Graph from 'graphology'
import { Sigma } from 'sigma'
import { useGraphStore } from '../stores/graphStore.js'

const props = defineProps({
  birdLimit: { type: Number, default: 80 },
  labelMode: { type: String, default: 'smart' },
  focusEntityId: { type: String, default: '' },
  activeTypes: { type: Array, default: () => ['location', 'habitat', 'status', 'threat'] },
  highlightPath: { type: Array, default: () => [] },
  darkMode: { type: Boolean, default: false }
})

const emit = defineEmits(['node-click'])

const containerRef = ref(null)
const store = useGraphStore()
let sigma = null
let graph = null
let resizeObserver = null
let hoveredNode = null

const tooltip = reactive({ visible: false, name: '', type: '', degree: null, latin: '', status: '', style: {} })

const palette = {
  light: {
    bird: '#4f8cf7', location: '#22c55e', habitat: '#f59e0b',
    status: '#8b5cf6', threat: '#ef4444', taxonomy: '#ec4899',
    birdStroke: '#3b72d3', locationStroke: '#16a34a', habitatStroke: '#d97706',
    statusStroke: '#7c3aed', threatStroke: '#dc2626', taxonomyStroke: '#db2777',
    edge: 'rgba(30, 41, 59, 0.5)', edgeActive: 'rgba(79, 140, 247, 0.75)',
    edgePath: 'rgba(217, 119, 6, 0.9)',
    label: '#0f172a', bg: '#ffffff',
    tooltipBg: 'rgba(255, 255, 255, 0.97)',
    tooltipBorder: 'rgba(79, 140, 247, 0.2)',
    tooltipShadow: '0 12px 40px rgba(0, 0, 0, 0.12)'
  },
  dark: {
    bird: '#93c5fd', location: '#6ee7b7', habitat: '#fde68a',
    status: '#c4b5fd', threat: '#fca5a5', taxonomy: '#f9a8d4',
    birdStroke: '#60a5fa', locationStroke: '#34d399', habitatStroke: '#fbbf24',
    statusStroke: '#a78bfa', threatStroke: '#f87171', taxonomyStroke: '#f472b6',
    edge: 'rgba(226, 232, 240, 0.3)', edgeActive: 'rgba(147, 197, 253, 0.7)',
    edgePath: 'rgba(251, 191, 36, 0.9)',
    label: '#ffffff', bg: 'transparent',
    tooltipBg: 'rgba(15, 23, 42, 0.96)',
    tooltipBorder: 'rgba(147, 197, 253, 0.2)',
    tooltipShadow: '0 12px 40px rgba(0, 0, 0, 0.5)'
  }
}

const c = () => props.darkMode ? palette.dark : palette.light

function buildGraph() {
  if (graph) graph.clear()
  else graph = new Graph({ multi: true, type: 'directed', allowSelfLoops: false })

  const enabled = new Set(props.activeTypes)
  const visibleIds = filterNodes(enabled)
  const { nodes, links } = getSnapshot(visibleIds, enabled)
  const col = c()
  const total = nodes.length
  const radius = Math.max(4, Math.sqrt(total) * 1.2)

  nodes.forEach((n, i) => {
    const size = nodeSize(n, total)
    const angle = (2 * Math.PI * i) / total
    graph.addNode(n.id, {
      label: computeLabel(n, total),
      size, color: col[n.type] || '#8b949e',
      x: Math.cos(angle) * radius, y: Math.sin(angle) * radius,
      entityType: n.type, name: n.name, degree: store.getNodeDegree(n.id),
      highlight: props.highlightPath.includes(n.id)
    })
  })

  links.forEach(l => {
    if (!graph.hasNode(l.source) || !graph.hasNode(l.target)) return
    const inPath = props.highlightPath.includes(l.source) && props.highlightPath.includes(l.target)
    try {
      graph.addEdgeWithKey(l.key, l.source, l.target, {
        type: 'arrow', size: inPath ? 3 : 1,
        color: inPath ? col.edgePath : col.edge,
        relation: l.relation
      })
    } catch (e) { /* skip duplicate */ }
  })
}

function filterNodes(enabled) {
  const ids = new Set()
  if (props.focusEntityId) {
    ids.add(props.focusEntityId)
    store.getIncidentLinks(props.focusEntityId).forEach(l => {
      const o = l.source === props.focusEntityId ? l.target : l.source
      const n = store.getNodeById(o)
      if (n && (n.type === 'bird' || enabled.has(n.type))) ids.add(o)
    })
  } else {
    const limit = props.birdLimit === 0 ? store.birdNodes.length : props.birdLimit
    store.birdNodes.slice(0, limit).forEach(b => {
      ids.add(b.id)
      store.getIncidentLinks(b.id).forEach(l => {
        const o = l.source === b.id ? l.target : l.source
        const n = store.getNodeById(o)
        if (n && enabled.has(n.type)) ids.add(o)
      })
    })
  }
  return ids
}

function getSnapshot(visibleIds, enabled) {
  const nodes = [...visibleIds].map(id => store.getNodeById(id)).filter(Boolean)
  const linkMap = new Map()
  visibleIds.forEach(nid => {
    store.getIncidentLinks(nid).forEach(l => {
      if (!visibleIds.has(l.source) || !visibleIds.has(l.target)) return
      const sn = store.getNodeById(l.source)
      const tn = store.getNodeById(l.target)
      if (!sn || !tn) return
      if (sn.type !== 'bird' && !enabled.has(sn.type) && sn.id !== props.focusEntityId) return
      if (tn.type !== 'bird' && !enabled.has(tn.type) && tn.id !== props.focusEntityId) return
      if (!linkMap.has(l.key)) linkMap.set(l.key, l)
    })
  })
  return { nodes, links: [...linkMap.values()] }
}

function computeLabel(n, count) {
  if (props.labelMode === 'all') return n.name || n.id
  if (props.labelMode === 'birds') return n.type === 'bird' ? n.name : ''
  const deg = store.getNodeDegree(n.id)
  if (n.type === 'bird') return count <= 54 || deg >= 6 ? n.name : ''
  if (n.type === 'location') return count <= 42 && deg >= 4 ? n.name : ''
  return count <= 28 && deg >= 5 ? n.name : ''
}

function nodeSize(n, count) {
  const scale = count > 260 ? 0.56 : count > 170 ? 0.68 : count > 90 ? 0.82 : 1
  const base = { bird: 14, location: 9, habitat: 7, status: 6, threat: 6, taxonomy: 6 }[n.type] ?? 7
  const boost = Math.min(n.type === 'bird' ? 5 : 3, store.getNodeDegree(n.id) * 0.35)
  return Math.max(4, Math.round((base + boost) * scale))
}

function getStageColor() {
  const el = containerRef.value
  if (!el) return c().bg
  const bg = getComputedStyle(el).backgroundColor
  return bg === 'rgba(0, 0, 0, 0)' || !bg ? c().bg : bg
}

function initSigma() {
  const el = containerRef.value
  if (!el || !store.nodes.length) return
  const w = el.clientWidth
  const h = el.clientHeight
  if (w === 0 || h === 0) { setTimeout(initSigma, 200); return }

  buildGraph()
  if (sigma) { sigma.kill(); sigma = null }

  const col = c()

  sigma = new Sigma(graph, el, {
    renderEdgeLabels: false,
    labelFont: 'Alegreya Sans, sans-serif',
    labelSize: 13,
    labelWeight: '700',
    labelRenderedSizeThreshold: 4,
    labelColor: { color: props.darkMode ? '#ffffff' : '#0f172a' },
    labelStroke: props.darkMode ? '#0f172a' : '#ffffff',
    labelStrokeWidth: props.darkMode ? 4 : 2,
    defaultEdgeColor: col.edge,
    defaultEdgeType: 'arrow',
    edgeLabelSize: 9,
    zIndex: true,
    enableEdgeEvents: true,
    nodeReducer: (nid, data) => {
      const node = store.getNodeById(nid)
      const type = node?.type || 'bird'
      const color = col[type] || col.bird
      const stroke = col[type + 'Stroke'] || col.birdStroke
      if (hoveredNode === nid) {
        return {
          ...data, color, size: (data.size || 8) * 2.5,
          label: node?.name || data.label,
          borderColor: '#fff', borderSize: 4,
          forceLabel: true
        }
      }
      if (hoveredNode && nid !== hoveredNode) {
        const connected = graph.edges(hoveredNode).some(e => {
          const [s, t] = graph.extremities(e)
          return s === nid || t === nid
        })
        if (!connected) {
          return {
            ...data, color, size: Math.max(2, (data.size || 8) * 0.2),
            borderColor: stroke, borderSize: 0.3
          }
        }
        return {
          ...data, color, size: (data.size || 8) * 0.85,
          borderColor: stroke, borderSize: 1.5,
          label: node?.name || data.label
        }
      }
      return { ...data, color, borderColor: stroke, borderSize: 1 }
    },
    edgeReducer: (eid, data) => {
      if (hoveredNode) {
        const [s, t] = graph.extremities(eid)
        if (s === hoveredNode || t === hoveredNode) {
          return { ...data, color: col.edgeActive, size: 4 }
        }
        return { ...data, size: (data.size || 1) * 0.08, color: col.edge }
      }
      return data
    }
  })

  sigma.on('clickNode', (e) => {
    const node = store.getNodeById(e.node)
    if (node) emit('node-click', node)
  })

  sigma.on('enterNode', (e) => {
    hoveredNode = e.node
    const n = store.getNodeById(e.node)
    if (n) {
      tooltip.visible = true
      tooltip.name = n.name || n.id
      tooltip.type = typeLabel(n.type)
      tooltip.degree = store.getNodeDegree(n.id)
      tooltip.latin = n.latinName || ''
      tooltip.status = n.status || ''
    }
    sigma.refresh()
  })

  sigma.on('leaveNode', () => {
    hoveredNode = null
    tooltip.visible = false
    sigma.refresh()
  })

  sigma.getCamera().animatedReset({ duration: 300 })
}

function typeLabel(t) {
  return { bird: '鸟类', location: '地点', habitat: '栖息地', status: '保护等级', threat: '威胁因素', taxonomy: '分类单元' }[t] || t
}

function updateTooltipPos(e) {
  if (!tooltip.visible) return
  const container = containerRef.value
  if (!container) return
  const rect = container.getBoundingClientRect()
  tooltip.style = {
    left: (e.x || e.clientX) - rect.left + 14 + 'px',
    top: (e.y || e.clientY) - rect.top - 10 + 'px'
  }
}

function startResizeObserver() {
  if (!containerRef.value) return
  resizeObserver = new ResizeObserver(() => {
    const el = containerRef.value
    if (!el) return
    if (!sigma) { initSigma(); return }
    if (el.clientWidth !== sigma.width || el.clientHeight !== sigma.height) {
      sigma.kill(); sigma = null; initSigma()
    }
  })
  resizeObserver.observe(containerRef.value)
}

watch(() => [props.birdLimit, props.labelMode, props.focusEntityId, props.activeTypes.join(','), props.darkMode],
  () => {
    hoveredNode = null; tooltip.visible = false
    if (sigma) { sigma.kill(); sigma = null }
    setTimeout(initSigma, 50)
  })

watch(() => props.highlightPath, () => {
  if (!sigma || !graph) return
  const col = c()
  graph.forEachNode(nid => {
    const inPath = props.highlightPath.includes(nid)
    graph.setNodeAttribute(nid, 'highlight', inPath)
  })
  graph.forEachEdge(eid => {
    const [s, t] = graph.extremities(eid)
    const inPath = props.highlightPath.includes(s) && props.highlightPath.includes(t)
    graph.setEdgeAttribute(eid, 'color', inPath ? col.edgePath : col.edge)
    graph.setEdgeAttribute(eid, 'size', inPath ? 3 : 1)
  })
  sigma.refresh()
}, { deep: true })

onMounted(() => {
  if (store.loaded) setTimeout(initSigma, 100)
  startResizeObserver()
  window.addEventListener('mousemove', updateTooltipPos)
})

watch(() => store.loaded, (v) => { if (v) setTimeout(initSigma, 100) })

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', updateTooltipPos)
  if (resizeObserver) resizeObserver.disconnect()
  if (sigma) { sigma.kill(); sigma = null }
})
</script>

<style scoped>
.sigma-wrapper { position: absolute; top: 0; left: 0; right: 0; bottom: 0; }

.sigma-tooltip {
  position: absolute; z-index: 10; pointer-events: none;
  padding: 12px 16px; border-radius: 14px;
  background: var(--card-bg, rgba(255, 255, 255, 0.97));
  border: 1px solid var(--panel-border, rgba(79, 140, 247, 0.2));
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(12px);
  white-space: nowrap;
  min-width: 120px;
}
.tooltip-name { font-weight: 700; font-size: 15px; color: var(--heading-color, #12303b); }
.tooltip-type { font-size: 11px; color: var(--text-secondary, rgba(18, 48, 59, 0.55)); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.05em; }
.tooltip-latin { font-size: 12px; font-style: italic; color: var(--text-secondary, rgba(18, 48, 59, 0.5)); margin-top: 3px; padding-top: 6px; border-top: 1px solid rgba(0,0,0,0.06); }
.tooltip-footer { display: flex; align-items: center; gap: 8px; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(0,0,0,0.06); }
.tooltip-degree { font-size: 11px; color: var(--accent, #4f8cf7); font-weight: 600; }
.tooltip-badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; color: #fff; letter-spacing: 0.03em; }
.badge-cr { background: #ef4444; } .badge-en { background: #f97316; } .badge-vu { background: #eab308; color: #1e293b; } .badge-nt { background: #22c55e; } .badge-lc { background: #16a34a; }
</style>

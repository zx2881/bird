<template>
  <div ref="containerRef" class="sigma-wrapper">
    <div v-if="tooltip.visible" class="sigma-tooltip" :style="tooltip.style">
      <div class="tooltip-name">{{ tooltip.name }}</div>
      <div class="tooltip-type">{{ tooltip.type }}</div>
      <div v-if="tooltip.degree != null" class="tooltip-degree">{{ tooltip.degree }} 条关联</div>
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

const tooltip = reactive({ visible: false, name: '', type: '', degree: null, style: {} })

const palette = {
  light: {
    bird: '#5a6b7f', location: '#4d7a74', habitat: '#6b8a4e',
    status: '#937a48', threat: '#7a555d', taxonomy: '#6e6791',
    edge: 'rgba(30, 41, 59, 0.25)', edgeActive: 'rgba(15, 118, 110, 0.55)',
    edgePath: 'rgba(251, 191, 36, 0.7)',
    label: '#1e293b', bg: '#ffffff'
  },
  dark: {
    bird: '#94a3b8', location: '#6f9e98', habitat: '#8da56b',
    status: '#b59a62', threat: '#9f727a', taxonomy: '#8b84ab',
    edge: 'rgba(255, 255, 255, 0.12)', edgeActive: 'rgba(94, 234, 212, 0.4)',
    edgePath: 'rgba(251, 191, 36, 0.7)',
    label: '#f1f5f9', bg: 'transparent'
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

  sigma = new Sigma(graph, el, {
    renderEdgeLabels: false,
    labelFont: 'Alegreya Sans, sans-serif',
    labelSize: 11,
    labelColor: { color: props.darkMode ? '#e2e8f0' : '#1e293b' },
    defaultEdgeColor: c().edge,
    defaultEdgeType: 'arrow',
    edgeLabelSize: 9,
    zIndex: true,
    // nodeReducer applies hover effect per-frame
    nodeReducer: (nid, data) => {
      if (hoveredNode === nid) {
        return { ...data, size: (data.size || 8) * 2, label: store.getNodeById(nid)?.name || data.label }
      }
      if (hoveredNode && nid !== hoveredNode) {
        const connected = graph.edges(hoveredNode).some(e => {
          const [s, t] = graph.extremities(e)
          return s === nid || t === nid
        })
        if (!connected) return { ...data, size: Math.max(3, (data.size || 8) * 0.4), label: data.label }
      }
      return data
    },
    edgeReducer: (eid, data) => {
      if (hoveredNode) {
        const [s, t] = graph.extremities(eid)
        if (s === hoveredNode || t === hoveredNode) {
          return { ...data, color: c().edgeActive, size: 2 }
        }
        return { ...data, size: (data.size || 1) * 0.2 }
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
  padding: 8px 12px; border-radius: 10px;
  background: var(--card-bg, rgba(255, 255, 255, 0.92));
  border: 1px solid var(--panel-border, rgba(18, 48, 59, 0.1));
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(8px);
  white-space: nowrap;
}
.tooltip-name { font-weight: 700; font-size: 14px; color: var(--heading-color, #12303b); }
.tooltip-type { font-size: 11px; color: var(--text-secondary, rgba(18, 48, 59, 0.55)); margin-top: 1px; }
.tooltip-degree { font-size: 11px; color: var(--accent, #0f766e); margin-top: 2px; }
</style>

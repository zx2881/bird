<template>
  <div class="page-wrapper">
    <div ref="graphRef" class="graph-stage"></div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ForceGraph3D from '3d-force-graph'
import * as THREE from 'three'
import { useGraphStore } from '../stores/graphStore.js'

const props = defineProps({
  activeTypes: {
    type: Array,
    default: () => ['location', 'habitat', 'status', 'threat']
  },
  darkMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['node-click'])

const store = useGraphStore()
const graphRef = ref(null)

let graph = null
let renderTimer = 0
let resizeObserver = null
let fitTimer = 0
let returnFrame = 0
let returnToken = 0

const cachedNodes = new Map()
const dragState = {
  centerId: '',
  wakeIds: []
}

const LOCAL_WAKE_LIMIT = 18
const RETURN_EASE = 0.22
const MAX_RETURN_FRAMES = 18

const UNIFORM_LAYOUT_RADIUS = 960
const DETAIL_CLUSTER_RADIUS = 30
const DETAIL_CLUSTER_JITTER = 18

const PREVIEW_NODE_COLOR = '#eaf3ff'
const DETAIL_NODE_COLOR = '#9fc0ff'
const BACKGROUND_DARK = '#0b1018'
const BACKGROUND_LIGHT = '#101827'
const LINK_COLOR = 'rgba(229, 239, 255, 0.18)'

function isPreviewNode(node) {
  return node?.type === 'bird' || node?.type === 'taxonomy'
}

function isNodeVisible(node) {
  if (!node) return false
  if (isPreviewNode(node)) return true
  return props.activeTypes.includes(node.type)
}

function nodeRadius(node) {
  if (!node) return 1.72
  if (isPreviewNode(node.rawNode || node)) return 1.82
  return 1.42
}

function sphereSegments(node) {
  return isPreviewNode(node.rawNode || node) ? 7 : 6
}

function hitRadius(node) {
  if (!node) return 5
  if (isPreviewNode(node.rawNode || node)) return 5.2
  return 4.5
}

function linkDistance(link) {
  if (!link) return 64
  if (link.relation === 'belongs_to_family' || link.relation === 'belongs_to_order') return 56
  return 42
}

function stableHash(value) {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function stableUnit(value, salt = '') {
  return stableHash(`${salt}:${value}`) / 4294967295
}

function buildUniformLayoutMap(sourceNodes) {
  const layoutNodes = sourceNodes
    .filter(isPreviewNode)
    .slice()
    .sort((left, right) => stableHash(left.id) - stableHash(right.id))

  const layoutMap = new Map()
  if (!layoutNodes.length) return layoutMap

  let sumX = 0
  let sumY = 0
  let sumZ = 0

  layoutNodes.forEach((node, index) => {
    const total = layoutNodes.length
    const volumeT = Math.max(1e-6, Math.min(0.999999, (index + stableUnit(node.id, 'radius')) / total))
    const radius = UNIFORM_LAYOUT_RADIUS * Math.cbrt(volumeT)
    const theta = Math.PI * 2 * stableUnit(node.id, 'theta')
    const cosPhi = 1 - 2 * stableUnit(node.id, 'phi')
    const sinPhi = Math.sqrt(Math.max(0, 1 - cosPhi * cosPhi))
    const x = radius * sinPhi * Math.cos(theta)
    const y = radius * sinPhi * Math.sin(theta)
    const z = radius * cosPhi

    sumX += x
    sumY += y
    sumZ += z

    layoutMap.set(node.id, {
      x,
      y,
      z
    })
  })

  const centerX = sumX / layoutNodes.length
  const centerY = sumY / layoutNodes.length
  const centerZ = sumZ / layoutNodes.length

  for (const [nodeId, position] of layoutMap.entries()) {
    position.x -= centerX
    position.y -= centerY
    position.z -= centerZ
    layoutMap.set(nodeId, position)
  }

  return layoutMap
}

function buildFallbackScatter(nodeId) {
  const theta = Math.PI * 2 * stableUnit(nodeId, 'fallback-theta')
  const cosPhi = 1 - 2 * stableUnit(nodeId, 'fallback-phi')
  const sinPhi = Math.sqrt(Math.max(0, 1 - cosPhi * cosPhi))
  const radius = UNIFORM_LAYOUT_RADIUS * 0.62 * Math.cbrt(stableUnit(nodeId, 'fallback-radius'))

  return {
    x: radius * sinPhi * Math.cos(theta),
    y: radius * sinPhi * Math.sin(theta),
    z: radius * cosPhi
  }
}

function buildAttachedScatter(nodeId, anchor) {
  const theta = Math.PI * 2 * stableUnit(nodeId, 'detail-theta')
  const cosPhi = 1 - 2 * stableUnit(nodeId, 'detail-phi')
  const sinPhi = Math.sqrt(Math.max(0, 1 - cosPhi * cosPhi))
  const radius = DETAIL_CLUSTER_RADIUS + stableUnit(nodeId, 'detail-radius') * DETAIL_CLUSTER_JITTER

  return {
    x: anchor.x + radius * sinPhi * Math.cos(theta),
    y: anchor.y + radius * sinPhi * Math.sin(theta),
    z: anchor.z + radius * cosPhi
  }
}

function resolveAnchorHome(nodeId, layoutMap) {
  for (const link of store.getIncidentLinks(nodeId)) {
    const otherId = link.source === nodeId ? link.target : link.source
    if (layoutMap.has(otherId)) return layoutMap.get(otherId)

    const cached = cachedNodes.get(otherId)
    if (
      cached &&
      Number.isFinite(cached.homeX) &&
      Number.isFinite(cached.homeY) &&
      Number.isFinite(cached.homeZ)
    ) {
      return {
        x: cached.homeX,
        y: cached.homeY,
        z: cached.homeZ
      }
    }
  }

  const activeNode = cachedNodes.get(store.activeNodeId)
  if (
    activeNode &&
    Number.isFinite(activeNode.homeX) &&
    Number.isFinite(activeNode.homeY) &&
    Number.isFinite(activeNode.homeZ)
  ) {
    return {
      x: activeNode.homeX,
      y: activeNode.homeY,
      z: activeNode.homeZ
    }
  }

  return null
}

function resolveNodeHome(rawNode, layoutMap) {
  if (layoutMap.has(rawNode.id)) return layoutMap.get(rawNode.id)

  const anchorHome = resolveAnchorHome(rawNode.id, layoutMap)
  if (anchorHome) return buildAttachedScatter(rawNode.id, anchorHome)

  return buildFallbackScatter(rawNode.id)
}

function buildNodeObject(node) {
  if (!node.__group) {
    node.__group = new THREE.Group()
  }

  const radius = nodeRadius(node)
  const pointerRadius = hitRadius(node)
  const segments = sphereSegments(node)

  if (!node.__sphereGeometry || node.__sphereRadius !== radius || node.__sphereSegments !== segments) {
    node.__sphereGeometry?.dispose?.()
    node.__sphereGeometry = new THREE.SphereGeometry(radius, segments, segments)
    node.__sphereRadius = radius
    node.__sphereSegments = segments
  }

  if (!node.__sphereMaterial) {
    node.__sphereMaterial = new THREE.MeshBasicMaterial({
      color: node.color,
      transparent: true,
      opacity: node.opacity
    })
  }

  node.__sphereMaterial.color = new THREE.Color(node.color)
  node.__sphereMaterial.opacity = node.opacity

  if (!node.__sphereMesh) {
    node.__sphereMesh = new THREE.Mesh(node.__sphereGeometry, node.__sphereMaterial)
    node.__group.add(node.__sphereMesh)
  } else {
    node.__sphereMesh.geometry = node.__sphereGeometry
    node.__sphereMesh.material = node.__sphereMaterial
  }

  if (!node.__hitGeometry || node.__hitRadius !== pointerRadius) {
    node.__hitGeometry?.dispose?.()
    node.__hitGeometry = new THREE.SphereGeometry(pointerRadius, 10, 10)
    node.__hitRadius = pointerRadius
  }

  if (!node.__hitMaterial) {
    node.__hitMaterial = new THREE.MeshBasicMaterial({
      color: '#ffffff',
      transparent: true,
      opacity: 0,
      depthWrite: false
    })
  }

  if (!node.__hitMesh) {
    node.__hitMesh = new THREE.Mesh(node.__hitGeometry, node.__hitMaterial)
    node.__group.add(node.__hitMesh)
  } else {
    node.__hitMesh.geometry = node.__hitGeometry
    node.__hitMesh.material = node.__hitMaterial
  }

  return node.__group
}

function buildTooltip(node) {
  if (!node?.rawNode) return node?.name || ''

  const raw = node.rawNode
  const lines = [
    `<div style="font-weight:700;margin-bottom:4px;">${raw.name || raw.id}</div>`
  ]

  if (raw.englishName && raw.englishName !== raw.name) {
    lines.push(`<div style="opacity:.82;">${raw.englishName}</div>`)
  }
  if (raw.latinName) lines.push(`<div style="opacity:.82;">${raw.latinName}</div>`)
  if (raw.orderCn || raw.order) lines.push(`<div style="opacity:.7;">目：${raw.orderCn || raw.order}</div>`)
  if (raw.familyCn || raw.family) lines.push(`<div style="opacity:.7;">科：${raw.familyCn || raw.family}</div>`)

  return lines.join('')
}

function ensureHomePosition(node) {
  if (node.homeX == null) node.homeX = Number.isFinite(node.x) ? node.x : 0
  if (node.homeY == null) node.homeY = Number.isFinite(node.y) ? node.y : 0
  if (node.homeZ == null) node.homeZ = Number.isFinite(node.z) ? node.z : 0
}

function pinNodeToHome(node) {
  ensureHomePosition(node)
  node.x = node.homeX
  node.y = node.homeY
  node.z = node.homeZ
  node.fx = node.homeX
  node.fy = node.homeY
  node.fz = node.homeZ
  node.vx = 0
  node.vy = 0
  node.vz = 0
}

function releaseNode(node) {
  ensureHomePosition(node)
  node.fx = undefined
  node.fy = undefined
  node.fz = undefined
}

function isWakeNode(nodeId) {
  return dragState.wakeIds.includes(nodeId)
}

function getWakeIds(centerId) {
  const ids = []
  const seen = new Set()

  function push(id) {
    if (!id || seen.has(id) || ids.length >= LOCAL_WAKE_LIMIT) return
    seen.add(id)
    ids.push(id)
  }

  push(centerId)

  for (const link of store.getIncidentLinks(centerId)) {
    if (ids.length >= LOCAL_WAKE_LIMIT) break
    const otherId = link.source === centerId ? link.target : link.source
    push(otherId)
  }

  return ids
}

function cancelReturnAnimation() {
  returnToken += 1
  if (returnFrame) {
    window.cancelAnimationFrame(returnFrame)
    returnFrame = 0
  }
}

function materializeGraphData() {
  const visibleNodes = store.nodes.filter(isNodeVisible)
  const visibleIds = new Set(visibleNodes.map(node => node.id))
  const layoutMap = buildUniformLayoutMap(visibleNodes)

  const nodes = visibleNodes.map(rawNode => {
    const cached = cachedNodes.get(rawNode.id)
    const nextNode = cached || { id: rawNode.id }
    const home = resolveNodeHome(rawNode, layoutMap)
    const previewNode = isPreviewNode(rawNode)

    nextNode.id = rawNode.id
    nextNode.name = rawNode.name || rawNode.englishName || rawNode.id
    nextNode.rawNode = rawNode
    nextNode.type = rawNode.type
    nextNode.color = previewNode ? PREVIEW_NODE_COLOR : DETAIL_NODE_COLOR
    nextNode.opacity = previewNode ? 0.98 : 0.92
    nextNode.distance = 0
    nextNode.homeX = home.x
    nextNode.homeY = home.y
    nextNode.homeZ = home.z

    if (!isWakeNode(nextNode.id)) {
      pinNodeToHome(nextNode)
    } else {
      if (!Number.isFinite(nextNode.x)) nextNode.x = nextNode.homeX
      if (!Number.isFinite(nextNode.y)) nextNode.y = nextNode.homeY
      if (!Number.isFinite(nextNode.z)) nextNode.z = nextNode.homeZ
      releaseNode(nextNode)
    }

    cachedNodes.set(rawNode.id, nextNode)
    return nextNode
  })

  const links = store.links
    .filter(link => visibleIds.has(link.source) && visibleIds.has(link.target))
    .map(link => ({
      source: link.source,
      target: link.target,
      relation: link.relation,
      distance: linkDistance(link)
    }))

  return { nodes, links }
}

function applyFrozenAnchors() {
  if (!graph) return
  for (const node of graph.graphData().nodes) {
    if (isWakeNode(node.id)) continue
    pinNodeToHome(node)
  }
  graph.cooldownTicks(0)
}

function ensureGraph() {
  if (graph || !graphRef.value) return

  graph = ForceGraph3D()(graphRef.value)
    .backgroundColor(props.darkMode ? BACKGROUND_DARK : BACKGROUND_LIGHT)
    .showNavInfo(false)
    .enableNodeDrag(true)
    .nodeOpacity(1)
    .linkOpacity(0.2)
    .linkWidth(() => 0.36)
    .linkColor(() => LINK_COLOR)
    .linkDirectionalParticles(0)
    .nodeLabel(buildTooltip)
    .nodeThreeObject(node => buildNodeObject(node))
    .onNodeClick(node => {
      if (!node?.rawNode) return
      emit('node-click', node.rawNode)
    })
    .onNodeHover(node => {
      if (!graphRef.value) return
      graphRef.value.style.cursor = node ? 'pointer' : 'grab'
    })
    .onNodeDrag(node => {
      if (!node?.id) return
      activateLocalWake(node.id)
    })
    .onNodeDragEnd(node => {
      if (!node?.id) return
      releaseNode(node)
      startReturnToHome(node.id)
    })

  graph.d3Force('charge').strength(node => {
    if (!isWakeNode(node?.id)) return -2
    return isPreviewNode(node) ? -56 : -32
  })
  graph.d3Force('link').distance(link => link.distance).strength(link => {
    if (link.relation === 'belongs_to_family' || link.relation === 'belongs_to_order') return 0.18
    return 0.12
  })
  graph.d3VelocityDecay(0.78)
  graph.cooldownTicks(0)
  graph.cameraPosition({ x: 0, y: 0, z: 1750 }, { x: 0, y: 0, z: 0 }, 0)

  const controls = graph.controls()
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.rotateSpeed = 0.72
  controls.zoomSpeed = 0.95
  controls.panSpeed = 0.9
  controls.minDistance = 120
  controls.maxDistance = 4200

  resizeGraph()
}

function activateLocalWake(centerId) {
  if (!graph) return
  if (dragState.centerId === centerId && dragState.wakeIds.length) return

  cancelReturnAnimation()
  const wakeIds = getWakeIds(centerId)
  if (!wakeIds.length) return

  dragState.centerId = centerId
  dragState.wakeIds = wakeIds

  for (const node of graph.graphData().nodes) {
    if (wakeIds.includes(node.id)) {
      releaseNode(node)
      continue
    }
    pinNodeToHome(node)
  }

  graph.cooldownTicks(70)
  graph.d3VelocityDecay(0.48)
  graph.d3ReheatSimulation()
}

function startReturnToHome(centerId) {
  if (!graph) return

  const wakeIds = dragState.wakeIds.length ? [...dragState.wakeIds] : getWakeIds(centerId)
  if (!wakeIds.length) return

  cancelReturnAnimation()
  const token = returnToken
  let frame = 0

  graph.cooldownTicks(0)

  const step = () => {
    if (!graph || token !== returnToken) return

    frame += 1
    let settled = true

    for (const node of graph.graphData().nodes) {
      if (!wakeIds.includes(node.id)) continue

      ensureHomePosition(node)

      node.x += (node.homeX - node.x) * RETURN_EASE
      node.y += (node.homeY - node.y) * RETURN_EASE
      node.z += (node.homeZ - node.z) * RETURN_EASE

      if (
        Math.abs(node.homeX - node.x) > 0.6 ||
        Math.abs(node.homeY - node.y) > 0.6 ||
        Math.abs(node.homeZ - node.z) > 0.6
      ) {
        settled = false
      }
    }

    if (!settled && frame < MAX_RETURN_FRAMES) {
      returnFrame = window.requestAnimationFrame(step)
      return
    }

    for (const node of graph.graphData().nodes) {
      if (!wakeIds.includes(node.id)) continue
      pinNodeToHome(node)
    }

    dragState.centerId = ''
    dragState.wakeIds = []
    graph.d3VelocityDecay(0.78)
    graph.cooldownTicks(0)
    returnFrame = 0
  }

  returnFrame = window.requestAnimationFrame(step)
}

function updateGraph(forceFit = false) {
  if (!graph) return
  graph.graphData(materializeGraphData())
  applyFrozenAnchors()

  if (forceFit) scheduleZoomToFit(220)
}

function scheduleRender(forceFit = false) {
  if (renderTimer) window.clearTimeout(renderTimer)
  renderTimer = window.setTimeout(() => {
    renderTimer = 0
    updateGraph(forceFit)
  }, 28)
}

function getGraphBounds() {
  if (!graph) return null
  const nodes = graph.graphData().nodes || []
  if (!nodes.length) return null

  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity
  let minZ = Infinity
  let maxZ = -Infinity

  for (const node of nodes) {
    const x = Number.isFinite(node.x) ? node.x : node.homeX
    const y = Number.isFinite(node.y) ? node.y : node.homeY
    const z = Number.isFinite(node.z) ? node.z : node.homeZ
    if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) continue

    minX = Math.min(minX, x)
    maxX = Math.max(maxX, x)
    minY = Math.min(minY, y)
    maxY = Math.max(maxY, y)
    minZ = Math.min(minZ, z)
    maxZ = Math.max(maxZ, z)
  }

  if (!Number.isFinite(minX)) return null

  return {
    center: {
      x: (minX + maxX) / 2,
      y: (minY + maxY) / 2,
      z: (minZ + maxZ) / 2
    },
    span: {
      x: Math.max(1, maxX - minX),
      y: Math.max(1, maxY - minY),
      z: Math.max(1, maxZ - minZ)
    }
  }
}

function scheduleZoomToFit(delay = 0) {
  if (!graph) return
  if (fitTimer) window.clearTimeout(fitTimer)

  fitTimer = window.setTimeout(() => {
    fitTimer = 0

    const bounds = getGraphBounds()
    if (!bounds) return

    const canvasWidth = Math.max(1, graph.width() || graphRef.value?.clientWidth || 1)
    const canvasHeight = Math.max(1, graph.height() || graphRef.value?.clientHeight || 1)
    const aspect = canvasWidth / canvasHeight
    const camera = graph.camera()
    const verticalFov = THREE.MathUtils.degToRad(camera.fov || 40)
    const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * aspect)

    const fitWidthDistance = (bounds.span.x * 0.54 + 80) / Math.tan(horizontalFov / 2)
    const fitHeightDistance = (bounds.span.y * 0.54 + 80) / Math.tan(verticalFov / 2)
    const depthDistance = bounds.span.z * 1.8 + 260
    const distance = Math.max(420, fitWidthDistance, fitHeightDistance, depthDistance)

    graph.cameraPosition(
      {
        x: bounds.center.x,
        y: bounds.center.y,
        z: bounds.center.z + distance
      },
      bounds.center,
      900
    )
  }, delay)
}

function resizeGraph() {
  if (!graph || !graphRef.value) return
  graph.width(graphRef.value.clientWidth)
  graph.height(graphRef.value.clientHeight)
}

function focusNode(nodeId) {
  if (!graph || !nodeId) return

  const node = graph.graphData().nodes.find(item => item.id === nodeId)
  if (!node) return
  ensureHomePosition(node)

  const targetX = Number.isFinite(node.x) ? node.x : node.homeX
  const targetY = Number.isFinite(node.y) ? node.y : node.homeY
  const targetZ = Number.isFinite(node.z) ? node.z : node.homeZ

  graph.cameraPosition(
    {
      x: targetX,
      y: targetY,
      z: targetZ + 210
    },
    { x: targetX, y: targetY, z: targetZ },
    750
  )
}

function startResizeObserver() {
  if (!graphRef.value || resizeObserver) return

  resizeObserver = new ResizeObserver(() => {
    resizeGraph()
  })

  resizeObserver.observe(graphRef.value)
}

onMounted(async () => {
  await nextTick()
  ensureGraph()
  startResizeObserver()

  if (store.loaded) {
    updateGraph(true)
  }
})

watch(() => store.loaded, async value => {
  if (!value) return
  await nextTick()
  ensureGraph()
  updateGraph(true)
})

watch(
  () => [
    store.nodeCount,
    store.linkCount,
    store.lastMutation?.serial || 0,
    store.activeNodeId,
    props.activeTypes.join(','),
    props.darkMode
  ],
  () => {
    if (!graph) return
    graph.backgroundColor(props.darkMode ? BACKGROUND_DARK : BACKGROUND_LIGHT)
    scheduleRender()
  }
)

watch(() => store.focusRequest.nonce, () => {
  if (!store.focusRequest.id) return
  focusNode(store.focusRequest.id)
})

watch(() => store.fitRequest.nonce, () => {
  if (!graph) return
  scheduleZoomToFit(40)
})

onBeforeUnmount(() => {
  cancelReturnAnimation()
  if (renderTimer) window.clearTimeout(renderTimer)
  if (fitTimer) window.clearTimeout(fitTimer)
  if (resizeObserver) resizeObserver.disconnect()
  if (graph) {
    graph.pauseAnimation()
  }
  graph = null
})
</script>

<style scoped>
.page-wrapper {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1;
}

.graph-stage {
  position: absolute;
  inset: 0;
  cursor: grab;
}
</style>

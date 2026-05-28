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
  },
  centerNodeId: {
    type: String,
    default: ''
  },
  focusedNodeId: {
    type: String,
    default: ''
  },
  activeTaxonomyLevels: {
    type: Array,
    default: () => ['order', 'family']
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

const BACKGROUND_DARK = '#0b1018'
const BACKGROUND_LIGHT = '#101827'

const TYPE_COLORS = {
  bird: '#4FC3F7',
  location: '#81C784',
  habitat: '#FFB74D',
  status: '#E57373',
  threat: '#BA68C8',
  taxonomy: '#90A4AE'
}

function nodeColor(rawNode) {
  if (rawNode.type === 'taxonomy') {
    return TAXONOMY_COLORS[rawNode.taxonomyLevel] || TYPE_COLORS.taxonomy
  }
  return TYPE_COLORS[rawNode.type] || '#eaf3ff'
}
const LINK_COLOR_DARK = 'rgba(210, 230, 255, 0.46)'
const LINK_COLOR_LIGHT = 'rgba(210, 230, 255, 0.4)'
const FOCUSED_LINK_COLOR = 'rgba(125, 211, 252, 0.88)'
const HIGH_TAXONOMY_LEVELS = new Set(['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species'])
const TAXONOMY_COLORS = {
  kingdom: '#64748b',
  phylum: '#78909c',
  class: '#90a4ae',
  order: '#38bdf8',
  family: '#22c55e',
  genus: '#f59e0b',
  species: '#ef4444'
}
const TAXONOMY_LABELS = {
  kingdom: '界',
  phylum: '门',
  class: '纲',
  order: '目',
  family: '科',
  genus: '属',
  species: '种'
}

function isPreviewNode(node) {
  return node?.type === 'bird' || node?.type === 'taxonomy'
}

function isHighTaxonomyNode(node) {
  return node?.type === 'taxonomy' && HIGH_TAXONOMY_LEVELS.has(node.taxonomyLevel)
}

function isActiveTaxonomyNode(node) {
  if (node?.type !== 'taxonomy') return false
  if (['kingdom', 'phylum', 'class'].includes(node.taxonomyLevel)) return true
  return props.activeTaxonomyLevels.includes(node.taxonomyLevel)
}

function getFocusedNeighborIds() {
  if (!props.focusedNodeId) return new Set()
  const neighborIds = new Set()
  neighborIds.add(props.focusedNodeId)
  for (const link of store.getIncidentLinks(props.focusedNodeId)) {
    const otherId = link.source === props.focusedNodeId ? link.target : link.source
    neighborIds.add(otherId)
  }
  return neighborIds
}

function isNodeVisible(node) {
  if (!node) return false

  if (props.focusedNodeId) {
    const neighborIds = getFocusedNeighborIds()
    return neighborIds.has(node.rawNode?.id || node.id)
  }

  if (node.type === 'taxonomy') {
    return props.activeTypes.includes('taxonomy') && isActiveTaxonomyNode(node) && (isHighTaxonomyNode(node) || store.getIncidentLinks(node.id).length > 0)
  }
  if (isPreviewNode(node)) return true
  return props.activeTypes.includes(node.type)
}

function nodeRadius(node) {
  if (!node) return 1.72
  const raw = node.rawNode || node
  const id = raw.id || node.id

  if (props.focusedNodeId) {
    if (id === props.focusedNodeId) return 5.6
    const neighborIds = getFocusedNeighborIds()
    if (neighborIds.has(id)) return 3.2
  }

  if (id === props.centerNodeId) return 2.8
  if (isPreviewNode(raw)) return 1.82
  return 1.42
}

function sphereSegments(node) {
  const raw = node.rawNode || node
  const id = raw.id || node.id

  if (props.focusedNodeId && id === props.focusedNodeId) return 16
  if (props.focusedNodeId && getFocusedNeighborIds().has(id)) return 12
  if (id === props.centerNodeId) return 12
  return isPreviewNode(raw) ? 7 : 6
}

function hitRadius(node) {
  if (!node) return 5
  const raw = node.rawNode || node
  const id = raw.id || node.id

  if (props.focusedNodeId) {
    if (id === props.focusedNodeId) return 14
    const neighborIds = getFocusedNeighborIds()
    if (neighborIds.has(id)) return 9
  }

  if (id === props.centerNodeId) return 8
  if (isPreviewNode(raw)) return 5.2
  return 4.5
}

function linkDistance(link) {
  if (!link) return 64
  if (link.relation?.startsWith('belongs_to_')) return 56
  return 42
}

function relationLabel(link) {
  return link?.label || link?.relation || ''
}

function endpointId(endpoint) {
  return typeof endpoint === 'object' ? endpoint?.id : endpoint
}

function shouldShowLinkLabel(link) {
  if (props.focusedNodeId) {
    const neighborIds = getFocusedNeighborIds()
    const sourceId = endpointId(link.source)
    const targetId = endpointId(link.target)
    return neighborIds.has(sourceId) && neighborIds.has(targetId)
  }
  return false
}

function isFocusedLink(link) {
  if (!props.focusedNodeId) return false
  const sourceId = endpointId(link.source)
  const targetId = endpointId(link.target)
  return sourceId === props.focusedNodeId || targetId === props.focusedNodeId
}

function buildLinkLabelObject(link) {
  if (!shouldShowLinkLabel(link)) return null
  const text = relationLabel(link)
  if (!text) return null

  const canvas = document.createElement('canvas')
  const context = canvas.getContext('2d')
  const fontSize = 36
  context.font = `700 ${fontSize}px "Source Han Sans SC", Arial, sans-serif`
  const width = Math.ceil(context.measureText(text).width + 32)
  canvas.width = Math.max(80, width)
  canvas.height = 56
  context.font = `700 ${fontSize}px "Source Han Sans SC", Arial, sans-serif`
  context.textAlign = 'center'
  context.textBaseline = 'middle'
  context.fillStyle = props.darkMode ? 'rgba(8, 20, 35, 0.88)' : 'rgba(248, 250, 252, 0.92)'
  context.strokeStyle = props.darkMode ? 'rgba(125, 211, 252, 0.55)' : 'rgba(15, 118, 110, 0.4)'
  context.lineWidth = 2.5
  roundRect(context, 1, 1, canvas.width - 2, canvas.height - 2, 16)
  context.fill()
  context.stroke()
  context.fillStyle = props.darkMode ? '#f8fafc' : '#12303b'
  context.fillText(text, canvas.width / 2, canvas.height / 2 + 2)

  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false })
  const sprite = new THREE.Sprite(material)
  sprite.scale.set(canvas.width * 0.22, canvas.height * 0.22, 1)
  return sprite
}

function roundRect(context, x, y, width, height, radius) {
  context.beginPath()
  context.moveTo(x + radius, y)
  context.lineTo(x + width - radius, y)
  context.quadraticCurveTo(x + width, y, x + width, y + radius)
  context.lineTo(x + width, y + height - radius)
  context.quadraticCurveTo(x + width, y + height, x + width - radius, y + height)
  context.lineTo(x + radius, y + height)
  context.quadraticCurveTo(x, y + height, x, y + height - radius)
  context.lineTo(x, y + radius)
  context.quadraticCurveTo(x, y, x + radius, y)
  context.closePath()
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
    node.__sphereMaterial = new THREE.MeshStandardMaterial({
      color: node.color,
      roughness: 0.38,
      metalness: 0.12,
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

  const isFocused = props.focusedNodeId && node.id === props.focusedNodeId
  if (isFocused) {
    if (!node.__glowRing) {
      const ringGeometry = new THREE.TorusGeometry(radius * 1.6, radius * 0.3, 12, 40)
      node.__glowRingMaterial = new THREE.MeshStandardMaterial({
        color: '#ffffff',
        roughness: 0.15,
        metalness: 0.5,
        emissive: '#aaddff',
        emissiveIntensity: 0.8,
        transparent: true,
        opacity: 0.75,
        depthWrite: false
      })
      node.__glowRing = new THREE.Mesh(ringGeometry, node.__glowRingMaterial)
      node.__glowRing.renderOrder = 999
      node.__glowRing.material.depthTest = true
      node.__glowRing.material.depthWrite = false
      node.__group.add(node.__glowRing)
    }
    node.__glowRing.visible = true
    node.__glowRing.scale.set(1, 1, 1)
  } else if (node.__glowRing) {
    node.__glowRing.visible = false
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
  if (raw.genusCn || raw.genus) lines.push(`<div style="opacity:.7;">属：${raw.genusCn || raw.genus}</div>`)
  if (raw.type === 'taxonomy' && raw.taxonomyLevel) {
    lines.push(`<div style="opacity:.7;">分类层级：${TAXONOMY_LABELS[raw.taxonomyLevel] || raw.taxonomyLevel}</div>`)
  }

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
    nextNode.color = nodeColor(rawNode)
    nextNode.opacity = rawNode.id === props.centerNodeId ? 1 : 0.88
    nextNode.distance = 0
    nextNode.homeX = home.x
    nextNode.homeY = home.y
    nextNode.homeZ = home.z

    if (props.focusedNodeId && rawNode.id === props.focusedNodeId) {
      nextNode.color = '#ffffff'
      nextNode.opacity = 1
    }

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
      label: link.label,
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
    .linkOpacity(link => (props.focusedNodeId ? (isFocusedLink(link) ? 0.9 : 0.12) : 0.48))
    .linkWidth(link => (isFocusedLink(link) ? 2.8 : (shouldShowLinkLabel(link) ? 1.15 : 0.56)))
    .linkColor(link => (isFocusedLink(link) ? FOCUSED_LINK_COLOR : (props.darkMode ? LINK_COLOR_DARK : LINK_COLOR_LIGHT)))
    .linkDirectionalParticles(link => (isFocusedLink(link) ? 1 : 0))
    .linkDirectionalParticleWidth(link => (isFocusedLink(link) ? 2.6 : 0))
    .linkDirectionalParticleSpeed(0.004)
    .linkLabel(link => relationLabel(link))
    .linkHoverPrecision(6)
    .linkThreeObject(link => buildLinkLabelObject(link))
    .linkThreeObjectExtend(true)
    .linkPositionUpdate((sprite, { start, end }, link) => {
      if (!sprite || !start || !end) return
      const midX = (start.x + end.x) / 2
      const midY = (start.y + end.y) / 2
      const midZ = (start.z + end.z) / 2
      Object.assign(sprite.position, { x: midX, y: midY, z: midZ })
    })
    .nodeLabel(buildTooltip)
    .nodeThreeObject(node => buildNodeObject(node))
    .onNodeClick(node => {
      if (!node?.rawNode) return
      const isCenter = node.id === props.centerNodeId
      emit('node-click', node.rawNode, isCenter)
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
    if (link.relation?.startsWith('belongs_to_')) return 0.16
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

  const scene = graph.scene()
  scene.add(new THREE.AmbientLight('#8899bb', 0.52))
  const keyLight = new THREE.DirectionalLight('#ffffff', 0.72)
  keyLight.position.set(0, 0, 1800)
  scene.add(keyLight)
  const fillLight = new THREE.DirectionalLight('#8899cc', 0.36)
  fillLight.position.set(800, -400, -600)
  scene.add(fillLight)
  const rimLight = new THREE.DirectionalLight('#aaccff', 0.28)
  rimLight.position.set(-600, 200, 400)
  scene.add(rimLight)

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

  const zoomDistance = props.focusedNodeId ? 120 : 210

  graph.cameraPosition(
    {
      x: targetX,
      y: targetY,
      z: targetZ + zoomDistance
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
    props.darkMode,
    props.centerNodeId,
    props.focusedNodeId,
    props.activeTaxonomyLevels.join('|')
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

watch(() => props.focusedNodeId, (newId) => {
  if (!graph || !newId) return
  focusNode(newId)
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

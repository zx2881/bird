<template>
  <div ref="stageRef" class="migration-globe">
    <div
      v-if="hoveredNode"
      class="globe-tooltip"
      :style="hoverLabelStyle"
    >
      <span>{{ getNodeTypeLabel(hoveredNode) }}</span>
      <strong>{{ hoveredNode.name || hoveredNode.id }}</strong>
      <small>{{ getNodeMetaLabel(hoveredNode) }}</small>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { useGraphStore } from '../stores/graphStore.js'

const props = defineProps({
  centerNodeId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['node-click'])

const store = useGraphStore()
const stageRef = ref(null)
const hoveredNode = ref(null)
const hoverLabelStyle = ref({})

let scene = null
let camera = null
let renderer = null
let globeGroup = null
let nodeGroup = null
let arcGroup = null
let ambientLight = null
let resizeObserver = null
let animationFrame = 0
let raycaster = null
let pointer = null
let dragged = false

const dragState = {
  active: false,
  x: 0,
  y: 0,
  rotationX: 0,
  rotationY: 0
}

const globeRadius = 190
const maxNodes = 1500
const maxRoutes = 320
const maxBirdNodes = 960
const maxLocationNodes = 160
const maxLocationsPerBird = 4
const birdPointRadius = 2.45
const locationPointRadius = 1.32
const activePointRadius = 3.05
const arcSurfaceOffset = 0.36
const earthTextureUrl = `${import.meta.env.BASE_URL}textures/earth-blue-marble-5400.jpg`
const interactivePoints = []

const locationIndex = computed(() => {
  const indexed = new Map()
  const addLocation = location => {
    if (!location?.name || location.lat == null || location.lng == null) return
    const normalized = {
      ...location,
      id: location.id || `loc-${location.name}`,
      type: 'location',
      lat: Number(location.lat),
      lng: Number(location.lng)
    }
    if (!Number.isFinite(normalized.lat) || !Number.isFinite(normalized.lng)) return
    indexed.set(normalized.name, normalized)
  }

  store.summaryLocations.forEach(addLocation)
  store.locationNodes.forEach(addLocation)
  return indexed
})

const birdGeoNodes = computed(() => {
  return store.birdNodes
    .filter(node => node.lat != null && node.lng != null)
    .slice()
    .sort((left, right) => {
      return String(left.name || left.id).localeCompare(String(right.name || right.id), 'zh-Hans-CN')
    })
    .slice(0, maxBirdNodes)
})

const locationGeoNodes = computed(() => {
  return Array.from(locationIndex.value.values())
    .sort((left, right) => String(left.name || left.id).localeCompare(String(right.name || right.id), 'zh-Hans-CN'))
    .slice(0, maxLocationNodes)
})

const habitatRoutes = computed(() => {
  const routes = []
  const used = new Set()
  for (const bird of birdGeoNodes.value) {
    const locationNames = Array.isArray(bird.locations) ? bird.locations : []
    for (const locationName of locationNames.slice(0, maxLocationsPerBird)) {
      const location = locationIndex.value.get(locationName)
      if (!location) continue
      const key = `${bird.id}__${location.id}`
      if (used.has(key)) continue
      used.add(key)
      routes.push({ source: bird, target: location })
      if (routes.length >= maxRoutes) return routes
    }
  }
  return routes
})

const geospatialNodes = computed(() => {
  const nodesById = new Map()
  for (const bird of birdGeoNodes.value) nodesById.set(bird.id, bird)
  for (const route of habitatRoutes.value) {
    if (nodesById.size >= maxNodes && !nodesById.has(route.target.id)) continue
    nodesById.set(route.target.id, route.target)
  }
  for (const location of locationGeoNodes.value) {
    if (nodesById.size >= maxNodes && !nodesById.has(location.id)) continue
    nodesById.set(location.id, location)
  }
  return Array.from(nodesById.values())
})

function latLngToVector(lat, lng, radius = globeRadius) {
  const phi = (90 - lat) * Math.PI / 180
  const theta = (lng + 180) * Math.PI / 180
  const x = -radius * Math.sin(phi) * Math.cos(theta)
  const z = radius * Math.sin(phi) * Math.sin(theta)
  const y = radius * Math.cos(phi)
  return new THREE.Vector3(x, y, z)
}

function getNodeTypeLabel(node) {
  return node?.type === 'location' ? '地点节点' : '鸟类观测点'
}

function getNodeMetaLabel(node) {
  if (!node) return ''
  if (node.type === 'location') return `${Number(node.lat).toFixed(2)}, ${Number(node.lng).toFixed(2)}`
  return [node.englishName, node.latinName].filter(Boolean).join(' · ') || `${Number(node.lat).toFixed(2)}, ${Number(node.lng).toFixed(2)}`
}

function makeGlowTexture() {
  const canvas = document.createElement('canvas')
  canvas.width = 128
  canvas.height = 128
  const context = canvas.getContext('2d')
  const gradient = context.createRadialGradient(64, 64, 0, 64, 64, 64)
  gradient.addColorStop(0, 'rgba(140, 255, 232, 1)')
  gradient.addColorStop(0.2, 'rgba(34, 211, 238, .82)')
  gradient.addColorStop(0.58, 'rgba(45, 212, 191, .28)')
  gradient.addColorStop(1, 'rgba(45, 212, 191, 0)')
  context.fillStyle = gradient
  context.fillRect(0, 0, 128, 128)
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  return texture
}

function makeEarthTexture() {
  const texture = new THREE.TextureLoader().load(
    earthTextureUrl,
    () => {
      if (renderer && scene && camera) renderer.render(scene, camera)
    },
    undefined,
    error => {
      console.warn('Failed to load earth texture', error)
    }
  )
  texture.colorSpace = THREE.SRGBColorSpace
  texture.anisotropy = renderer?.capabilities?.getMaxAnisotropy?.() || 8
  return texture
}

function disposeObject(object) {
  if (!object) return
  object.traverse(child => {
    child.geometry?.dispose?.()
    if (Array.isArray(child.material)) {
      child.material.forEach(material => material.dispose?.())
    } else {
      child.material?.dispose?.()
    }
  })
}

function clearGroup(group) {
  if (!group) return
  while (group.children.length) {
    const child = group.children.pop()
    disposeObject(child)
  }
}

function createGlobe() {
  const sphereGeometry = new THREE.SphereGeometry(globeRadius, 128, 128)
  const sphereMaterial = new THREE.MeshPhongMaterial({
    color: '#a7d8c8',
    map: makeEarthTexture(),
    emissive: '#092b2a',
    emissiveIntensity: 0.11,
    specular: '#155c55',
    shininess: 6
  })
  const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial)
  globeGroup.add(sphere)

  const atmosphereGeometry = new THREE.SphereGeometry(globeRadius * 1.035, 96, 96)
  const atmosphereMaterial = new THREE.MeshBasicMaterial({
    color: '#1de9d1',
    transparent: true,
    opacity: 0.022,
    blending: THREE.AdditiveBlending,
    side: THREE.BackSide
  })
  globeGroup.add(new THREE.Mesh(atmosphereGeometry, atmosphereMaterial))

  const gridMaterial = new THREE.LineBasicMaterial({
    color: '#2dd4bf',
    transparent: true,
    opacity: 0.16,
    blending: THREE.AdditiveBlending
  })

  for (let lat = -60; lat <= 60; lat += 30) {
    const points = []
    for (let lng = -180; lng <= 180; lng += 4) points.push(latLngToVector(lat, lng, globeRadius * 1.006))
    globeGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), gridMaterial.clone()))
  }

  for (let lng = -150; lng <= 180; lng += 30) {
    const points = []
    for (let lat = -86; lat <= 86; lat += 3) points.push(latLngToVector(lat, lng, globeRadius * 1.007))
    globeGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), gridMaterial.clone()))
  }
}

function buildRoutes(nodes) {
  const visibleNodeIds = new Set(nodes.map(node => node.id))
  return habitatRoutes.value
    .filter(route => visibleNodeIds.has(route.source.id) && visibleNodeIds.has(route.target.id))
    .filter(route => {
      const latDelta = Math.abs(Number(route.source.lat) - Number(route.target.lat))
      const lngDelta = Math.abs(Number(route.source.lng) - Number(route.target.lng))
      return latDelta + lngDelta > 2
    })
    .slice(0, maxRoutes)
}

function createArcCurve(source, target) {
  const start = latLngToVector(source.lat, source.lng, globeRadius + arcSurfaceOffset)
  const end = latLngToVector(target.lat, target.lng, globeRadius + arcSurfaceOffset)
  const mid = start.clone().add(end)
  if (mid.lengthSq() < 0.001) mid.crossVectors(start, new THREE.Vector3(0, 1, 0))
  mid.normalize()
  const distance = start.distanceTo(end)
  const lift = Math.min(58, Math.max(18, distance * 0.14))
  const control = mid.multiplyScalar(globeRadius + lift)
  return new THREE.QuadraticBezierCurve3(start, control, end)
}

function rebuildDataObjects() {
  if (!nodeGroup || !arcGroup) return
  clearGroup(nodeGroup)
  clearGroup(arcGroup)
  interactivePoints.length = 0

  const glowTexture = makeGlowTexture()
  const nodeById = new Map(geospatialNodes.value.map(node => [node.id, node]))
  const birdPointGeometry = new THREE.SphereGeometry(birdPointRadius, 14, 14)
  const locationPointGeometry = new THREE.SphereGeometry(locationPointRadius, 10, 10)
  const activePointGeometry = new THREE.SphereGeometry(activePointRadius, 16, 16)

  for (const node of geospatialNodes.value) {
    const isActive = node.id === props.centerNodeId
    const nodePointRadius = node.type === 'location' ? locationPointRadius : birdPointRadius
    const surfaceOffset = (isActive ? activePointRadius : nodePointRadius) * 0.5
    const position = latLngToVector(node.lat, node.lng, globeRadius + surfaceOffset)
    const material = new THREE.MeshBasicMaterial({
      color: isActive ? '#d9fff8' : (node.type === 'location' ? '#7cff6b' : '#22d3ee'),
      transparent: true,
      opacity: isActive ? 1 : (node.type === 'location' ? 0.82 : 0.98),
      depthTest: true,
      depthWrite: false
    })
    const mesh = new THREE.Mesh(isActive ? activePointGeometry : (node.type === 'location' ? locationPointGeometry : birdPointGeometry), material)
    mesh.position.copy(position)
    mesh.userData.node = node
    mesh.renderOrder = 20
    nodeGroup.add(mesh)
    interactivePoints.push({ mesh, node })

    const spriteMaterial = new THREE.SpriteMaterial({
      map: glowTexture,
      color: node.type === 'location' ? '#a3ff6f' : '#5eead4',
      transparent: true,
      opacity: isActive ? 0.34 : 0.13,
      blending: THREE.AdditiveBlending,
      depthTest: true,
      depthWrite: false
    })
    const sprite = new THREE.Sprite(spriteMaterial)
    sprite.position.copy(latLngToVector(node.lat, node.lng, globeRadius + surfaceOffset + 0.08))
    const scale = isActive ? 7.2 : (node.type === 'location' ? 2.6 : 5.2)
    sprite.scale.set(scale, scale, 1)
    sprite.renderOrder = 19
    nodeGroup.add(sprite)
  }

  const routes = buildRoutes(geospatialNodes.value)
  const arcMaterial = new THREE.MeshBasicMaterial({
    color: '#7cff6b',
    transparent: true,
    opacity: 0.74,
    blending: THREE.AdditiveBlending,
    depthTest: true,
    depthWrite: false
  })
  const arcLineMaterial = new THREE.LineBasicMaterial({
    color: '#d9fff8',
    transparent: true,
    opacity: 0.62,
    blending: THREE.AdditiveBlending,
    depthTest: true,
    depthWrite: false
  })

  routes.forEach(route => {
    const source = nodeById.get(route.source.id) || route.source
    const target = nodeById.get(route.target.id) || route.target
    if (!source || !target || source.lat == null || target.lat == null) return
    const curve = createArcCurve(source, target)
    const points = curve.getPoints(52)
    const tube = new THREE.Mesh(
      new THREE.TubeGeometry(curve, 64, 0.72, 8, false),
      arcMaterial.clone()
    )
    tube.material.opacity = 0.68
    tube.renderOrder = 12
    arcGroup.add(tube)

    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), arcLineMaterial.clone())
    line.material.opacity = 0.68
    line.renderOrder = 13
    arcGroup.add(line)
  })
}

function resizeRenderer() {
  if (!stageRef.value || !renderer || !camera) return
  const { clientWidth, clientHeight } = stageRef.value
  renderer.setSize(clientWidth, clientHeight, false)
  const aspect = clientWidth / Math.max(1, clientHeight)
  const viewSize = 660
  camera.left = -viewSize * aspect / 2
  camera.right = viewSize * aspect / 2
  camera.top = viewSize / 2
  camera.bottom = -viewSize / 2
  camera.updateProjectionMatrix()
}

function onPointerDown(event) {
  dragState.active = true
  dragged = false
  dragState.x = event.clientX
  dragState.y = event.clientY
  dragState.rotationX = globeGroup.rotation.x
  dragState.rotationY = globeGroup.rotation.y
  stageRef.value?.setPointerCapture?.(event.pointerId)
}

function onPointerMove(event) {
  if (dragState.active && globeGroup) {
    const dx = event.clientX - dragState.x
    const dy = event.clientY - dragState.y
    if (Math.abs(dx) + Math.abs(dy) > 4) dragged = true
    globeGroup.rotation.y = dragState.rotationY + dx * 0.006
    globeGroup.rotation.x = Math.max(-0.85, Math.min(0.85, dragState.rotationX + dy * 0.004))
    hoveredNode.value = null
    return
  }

  updateHover(event)
}

function onPointerUp(event) {
  dragState.active = false
  stageRef.value?.releasePointerCapture?.(event.pointerId)
}

function isMeshFacingCamera(mesh) {
  if (!mesh || !camera || !globeGroup) return false
  const nodePosition = new THREE.Vector3()
  const globePosition = new THREE.Vector3()
  const cameraPosition = new THREE.Vector3()
  mesh.getWorldPosition(nodePosition)
  globeGroup.getWorldPosition(globePosition)
  camera.getWorldPosition(cameraPosition)
  const surfaceNormal = nodePosition.sub(globePosition).normalize()
  const cameraDirection = cameraPosition.sub(globePosition).normalize()
  return surfaceNormal.dot(cameraDirection) > 0.05
}

function getPointerHit(event) {
  if (!camera || !stageRef.value) return null
  const rect = stageRef.value.getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const mouseY = event.clientY - rect.top
  const projected = new THREE.Vector3()
  let best = null

  camera.updateMatrixWorld()
  globeGroup?.updateMatrixWorld(true)

  for (const point of interactivePoints) {
    if (!isMeshFacingCamera(point.mesh)) continue
    point.mesh.getWorldPosition(projected)
    projected.project(camera)
    if (projected.z < -1 || projected.z > 1) continue
    const screenX = (projected.x + 1) * rect.width / 2
    const screenY = (-projected.y + 1) * rect.height / 2
    const distance = Math.hypot(mouseX - screenX, mouseY - screenY)
    const threshold = point.node.type === 'location' ? 11 : 18
    if (distance > threshold) continue
    const score = distance + (point.node.type === 'location' ? 2 : 0)
    if (!best || score < best.score) best = { ...point, score, screenX, screenY }
  }

  return best
}

function updateHover(event) {
  const hit = getPointerHit(event)
  hoveredNode.value = hit?.object?.userData?.node || null
  if (!stageRef.value || !hoveredNode.value) {
    hoverLabelStyle.value = {}
    return
  }
  const rect = stageRef.value.getBoundingClientRect()
  hoverLabelStyle.value = {
    left: `${Math.min(rect.width - 220, Math.max(12, hit.screenX + 14))}px`,
    top: `${Math.min(rect.height - 96, Math.max(12, hit.screenY - 16))}px`
  }
}

function onPointerLeave() {
  hoveredNode.value = null
  hoverLabelStyle.value = {}
}

function onClick(event) {
  if (dragged) return
  const hit = getPointerHit(event)
  if (hit?.node) emit('node-click', hit.node, hit.node.id === props.centerNodeId)
}

function onWheel(event) {
  if (!camera) return
  event.preventDefault()
  const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1
  camera.zoom = Math.max(0.7, Math.min(2.8, camera.zoom * zoomFactor))
  camera.updateProjectionMatrix()
}

function animate() {
  if (!renderer || !scene || !camera || !globeGroup) return
  renderer.render(scene, camera)
  animationFrame = window.requestAnimationFrame(animate)
}

function initScene() {
  if (!stageRef.value || renderer) return
  scene = new THREE.Scene()
  camera = new THREE.OrthographicCamera(-300, 300, 220, -220, 0.1, 1800)
  camera.position.set(0, 0, 620)
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  stageRef.value.appendChild(renderer.domElement)

  globeGroup = new THREE.Group()
  globeGroup.rotation.set(-0.18, -0.62, 0)
  globeGroup.position.set(-70, 104, 0)
  nodeGroup = new THREE.Group()
  arcGroup = new THREE.Group()
  globeGroup.add(arcGroup, nodeGroup)
  scene.add(globeGroup)

  ambientLight = new THREE.AmbientLight('#9ee8dc', 0.88)
  scene.add(ambientLight)
  const light = new THREE.DirectionalLight('#eafff8', 0.78)
  light.position.set(-200, 180, 420)
  scene.add(light)

  raycaster = new THREE.Raycaster()
  pointer = new THREE.Vector2()
  createGlobe()
  resizeRenderer()
  rebuildDataObjects()

  stageRef.value.addEventListener('pointerdown', onPointerDown)
  stageRef.value.addEventListener('pointermove', onPointerMove)
  stageRef.value.addEventListener('pointerup', onPointerUp)
  stageRef.value.addEventListener('pointercancel', onPointerUp)
  stageRef.value.addEventListener('pointerleave', onPointerLeave)
  stageRef.value.addEventListener('click', onClick)
  stageRef.value.addEventListener('wheel', onWheel, { passive: false })
  resizeObserver = new ResizeObserver(resizeRenderer)
  resizeObserver.observe(stageRef.value)
  animate()
}

watch(
  () => [store.lastMutation?.serial, store.nodeCount, store.linkCount, props.centerNodeId],
  () => nextTick(rebuildDataObjects)
)

onMounted(() => {
  nextTick(initScene)
})

onBeforeUnmount(() => {
  if (animationFrame) window.cancelAnimationFrame(animationFrame)
  resizeObserver?.disconnect()
  if (stageRef.value) {
    stageRef.value.removeEventListener('pointerdown', onPointerDown)
    stageRef.value.removeEventListener('pointermove', onPointerMove)
    stageRef.value.removeEventListener('pointerup', onPointerUp)
    stageRef.value.removeEventListener('pointercancel', onPointerUp)
    stageRef.value.removeEventListener('pointerleave', onPointerLeave)
    stageRef.value.removeEventListener('click', onClick)
    stageRef.value.removeEventListener('wheel', onWheel)
  }
  disposeObject(scene)
  renderer?.dispose()
})
</script>

<style scoped>
.migration-globe {
  position: absolute;
  inset: 0;
  cursor: grab;
  background:
    radial-gradient(circle at 62% 45%, rgba(34, 211, 238, 0.1), transparent 32%),
    radial-gradient(circle at 48% 50%, rgba(20, 184, 166, 0.06), transparent 40%),
    linear-gradient(135deg, #020617 0%, #07111f 46%, #02040a 100%);
}

.migration-globe:active {
  cursor: grabbing;
}

.migration-globe canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.globe-tooltip {
  position: absolute;
  z-index: 4;
  min-width: 172px;
  max-width: 220px;
  padding: 10px 12px;
  border: 1px solid rgba(124, 255, 107, 0.34);
  border-radius: 8px;
  background: rgba(2, 8, 23, 0.86);
  box-shadow: 0 0 22px rgba(34, 211, 238, 0.18), inset 0 0 16px rgba(124, 255, 107, 0.06);
  color: #d9fff8;
  pointer-events: none;
  transform: translateY(-100%);
  backdrop-filter: blur(10px);
}

.globe-tooltip span,
.globe-tooltip small {
  display: block;
  color: rgba(217, 255, 248, 0.62);
  font-size: 11px;
  line-height: 1.45;
}

.globe-tooltip strong {
  display: block;
  margin: 2px 0;
  color: #7cff6b;
  font-size: 14px;
  line-height: 1.35;
  text-shadow: 0 0 12px rgba(124, 255, 107, 0.34);
}
</style>

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

function uniqueStrings(values) {
  return Array.from(new Set((values || []).filter(Boolean)))
}

function toNumber(value) {
  if (value == null || value === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function makeAssetUrl(path) {
  const base = import.meta.env.DEV ? '' : import.meta.env.BASE_URL
  return `${base}${path}`
}

const COUNTRY_LOCATION_NAMES = new Set([
  '中国', '中华人民共和国', '日本', '韩国', '朝鲜', '蒙古', '俄罗斯', '俄羅斯', '印度', '尼泊尔', '不丹',
  '缅甸', '越南', '老挝', '泰国', '柬埔寨', '菲律宾', '印度尼西亚', '马来西亚', '新加坡',
  '澳大利亚', '新西兰', '美国', '加拿大', '墨西哥', '巴西', '阿根廷', '智利', '秘鲁',
  '南非', '肯尼亚', '坦桑尼亚', '埃塞俄比亚', '英国', '法国', '德国', '意大利', '西班牙',
  '葡萄牙', '荷兰', '波兰', '挪威', '瑞典', '芬兰', '丹麦',
  'china', 'japan', 'south korea', 'north korea', 'mongolia', 'russia', 'india', 'nepal', 'bhutan',
  'myanmar', 'vietnam', 'laos', 'thailand', 'cambodia', 'philippines', 'indonesia', 'malaysia',
  'singapore', 'australia', 'new zealand', 'united states', 'united states of america', 'canada',
  'mexico', 'brazil', 'argentina', 'chile', 'peru', 'south africa', 'kenya', 'tanzania', 'ethiopia',
  'united kingdom', 'france', 'germany', 'italy', 'spain', 'portugal', 'netherlands', 'poland',
  'norway', 'sweden', 'finland', 'denmark'
])

function isCountryLocation(node) {
  return node?.type === 'location' && COUNTRY_LOCATION_NAMES.has(String(node.name || '').trim().toLowerCase())
}

function normalizeNode(node) {
  const normalized = {
    ...node,
    type: node.type || 'bird',
    englishName: node.englishName || '',
    latinName: node.latinName || '',
    summary: node.summary || '',
    shortSummary: node.shortSummary || '',
    imageUrl: node.imageUrl || '',
    status: node.status || '',
    kingdom: node.kingdom || '',
    phylum: node.phylum || '',
    class: node.class || '',
    order: node.order || '',
    family: node.family || '',
    genus: node.genus || '',
    species: node.species || '',
    kingdomCn: node.kingdomCn || '',
    phylumCn: node.phylumCn || '',
    classCn: node.classCn || '',
    orderCn: node.orderCn || '',
    familyCn: node.familyCn || '',
    genusCn: node.genusCn || '',
    speciesCn: node.speciesCn || '',
    kingdomId: node.kingdomId || '',
    phylumId: node.phylumId || '',
    classId: node.classId || '',
    orderId: node.orderId || '',
    familyId: node.familyId || '',
    genusId: node.genusId || '',
    speciesId: node.speciesId || '',
    taxonomyIds: node.taxonomyIds || {},
    taxonomyLevel: node.taxonomyLevel || '',
    locations: uniqueStrings(node.locations),
    habitats: uniqueStrings(node.habitats),
    threats: uniqueStrings(node.threats),
    expandable: node.expandable ?? (node.type === 'bird' || node.type === 'taxonomy'),
    x: toNumber(node.x),
    y: toNumber(node.y),
    z: toNumber(node.z),
    homeX: toNumber(node.homeX ?? node.x),
    homeY: toNumber(node.homeY ?? node.y),
    homeZ: toNumber(node.homeZ ?? node.z),
    lat: toNumber(node.lat),
    lng: toNumber(node.lng)
  }
  return normalized
}

function mergeNodeData(existing, incoming) {
  const merged = {
    ...existing,
    ...incoming,
    locations: uniqueStrings([...(existing.locations || []), ...(incoming.locations || [])]),
    habitats: uniqueStrings([...(existing.habitats || []), ...(incoming.habitats || [])]),
    threats: uniqueStrings([...(existing.threats || []), ...(incoming.threats || [])]),
    expandable: Boolean(existing.expandable || incoming.expandable)
  }

  if (!incoming.summary && existing.summary) merged.summary = existing.summary
  if (!incoming.shortSummary && existing.shortSummary) merged.shortSummary = existing.shortSummary
  if (!incoming.englishName && existing.englishName) merged.englishName = existing.englishName
  if (!incoming.latinName && existing.latinName) merged.latinName = existing.latinName
  if (!incoming.imageUrl && existing.imageUrl) merged.imageUrl = existing.imageUrl
  if (!incoming.status && existing.status) merged.status = existing.status
  if (!incoming.kingdom && existing.kingdom) merged.kingdom = existing.kingdom
  if (!incoming.phylum && existing.phylum) merged.phylum = existing.phylum
  if (!incoming.class && existing.class) merged.class = existing.class
  if (!incoming.order && existing.order) merged.order = existing.order
  if (!incoming.family && existing.family) merged.family = existing.family
  if (!incoming.genus && existing.genus) merged.genus = existing.genus
  if (!incoming.species && existing.species) merged.species = existing.species
  if (!incoming.kingdomCn && existing.kingdomCn) merged.kingdomCn = existing.kingdomCn
  if (!incoming.phylumCn && existing.phylumCn) merged.phylumCn = existing.phylumCn
  if (!incoming.classCn && existing.classCn) merged.classCn = existing.classCn
  if (!incoming.orderCn && existing.orderCn) merged.orderCn = existing.orderCn
  if (!incoming.familyCn && existing.familyCn) merged.familyCn = existing.familyCn
  if (!incoming.genusCn && existing.genusCn) merged.genusCn = existing.genusCn
  if (!incoming.speciesCn && existing.speciesCn) merged.speciesCn = existing.speciesCn
  if (!incoming.kingdomId && existing.kingdomId) merged.kingdomId = existing.kingdomId
  if (!incoming.phylumId && existing.phylumId) merged.phylumId = existing.phylumId
  if (!incoming.classId && existing.classId) merged.classId = existing.classId
  if (!incoming.orderId && existing.orderId) merged.orderId = existing.orderId
  if (!incoming.familyId && existing.familyId) merged.familyId = existing.familyId
  if (!incoming.genusId && existing.genusId) merged.genusId = existing.genusId
  if (!incoming.speciesId && existing.speciesId) merged.speciesId = existing.speciesId
  if (!Object.keys(incoming.taxonomyIds || {}).length && Object.keys(existing.taxonomyIds || {}).length) {
    merged.taxonomyIds = existing.taxonomyIds
  }
  if (!incoming.taxonomyLevel && existing.taxonomyLevel) merged.taxonomyLevel = existing.taxonomyLevel
  if (incoming.x == null && existing.x != null) merged.x = existing.x
  if (incoming.y == null && existing.y != null) merged.y = existing.y
  if (incoming.z == null && existing.z != null) merged.z = existing.z
  if (incoming.homeX == null && existing.homeX != null) merged.homeX = existing.homeX
  if (incoming.homeY == null && existing.homeY != null) merged.homeY = existing.homeY
  if (incoming.homeZ == null && existing.homeZ != null) merged.homeZ = existing.homeZ
  if (incoming.lat == null && existing.lat != null) merged.lat = existing.lat
  if (incoming.lng == null && existing.lng != null) merged.lng = existing.lng

  return merged
}

function normalizeLink(link) {
  const key = link.key || `${link.source}__${link.relation}__${link.target}`
  return {
    key,
    source: link.source,
    target: link.target,
    relation: link.relation,
    label: link.label || link.relation,
    evidence: link.evidence || ''
  }
}

function inflateSummaryItems(summary) {
  const columns = summary.columns || []
  const indexByKey = Object.fromEntries(columns.map((key, index) => [key, index]))
  return (summary.items || []).map(item => {
    const bird = {
      id: item[indexByKey.id],
      name: item[indexByKey.name],
      englishName: item[indexByKey.englishName] || '',
      latinName: item[indexByKey.latinName] || '',
      type: 'bird',
      expandable: true
    }
    bird.searchText = [bird.name, bird.englishName, bird.latinName].filter(Boolean).join(' ').toLowerCase()
    return bird
  })
}

const PREVIEW_TAXONOMY_LEVELS = new Set(['kingdom', 'phylum', 'class', 'order', 'family'])

function trimGraphPreviewPayload(payload) {
  const keepNodeIds = new Set()
  const nodes = (payload.nodes || []).filter(node => {
    const keep = node.type !== 'taxonomy' || PREVIEW_TAXONOMY_LEVELS.has(node.taxonomyLevel)
    if (keep) keepNodeIds.add(node.id)
    return keep
  })

  return {
    ...payload,
    nodes,
    links: (payload.links || []).filter(link => keepNodeIds.has(link.source) && keepNodeIds.has(link.target))
  }
}

export const useGraphStore = defineStore('graph', () => {
  const meta = ref(null)
  const nodes = ref([])
  const links = ref([])
  const loading = ref(false)
  const loaded = ref(false)
  const summaryLoaded = ref(false)
  const skeletonLoaded = ref(false)

  const summaryBirds = ref([])
  const nodeMap = ref(new Map())
  const summaryMap = ref(new Map())
  const linkMap = ref(new Map())
  const linksByNode = ref(new Map())
  const degreeMap = ref(new Map())

  const loadedChunkIds = ref(new Set())
  const pendingChunkIds = ref(new Set())
  const lastMutation = ref(null)
  const activeNodeId = ref('')
  const focusRequest = ref({ id: '', nonce: 0 })
  const fitRequest = ref({ nonce: 0 })
  const previewLoading = ref(false)
  const previewLoaded = ref(false)
  const previewLoadProgress = ref({ loaded: 0, total: 0, failed: 0 })

  let initialPromise = null
  let previewPromise = null
  const chunkPromises = new Map()
  let mutationSerial = 0

  const birdNodes = computed(() => nodes.value.filter(node => node.type === 'bird'))
  const locationNodes = computed(() => nodes.value.filter(node => node.type === 'location'))
  const habitatNodes = computed(() => nodes.value.filter(node => node.type === 'habitat'))
  const taxonomyNodes = computed(() => nodes.value.filter(node => node.type === 'taxonomy'))
  const nodeCount = computed(() => nodes.value.length)
  const linkCount = computed(() => links.value.length)
  const totalBirdCount = computed(() => summaryBirds.value.length)
  const loadedBirdCount = computed(() => birdNodes.value.length)
  const loadedChunkCount = computed(() => loadedChunkIds.value.size)

  function hasLoadedChunk(nodeId) {
    return loadedChunkIds.value.has(nodeId)
  }

  function isChunkPending(nodeId) {
    return pendingChunkIds.value.has(nodeId)
  }

  function addSetValue(setRef, value) {
    if (setRef.value.has(value)) return
    const next = new Set(setRef.value)
    next.add(value)
    setRef.value = next
  }

  function addSetValues(setRef, values) {
    const next = new Set(setRef.value)
    let changed = false
    for (const value of values || []) {
      if (next.has(value)) continue
      next.add(value)
      changed = true
    }
    if (changed) setRef.value = next
  }

  function removeSetValue(setRef, value) {
    if (!setRef.value.has(value)) return
    const next = new Set(setRef.value)
    next.delete(value)
    setRef.value = next
  }

  function ensureNodeBuckets(nodeId) {
    if (!linksByNode.value.has(nodeId)) linksByNode.value.set(nodeId, [])
    if (!degreeMap.value.has(nodeId)) degreeMap.value.set(nodeId, 0)
  }

  function syncReactiveCollections() {
    nodes.value = Array.from(nodeMap.value.values())
    links.value = Array.from(linkMap.value.values())
  }

  async function fetchJson(path) {
    const response = await fetch(makeAssetUrl(path))
    if (!response.ok) {
      throw new Error(`Failed to load ${path}: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }

  function rebuildIndexes() {
    const nextLinksByNode = new Map()
    const nextDegreeMap = new Map()

    nodeMap.value.forEach((_, nodeId) => {
      nextLinksByNode.set(nodeId, [])
      nextDegreeMap.set(nodeId, 0)
    })

    linkMap.value.forEach(link => {
      if (!nextLinksByNode.has(link.source)) nextLinksByNode.set(link.source, [])
      if (!nextLinksByNode.has(link.target)) nextLinksByNode.set(link.target, [])
      if (!nextDegreeMap.has(link.source)) nextDegreeMap.set(link.source, 0)
      if (!nextDegreeMap.has(link.target)) nextDegreeMap.set(link.target, 0)
      nextLinksByNode.get(link.source).push(link)
      nextLinksByNode.get(link.target).push(link)
      nextDegreeMap.set(link.source, (nextDegreeMap.get(link.source) ?? 0) + 1)
      nextDegreeMap.set(link.target, (nextDegreeMap.get(link.target) ?? 0) + 1)
    })

    linksByNode.value = nextLinksByNode
    degreeMap.value = nextDegreeMap
    syncReactiveCollections()
  }

  function mergeGraphPayloads(payloads, options = {}) {
    const addedNodes = []
    const updatedNodes = []
    const addedLinks = []
    const touchedNodeIds = new Set()

    for (const payload of payloads || []) {
      for (const rawNode of payload.nodes || []) {
        const incoming = normalizeNode(rawNode)
        if (isCountryLocation(incoming)) continue
        const existing = nodeMap.value.get(incoming.id)
        const merged = existing ? mergeNodeData(existing, incoming) : incoming
        nodeMap.value.set(merged.id, merged)
        ensureNodeBuckets(merged.id)
        touchedNodeIds.add(merged.id)
        if (existing) updatedNodes.push(merged)
        else addedNodes.push(merged)
      }

      for (const rawLink of payload.links || []) {
        const normalized = normalizeLink(rawLink)
        if (linkMap.value.has(normalized.key)) continue
        if (!nodeMap.value.has(normalized.source) || !nodeMap.value.has(normalized.target)) continue
        linkMap.value.set(normalized.key, normalized)
        ensureNodeBuckets(normalized.source)
        ensureNodeBuckets(normalized.target)
        linksByNode.value.get(normalized.source).push(normalized)
        linksByNode.value.get(normalized.target).push(normalized)
        degreeMap.value.set(normalized.source, (degreeMap.value.get(normalized.source) ?? 0) + 1)
        degreeMap.value.set(normalized.target, (degreeMap.value.get(normalized.target) ?? 0) + 1)
        addedLinks.push(normalized)
        touchedNodeIds.add(normalized.source)
        touchedNodeIds.add(normalized.target)
      }
    }

    syncReactiveCollections()

    if (options.chunkId) addSetValue(loadedChunkIds, options.chunkId)
    if (options.chunkIds?.length) addSetValues(loadedChunkIds, options.chunkIds)

    if (options.emitMutation !== false) {
      lastMutation.value = {
        serial: ++mutationSerial,
        centerId: options.centerId || null,
        addedNodes,
        updatedNodes,
        addedLinks,
        touchedNodeIds: Array.from(touchedNodeIds)
      }
    }

    return {
      addedNodes,
      updatedNodes,
      addedLinks,
      touchedNodeIds: Array.from(touchedNodeIds)
    }
  }

  function mergeGraphData(payload, options = {}) {
    return mergeGraphPayloads([payload], options)
  }

  async function loadInitialData() {
    if (loaded.value) return
    if (initialPromise) return initialPromise

    loading.value = true
    initialPromise = fetchJson('data/summary.json').then(summary => {
      const birds = inflateSummaryItems(summary)
      summaryBirds.value = birds
      summaryMap.value = new Map(birds.map(bird => [bird.id, bird]))
      summaryLoaded.value = true

      meta.value = summary.meta || null
      skeletonLoaded.value = true
      loaded.value = true
    }).finally(() => {
      loading.value = false
    })

    return initialPromise
  }

  async function loadNodeChunk(nodeId) {
    if (!nodeId) return null
    await loadInitialData()

    if (hasLoadedChunk(nodeId)) {
      activeNodeId.value = nodeId
      requestNodeFocus(nodeId)
      return getNodeById(nodeId)
    }

    if (chunkPromises.has(nodeId)) return chunkPromises.get(nodeId)

    addSetValue(pendingChunkIds, nodeId)

    const promise = fetchJson(`data/nodes/${encodeURIComponent(nodeId)}.json`)
      .then(chunk => {
        mergeGraphData(chunk, {
          chunkId: nodeId,
          centerId: chunk.meta?.centerNodeId || nodeId
        })
        activeNodeId.value = chunk.meta?.centerNodeId || nodeId
        requestNodeFocus(activeNodeId.value)
        return chunk
      })
      .finally(() => {
        removeSetValue(pendingChunkIds, nodeId)
        chunkPromises.delete(nodeId)
      })

    chunkPromises.set(nodeId, promise)
    return promise
  }

  async function loadGraphPreview() {
    await loadInitialData()

    if (previewLoaded.value) return previewLoadProgress.value
    if (previewPromise) return previewPromise

    const previewChunkId = 'graph_preview'
    const alreadyLoaded = loadedChunkIds.value.has(previewChunkId) ? totalBirdCount.value : 0

    previewLoadProgress.value = {
      loaded: alreadyLoaded,
      total: totalBirdCount.value,
      failed: 0
    }

    if (loadedChunkIds.value.has(previewChunkId)) {
      previewLoaded.value = true
      requestGraphFit()
      return previewLoadProgress.value
    }

    previewLoading.value = true

    previewPromise = fetchJson('data/graph_preview.json')
      .then(preview => {
        const trimmedPreview = trimGraphPreviewPayload(preview)
        mergeGraphData(trimmedPreview, {
          chunkId: previewChunkId,
          centerId: null
        })

        const loadedCount = preview.meta?.counts?.birds || totalBirdCount.value
        previewLoadProgress.value = {
          loaded: loadedCount,
          total: totalBirdCount.value,
          failed: 0
        }
        previewLoaded.value = loadedCount >= totalBirdCount.value
        requestGraphFit()
        return previewLoadProgress.value
      })
      .catch(error => {
        previewLoadProgress.value = {
          loaded: 0,
          total: totalBirdCount.value,
          failed: totalBirdCount.value
        }
        throw error
      })
      .finally(() => {
        previewLoading.value = false
        previewPromise = null
      })

    return previewPromise
  }

  async function ensureBirdLoaded(nodeId) {
    await loadInitialData()
    return loadNodeChunk(nodeId)
  }

  function requestNodeFocus(nodeId) {
    if (!nodeId) return
    focusRequest.value = {
      id: nodeId,
      nonce: focusRequest.value.nonce + 1
    }
  }

  function setActiveNode(nodeId) {
    activeNodeId.value = nodeId || ''
  }

  function requestGraphFit() {
    fitRequest.value = {
      nonce: fitRequest.value.nonce + 1
    }
  }

  function buildIndexes() {
    rebuildIndexes()
  }

  function loadData() {
    return loadInitialData()
  }

  function getNodeById(id) {
    return nodeMap.value.get(id) || summaryMap.value.get(id) || null
  }

  function getNodeDegree(id) {
    return degreeMap.value.get(id) ?? 0
  }

  function getIncidentLinks(id) {
    return linksByNode.value.get(id) ?? []
  }

  function findBirdMatches(query, limit = 8) {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return []
    return summaryBirds.value
      .filter(bird => bird.searchText.includes(normalized))
      .slice(0, limit)
  }

  function getRelatedBirds(birdId, relation) {
    const results = []
    const incident = getIncidentLinks(birdId)
    for (const link of incident) {
      if (relation && link.relation !== relation) continue
      const otherId = link.source === birdId ? link.target : link.source
      const other = getNodeById(otherId)
      if (other && other.type === 'bird') results.push({ bird: other, link })
    }
    return results
  }

  function getContinent(lat, lng) {
    if (lat == null || lng == null) return '未知'
    if (lng >= -30 && lng <= 60 && lat >= -35 && lat <= 37) return '非洲'
    if (lng >= -180 && lng <= -30 && lat >= 7 && lat <= 83) return '北美洲'
    if (lng >= -90 && lng <= -30 && lat >= -60 && lat <= 7) return '南美洲'
    if (lng >= 60 && lng <= 180 && lat >= -10 && lat <= 80) return '亚洲'
    if (lng >= -30 && lng <= 60 && lat >= 36 && lat <= 70) return '欧洲'
    if ((lng >= 100 && lng <= 180 && lat >= -55 && lat <= -10) ||
        (lng >= -180 && lng <= -140 && lat >= -25 && lat <= 20)) return '大洋洲'
    if (lat <= -55) return '南极洲'
    return '未知'
  }

  function getBirdContinent(birdId) {
    const bird = getNodeById(birdId)
    if (!bird) return '未知'
    if (bird.lat != null && bird.lng != null) return getContinent(bird.lat, bird.lng)
    const incident = getIncidentLinks(birdId)
    for (const link of incident) {
      const otherId = link.source === birdId ? link.target : link.source
      const other = getNodeById(otherId)
      if (other && other.type === 'location' && other.lat != null && other.lng != null) {
        return getContinent(other.lat, other.lng)
      }
    }
    return '未知'
  }

  function getBirdLocations(birdId) {
    const bird = getNodeById(birdId)
    if (!bird || !bird.locations) return []
    return bird.locations
      .map(name => nodes.value.find(node => node.type === 'location' && node.name === name))
      .filter(Boolean)
  }

  return {
    meta,
    nodes,
    links,
    loading,
    loaded,
    summaryLoaded,
    skeletonLoaded,
    summaryBirds,
    nodeMap,
    summaryMap,
    linkMap,
    linksByNode,
    degreeMap,
    loadedChunkIds,
    pendingChunkIds,
    lastMutation,
    activeNodeId,
    focusRequest,
    fitRequest,
    previewLoading,
    previewLoaded,
    previewLoadProgress,
    birdNodes,
    locationNodes,
    habitatNodes,
    taxonomyNodes,
    nodeCount,
    linkCount,
    totalBirdCount,
    loadedBirdCount,
    loadedChunkCount,
    hasLoadedChunk,
    isChunkPending,
    buildIndexes,
    loadData,
    loadInitialData,
    loadNodeChunk,
    loadGraphPreview,
    ensureBirdLoaded,
    requestNodeFocus,
    requestGraphFit,
    setActiveNode,
    getNodeById,
    getNodeDegree,
    getIncidentLinks,
    findBirdMatches,
    getRelatedBirds,
    getContinent,
    getBirdContinent,
    getBirdLocations
  }
})

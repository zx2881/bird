import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGraphStore = defineStore('graph', () => {
  const meta = ref(null)
  const nodes = ref([])
  const links = ref([])
  const loaded = ref(false)
  const loading = ref(false)

  const nodeMap = ref(new Map())
  const linksByNode = ref(new Map())
  const degreeMap = ref(new Map())

  const birdNodes = computed(() => nodes.value.filter(n => n.type === 'bird'))
  const locationNodes = computed(() => nodes.value.filter(n => n.type === 'location'))
  const habitatNodes = computed(() => nodes.value.filter(n => n.type === 'habitat'))
  const nodeCount = computed(() => nodes.value.length)
  const linkCount = computed(() => links.value.length)

  function buildIndexes() {
    const nm = new Map()
    const lbn = new Map()
    const dm = new Map()
    nodes.value.forEach(n => { nm.set(n.id, n); lbn.set(n.id, []); dm.set(n.id, 0) })
    links.value.forEach((link, i) => {
      const key = `${link.source}__${link.relation}__${link.target}__${i}`
      const enriched = { ...link, key }
      if (!lbn.has(link.source)) { lbn.set(link.source, []); dm.set(link.source, 0) }
      if (!lbn.has(link.target)) { lbn.set(link.target, []); dm.set(link.target, 0) }
      lbn.get(link.source).push(enriched)
      lbn.get(link.target).push(enriched)
      dm.set(link.source, (dm.get(link.source) ?? 0) + 1)
      dm.set(link.target, (dm.get(link.target) ?? 0) + 1)
    })
    nodeMap.value = nm
    linksByNode.value = lbn
    degreeMap.value = dm
  }

  async function loadData() {
    if (loaded.value) return
    loading.value = true
    try {
      const res = await fetch(`${import.meta.env.BASE_URL}knowledge.json`)// 关键修改点：使用 import.meta.env.BASE_URL 来构建正确的路径
      if (!res.ok) {
        throw new Error(`Failed to load knowledge.json: ${res.status} ${res.statusText}`)
      }
      const data = await res.json()
      meta.value = data.meta
      nodes.value = data.nodes
      links.value = data.links
      loaded.value = true
      buildIndexes()
    } finally {
      loading.value = false
    }
  }

  function getNodeById(id) { return nodeMap.value.get(id) }
  function getNodeDegree(id) { return degreeMap.value.get(id) ?? 0 }
  function getIncidentLinks(id) { return linksByNode.value.get(id) ?? [] }

  function getRelatedBirds(birdId, relation) {
    const results = []
    const links = getIncidentLinks(birdId)
    for (const link of links) {
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
    const links = getIncidentLinks(birdId)
    for (const link of links) {
      const otherId = link.source === birdId ? link.target : link.source
      const other = getNodeById(otherId)
      if (other && other.type === 'location' && other.lat != null && other.lng != null)
        return getContinent(other.lat, other.lng)
    }
    return '未知'
  }

  function getBirdLocations(birdId) {
    const bird = getNodeById(birdId)
    if (!bird || !bird.locations) return []
    return bird.locations.map(name =>
      nodes.value.find(n => n.type === 'location' && n.name === name)
    ).filter(Boolean)
  }

  return {
    meta, nodes, links, loaded, loading,
    nodeMap, linksByNode, degreeMap,
    birdNodes, locationNodes, habitatNodes, nodeCount, linkCount,
    loadData, buildIndexes,
    getNodeById, getNodeDegree, getIncidentLinks,
    getRelatedBirds, getContinent, getBirdContinent, getBirdLocations
  }
})

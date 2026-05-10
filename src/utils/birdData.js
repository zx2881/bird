import { ref } from 'vue'

const knowledge = ref({ meta: null, nodes: [], links: [] })
const loaded = ref(false)

export function getContinent(lat, lng) {
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

async function loadData() {
  if (loaded.value) return
  const response = await fetch('/knowledge.json')
  const data = await response.json()
  knowledge.value = data
  loaded.value = true
}

export function useBirdData() {
  const nodeMap = new Map()
  const linksByNode = new Map()
  const degreeMap = new Map()

  function buildIndexes() {
    nodeMap.clear()
    linksByNode.clear()
    degreeMap.clear()
    knowledge.value.nodes.forEach((node) => {
      nodeMap.set(node.id, node)
      linksByNode.set(node.id, [])
      degreeMap.set(node.id, 0)
    })
    knowledge.value.links.forEach((link, index) => {
      const enriched = { ...link, key: `${link.source}__${link.relation}__${link.target}__${index}` }
      if (!linksByNode.has(link.source)) {
        linksByNode.set(link.source, [])
        degreeMap.set(link.source, 0)
      }
      if (!linksByNode.has(link.target)) {
        linksByNode.set(link.target, [])
        degreeMap.set(link.target, 0)
      }
      linksByNode.get(link.source).push(enriched)
      linksByNode.get(link.target).push(enriched)
      degreeMap.set(link.source, (degreeMap.get(link.source) ?? 0) + 1)
      degreeMap.set(link.target, (degreeMap.get(link.target) ?? 0) + 1)
    })
  }

  function getNodeById(id) {
    return nodeMap.get(id)
  }

  function getNodeDegree(id) {
    return degreeMap.get(id) ?? 0
  }

  function getIncidentLinks(nodeId) {
    return linksByNode.get(nodeId) ?? []
  }

  function getBirdContinent(birdId) {
    const bird = getNodeById(birdId)
    if (!bird) return '未知'
    if (bird.lat != null && bird.lng != null) return getContinent(bird.lat, bird.lng)
    const links = getIncidentLinks(birdId)
    for (const link of links) {
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
    return bird.locations.map((name) => {
      return knowledge.value.nodes.find((n) => n.type === 'location' && n.name === name)
    }).filter(Boolean)
  }

  function getRelatedBirds(birdId, relation) {
    const results = []
    const links = getIncidentLinks(birdId)
    for (const link of links) {
      if (relation && link.relation !== relation) continue
      const otherId = link.source === birdId ? link.target : link.source
      const other = getNodeById(otherId)
      if (other && other.type === 'bird') {
        results.push({ bird: other, link })
      }
    }
    return results
  }

  const birdNodes = () => knowledge.value.nodes.filter((n) => n.type === 'bird')
  const locationNodes = () => knowledge.value.nodes.filter((n) => n.type === 'location')
  const habitatNodes = () => knowledge.value.nodes.filter((n) => n.type === 'habitat')

  return {
    knowledge,
    loaded,
    loadData,
    buildIndexes,
    getNodeById,
    getNodeDegree,
    getIncidentLinks,
    getBirdContinent,
    getBirdLocations,
    getRelatedBirds,
    birdNodes,
    locationNodes,
    habitatNodes,
    nodeMap,
    linksByNode,
    degreeMap
  }
}

export { knowledge, loaded, loadData }

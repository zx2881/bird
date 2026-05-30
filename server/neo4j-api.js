import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')

function loadEnvFile() {
  const envPath = path.join(rootDir, '.env')
  if (!fs.existsSync(envPath)) return

  for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const separator = trimmed.indexOf('=')
    if (separator === -1) continue
    const key = trimmed.slice(0, separator).trim()
    const value = trimmed.slice(separator + 1).trim().replace(/^["']|["']$/g, '')
    if (key && process.env[key] == null) process.env[key] = value
  }
}

loadEnvFile()

const PORT = Number(process.env.API_PORT || 5174)
const NEO4J_HTTP_URL = (process.env.NEO4J_HTTP_URL || 'http://localhost:7474').replace(/\/$/, '')
const NEO4J_DATABASE = process.env.NEO4J_DATABASE || 'neo4j'
const NEO4J_USER = process.env.NEO4J_USER || 'neo4j'
const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD || 'birdneo4j123'
const DEFAULT_PREVIEW_BIRD_LIMIT = Number(process.env.PREVIEW_BIRD_LIMIT || 360)
const DEFAULT_NODE_NEIGHBOR_LIMIT = Number(process.env.NODE_NEIGHBOR_LIMIT || 80)
const NODE_NEIGHBOR_MAX_LIMIT = Number(process.env.NODE_NEIGHBOR_MAX_LIMIT || 300)

function jsonResponse(response, statusCode, payload) {
  const body = JSON.stringify(payload)
  response.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  })
  response.end(body)
}

function clampLimit(value, fallback, max) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback
  return Math.min(Math.floor(parsed), max)
}

async function cypher(statement, parameters = {}) {
  const response = await fetch(`${NEO4J_HTTP_URL}/db/${encodeURIComponent(NEO4J_DATABASE)}/tx/commit`, {
    method: 'POST',
    headers: {
      Authorization: `Basic ${Buffer.from(`${NEO4J_USER}:${NEO4J_PASSWORD}`).toString('base64')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      statements: [
        {
          statement,
          parameters,
          resultDataContents: ['row']
        }
      ]
    })
  })

  if (!response.ok) {
    throw new Error(`Neo4j HTTP ${response.status}: ${response.statusText}`)
  }

  const payload = await response.json()
  if (payload.errors?.length) {
    throw new Error(payload.errors.map(error => `${error.code}: ${error.message}`).join('\n'))
  }

  return payload.results?.[0]?.data?.map(item => item.row) || []
}

function cleanNode(node) {
  return Object.fromEntries(
    Object.entries(node || {}).filter(([, value]) => value !== null && value !== '' && !(Array.isArray(value) && value.length === 0))
  )
}

function cleanLink(link) {
  const relation = link.relation || ''
  return {
    key: link.key || `${link.source}__${relation}__${link.target}`,
    source: link.source,
    target: link.target,
    relation,
    label: link.label || relation,
    evidence: link.evidence || ''
  }
}

function graphPayload(nodes, links, meta = {}) {
  const nodeMap = new Map()
  const linkMap = new Map()

  for (const node of nodes) {
    const cleaned = cleanNode(node)
    if (cleaned.id) nodeMap.set(cleaned.id, cleaned)
  }

  for (const link of links) {
    const cleaned = cleanLink(link)
    if (cleaned.source && cleaned.target) linkMap.set(cleaned.key, cleaned)
  }

  return {
    meta: {
      ...meta,
      counts: {
        ...(meta.counts || {}),
        nodes: nodeMap.size,
        links: linkMap.size
      }
    },
    nodes: Array.from(nodeMap.values()),
    links: Array.from(linkMap.values())
  }
}

async function getSummary() {
  const rows = await cypher(`
    MATCH (b:Bird)
    RETURN b.id AS id, b.name AS name, b.englishName AS englishName, b.latinName AS latinName
    ORDER BY coalesce(b.name, b.englishName, b.id)
  `)

  const relationRows = await cypher(`
    MATCH ()-[r]->()
    WITH coalesce(r.relation, type(r)) AS relation, count(r) AS count
    RETURN relation, count
    ORDER BY relation
  `)

  const locationRows = await cypher(`
    MATCH (l:Location)
    RETURN l.id AS id, l.name AS name, l.lat AS lat, l.lng AS lng
    ORDER BY coalesce(l.name, l.id)
  `)

  const relationTypes = Object.fromEntries(relationRows.map(([relation, count]) => [relation, count]))
  const totalRelations = Object.values(relationTypes).reduce((sum, count) => sum + count, 0)

  return {
    meta: {
      source: 'neo4j',
      counts: {
        birds: rows.length,
        totalRelations,
        relationTypes
      }
    },
    columns: ['id', 'name', 'englishName', 'latinName'],
    items: rows.map(([id, name, englishName, latinName]) => [id, name, englishName || '', latinName || '']),
    locations: locationRows.map(([id, name, lat, lng]) => ({ id, name, lat, lng }))
  }
}

async function searchBirds(query, limit) {
  const normalized = String(query || '').trim().toLowerCase()
  if (!normalized) return []

  const rows = await cypher(
    `
      MATCH (b:Bird)
      WHERE toLower(coalesce(b.name, '')) CONTAINS $query
         OR toLower(coalesce(b.englishName, '')) CONTAINS $query
         OR toLower(coalesce(b.latinName, '')) CONTAINS $query
      RETURN properties(b) AS bird
      ORDER BY coalesce(b.name, b.englishName, b.id)
      LIMIT $limit
    `,
    { query: normalized, limit }
  )

  return rows.map(([bird]) => cleanNode(bird))
}

async function getPreview(limit) {
  const highTaxonomyLevels = ['kingdom', 'phylum', 'class', 'order', 'family']
  const taxNodeRows = await cypher(
    `
      MATCH (t:Taxon)
      WHERE t.taxonomyLevel IN $levels
      RETURN properties(t) AS node
    `,
    { levels: highTaxonomyLevels }
  )

  const taxLinkRows = await cypher(
    `
      MATCH (source:Taxon)-[r]->(target:Taxon)
      WHERE source.taxonomyLevel IN $levels
        AND target.taxonomyLevel IN $levels
        AND r.relation STARTS WITH 'belongs_to_'
      RETURN r {.*, source: source.id, target: target.id} AS link
    `,
    { levels: highTaxonomyLevels }
  )

  const birdRows = await cypher(
    `
      MATCH (bird:Bird)-[r]->(taxon:Taxon)
      WHERE r.relation IN ['belongs_to_family', 'belongs_to_order']
      RETURN properties(bird) AS bird, properties(taxon) AS taxon, r {.*, source: bird.id, target: taxon.id} AS link
      ORDER BY coalesce(bird.name, bird.englishName, bird.id)
      LIMIT $limit
    `,
    { limit }
  )

  const countRows = await cypher(`
    MATCH (b:Bird)
    WITH count(b) AS birds
    MATCH (t:Taxon)
    RETURN birds, count(t) AS taxonomy
  `)
  const [birdCount = 0, taxonomyCount = 0] = countRows[0] || []

  const nodes = [
    ...taxNodeRows.map(([node]) => node),
    ...birdRows.flatMap(([bird, taxon]) => [bird, taxon])
  ]
  const links = [
    ...taxLinkRows.map(([link]) => link),
    ...birdRows.map(([, , link]) => link)
  ]

  return graphPayload(nodes, links, {
    source: 'neo4j',
    scope: 'startup-graph-preview',
    layoutMode: 'precomputed-static',
    counts: {
      birds: Math.min(limit, birdCount),
      totalBirds: birdCount,
      taxonomy: taxonomyCount
    }
  })
}

async function getNodeNeighborhood(id, limit) {
  const rows = await cypher(
    `
      MATCH (center:GraphNode {id: $id})
      OPTIONAL MATCH (center)-[r]-(neighbor:GraphNode)
      WITH center, neighbor, r,
        CASE
          WHEN neighbor IS NULL THEN 99
          WHEN center:Taxon AND neighbor:Taxon AND endNode(r).id = center.id THEN 0
          WHEN center:Taxon AND neighbor:Bird THEN 1
          WHEN center:Bird AND neighbor:Taxon THEN 0
          WHEN center:Bird AND neighbor:Location THEN 1
          WHEN center:Bird THEN 2
          ELSE 3
        END AS priority
      ORDER BY priority ASC,
        coalesce(neighbor.memberCount, 0) DESC,
        coalesce(neighbor.name, neighbor.englishName, neighbor.id) ASC
      WITH center, collect({
        node: properties(neighbor),
        link: r {.*, source: startNode(r).id, target: endNode(r).id}
      })[..$limit] AS items
      RETURN properties(center) AS center, items
    `,
    { id, limit }
  )

  if (!rows.length) return null

  const [center, items] = rows[0]
  const nodes = [center]
  const links = []

  for (const item of items || []) {
    if (!item?.node?.id || !item?.link?.source || !item?.link?.target) continue
    nodes.push(item.node)
    links.push(item.link)
  }

  return graphPayload(nodes, links, {
    source: 'neo4j',
    centerNodeId: id,
      scope: 'node-neighborhood',
      neighborLimit: limit
    })
}

async function getHealth() {
  const rows = await cypher('RETURN 1 AS ok')
  return { ok: rows[0]?.[0] === 1 }
}

async function handleRequest(request, response) {
  if (request.method === 'OPTIONS') {
    response.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    })
    response.end()
    return
  }

  const url = new URL(request.url, `http://${request.headers.host}`)

  try {
    if (url.pathname === '/api/health') {
      jsonResponse(response, 200, await getHealth())
      return
    }

    if (url.pathname === '/api/summary') {
      jsonResponse(response, 200, await getSummary())
      return
    }

    if (url.pathname === '/api/search') {
      const limit = clampLimit(url.searchParams.get('limit'), 8, 50)
      jsonResponse(response, 200, await searchBirds(url.searchParams.get('q'), limit))
      return
    }

    if (url.pathname === '/api/graph/preview') {
      const limit = clampLimit(url.searchParams.get('limit'), DEFAULT_PREVIEW_BIRD_LIMIT, 1000)
      jsonResponse(response, 200, await getPreview(limit))
      return
    }

    const nodeMatch = url.pathname.match(/^\/api\/nodes\/([^/]+)$/)
    if (nodeMatch) {
      const limit = clampLimit(url.searchParams.get('limit'), DEFAULT_NODE_NEIGHBOR_LIMIT, NODE_NEIGHBOR_MAX_LIMIT)
      const payload = await getNodeNeighborhood(decodeURIComponent(nodeMatch[1]), limit)
      if (!payload) {
        jsonResponse(response, 404, { error: 'Node not found' })
        return
      }
      jsonResponse(response, 200, payload)
      return
    }

    jsonResponse(response, 404, { error: 'Not found' })
  } catch (error) {
    jsonResponse(response, 500, {
      error: error.message,
      hint: '请确认 Neo4j 已启动，并已运行 npm run import:neo4j。'
    })
  }
}

http.createServer(handleRequest).listen(PORT, () => {
  console.log(`Neo4j API listening on http://localhost:${PORT}`)
})

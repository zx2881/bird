import { createServer } from 'node:http'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { extractTriplesFromDocuments, extractTriplesFromText } from './services/tripleExtractor.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const sampleDocsPath = path.join(__dirname, 'data', 'sample-docs.json')
const port = Number(process.env.PORT || 3001)

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  })
  response.end(JSON.stringify(payload, null, 2))
}

async function readRequestBody(request) {
  return new Promise((resolve, reject) => {
    let data = ''

    request.on('data', (chunk) => {
      data += chunk
      if (data.length > 2_000_000) {
        reject(new Error('请求体过大'))
      }
    })

    request.on('end', () => resolve(data))
    request.on('error', reject)
  })
}

const server = createServer(async (request, response) => {
  const requestUrl = new URL(request.url, `http://${request.headers.host}`)

  if (request.method === 'OPTIONS') {
    sendJson(response, 204, {})
    return
  }

  if (request.method === 'GET' && requestUrl.pathname === '/api/health') {
    sendJson(response, 200, {
      ok: true,
      service: 'bird-triple-test',
      timestamp: new Date().toISOString()
    })
    return
  }

  if (request.method === 'GET' && requestUrl.pathname === '/api/triples/test') {
    const raw = await readFile(sampleDocsPath, 'utf8')
    const documents = JSON.parse(raw)
    const triples = extractTriplesFromDocuments(documents)

    sendJson(response, 200, {
      documents,
      triples,
      count: triples.length,
      generated_at: new Date().toISOString()
    })
    return
  }

  if (request.method === 'POST' && requestUrl.pathname === '/api/triples/extract') {
    try {
      const rawBody = await readRequestBody(request)
      const body = rawBody ? JSON.parse(rawBody) : {}
      const text = String(body.text || '').trim()

      if (!text) {
        sendJson(response, 400, {
          error: 'text 字段不能为空'
        })
        return
      }

      const triples = extractTriplesFromText(text)
      sendJson(response, 200, {
        triples,
        count: triples.length
      })
    } catch (error) {
      sendJson(response, 400, {
        error: '请求体必须是 JSON'
      })
    }
    return
  }

  sendJson(response, 404, {
    error: 'Not Found'
  })
})

server.listen(port, () => {
  console.log(`Bird triple test server listening on http://localhost:${port}`)
})


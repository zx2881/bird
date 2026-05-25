export function useGraphExport() {

  function exportPNG(container) {
    if (!container) return
    const canvas = container.querySelector('canvas')
    if (!canvas) return
    const output = document.createElement('canvas')
    const width = canvas.width || canvas.clientWidth
    const height = canvas.height || canvas.clientHeight
    output.width = width
    output.height = height

    const ctx = output.getContext('2d')
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
    ctx.fillStyle = isDark ? '#0b1018' : '#101827'
    ctx.fillRect(0, 0, width, height)
    ctx.drawImage(canvas, 0, 0, width, height)

    const link = document.createElement('a')
    link.download = `bird-graph-${Date.now()}.png`
    link.href = output.toDataURL('image/png')
    link.click()
  }

  function exportJSON(nodes, links) {
    const data = { meta: { exported_at: new Date().toISOString() }, nodes, links }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    downloadBlob(blob, `bird-graph-${Date.now()}.json`)
  }

  function exportGraphML(nodes, links) {
    let xml = `<?xml version="1.0" encoding="UTF-8"?>\n<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n`
    xml += `  <key id="type" for="node" attr.name="type" attr.type="string"/>\n`
    xml += `  <key id="label" for="node" attr.name="label" attr.type="string"/>\n`
    xml += `  <key id="relation" for="edge" attr.name="relation" attr.type="string"/>\n`
    xml += `  <graph id="G" edgedefault="directed">\n`
    nodes.forEach(n => {
      xml += `    <node id="${escapeXml(n.id)}">\n`
      xml += `      <data key="type">${escapeXml(n.type)}</data>\n`
      xml += `      <data key="label">${escapeXml(n.name || n.id)}</data>\n`
      xml += `    </node>\n`
    })
    links.forEach(l => {
      xml += `    <edge source="${escapeXml(l.source)}" target="${escapeXml(l.target)}">\n`
      xml += `      <data key="relation">${escapeXml(l.relation)}</data>\n`
      xml += `    </edge>\n`
    })
    xml += `  </graph>\n</graphml>`
    downloadBlob(new Blob([xml], { type: 'application/xml' }), `bird-graph-${Date.now()}.graphml`)
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  }

  function escapeXml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
  }

  return { exportPNG, exportJSON, exportGraphML }
}

/** 维基抓取常用的占位坐标，不宜作为地图默认中心 */
const PLACEHOLDER_COORD_KEYS = new Set([
  '4.000,-72.000',
  '-34.000,-64.000',
  '-6.000,142.000',
  '-25.000,133.000',
  '-32.000,-70.000',
  '-16.712,-64.666',
  '-10.000,-52.000',
  '-12.500,18.500'
])

/** Leaflet maxBounds: [[south, west], [north, east]] */
export const MAP_MAX_BOUNDS = Object.freeze([[-85, -180], [85, 180]])

/** 概览页默认全球视野（避免 fitBounds 跨日界线导致异常缩放） */
export const DEFAULT_WORLD_VIEW = Object.freeze({ center: [15, 0], zoom: 2 })

function coordKey(lat, lng) {
  return `${Number(lat).toFixed(3)},${Number(lng).toFixed(3)}`
}

export function isReliableMapCoord(lat, lng) {
  if (lat == null || lng == null) return false
  const latitude = Number(lat)
  const longitude = Number(lng)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return false
  if (Math.abs(latitude) > 90 || Math.abs(longitude) > 180) return false
  return !PLACEHOLDER_COORD_KEYS.has(coordKey(latitude, longitude))
}

export function toLatLng(lat, lng) {
  return [Number(lat), Number(lng)]
}

export function applyLeafletMapLimits(map, leaflet) {
  map.setMaxBounds(leaflet.latLngBounds(MAP_MAX_BOUNDS))
  map.options.maxBoundsViscosity = 1
}

export function addOsmTileLayer(map, leaflet) {
  return leaflet.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    noWrap: true,
    bounds: leaflet.latLngBounds(MAP_MAX_BOUNDS),
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map)
}

export function fitMapToPoints(map, leaflet, points, options = {}) {
  const padding = options.padding ?? [28, 28]
  const maxZoom = options.maxZoom ?? 7

  if (!points.length) {
    map.setView(DEFAULT_WORLD_VIEW.center, DEFAULT_WORLD_VIEW.zoom, { animate: false })
    return
  }

  if (points.length === 1) {
    map.setView(points[0], options.singleZoom ?? 6, { animate: false })
    return
  }

  const lngs = points.map(point => point[1])
  const lngSpan = Math.max(...lngs) - Math.min(...lngs)

  // 分布跨度过大时直接用全球视野，避免 fitBounds 与日界线交互异常
  if (lngSpan > 200) {
    map.setView(DEFAULT_WORLD_VIEW.center, DEFAULT_WORLD_VIEW.zoom, { animate: false })
    return
  }

  map.fitBounds(leaflet.latLngBounds(points), {
    padding,
    maxZoom,
    animate: false
  })
}

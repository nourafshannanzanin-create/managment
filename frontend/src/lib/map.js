import 'leaflet/dist/leaflet.css'

let leafletLibraryPromise = null

const MAP_MIN_ZOOM = 5
const MAP_MAX_ZOOM = 18
const PRIMARY_TILE_TEMPLATE = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
const FALLBACK_TILE_TEMPLATE = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

export async function getLeafletLibrary() {
  if (leafletLibraryPromise) return leafletLibraryPromise
  leafletLibraryPromise = import('leaflet')
    .then((module) => module.default || module)
    .catch((error) => {
      leafletLibraryPromise = null
      throw error
    })
  return leafletLibraryPromise
}

export function createBaseMap(L, container, center) {
  const map = L.map(container, {
    zoomControl: false,
    attributionControl: false,
    preferCanvas: true,
    minZoom: MAP_MIN_ZOOM,
    maxZoom: MAP_MAX_ZOOM,
    fadeAnimation: false,
    zoomAnimation: true,
    markerZoomAnimation: true,
  }).setView(
    [center.latitude, center.longitude],
    clamp(center.zoom || 12, MAP_MIN_ZOOM, MAP_MAX_ZOOM),
  )
  return map
}

export function attachReliableTileLayer(L, map) {
  let activeLayer = null
  let fallbackMounted = false

  const mount = (url, options = {}) => {
    const layer = L.tileLayer(url, {
      minZoom: MAP_MIN_ZOOM,
      maxZoom: MAP_MAX_ZOOM,
      detectRetina: true,
      updateWhenIdle: true,
      updateWhenZooming: false,
      keepBuffer: 2,
      crossOrigin: true,
      errorTileUrl: 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==',
      ...options,
    })
    layer.addTo(map)
    return layer
  }

  activeLayer = mount(PRIMARY_TILE_TEMPLATE, {
    subdomains: 'abcd',
    attribution: '&copy; OpenStreetMap &copy; CARTO',
  })

  let errorCount = 0
  activeLayer.on('tileerror', () => {
    errorCount += 1
    if (fallbackMounted || errorCount < 3) return
    fallbackMounted = true
    activeLayer?.remove()
    activeLayer = mount(FALLBACK_TILE_TEMPLATE, {
      subdomains: 'abc',
      attribution: '&copy; OpenStreetMap',
    })
  })

  return {
    destroy() {
      activeLayer?.remove()
      activeLayer = null
    },
  }
}

export function createMapSizeKeeper(map, container) {
  let rafId = null
  let debounceId = null
  let resizeObserver = null

  const invalidate = () => {
    if (!container?.isConnected) return
    if (container.clientWidth === 0 || container.clientHeight === 0) return
    map.invalidateSize(false)
  }

  const schedule = () => {
    if (rafId != null) cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(() => {
      invalidate()
      rafId = null
    })
    if (debounceId) clearTimeout(debounceId)
    debounceId = setTimeout(() => {
      debounceId = null
      invalidate()
    }, 160)
  }

  return {
    start() {
      schedule()
      window.setTimeout(invalidate, 80)
      if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(schedule)
        resizeObserver.observe(container)
      }
      window.addEventListener('resize', schedule)
      window.addEventListener('orientationchange', schedule)
    },
    stop() {
      if (rafId != null) cancelAnimationFrame(rafId)
      if (debounceId) clearTimeout(debounceId)
      resizeObserver?.disconnect()
      window.removeEventListener('resize', schedule)
      window.removeEventListener('orientationchange', schedule)
    },
    invalidate: schedule,
  }
}

export function createDivMarkerIcon(L, { className = 'attendance-map-marker', html = '📍', size = 44 } = {}) {
  return L.divIcon({
    className,
    html: `<span class="attendance-map-marker-inner">${html}</span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size - 2],
  })
}

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import IconlyIcon from './base/IconlyIcon.vue'
import {
  getCitiesByProvinceId,
  getCityMapCenter,
  getProvinceMapCenter,
  provinces,
  resolveMapCenter,
} from '../data/iranLocations'
import { readDeviceLocation } from '../lib/geolocation'
import {
  attachReliableTileLayer,
  configureMapViewerMode,
  createBaseMap,
  createDivMarkerIcon,
  createMapSizeKeeper,
  getLeafletLibrary,
} from '../lib/map'
import { reverseGeocodeNeshan } from '../lib/neshan'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      latitude: null,
      longitude: null,
      label: '',
      radiusMeters: 20,
      provinceId: null,
      cityId: null,
      provinceName: '',
      cityName: '',
    }),
  },
  mode: {
    type: String,
    default: 'picker', // picker | viewer
  },
  height: {
    type: String,
    default: '420px',
  },
  showRadius: {
    type: Boolean,
    default: true,
  },
  userLocation: {
    type: Object,
    default: null,
  },
  autoLocateOnMount: {
    type: Boolean,
    default: false,
  },
  canEdit: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:modelValue', 'change', 'locate', 'error'])

const mapContainer = ref(null)
const mapError = ref('')
const busy = ref(false)
const statusMessage = ref('')
const selectedProvinceId = ref(Number(props.modelValue.provinceId) || 0)
const selectedCityId = ref(Number(props.modelValue.cityId) || 0)

let LeafletLib = null
let map = null
let workplaceMarker = null
let userMarker = null
let radiusCircle = null
let tileController = null
let sizeKeeper = null

const editable = computed(() => props.mode === 'picker' && props.canEdit)
const provinceCities = computed(() => (selectedProvinceId.value ? getCitiesByProvinceId(selectedProvinceId.value) : []))
const selectedProvinceName = computed(
  () => provinces.find((item) => item.id === selectedProvinceId.value)?.name || props.modelValue.provinceName || '',
)
const selectedCityName = computed(
  () => provinceCities.value.find((item) => item.id === selectedCityId.value)?.name || props.modelValue.cityName || '',
)

const currentPoint = computed(() => ({
  latitude: props.modelValue.latitude == null ? null : Number(props.modelValue.latitude),
  longitude: props.modelValue.longitude == null ? null : Number(props.modelValue.longitude),
  label: props.modelValue.label || '',
  radiusMeters: Number(props.modelValue.radiusMeters) || 20,
}))

function emitValue(patch) {
  const next = {
    ...props.modelValue,
    ...patch,
    provinceId: selectedProvinceId.value || null,
    cityId: selectedCityId.value || null,
    provinceName: selectedProvinceName.value,
    cityName: selectedCityName.value,
  }
  emit('update:modelValue', next)
  emit('change', next)
}

function syncProvinceCityFromModel() {
  if (props.modelValue.provinceId) {
    selectedProvinceId.value = Number(props.modelValue.provinceId)
  } else if (props.modelValue.provinceName) {
    const province = provinces.find((item) => item.name === props.modelValue.provinceName)
    selectedProvinceId.value = province?.id || 0
  }
  if (props.modelValue.cityId) {
    selectedCityId.value = Number(props.modelValue.cityId)
  } else if (props.modelValue.cityName && selectedProvinceId.value) {
    const city = getCitiesByProvinceId(selectedProvinceId.value).find((item) => item.name === props.modelValue.cityName)
    selectedCityId.value = city?.id || 0
  }
}

async function buildLabel(latitude, longitude) {
  const result = await reverseGeocodeNeshan(latitude, longitude, {
    provinceName: selectedProvinceName.value,
    cityName: selectedCityName.value,
  })
  return {
    label: result.label || buildLocalFallback(latitude, longitude),
    addressMeta: {
      source: result.source,
      neighbourhood: result.neighbourhood,
      city: result.city,
      state: result.state,
      routeName: result.routeName,
      place: result.place,
      county: result.county,
      district: result.district,
      municipalityZone: result.municipalityZone,
    },
    fromNeshan: result.source?.startsWith('neshan'),
  }
}

function buildLocalFallback(latitude, longitude) {
  const parts = [selectedProvinceName.value, selectedCityName.value].filter(Boolean)
  if (parts.length) return `${parts.join('، ')}، نقطه ثبت‌شده روی نقشه`
  return `نقطه انتخاب‌شده · ${latitude.toFixed(5)}، ${longitude.toFixed(5)}`
}

function ensureRadiusCircle(lat, lng) {
  if (!map || !LeafletLib || !props.showRadius) return
  const radius = Math.max(5, Number(currentPoint.value.radiusMeters) || 20)
  if (radiusCircle) {
    radiusCircle.setLatLng([lat, lng])
    radiusCircle.setRadius(radius)
    return
  }
  radiusCircle = LeafletLib.circle([lat, lng], {
    radius,
    color: '#34908B',
    weight: 2,
    fillColor: '#34908B',
    fillOpacity: 0.12,
  }).addTo(map)
}

function placeWorkplaceMarker(lat, lng) {
  if (!map || !LeafletLib) return
  const icon = createDivMarkerIcon(LeafletLib, {
    className: 'attendance-map-marker is-workplace',
    html: '🏢',
  })
  if (workplaceMarker) {
    workplaceMarker.setLatLng([lat, lng])
  } else {
    workplaceMarker = LeafletLib.marker([lat, lng], {
      draggable: editable.value,
      icon,
    }).addTo(map)
    if (editable.value) {
      workplaceMarker.on('dragend', async () => {
        const position = workplaceMarker.getLatLng()
        busy.value = true
        try {
          const geocoded = await buildLabel(position.lat, position.lng)
          emitValue({
            latitude: Number(position.lat.toFixed(6)),
            longitude: Number(position.lng.toFixed(6)),
            label: geocoded.label,
            addressMeta: geocoded.addressMeta,
          })
          ensureRadiusCircle(position.lat, position.lng)
          statusMessage.value = geocoded.fromNeshan
            ? 'آدرس از سرویس نشان دریافت شد.'
            : 'موقعیت ذخیره شد (آدرس موقت؛ دامنه را در وایت‌لیست نشان قرار دهید).'
        } finally {
          busy.value = false
        }
      })
    }
  }
  ensureRadiusCircle(lat, lng)
}

function placeUserMarker(lat, lng) {
  if (!map || !LeafletLib) return
  const icon = createDivMarkerIcon(LeafletLib, {
    className: 'attendance-map-marker is-user',
    html: '📍',
    size: 40,
  })
  if (userMarker) {
    userMarker.setLatLng([lat, lng])
    return
  }
  userMarker = LeafletLib.marker([lat, lng], { icon, interactive: false }).addTo(map)
}

async function applyPoint(lat, lng, { fly = true, reverse = true } = {}) {
  placeWorkplaceMarker(lat, lng)
  if (fly && map) {
    sizeKeeper?.invalidate()
    map.flyTo([lat, lng], Math.max(map.getZoom(), 16), { duration: 0.65 })
  }
  let label = currentPoint.value.label
  let addressMeta = props.modelValue.addressMeta || null
  let fromNeshan = false
  if (reverse && editable.value) {
    busy.value = true
    try {
      const geocoded = await buildLabel(lat, lng)
      label = geocoded.label
      addressMeta = geocoded.addressMeta
      fromNeshan = geocoded.fromNeshan
      statusMessage.value = fromNeshan
        ? 'آدرس از سرویس نشان دریافت شد.'
        : 'لوکیشن انتخاب شد (آدرس موقت تا وایت‌لیست دامنه نشان فعال شود).'
    } finally {
      busy.value = false
    }
  }
  emitValue({
    latitude: Number(lat.toFixed(6)),
    longitude: Number(lng.toFixed(6)),
    label,
    addressMeta,
  })
}

async function initializeMap() {
  if (map || !mapContainer.value) return
  mapError.value = ''
  syncProvinceCityFromModel()
  const center = resolveMapCenter({
    latitude: currentPoint.value.latitude,
    longitude: currentPoint.value.longitude,
    cityId: selectedCityId.value,
    provinceId: selectedProvinceId.value,
    cityName: selectedCityName.value,
    provinceName: selectedProvinceName.value,
    zoom: currentPoint.value.latitude != null ? 16 : 12,
  })

  await nextTick()
  if (!mapContainer.value || map) return

  try {
    LeafletLib = await getLeafletLibrary()
    map = createBaseMap(LeafletLib, mapContainer.value, center)
    if (!editable.value) {
      configureMapViewerMode(map)
    } else {
      LeafletLib.control.zoom({ position: 'bottomright' }).addTo(map)
    }
    tileController = attachReliableTileLayer(LeafletLib, map)
    sizeKeeper = createMapSizeKeeper(map, mapContainer.value)
    sizeKeeper.start()

    if (editable.value) {
      map.on('click', async (event) => {
        await applyPoint(event.latlng.lat, event.latlng.lng)
      })
    }

    if (currentPoint.value.latitude != null && currentPoint.value.longitude != null) {
      placeWorkplaceMarker(currentPoint.value.latitude, currentPoint.value.longitude)
    }

    if (props.userLocation?.latitude != null && props.userLocation?.longitude != null) {
      placeUserMarker(Number(props.userLocation.latitude), Number(props.userLocation.longitude))
    }

    sizeKeeper.invalidate()
  } catch (error) {
    mapError.value = error?.message || 'بارگذاری نقشه ناموفق بود.'
    emit('error', mapError.value)
  }
}

async function locateCurrentPosition() {
  if (!editable.value || busy.value) return
  busy.value = true
  statusMessage.value = ''
  mapError.value = ''
  try {
    const coords = await readDeviceLocation()
    await applyPoint(coords.latitude, coords.longitude)
    if (!statusMessage.value) {
      statusMessage.value = 'موقعیت فعلی دستگاه روی نقشه قرار گرفت.'
    }
    emit('locate', coords)
  } catch (error) {
    mapError.value = error?.message || 'دریافت موقعیت فعلی ناموفق بود.'
    emit('error', mapError.value)
  } finally {
    busy.value = false
  }
}

function focusCity() {
  if (!selectedCityId.value || !map) return
  const center = getCityMapCenter(selectedCityId.value)
  sizeKeeper?.invalidate()
  map.flyTo([center.latitude, center.longitude], center.zoom, { duration: 0.7 })
  if (editable.value && (currentPoint.value.latitude == null || currentPoint.value.longitude == null)) {
    placeWorkplaceMarker(center.latitude, center.longitude)
    emitValue({
      latitude: Number(center.latitude.toFixed(6)),
      longitude: Number(center.longitude.toFixed(6)),
      label: `${selectedProvinceName.value}، ${selectedCityName.value}`,
    })
  }
}

function focusProvince() {
  if (!selectedProvinceId.value || !map) return
  const center = getProvinceMapCenter(selectedProvinceId.value)
  sizeKeeper?.invalidate()
  map.flyTo([center.latitude, center.longitude], center.zoom, { duration: 0.7 })
}

watch(selectedProvinceId, (value) => {
  if (!value) {
    selectedCityId.value = 0
    emitValue({})
    return
  }
  if (!provinceCities.value.some((city) => city.id === selectedCityId.value)) {
    selectedCityId.value = 0
  }
  emitValue({})
  focusProvince()
})

watch(selectedCityId, () => {
  emitValue({})
  focusCity()
})

watch(
  () => [props.modelValue.latitude, props.modelValue.longitude, props.modelValue.radiusMeters],
  () => {
    if (!map) return
    if (currentPoint.value.latitude != null && currentPoint.value.longitude != null) {
      placeWorkplaceMarker(currentPoint.value.latitude, currentPoint.value.longitude)
    }
  },
)

watch(
  () => props.userLocation,
  (value) => {
    if (!map || value?.latitude == null || value?.longitude == null) return
    placeUserMarker(Number(value.latitude), Number(value.longitude))
  },
  { deep: true },
)

onMounted(async () => {
  syncProvinceCityFromModel()
  await initializeMap()
  // Never auto-request geolocation: iOS Safari only shows the permission prompt
  // after an explicit user tap. Use the locate button instead.
})

onBeforeUnmount(() => {
  sizeKeeper?.stop()
  sizeKeeper = null
  tileController?.destroy()
  tileController = null
  map?.remove()
  map = null
  workplaceMarker = null
  userMarker = null
  radiusCircle = null
  LeafletLib = null
})

defineExpose({
  locateCurrentPosition,
  invalidateSize: () => sizeKeeper?.invalidate(),
})
</script>

<template>
  <section class="location-map-shell">
    <div v-if="editable" class="location-map-toolbar">
      <label class="field-shell">
        <span>استان</span>
        <select v-model.number="selectedProvinceId">
          <option :value="0">انتخاب استان</option>
          <option v-for="province in provinces" :key="province.id" :value="province.id">{{ province.name }}</option>
        </select>
      </label>
      <label class="field-shell">
        <span>شهر</span>
        <select v-model.number="selectedCityId" :disabled="!selectedProvinceId">
          <option :value="0">انتخاب شهر</option>
          <option v-for="city in provinceCities" :key="city.id" :value="city.id">{{ city.name }}</option>
        </select>
      </label>
      <button class="action-btn tone-primary" type="button" :disabled="busy" @click="locateCurrentPosition">
        <IconlyIcon name="profile" decorative />
        <span>{{ busy ? 'در حال دریافت...' : 'اجازه موقعیت و یافتن من' }}</span>
      </button>
    </div>

    <div :class="['location-map-stage', !editable && 'is-viewer-mode']" :style="{ minHeight: height }">
      <div ref="mapContainer" class="location-map-canvas"></div>
      <div class="location-map-hint">
        <strong v-if="editable">روی نقشه کلیک کنید یا پین را بکشید</strong>
        <strong v-else>نقشه محل کار و موقعیت شما</strong>
        <small v-if="currentPoint.latitude != null">
          {{ Number(currentPoint.latitude).toFixed(5) }} ، {{ Number(currentPoint.longitude).toFixed(5) }}
          <template v-if="showRadius"> · شعاع {{ currentPoint.radiusMeters }} متر</template>
        </small>
      </div>
      <div v-if="mapError" class="location-map-alert is-danger">{{ mapError }}</div>
      <div v-else-if="statusMessage" class="location-map-alert is-success">{{ statusMessage }}</div>
    </div>

    <label v-if="editable" class="field-shell location-map-label">
      <span>آدرس / عنوان محل کار</span>
      <textarea
        :value="modelValue.label"
        rows="2"
        placeholder="پس از انتخاب نقطه، آدرس از نشان پر می‌شود و قابل ویرایش است"
        @input="emitValue({ label: $event.target.value })"
      />
    </label>
  </section>
</template>

<style scoped>
.location-map-shell {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.location-map-toolbar {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr)) auto;
  gap: 10px;
  align-items: stretch;
}

.location-map-stage {
  position: relative;
  overflow: hidden;
  border-radius: 18px;
  border: 1px solid var(--line, #b7cbc7);
  background:
    radial-gradient(circle at 18% 20%, rgba(52, 144, 139, 0.16), transparent 42%),
    linear-gradient(180deg, #eef7f5 0%, #f7fbfa 100%);
  min-width: 0;
}

.location-map-stage.is-viewer-mode {
  touch-action: pan-y;
}

.location-map-stage.is-viewer-mode :deep(.leaflet-container) {
  touch-action: pan-y;
}

.location-map-canvas {
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
}

.location-map-hint {
  position: absolute;
  top: 12px;
  right: 12px;
  left: 12px;
  z-index: 500;
  display: grid;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(183, 203, 199, 0.9);
  backdrop-filter: blur(8px);
  pointer-events: none;
}

.location-map-hint strong {
  color: #1f5c59;
  font-size: 0.86rem;
}

.location-map-hint small {
  color: #5f746f;
  direction: ltr;
  text-align: right;
}

.location-map-alert {
  position: absolute;
  bottom: 12px;
  right: 12px;
  left: 12px;
  z-index: 500;
  padding: 10px 12px;
  border-radius: 14px;
  font-size: 0.84rem;
  font-weight: 700;
}

.location-map-alert.is-danger {
  background: rgba(196, 90, 74, 0.12);
  color: #c45a4a;
}

.location-map-alert.is-success {
  background: rgba(31, 122, 114, 0.12);
  color: #1f7a72;
}

.location-map-label textarea {
  width: 100%;
  min-height: 72px;
  resize: vertical;
  border: 0;
  background: transparent;
  font: inherit;
  color: inherit;
}

@media (max-width: 760px) {
  .location-map-toolbar {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
.leaflet-container {
  width: 100%;
  height: 100%;
  font: inherit;
  background: #eef7f5;
}

.leaflet-pane,
.leaflet-top,
.leaflet-bottom {
  z-index: 10 !important;
}

.leaflet-control-zoom {
  border: 0 !important;
  box-shadow: 0 8px 20px rgba(31, 92, 89, 0.16) !important;
}

.leaflet-control-zoom a {
  width: 34px !important;
  height: 34px !important;
  line-height: 34px !important;
  color: #1f5c59 !important;
  background: rgba(255, 255, 255, 0.95) !important;
}

.attendance-map-marker {
  display: flex !important;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 2px solid #fff;
  box-shadow: 0 10px 22px rgba(31, 92, 89, 0.28);
  background: #34908b;
}

.attendance-map-marker.is-workplace {
  background: #c45a4a;
}

.attendance-map-marker.is-user {
  background: #34908b;
}

.attendance-map-marker-inner {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  font-size: 18px;
  line-height: 1;
}
</style>

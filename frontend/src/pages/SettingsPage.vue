<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, ref } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import LocationMapPicker from '../components/LocationMapPicker.vue'
import ProfileAvatarEditor from '../components/ProfileAvatarEditor.vue'
import SectionHeading from '../components/SectionHeading.vue'
import UserAvatar from '../components/UserAvatar.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const saving = ref(false)
const avatarBusy = ref(false)
const avatarMessage = ref('')
const accessModalOpen = ref(false)
const selectedSectionKey = ref('')
const selectedUserIds = ref([])
const userSearch = ref('')
const sectionSearch = ref('')
const newDepartmentName = ref('')
const activeLetter = ref('همه')
const locationBusy = ref(false)
const locationMessage = ref('')
const scheduleMessage = ref('')
const mapPickerRef = ref(null)
const locationDraft = ref({
  label: '',
  radiusMeters: 20,
  latitude: null,
  longitude: null,
  provinceId: null,
  provinceName: '',
  cityId: null,
  cityName: '',
})

const { clearOwnAvatar, loadSettings, saveSettings, setLastError, state, uploadOwnAvatar, loadTaskingSettings, saveTaskingSettings } = useWorkflowHub()
const taskingMessage = ref('')
const taskingDraft = ref(null)

const selectedSection = computed(() => state.settings.sections.find((item) => item.key === selectedSectionKey.value) || null)
const hasOwnProfilePhoto = computed(() => Boolean(state.currentUser.avatarUrl))
const attendanceLocation = computed(() => state.settings.attendanceLocation || {})
const locationConfigured = computed(() => Boolean(attendanceLocation.value.configured && attendanceLocation.value.latitude != null && attendanceLocation.value.longitude != null))

function syncLocationDraftFromState() {
  const current = state.settings.attendanceLocation || {}
  const geo = state.settings.organizationGeo || {}
  locationDraft.value = {
    label: current.label || '',
    radiusMeters: current.radiusMeters || 20,
    latitude: current.latitude ?? null,
    longitude: current.longitude ?? null,
    provinceId: current.provinceId ?? geo.provinceId ?? null,
    provinceName: current.provinceName || geo.provinceName || '',
    cityId: current.cityId ?? geo.cityId ?? null,
    cityName: current.cityName || geo.cityName || '',
  }
}

const filteredSettingsSections = computed(() => {
  const query = sectionSearch.value.trim().toLowerCase()
  if (!query) return state.settings.sections
  return state.settings.sections.filter((item) =>
    [item.title, item.description, item.key].some((field) => String(field || '').toLowerCase().includes(query)),
  )
})

const availableLetters = computed(() => {
  const letters = new Set(
    (state.settings.organizationUsers || [])
      .map((item) => String(item.name || '').trim().slice(0, 1))
      .filter(Boolean),
  )
  return ['همه', ...[...letters].sort((a, b) => a.localeCompare(b, 'fa'))]
})

const filteredOrganizationUsers = computed(() => {
  const query = userSearch.value.trim().toLowerCase()

  return [...(state.settings.organizationUsers || [])]
    .filter((item) => {
      const firstLetter = String(item.name || '').trim().slice(0, 1)
      const matchesLetter = activeLetter.value === 'همه' || firstLetter === activeLetter.value
      const matchesQuery = !query ||
        ['name', 'role', 'department'].some((field) => String(item[field] || '').toLowerCase().includes(query))
      return matchesLetter && matchesQuery
    })
    .sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), 'fa'))
})

async function persistSettings() {
  if (!state.settings.canEdit || saving.value) return
  saving.value = true
  try {
    await saveSettings({
      organizationName: state.settings.organizationName,
      systemId: state.settings.systemId,
    })
  } finally {
    saving.value = false
  }
}

async function onOwnAvatarSelected(file) {
  if (!file || avatarBusy.value) return
  avatarBusy.value = true
  avatarMessage.value = ''
  try {
    await uploadOwnAvatar(file)
    avatarMessage.value = 'عکس پروفایل با موفقیت ذخیره شد.'
  } catch (error) {
    setLastError(error, 'ذخیره عکس پروفایل ناموفق بود.')
    avatarMessage.value = error?.message || 'ذخیره عکس پروفایل ناموفق بود.'
  } finally {
    avatarBusy.value = false
  }
}

async function onOwnAvatarCleared() {
  if (avatarBusy.value || !hasOwnProfilePhoto.value) return
  avatarBusy.value = true
  avatarMessage.value = ''
  try {
    await clearOwnAvatar()
    avatarMessage.value = 'عکس پروفایل حذف شد.'
  } catch (error) {
    setLastError(error, 'حذف عکس پروفایل ناموفق بود.')
    avatarMessage.value = error?.message || 'حذف عکس پروفایل ناموفق بود.'
  } finally {
    avatarBusy.value = false
  }
}

function openSectionAccess(section) {
  if (!state.settings.canEdit) return
  selectedSectionKey.value = section.key
  selectedUserIds.value = [...(section.allowedUserIds || [])]
  userSearch.value = ''
  activeLetter.value = 'همه'
  accessModalOpen.value = true
}

async function persistSectionAccess() {
  if (!selectedSection.value || saving.value) return
  saving.value = true
  try {
    await saveSettings({
      sectionKey: selectedSection.value.key,
      allowedUserIds: selectedUserIds.value,
    })
    accessModalOpen.value = false
  } finally {
    saving.value = false
  }
}

function isSelected(userId) {
  return selectedUserIds.value.includes(userId)
}

async function persistDepartments() {
  if (!state.settings.canEdit || saving.value) return
  const departments = (state.settings.departments || [])
    .map((item) => ({ id: item.id, code: item.code, name: String(item.name || '').trim() }))
    .filter((item) => item.name)
  const newName = newDepartmentName.value.trim()
  if (newName) departments.push({ name: newName })

  saving.value = true
  try {
    await saveSettings({ departments })
    newDepartmentName.value = ''
  } finally {
    saving.value = false
  }
}

function toggleUser(userId) {
  const next = new Set(selectedUserIds.value)
  if (next.has(userId)) next.delete(userId)
  else next.add(userId)
  selectedUserIds.value = [...next]
}

function removeDepartment(index) {
  if (!state.settings.canEdit || saving.value) return
  state.settings.departments = state.settings.departments.filter((_, itemIndex) => itemIndex !== index)
}

async function captureWorkplaceLocation() {
  if (!state.settings.canEdit || locationBusy.value) return
  locationBusy.value = true
  locationMessage.value = ''
  try {
    await mapPickerRef.value?.locateCurrentPosition?.()
    locationMessage.value = 'موقعیت فعلی روی نقشه قرار گرفت. برای اعمال، ذخیره کنید.'
  } catch (error) {
    locationMessage.value = error?.message || 'دریافت موقعیت مکانی ناموفق بود.'
  } finally {
    locationBusy.value = false
  }
}

async function persistAttendanceLocation() {
  if (!state.settings.canEdit || saving.value) return
  if (locationDraft.value.latitude == null || locationDraft.value.longitude == null) {
    locationMessage.value = 'ابتدا روی نقشه نقطه محل کار را انتخاب کنید یا موقعیت فعلی را بگیرید.'
    return
  }
  saving.value = true
  locationMessage.value = ''
  try {
    await saveSettings({
      attendanceLocation: {
        latitude: Number(locationDraft.value.latitude),
        longitude: Number(locationDraft.value.longitude),
        label: locationDraft.value.label || '',
        radiusMeters: Number(locationDraft.value.radiusMeters) || 20,
        provinceId: locationDraft.value.provinceId || null,
        provinceName: locationDraft.value.provinceName || '',
        cityId: locationDraft.value.cityId || null,
        cityName: locationDraft.value.cityName || '',
      },
    })
    syncLocationDraftFromState()
    locationMessage.value = 'لوکیشن محل کار برای ورود و خروج ذخیره شد.'
  } catch (error) {
    setLastError(error, 'ذخیره لوکیشن محل کار ناموفق بود.')
    locationMessage.value = error?.message || 'ذخیره لوکیشن محل کار ناموفق بود.'
  } finally {
    saving.value = false
  }
}

async function clearAttendanceLocation() {
  if (!state.settings.canEdit || saving.value) return
  saving.value = true
  locationMessage.value = ''
  try {
    await saveSettings({ attendanceLocation: { clear: true } })
    syncLocationDraftFromState()
    locationMessage.value = 'لوکیشن محل کار حذف شد.'
  } catch (error) {
    setLastError(error, 'حذف لوکیشن محل کار ناموفق بود.')
    locationMessage.value = error?.message || 'حذف لوکیشن محل کار ناموفق بود.'
  } finally {
    saving.value = false
  }
}

async function persistWorkSchedule() {
  if (!state.settings.canEdit || saving.value) return
  saving.value = true
  scheduleMessage.value = ''
  try {
    await saveSettings({
      workSchedule: {
        workDayStart: state.settings.workSchedule.workDayStart || '09:00',
        workDayEnd: state.settings.workSchedule.workDayEnd || '17:00',
        monthlyLeaveHours: Number(state.settings.workSchedule.monthlyLeaveHours) || 20,
      },
    })
    scheduleMessage.value = 'ساعات کاری و سهمیه مرخصی ذخیره شد.'
  } catch (error) {
    setLastError(error, 'ذخیره ساعات کاری ناموفق بود.')
    scheduleMessage.value = error?.message || 'ذخیره ساعات کاری ناموفق بود.'
  } finally {
    saving.value = false
  }
}

async function persistTaskingSettings() {
  if (!state.settings.canEdit || saving.value || !taskingDraft.value) return
  saving.value = true
  taskingMessage.value = ''
  try {
    const saved = await saveTaskingSettings(taskingDraft.value)
    taskingDraft.value = { ...saved }
    taskingMessage.value = 'تنظیمات تسکینگ ذخیره شد.'
  } catch (error) {
    setLastError(error, 'ذخیره تنظیمات تسکینگ ناموفق بود.')
    taskingMessage.value = error?.message || 'ذخیره تنظیمات تسکینگ ناموفق بود.'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadSettings(true)
  syncLocationDraftFromState()
  try {
    const settings = await loadTaskingSettings()
    taskingDraft.value = { ...settings }
  } catch {
    taskingDraft.value = null
  }
})
</script>

<template>
  <section class="page-shell enterprise-page">
    <section class="surface-block settings-profile-panel">
      <div class="section-label-row">
        <SectionHeading
          title="پروفایل من"
          description="عکس پروفایل شما در کاربران، تنظیمات و صفحه ورود/خروج نمایش داده می‌شود."
        />
      </div>

      <ProfileAvatarEditor
        :name="state.currentUser.name"
        :avatar="state.currentUser.avatar"
        :avatar-url="state.currentUser.avatarUrl"
        :avatar-file-name="state.currentUser.avatarFileName"
        :busy="avatarBusy"
        title="عکس پروفایل شخصی"
        description="برای اسامی خانم‌ها پس‌زمینه ملایم صورتی و برای آقایان سبز-فیروزه‌ای نمایش داده می‌شود؛ آیکون پروفایل مینیمال و یکدست است."
        @select="onOwnAvatarSelected"
        @clear="onOwnAvatarCleared"
      />
      <p v-if="avatarMessage" class="settings-avatar-note">{{ avatarMessage }}</p>
    </section>

    <section class="dashboard-grid settings-modern-grid">
      <article class="surface-block">
        <div class="section-label-row">
          <SectionHeading
            title="پروفایل سازمان"
            description="اطلاعات هویتی و کدنوم سازمان از همین بخش مدیریت می‌شود."
          />
        </div>

        <div class="settings-stack">
          <label class="field-shell">
            <span>نام سازمان</span>
            <input v-model="state.settings.organizationName" type="text" :readonly="!state.settings.canEdit" />
          </label>

          <label class="field-shell">
            <span>کدنوم سازمان</span>
            <input v-model="state.settings.systemId" type="text" dir="ltr" :readonly="!state.settings.canEdit" />
          </label>

          <button v-if="state.settings.canEdit" class="action-btn tone-primary" type="button" @click="persistSettings">
            <IconlyIcon name="save" decorative />
            <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات' }}</span>
          </button>
        </div>
      </article>

      <article class="surface-block">
        <div class="section-label-row">
          <SectionHeading
            title="خلاصه دسترسی‌ها"
            description="نمای فشرده‌ای از تعداد کاربران مجاز هر بخش."
          />
        </div>

        <div class="progress-list">
          <article v-for="item in state.settings.sections" :key="item.key" class="progress-row">
            <strong>{{ item.title }}</strong>
            <div class="progress-bar">
              <span :style="{ width: `${Math.max(12, ((item.allowedUsers || []).length / Math.max(state.settings.organizationUsers.length, 1)) * 100)}%` }"></span>
            </div>
            <small>{{ (item.allowedUsers || []).length }} نفر</small>
          </article>
        </div>
      </article>
    </section>

    <section class="surface-block attendance-location-panel">
      <div class="section-label-row">
        <SectionHeading
          title="لوکیشن ورود و خروج"
          description="نقشه محل کار را با نشان تنظیم کنید. پرسنل فقط داخل شعاع مجاز می‌توانند ورود و خروج ثبت کنند."
        />
      </div>

      <div class="settings-stack attendance-location-stack">
        <div :class="['attendance-location-status', locationConfigured ? 'is-ready' : 'is-empty']">
          <strong>{{ locationConfigured ? 'لوکیشن محل کار فعال است' : 'لوکیشن محل کار تنظیم نشده' }}</strong>
          <small v-if="locationConfigured">
            شعاع مجاز {{ attendanceLocation.radiusMeters || 20 }} متر
            <template v-if="attendanceLocation.label"> · {{ attendanceLocation.label }}</template>
          </small>
          <small v-else>
            نقشه روی شهر ثبت‌نام مجموعه باز می‌شود. موقعیت فعلی بگیرید یا روی نقشه نقطه را مشخص کنید.
          </small>
        </div>

        <LocationMapPicker
          ref="mapPickerRef"
          v-model="locationDraft"
          mode="picker"
          height="460px"
          :can-edit="state.settings.canEdit"
          :show-radius="true"
        />

        <label class="field-shell">
          <span>شعاع مجاز (متر)</span>
          <input
            v-model.number="locationDraft.radiusMeters"
            type="number"
            min="5"
            max="2000"
            :readonly="!state.settings.canEdit"
          />
        </label>

        <p v-if="locationMessage" class="settings-avatar-note">{{ locationMessage }}</p>

        <div v-if="state.settings.canEdit" class="attendance-location-actions">
          <button class="action-btn tone-soft" type="button" :disabled="locationBusy || saving" @click="captureWorkplaceLocation">
            <IconlyIcon name="profile" decorative />
            <span>{{ locationBusy ? 'در حال دریافت...' : 'موقعیت فعلی شرکت' }}</span>
          </button>
          <button class="action-btn tone-primary" type="button" :disabled="saving || locationBusy" @click="persistAttendanceLocation">
            <IconlyIcon name="save" decorative />
            <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره لوکیشن' }}</span>
          </button>
          <button
            v-if="locationConfigured"
            class="action-btn tone-danger"
            type="button"
            :disabled="saving || locationBusy"
            @click="clearAttendanceLocation"
          >
            <IconlyIcon name="delete" decorative />
            <span>حذف لوکیشن</span>
          </button>
        </div>
      </div>
    </section>

    <section class="surface-block attendance-location-panel">
      <div class="section-label-row">
        <SectionHeading
          title="ساعات کاری و مرخصی"
          description="بازه شیفت روزانه و سهمیه مرخصی ماهانه برای محاسبه اضافه‌کار و گزارش حضور."
        />
      </div>

      <div class="settings-stack">
        <div class="modal-grid two-col">
          <label class="field-shell">
            <span>شروع شیفت</span>
            <input v-model="state.settings.workSchedule.workDayStart" type="time" :readonly="!state.settings.canEdit" />
          </label>
          <label class="field-shell">
            <span>پایان شیفت</span>
            <input v-model="state.settings.workSchedule.workDayEnd" type="time" :readonly="!state.settings.canEdit" />
          </label>
          <label class="field-shell">
            <span>سهمیه مرخصی ماهانه (ساعت)</span>
            <input
              v-model.number="state.settings.workSchedule.monthlyLeaveHours"
              type="number"
              min="0"
              max="320"
              :readonly="!state.settings.canEdit"
            />
          </label>
        </div>
        <p v-if="scheduleMessage" class="settings-avatar-note">{{ scheduleMessage }}</p>
        <button
          v-if="state.settings.canEdit"
          class="action-btn tone-primary"
          type="button"
          :disabled="saving"
          @click="persistWorkSchedule"
        >
          <IconlyIcon name="save" decorative />
          <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره ساعات کاری' }}</span>
        </button>
      </div>
    </section>

    <section v-if="taskingDraft" class="surface-block">
      <div class="section-label-row">
        <SectionHeading
          title="تسکینگ و ظرفیت کاری"
          description="هدف ظرفیت، سقف برنامه‌ریزی، پذیرش ارجاع و قوانین بررسی تسک‌ها."
        />
      </div>

      <div class="settings-stack">
        <div class="modal-grid two-col">
          <label class="field-shell">
            <span>فعال بودن تسکینگ</span>
            <select v-model="taskingDraft.enabled" :disabled="!state.settings.canEdit">
              <option :value="true">فعال</option>
              <option :value="false">غیرفعال</option>
            </select>
          </label>
          <label class="field-shell">
            <span>هدف ظرفیت (%)</span>
            <input v-model.number="taskingDraft.targetUtilizationPercent" type="number" min="50" max="95" :readonly="!state.settings.canEdit" />
          </label>
          <label class="field-shell">
            <span>سقف برنامه‌ریزی (%)</span>
            <input v-model.number="taskingDraft.maxUtilizationPercent" type="number" min="50" max="100" :readonly="!state.settings.canEdit" />
          </label>
          <label class="field-shell">
            <span>حداقل قطعه زمانی (دقیقه)</span>
            <input v-model.number="taskingDraft.minimumSegmentMinutes" type="number" min="5" max="120" :readonly="!state.settings.canEdit" />
          </label>
          <label class="field-shell">
            <span>ارجاع نیازمند پذیرش</span>
            <select v-model="taskingDraft.assignmentRequiresAcceptance" :disabled="!state.settings.canEdit">
              <option :value="true">بله</option>
              <option :value="false">خیر</option>
            </select>
          </label>
          <label class="field-shell">
            <span>پایان کار نیازمند بررسی</span>
            <select v-model="taskingDraft.completionRequiresReview" :disabled="!state.settings.canEdit">
              <option :value="true">بله</option>
              <option :value="false">خیر</option>
            </select>
          </label>
          <label class="field-shell">
            <span>تقسیم تسک بین روزها</span>
            <select v-model="taskingDraft.allowTaskSplitting" :disabled="!state.settings.canEdit">
              <option :value="true">فعال</option>
              <option :value="false">غیرفعال</option>
            </select>
          </label>
          <label class="field-shell">
            <span>شروع شیفت تسکینگ</span>
            <input v-model="taskingDraft.workDayStart" type="time" :readonly="!state.settings.canEdit" />
          </label>
          <label class="field-shell">
            <span>پایان شیفت تسکینگ</span>
            <input v-model="taskingDraft.workDayEnd" type="time" :readonly="!state.settings.canEdit" />
          </label>
        </div>
        <p v-if="taskingMessage" class="settings-avatar-note">{{ taskingMessage }}</p>
        <button
          v-if="state.settings.canEdit"
          class="action-btn tone-primary"
          type="button"
          :disabled="saving"
          @click="persistTaskingSettings"
        >
          <IconlyIcon name="save" decorative />
          <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات تسکینگ' }}</span>
        </button>
      </div>
    </section>

    <section class="surface-block departments-panel">
      <div class="section-label-row">
        <SectionHeading
          title="بخش‌های سازمان"
          description="این فهرست در فرم‌های درخواست، هزینه، سند و کاربران نمایش داده می‌شود."
        />
      </div>

      <div class="settings-stack">
        <div v-for="(department, index) in state.settings.departments" :key="department.id || department.code" class="department-row">
          <div class="department-card">
            <div class="department-card-head">
              <span class="department-code">{{ department.code }}</span>
              <button
                v-if="state.settings.canEdit"
                class="action-btn tone-danger department-delete-btn"
                type="button"
                @click="removeDepartment(index)"
              >
                <IconlyIcon name="delete" decorative />
                <span>حذف</span>
              </button>
            </div>

            <label class="field-shell">
              <span>نام بخش</span>
              <input v-model="department.name" type="text" :readonly="!state.settings.canEdit" />
            </label>
          </div>
        </div>

        <label v-if="state.settings.canEdit" class="field-shell">
          <span>بخش جدید</span>
          <input v-model="newDepartmentName" type="text" placeholder="مثلا فروش، عملیات، مالی..." />
        </label>

        <button v-if="state.settings.canEdit" class="action-btn tone-primary" type="button" @click="persistDepartments">
          <IconlyIcon name="save" decorative />
          <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره بخش‌ها' }}</span>
        </button>
      </div>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <SectionHeading
          title="دسترسی به بخش‌ها"
          description="کاربران مجاز هر بخش را از این جدول جستجو و مدیریت کنید."
        />
      </div>

      <label class="search-shell search-shell-wide settings-section-search">
        <IconlyIcon name="search" decorative />
        <input v-model="sectionSearch" type="text" placeholder="جستجو در بخش‌ها..." />
      </label>

      <div v-if="filteredSettingsSections.length" class="settings-access-table">
        <div class="settings-access-table-head">
          <span>بخش</span>
          <span>شرح</span>
          <span>کاربران مجاز</span>
          <span>عملیات</span>
        </div>

        <button
          v-for="item in filteredSettingsSections"
          :key="item.key"
          class="settings-access-table-row"
          type="button"
          @click="openSectionAccess(item)"
        >
          <strong>{{ item.title }}</strong>
          <span>{{ item.description }}</span>
          <span>{{ (item.allowedUsers || []).length }} نفر</span>
          <span class="table-link">مدیریت</span>
        </button>
      </div>
      <div v-else class="empty-state-inline">
        <IconlyIcon name="rule" decorative />
        <p>{{ state.settings.sections.length ? 'بخشی مطابق جستجو پیدا نشد.' : 'بخشی برای تنظیم دسترسی دریافت نشد.' }}</p>
      </div>
    </section>
  </section>

  <BaseModal :open="accessModalOpen" size="detail" @close="accessModalOpen = false">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">دسترسی بخش</p>
        <h2>{{ selectedSection?.title || 'بخش' }}</h2>
      </div>

      <section class="surface-inline access-directory-panel">
        <div class="filter-toolbar users-filter-toolbar">
          <label class="search-shell search-shell-wide">
            <IconlyIcon name="search" decorative />
            <input v-model="userSearch" type="text" placeholder="جستجو در اعضا..." />
          </label>

          <div class="alphabet-strip">
            <button
              v-for="letter in availableLetters"
              :key="letter"
              :class="['alphabet-chip', activeLetter === letter && 'is-active']"
              type="button"
              @click="activeLetter = letter"
            >
              {{ letter }}
            </button>
          </div>
        </div>

        <div class="access-selection-table">
          <div class="settings-access-table-head">
            <span>وضعیت</span>
            <span>نام</span>
            <span>سمت</span>
            <span>بخش</span>
          </div>

          <button
            v-for="user in filteredOrganizationUsers"
            :key="user.id"
            :class="['access-selection-row', isSelected(user.id) && 'is-selected']"
            type="button"
            @click="toggleUser(user.id)"
          >
            <span class="access-selection-state">{{ isSelected(user.id) ? 'انتخاب شده' : 'انتخاب نشده' }}</span>
            <span class="access-selection-user">
              <UserAvatar
                :name="user.name"
                :avatar="user.avatar"
                :avatar-url="user.avatarUrl"
                size="sm"
              />
              <span class="access-selection-user-copy">
                <strong>{{ user.name }}</strong>
                <small v-if="user.avatarFileName" dir="ltr">{{ user.avatarFileName }}</small>
              </span>
            </span>
            <span>{{ user.role || '-' }}</span>
            <span>{{ user.department || '-' }}</span>
          </button>
        </div>
      </section>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="accessModalOpen = false">
          <IconlyIcon name="close" decorative />
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" type="button" @click="persistSectionAccess">
          <IconlyIcon name="save" decorative />
          <span>{{ saving ? 'در حال ذخیره...' : 'ذخیره دسترسی' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.settings-stack {
  gap: 10px;
}

.settings-profile-panel {
  margin-bottom: 16px;
}

.settings-avatar-note {
  margin: 10px 0 0;
  color: #1f5c59;
  font-size: 0.82rem;
  font-weight: 700;
}

.access-selection-user {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.access-selection-user-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.access-selection-user-copy strong,
.access-selection-user-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.access-selection-user-copy small {
  color: #5f746f;
  font-size: 0.72rem;
}

.settings-modern-grid {
  min-width: 0;
}

.settings-modern-grid .surface-block {
  min-width: 0;
  overflow: hidden;
}

.settings-stack .field-shell,
.progress-list {
  min-width: 0;
}

.settings-stack .field-shell input {
  min-height: 42px;
}

.department-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  padding: 14px;
  border-radius: 14px;
  background: #ffffff;
  border: 0;
  box-shadow: 0 4px 14px rgba(40, 110, 105, 0.1);
}

.department-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.department-code {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  color: #1f5c59;
  background: #dcefec;
}

.department-row .field-shell {
  margin: 0;
  background: #e4f4f2;
  border: 0;
  padding: 8px 12px;
  border-radius: 10px;
}

.department-delete-btn {
  min-height: 32px;
  flex-shrink: 0;
}

.settings-section-search {
  margin-bottom: 14px;
  max-width: 420px;
}

.attendance-location-stack {
  display: grid;
  gap: 12px;
}

.attendance-location-status {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--line, #b7cbc7);
}

.attendance-location-status.is-ready {
  background: rgba(31, 122, 114, 0.1);
  color: #1f5c59;
}

.attendance-location-status.is-empty {
  background: rgba(176, 122, 18, 0.12);
  color: #8a5d0a;
}

.attendance-location-status small {
  color: inherit;
  opacity: 0.9;
}

.attendance-location-coords {
  display: none;
}

.attendance-location-panel {
  overflow: visible;
}

.attendance-location-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 640px) {
  .attendance-location-coords {
    grid-template-columns: 1fr;
  }
}

@media (min-width: 860px) {
  .departments-panel .settings-stack {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    align-items: stretch;
  }
}

</style>

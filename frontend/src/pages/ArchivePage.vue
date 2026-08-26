<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted, ref } from 'vue'

import SectionHeading from '../components/SectionHeading.vue'
import { isoToJalali } from '../utils/jalali'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  state,
  filteredArchiveDocuments,
  loadArchiveDocuments,
  openArchiveDetail,
  downloadProtectedFile,
} = useWorkflowHub()

const scope = ref('all')
const stats = computed(() => state.archive.stats || { total: 0, mine: 0, shared: 0 })

const filteredItems = computed(() => {
  return (filteredArchiveDocuments.value || []).filter((item) => {
    if (scope.value === 'mine' && !item.isOwner) return false
    if (scope.value === 'shared' && !(item.isReferred && !item.isOwner)) return false
    return true
  })
})

const metricCards = computed(() => [
  { key: 'all', label: 'کل اسناد', value: stats.value.total, icon: 'folder_open', tone: 'is-total' },
  { key: 'mine', label: 'اسناد من', value: stats.value.mine, icon: 'badge', tone: 'is-pending' },
  { key: 'shared', label: 'ارجاع‌شده به من', value: stats.value.shared, icon: 'forward', tone: 'is-approved' },
])

function shamsi(value) {
  if (!value) return '-'
  return isoToJalali(String(value).slice(0, 10)) || value
}

function setScope(key) {
  scope.value = key === 'all' ? 'all' : key
}

function openItem(item) {
  openArchiveDetail(item)
}

onMounted(() => {
  void loadArchiveDocuments(true)
})
</script>

<template>
  <section class="page-shell enterprise-page archive-page">
    <section class="metric-grid">
      <button
        v-for="item in metricCards"
        :key="item.key"
        type="button"
        :class="['metric-card', 'approval-metric-card', 'is-filterable', item.tone, scope === item.key && 'is-selected']"
        @click="setScope(item.key)"
      >
        <div class="approval-metric-top">
          <div class="approval-metric-copy">
            <span class="metric-label approval-metric-label">{{ item.label }}</span>
            <strong class="approval-metric-value">{{ item.value }}</strong>
          </div>
          <IconlyIcon :name="item.icon" class="approval-metric-icon" decorative />
        </div>
      </button>
    </section>

    <section class="surface-block archive-table-panel">
      <div class="section-label-row">
        <SectionHeading
          title="فهرست بایگانی"
          :description="`${filteredItems.length} سند با فیلتر فعلی`"
        />
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>نام سند</th>
              <th>تاریخ</th>
              <th>وضعیت</th>
              <th>ثبت‌کننده</th>
              <th>ارجاع</th>
              <th>فایل</th>
              <th>عملیات</th>
            </tr>
          </thead>
          <tbody v-if="filteredItems.length">
            <tr
              v-for="item in filteredItems"
              :key="item.id"
              class="table-click-row"
              tabindex="0"
              @click="openItem(item)"
              @keydown.enter.prevent="openItem(item)"
            >
              <td class="cell-mobile-primary">
                <strong>{{ item.title }}</strong>
                <small>{{ item.description || item.code }}</small>
              </td>
              <td data-label="تاریخ">{{ shamsi(item.documentDate) }}</td>
              <td data-label="وضعیت">
                <span :class="['archive-status-chip', `is-${item.status || 'recorded'}`]">
                  {{ item.statusLabel || 'ثبت شده' }}
                </span>
              </td>
              <td class="cell-mobile-hide">{{ item.ownerName || item.owner?.name || '-' }}</td>
              <td class="cell-mobile-hide">
                <span v-if="item.referralNames?.length">{{ item.referralNames.join('، ') }}</span>
                <span v-else class="table-muted">بدون ارجاع</span>
              </td>
              <td class="cell-mobile-hide">{{ item.fileName || '-' }}</td>
              <td class="cell-mobile-hide">
                <div class="row-actions" @click.stop>
                  <button class="table-link" type="button" @click="openItem(item)">مشاهده</button>
                  <button class="table-link" type="button" @click="downloadProtectedFile(item.downloadUrl, item.fileName)">دانلود</button>
                  <button class="table-link" type="button" @click="openItem(item)">جزئیات</button>
                </div>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="7" class="table-empty">
                <div class="archive-empty">
                  <IconlyIcon name="folder_open" decorative />
                  <strong>سندی با این فیلترها پیدا نشد</strong>
                  <p>فیلترها را تغییر دهید یا از دکمه «ثبت سند بایگانی» بالای صفحه سند جدید ثبت کنید.</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<style scoped>
.archive-page {
  min-width: 0;
}

.archive-page .metric-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.metric-card.is-filterable {
  width: 100%;
  text-align: right;
  cursor: pointer;
  font: inherit;
}

.metric-card.is-filterable.is-selected {
  outline: 2px solid rgba(52, 144, 139, 0.45);
  outline-offset: 1px;
}

.row-actions {
  display: inline-flex;
  gap: 10px;
  flex-wrap: wrap;
}

.archive-status-chip {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 800;
  background: rgba(100, 116, 139, 0.12);
  color: #334155;
}
.archive-status-chip.is-reviewing {
  background: rgba(217, 119, 6, 0.14);
  color: #b45309;
}
.archive-status-chip.is-approved {
  background: rgba(22, 163, 74, 0.14);
  color: #15803d;
}

.archive-empty {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 28px 12px;
  text-align: center;
  color: #5f7a76;
}

.archive-empty strong {
  color: #123735;
  font-size: 1.05rem;
}

.archive-empty p {
  margin: 0;
  max-width: 360px;
  line-height: 1.7;
}

@media (max-width: 720px) {
  .archive-page .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
#app .app-shell:not(.is-auth-route) .archive-page .metric-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
}
@media (max-width: 920px) {
  #app .app-shell:not(.is-auth-route) .archive-page .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}
@media (max-width: 640px) {
  #app .app-shell:not(.is-auth-route) .archive-page .metric-grid {
    grid-template-columns: 1fr !important;
  }
}
</style>

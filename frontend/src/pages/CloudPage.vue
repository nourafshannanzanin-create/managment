<script setup>
import { computed, onMounted } from 'vue'

import { useWorkflowHub } from '../stores/workflowHub'

const { state, loadWalletOptions, openDocumentComposer, openProtectedFile, downloadProtectedFile } = useWorkflowHub()

const canUseCloud = computed(() => state.currentUser.isHq || state.currentUser.menuAccess?.cloud_storage === true)
const cloudOption = computed(() =>
  (state.wallet.options || []).find((item) => (item.featureKey || item.feature_key) === 'cloud_storage') || null,
)
const cloudRetentionText = computed(() =>
  cloudOption.value?.retentionSummary ||
  cloudOption.value?.retention_summary ||
  'داده‌های عملیاتی سامانه به صورت پیش‌فرض تا ۳ ماه نگهداری می‌شوند. با فعال‌سازی فضای ابری، نگهداری کامل داده‌ها تا یک سال انجام می‌شود.',
)
const cloudRetentionDays = computed(() =>
  canUseCloud.value
    ? (cloudOption.value?.retentionDays || cloudOption.value?.retention_days || 365)
    : (cloudOption.value?.includedRetentionDays || cloudOption.value?.included_retention_days || 90),
)
const files = computed(() =>
  (state.approvals || [])
    .filter((item) => item.previewUrl || item.downloadUrl)
    .map((item) => ({
      id: item.id,
      title: item.title,
      owner: item.owner,
      department: item.department,
      status: item.status,
      uploadedAt: item.uploadedAt,
      previewUrl: item.previewUrl,
      downloadUrl: item.downloadUrl,
    })),
)

const stats = computed(() => [
  { label: 'فایل‌ها', value: files.value.length, icon: 'folder_open' },
  { label: 'نگهداری داده', value: `${cloudRetentionDays.value} روز`, icon: 'database' },
  { label: 'منتظر تایید', value: state.approvalMetrics.pending || 0, icon: 'pending_actions' },
  { label: 'تایید شده', value: state.approvalMetrics.approved || 0, icon: 'verified' },
])

onMounted(() => {
  if (state.currentUser.isManager || state.currentUser.canUseHq) void loadWalletOptions()
})
</script>

<template>
  <section class="cloud-page">
    <div v-if="!canUseCloud" class="cloud-empty">
      <span class="material-symbols-outlined">lock</span>
      <strong>فضای ابری برای این مجموعه فعال نیست.</strong>
      <p>{{ cloudRetentionText }}</p>
    </div>

    <template v-else>
      <header class="cloud-head">
        <div>
          <span>Cloud workspace</span>
          <h1>فضای ابری</h1>
          <p>{{ cloudRetentionText }}</p>
        </div>
        <button class="action-btn tone-primary" type="button" @click="openDocumentComposer">
          <span class="material-symbols-outlined">upload_file</span>
          <span>بارگذاری سند</span>
        </button>
      </header>

      <div class="cloud-stats">
        <article v-for="item in stats" :key="item.label">
          <span class="material-symbols-outlined">{{ item.icon }}</span>
          <small>{{ item.label }}</small>
          <strong>{{ item.value }}</strong>
        </article>
      </div>

      <div class="cloud-list">
        <article v-for="file in files" :key="file.id" class="cloud-row">
          <span class="material-symbols-outlined">description</span>
          <div>
            <strong>{{ file.title }}</strong>
            <small>{{ file.owner }} · {{ file.department }} · {{ file.uploadedAt }}</small>
          </div>
          <b>{{ file.status }}</b>
          <button class="icon-btn" type="button" :disabled="!file.previewUrl" @click="openProtectedFile(file.previewUrl, file.title)">
            <span class="material-symbols-outlined">visibility</span>
          </button>
          <button class="icon-btn" type="button" :disabled="!file.downloadUrl" @click="downloadProtectedFile(file.downloadUrl, file.title)">
            <span class="material-symbols-outlined">download</span>
          </button>
        </article>

        <div v-if="!files.length" class="cloud-empty compact">
          <span class="material-symbols-outlined">cloud_upload</span>
          <strong>هنوز فایلی در فضای ابری ثبت نشده است.</strong>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.cloud-page {
  display: grid;
  gap: 18px;
}

.cloud-head {
  min-height: 150px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
  border: 1px solid rgba(40, 122, 110, 0.14);
  border-radius: 8px;
  background: var(--surface, #fff);
}

.cloud-head span,
.cloud-row small,
.cloud-stats small {
  color: #65746f;
  font-weight: 750;
}

.cloud-head h1 {
  margin: 6px 0 0;
  color: #1f4f48;
  font-size: 32px;
}

.cloud-head p,
.cloud-empty p {
  max-width: 760px;
  margin: 8px 0 0;
  color: #3f5f59;
  line-height: 1.9;
  font-weight: 700;
}

.cloud-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.cloud-stats article,
.cloud-row,
.cloud-empty {
  border: 1px solid rgba(34, 82, 75, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: none;
}

.cloud-stats article {
  display: grid;
  gap: 8px;
  min-height: 116px;
  padding: 18px;
}

.cloud-stats .material-symbols-outlined {
  color: #287a6e;
}

.cloud-stats strong {
  color: #1f4f48;
  font-size: 22px;
}

.cloud-list {
  display: grid;
  gap: 10px;
}

.cloud-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto auto;
  align-items: center;
  gap: 12px;
  padding: 14px;
}

.cloud-row > .material-symbols-outlined {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #287a6e;
  background: rgba(40, 122, 110, 0.1);
}

.cloud-row strong {
  color: #193f3a;
}

.cloud-row b {
  color: #287a6e;
  font-size: 12px;
}

.cloud-empty {
  min-height: 260px;
  display: grid;
  place-items: center;
  gap: 10px;
  color: #55706b;
}

.cloud-empty.compact {
  min-height: 190px;
}

@media (max-width: 720px) {
  .cloud-head,
  .cloud-row {
    grid-template-columns: 1fr;
  }

  .cloud-head {
    display: grid;
  }

  .cloud-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>

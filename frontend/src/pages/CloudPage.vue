<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useWorkflowHub } from '../stores/workflowHub'

const router = useRouter()
const { state, loadWalletOptions, openProtectedFile, downloadProtectedFile } = useWorkflowHub()

const canUseCloud = computed(() => state.currentUser.isHq || state.currentUser.menuAccess?.cloud_storage === true)
const cloudOption = computed(() =>
  (state.wallet.options || []).find((item) => (item.featureKey || item.feature_key) === 'cloud_storage') || null,
)
const cloudRetentionText = computed(() =>
  cloudOption.value?.retentionSummary ||
  cloudOption.value?.retention_summary ||
  'بدون فضای ابری، داده‌های عملیاتی مانند گزارش‌ها، هزینه‌ها، تاییدها و گفتگوها تا ۳ ماه نگهداری می‌شوند. با خرید فضای ابری، ثبت تا پایان دوره یک‌ساله فعال می‌ماند. اطلاعات پایه کاربران و تنظیمات همیشه باقی می‌مانند.',
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
      <IconlyIcon name="lock" decorative />
      <strong>فضای ابری برای این مجموعه فعال نیست.</strong>
      <p>{{ cloudRetentionText }}</p>
      <button
        v-if="state.currentUser.isManager || state.currentUser.canUseHq"
        class="action-btn tone-primary"
        type="button"
        @click="router.push('/wallet')"
      >
        <IconlyIcon name="account_balance_wallet" decorative />
        <span>فعال‌سازی از کیف پول</span>
      </button>
    </div>

    <template v-else>
      <header class="cloud-head">
        <div class="cloud-head-copy">
          <h1>فضای ابری</h1>
          <p>{{ cloudRetentionText }}</p>
        </div>
      </header>

      <div class="cloud-stats">
        <article v-for="item in stats" :key="item.label">
          <IconlyIcon :name="item.icon" decorative />
          <small>{{ item.label }}</small>
          <strong>{{ item.value }}</strong>
        </article>
      </div>

      <div class="cloud-list">
        <article v-for="file in files" :key="file.id" class="cloud-row">
          <IconlyIcon name="description" decorative />
          <div class="cloud-row-copy">
            <strong>{{ file.title }}</strong>
            <small>{{ [file.owner, file.department, file.uploadedAt].filter(Boolean).join(' · ') }}</small>
          </div>
          <b class="cloud-row-status">{{ file.status }}</b>
          <div class="cloud-row-actions">
            <button class="icon-btn" type="button" :disabled="!file.previewUrl" @click="openProtectedFile(file.previewUrl, file.title)">
              <IconlyIcon name="visibility" decorative />
            </button>
            <button class="icon-btn" type="button" :disabled="!file.downloadUrl" @click="downloadProtectedFile(file.downloadUrl, file.title)">
              <IconlyIcon name="download" decorative />
            </button>
          </div>
        </article>

        <div v-if="!files.length" class="cloud-empty compact">
          <IconlyIcon name="cloud_done" decorative />
          <strong>هنوز فایلی در فضای ابری ثبت نشده است.</strong>
          <p>اسناد تاییدشده پس از ثبت در بخش تاییدیه‌ها، اینجا نمایش داده می‌شوند.</p>
          <button class="action-btn tone-soft" type="button" @click="router.push('/approvals')">
            <IconlyIcon name="fact_check" decorative />
            <span>رفتن به تاییدیه‌ها</span>
          </button>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.cloud-page {
  display: grid;
  gap: 18px;
  min-width: 0;
}

.cloud-head {
  display: grid;
  gap: 10px;
  padding: 22px 24px;
  border: 1px solid rgba(40, 122, 110, 0.14);
  border-radius: 12px;
  background: var(--surface, #fff);
  min-width: 0;
}

.cloud-head-copy {
  min-width: 0;
  display: grid;
  gap: 8px;
}

.cloud-head h1 {
  margin: 0;
  color: #1f4f48;
  font-size: clamp(1.35rem, 3vw, 1.9rem);
  line-height: 1.35;
}

.cloud-head p,
.cloud-empty p {
  margin: 0;
  color: #3f5f59;
  line-height: 1.8;
  font-weight: 650;
  overflow-wrap: break-word;
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
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  min-width: 0;
}

.cloud-stats article {
  display: grid;
  gap: 8px;
  min-height: 108px;
  padding: 16px;
}

.cloud-stats small,
.cloud-row small {
  color: #65746f;
  font-weight: 700;
}

.cloud-stats strong {
  color: #1f4f48;
  font-size: 1.25rem;
  overflow-wrap: anywhere;
}

.cloud-list {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.cloud-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 12px;
  padding: 14px;
}

.cloud-row > .iconly-shell {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #287a6e;
  background: rgba(40, 122, 110, 0.1);
  flex: 0 0 auto;
}

.cloud-row-copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.cloud-row-copy strong,
.cloud-row-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cloud-row-status {
  color: #287a6e;
  font-size: 12px;
  white-space: nowrap;
}

.cloud-row-actions {
  display: inline-flex;
  gap: 6px;
  flex: 0 0 auto;
}

.cloud-empty {
  min-height: 240px;
  display: grid;
  place-items: center;
  justify-items: center;
  gap: 10px;
  padding: 24px 16px;
  text-align: center;
  color: #55706b;
}

.cloud-empty.compact {
  min-height: 180px;
}

.cloud-empty .action-btn {
  margin-top: 6px;
}

@media (max-width: 920px) {
  .cloud-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .cloud-head {
    padding: 16px;
  }

  .cloud-row {
    grid-template-columns: auto minmax(0, 1fr) auto;
    grid-template-areas:
      "icon copy actions"
      "icon status actions";
  }

  .cloud-row > .iconly-shell { grid-area: icon; }
  .cloud-row-copy { grid-area: copy; }
  .cloud-row-status { grid-area: status; }
  .cloud-row-actions { grid-area: actions; align-self: center; }
}
</style>

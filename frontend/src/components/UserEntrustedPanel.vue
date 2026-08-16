<script setup>
import { computed, reactive, ref, watch } from 'vue'

import IconlyIcon from './base/IconlyIcon.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'
import { formatAmountInput, normalizeAmountValue } from '../utils/amount'
import { formatJalali, getTodayJalali, isoToJalali, jalaliToIso } from '../utils/jalali'

const props = defineProps({
  items: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
  mode: { type: String, default: 'local' }, // local | remote
  defaultOpen: { type: Boolean, default: false },
})

const emit = defineEmits(['add', 'remove', 'update:items'])

const isOpen = ref(Boolean(props.defaultOpen))
const revealKey = ref(0)

const draft = reactive({
  title: '',
  amount: '',
  date: formatJalali(getTodayJalali()),
  description: '',
})

const localError = ref('')

const displayItems = computed(() => (Array.isArray(props.items) ? props.items : []))

const totalAmountLabel = computed(() => {
  const total = displayItems.value.reduce((sum, item) => sum + Number(item.amountRaw || normalizeAmountValue(item.amount) || 0), 0)
  return new Intl.NumberFormat('fa-IR').format(Math.round(total))
})

watch(
  () => props.items,
  () => {
    localError.value = ''
  },
)

function togglePanel() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    revealKey.value += 1
  }
}

function resetDraft() {
  draft.title = ''
  draft.amount = ''
  draft.date = formatJalali(getTodayJalali())
  draft.description = ''
  localError.value = ''
}

function handleAmountInput(value) {
  draft.amount = formatAmountInput(value)
}

function displayDate(item) {
  const iso = String(item?.entrustedAtIso || item?.entrustedAt || item?.date || '').trim()
  if (!iso) return '-'
  if (iso.includes('/')) return iso
  return isoToJalali(iso.slice(0, 10)) || iso
}

function formatListedAmount(item) {
  const raw = Number(item?.amountRaw || normalizeAmountValue(item?.amount) || 0)
  if (!Number.isFinite(raw)) return item?.amount || '۰'
  return new Intl.NumberFormat('fa-IR').format(Math.round(raw))
}

function buildPayload() {
  const title = String(draft.title || '').trim()
  const amount = normalizeAmountValue(draft.amount || 0)
  const description = String(draft.description || '').trim()
  const jalaliDate = String(draft.date || '').trim()
  if (!title) {
    localError.value = 'نام امانت را وارد کنید.'
    return null
  }
  if (!amount || Number(amount) < 0) {
    localError.value = 'مبلغ امانت معتبر نیست.'
    return null
  }
  const isoDate = jalaliToIso(jalaliDate) || jalaliDate
  if (!isoDate) {
    localError.value = 'تاریخ امانت را انتخاب کنید.'
    return null
  }
  return {
    title,
    amount,
    entrustedAt: isoDate,
    entrustedAtIso: isoDate,
    description,
  }
}

async function submitDraft() {
  if (props.disabled || props.busy) return
  const payload = buildPayload()
  if (!payload) return
  localError.value = ''

  if (props.mode === 'remote') {
    emit('add', payload)
    return
  }

  const next = [
    {
      id: `local-${Date.now()}`,
      title: payload.title,
      amount: payload.amount,
      amountRaw: Number(payload.amount),
      entrustedAt: payload.entrustedAt,
      entrustedAtIso: payload.entrustedAtIso,
      description: payload.description,
    },
    ...displayItems.value,
  ]
  emit('update:items', next)
  resetDraft()
}

function onDraftAddedExternally() {
  resetDraft()
}

function removeItem(item) {
  if (props.disabled || props.busy) return
  if (props.mode === 'remote') {
    emit('remove', item)
    return
  }
  emit(
    'update:items',
    displayItems.value.filter((entry) => entry.id !== item.id),
  )
}

defineExpose({ resetDraft, onDraftAddedExternally, open: () => { isOpen.value = true; revealKey.value += 1 }, close: () => { isOpen.value = false } })
</script>

<template>
  <section :class="['entrusted-panel', isOpen && 'is-open']">
    <button
      class="entrusted-toggle"
      type="button"
      :aria-expanded="isOpen ? 'true' : 'false'"
      @click="togglePanel"
    >
      <span class="entrusted-toggle-main">
        <span class="entrusted-toggle-icon" aria-hidden="true">
          <IconlyIcon name="folder_open" decorative />
        </span>
        <span class="entrusted-toggle-copy">
          <strong>امانات</strong>
          <small>ثبت و مدیریت اموال تحویل‌شده به کاربر</small>
        </span>
      </span>

      <span class="entrusted-toggle-meta">
        <span v-if="displayItems.length" class="entrusted-toggle-chip">{{ displayItems.length }} مورد</span>
        <span class="entrusted-toggle-chevron" aria-hidden="true">
          <IconlyIcon :name="isOpen ? 'expand_less' : 'expand_more'" decorative />
        </span>
      </span>
    </button>

    <div class="entrusted-collapse" :aria-hidden="isOpen ? 'false' : 'true'">
      <div class="entrusted-collapse-inner">
        <div :key="revealKey" class="entrusted-body">
          <div class="entrusted-panel-head">
            <p class="entrusted-lead">
              نام، مبلغ، تاریخ و توضیحات امانت را وارد کنید و با دکمه افزودن ثبت کنید.
            </p>
            <div class="entrusted-summary" role="status">
              <div class="entrusted-summary-item">
                <span>تعداد</span>
                <strong>{{ displayItems.length }}</strong>
              </div>
              <span class="entrusted-summary-divider" aria-hidden="true"></span>
              <div class="entrusted-summary-item">
                <span>جمع مبلغ</span>
                <strong>{{ totalAmountLabel }}</strong>
              </div>
            </div>
          </div>

          <div class="entrusted-composer">
            <div class="entrusted-composer-label">افزودن امانت جدید</div>
            <div class="entrusted-composer-grid">
              <label class="field-shell">
                <span>نام امانت</span>
                <input
                  v-model="draft.title"
                  type="text"
                  placeholder="مثلا لپ‌تاپ سازمانی"
                  :disabled="disabled || busy"
                />
              </label>

              <label class="field-shell">
                <span>مبلغ</span>
                <input
                  :value="draft.amount"
                  type="text"
                  inputmode="numeric"
                  placeholder="۰"
                  :disabled="disabled || busy"
                  @input="handleAmountInput($event.target.value)"
                />
              </label>

              <label class="field-shell">
                <span>تاریخ</span>
                <ShamsiDatePicker
                  v-model="draft.date"
                  model-type="jalali"
                  placeholder="انتخاب تاریخ"
                />
              </label>
            </div>

            <label class="field-shell entrusted-note-field">
              <span>توضیحات مربوطه</span>
              <textarea
                v-model="draft.description"
                rows="3"
                placeholder="جزئیات تحویل، سریال، وضعیت و شرایط امانت..."
                :disabled="disabled || busy"
              />
            </label>

            <div class="entrusted-composer-actions">
              <p v-if="localError" class="entrusted-error">{{ localError }}</p>
              <button
                class="action-btn tone-primary entrusted-add-btn"
                type="button"
                :disabled="disabled || busy"
                @click="submitDraft"
              >
                <IconlyIcon name="add_circle" decorative />
                <span>{{ busy ? 'در حال افزودن...' : 'افزودن امانت' }}</span>
              </button>
            </div>
          </div>

          <div v-if="displayItems.length" class="entrusted-list">
            <article v-for="item in displayItems" :key="item.id" class="entrusted-card">
              <div class="entrusted-card-icon">
                <IconlyIcon name="folder_open" decorative />
              </div>
              <div class="entrusted-card-body">
                <div class="entrusted-card-top">
                  <strong>{{ item.title }}</strong>
                  <span class="entrusted-amount">{{ formatListedAmount(item) }}</span>
                </div>
                <div class="entrusted-card-meta">
                  <span>
                    <IconlyIcon name="calendar_month" decorative />
                    {{ displayDate(item) }}
                  </span>
                </div>
                <p v-if="item.description" class="entrusted-card-note">{{ item.description }}</p>
              </div>
              <button
                class="icon-btn entrusted-remove-btn"
                type="button"
                title="حذف امانت"
                :disabled="disabled || busy"
                @click="removeItem(item)"
              >
                <IconlyIcon name="delete" decorative />
              </button>
            </article>
          </div>

          <div v-else class="entrusted-empty">
            <div class="entrusted-empty-icon">
              <IconlyIcon name="folder_open" decorative />
            </div>
            <strong>امانتی ثبت نشده</strong>
            <p>نام، مبلغ، تاریخ و توضیحات را وارد کنید و دکمه افزودن را بزنید.</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.entrusted-panel {
  display: grid;
  gap: 0;
  border-radius: 16px;
  overflow: hidden;
  background:
    radial-gradient(120% 90% at 100% 0%, rgba(52, 144, 139, 0.12), transparent 55%),
    linear-gradient(160deg, rgba(247, 251, 250, 0.98), rgba(228, 244, 242, 0.88));
  border: 1px solid rgba(52, 144, 139, 0.16);
}

.entrusted-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  min-height: 64px;
  padding: 14px 16px;
  border: 0;
  background: transparent;
  cursor: pointer;
  text-align: right;
  color: inherit;
  transition: background 0.22s ease, box-shadow 0.22s ease;
}

.entrusted-toggle:hover {
  background: rgba(255, 255, 255, 0.42);
}

.entrusted-panel.is-open .entrusted-toggle {
  background: rgba(255, 255, 255, 0.55);
  box-shadow: inset 0 -1px 0 rgba(52, 144, 139, 0.12);
}

.entrusted-toggle-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.entrusted-toggle-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  color: #1f5c59;
  background: linear-gradient(160deg, #ffffff, #dcefec);
  border: 1px solid rgba(52, 144, 139, 0.2);
  box-shadow: 0 8px 18px rgba(31, 92, 89, 0.08);
  transition: transform 0.28s ease;
}

.entrusted-panel.is-open .entrusted-toggle-icon {
  transform: scale(1.04);
}

.entrusted-toggle-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.entrusted-toggle-copy strong {
  color: #152523;
  font-size: 1rem;
  font-weight: 800;
}

.entrusted-toggle-copy small {
  color: #5f746f;
  font-size: 0.78rem;
  line-height: 1.5;
}

.entrusted-toggle-meta {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
}

.entrusted-toggle-chip {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
  font-size: 0.75rem;
  font-weight: 800;
}

.entrusted-toggle-chevron {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  color: #1f5c59;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(52, 144, 139, 0.14);
  transition: transform 0.32s cubic-bezier(0.22, 1, 0.36, 1), background 0.22s ease;
}

.entrusted-panel.is-open .entrusted-toggle-chevron {
  transform: rotate(180deg);
  background: #dcefec;
}

.entrusted-collapse {
  display: grid;
  grid-template-rows: 0fr;
  opacity: 0;
  transition:
    grid-template-rows 0.42s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.28s ease;
}

.entrusted-panel.is-open .entrusted-collapse {
  grid-template-rows: 1fr;
  opacity: 1;
}

.entrusted-collapse-inner {
  overflow: hidden;
  min-height: 0;
}

.entrusted-body {
  display: grid;
  gap: 14px;
  padding: 4px 16px 16px;
  transform: translateY(-14px);
  opacity: 0;
  animation: entrusted-rise 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.entrusted-panel:not(.is-open) .entrusted-body {
  animation: none;
}

@keyframes entrusted-rise {
  from {
    opacity: 0;
    transform: translateY(-14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .entrusted-collapse,
  .entrusted-toggle-chevron,
  .entrusted-toggle-icon,
  .entrusted-body {
    transition: none !important;
    animation: none !important;
  }

  .entrusted-body {
    opacity: 1;
    transform: none;
  }
}

.entrusted-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.entrusted-lead {
  margin: 0;
  max-width: 42ch;
  color: #45605c;
  font-size: 0.82rem;
  line-height: 1.7;
}

.entrusted-summary {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-height: 44px;
  padding: 8px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(52, 144, 139, 0.14);
  color: #1f5c59;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.entrusted-summary-item {
  display: grid;
  gap: 2px;
  justify-items: start;
}

.entrusted-summary-item span {
  font-size: 0.72rem;
  font-weight: 700;
  color: #5f746f;
}

.entrusted-summary-item strong {
  font-size: 0.95rem;
  font-weight: 800;
  direction: ltr;
}

.entrusted-summary-divider {
  width: 1px;
  align-self: stretch;
  background: rgba(31, 92, 89, 0.16);
}

.entrusted-composer {
  display: grid;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(52, 144, 139, 0.12);
  box-shadow: 0 10px 24px rgba(31, 92, 89, 0.05);
}

.entrusted-composer-label {
  color: #1f5c59;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.entrusted-composer-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.entrusted-note-field textarea {
  min-height: 88px;
  resize: vertical;
}

.entrusted-composer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.entrusted-error {
  margin: 0;
  color: #b42318;
  font-size: 0.82rem;
  font-weight: 700;
}

.entrusted-add-btn {
  margin-inline-start: auto;
  min-height: 44px;
}

.entrusted-list {
  display: grid;
  gap: 10px;
}

.entrusted-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
  padding: 13px 14px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid rgba(38, 56, 92, 0.08);
  box-shadow: 0 8px 20px rgba(31, 92, 89, 0.06);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.entrusted-card:hover {
  border-color: rgba(52, 144, 139, 0.22);
  box-shadow: 0 12px 26px rgba(31, 92, 89, 0.1);
  transform: translateY(-1px);
}

.entrusted-card-icon {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  background: linear-gradient(160deg, #eef8f6, #dcefec);
  color: #1f5c59;
  border: 1px solid rgba(52, 144, 139, 0.14);
}

.entrusted-card-body {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.entrusted-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.entrusted-card-top strong {
  color: #152523;
  font-size: 0.95rem;
}

.entrusted-amount {
  flex: 0 0 auto;
  padding: 5px 11px;
  border-radius: 999px;
  background: #e4f4f2;
  color: #1f5c59;
  font-size: 0.78rem;
  font-weight: 800;
  direction: ltr;
}

.entrusted-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: #5f746f;
  font-size: 0.78rem;
}

.entrusted-card-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.entrusted-card-note {
  margin: 0;
  color: #45605c;
  font-size: 0.82rem;
  line-height: 1.7;
  white-space: pre-wrap;
  padding-top: 2px;
  border-top: 1px dashed rgba(52, 144, 139, 0.18);
}

.entrusted-remove-btn {
  color: #ab4343;
}

.entrusted-empty {
  display: grid;
  justify-items: center;
  gap: 6px;
  padding: 26px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px dashed rgba(52, 144, 139, 0.28);
  color: #5f746f;
  text-align: center;
}

.entrusted-empty-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  margin-bottom: 4px;
  color: #1f5c59;
  background: rgba(220, 239, 236, 0.9);
}

.entrusted-empty strong {
  color: #203255;
  font-size: 0.92rem;
}

.entrusted-empty p {
  margin: 0;
  max-width: 34ch;
  font-size: 0.82rem;
  line-height: 1.7;
}

@media (max-width: 760px) {
  .entrusted-toggle {
    align-items: flex-start;
  }

  .entrusted-toggle-copy small {
    display: none;
  }

  .entrusted-composer-grid {
    grid-template-columns: 1fr;
  }

  .entrusted-card {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .entrusted-remove-btn {
    grid-column: 1 / -1;
    justify-self: end;
  }

  .entrusted-summary {
    width: 100%;
    justify-content: space-between;
  }
}
</style>

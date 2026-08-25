<script setup>
import { computed } from 'vue'
import { useWorkflowHub } from '../stores/workflowHub'

const props = defineProps({
  page: {
    type: String,
    required: true,
    validator: (value) => ['requests', 'expenses', 'approvals'].includes(value),
  },
})

const { state, updatePageFilter } = useWorkflowHub()

const options = [
  { value: '', label: 'همه' },
  { value: 'pending', label: 'در حال بررسی' },
  { value: 'approved', label: 'تایید شده' },
  { value: 'rejected', label: 'رد شده' },
]

const activeStatus = computed(() => String(state.filters?.[props.page]?.status || ''))

function setStatus(value) {
  updatePageFilter(props.page, 'status', value)
}
</script>

<template>
  <div class="workflow-status-filter" role="group" aria-label="فیلتر وضعیت">
    <button
      v-for="item in options"
      :key="item.value || 'all'"
      type="button"
      :class="['workflow-status-chip', activeStatus === item.value && 'is-active', item.value && `is-${item.value}`]"
      @click="setStatus(item.value)"
    >
      {{ item.label }}
    </button>
  </div>
</template>

<style scoped>
.workflow-status-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 14px;
}

.workflow-status-chip {
  min-height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(52, 144, 139, 0.18);
  background: rgba(255, 255, 255, 0.92);
  color: #4d6662;
  font: inherit;
  font-size: 0.86rem;
  font-weight: 750;
  cursor: pointer;
  transition: background-color 0.16s ease, border-color 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
}

.workflow-status-chip:hover {
  border-color: rgba(52, 144, 139, 0.28);
  color: #1f5c59;
  background: rgba(52, 144, 139, 0.06);
}

.workflow-status-chip.is-active {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, #34908b, #2a7a72);
  box-shadow: 0 8px 18px rgba(45, 122, 110, 0.22);
}

.workflow-status-chip.is-active.is-pending {
  background: linear-gradient(135deg, #d9a441, #b57900);
  box-shadow: 0 8px 18px rgba(181, 121, 0, 0.2);
}

.workflow-status-chip.is-active.is-approved {
  background: linear-gradient(135deg, #22956d, #1b7a59);
  box-shadow: 0 8px 18px rgba(27, 122, 89, 0.2);
}

.workflow-status-chip.is-active.is-rejected {
  background: linear-gradient(135deg, #cd5c5c, #b44646);
  box-shadow: 0 8px 18px rgba(180, 70, 70, 0.2);
}

@media (max-width: 640px) {
  .workflow-status-filter {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .workflow-status-chip {
    width: 100%;
    justify-content: center;
  }
}
</style>

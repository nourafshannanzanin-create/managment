<script setup>
import CompactStatRow from '../components/CompactStatRow.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state, filteredExpenses, toggleSidebar } = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader
      eyebrow="هزینه‌ها"
      title="نمای فشرده هزینه‌ها"
      description="مرور سریع ارقام، پیشرفت و وضعیت ثبت هزینه‌ها."
      :show-search="true"
      :search-value="state.searchQuery"
      search-placeholder="جست‌وجو در عنوان، دسته‌بندی یا مالک هزینه"
      @update:search-value="state.searchQuery = $event"
      @menu="toggleSidebar"
    />

    <CompactStatRow :items="state.expenseSummary" />

    <section class="surface-block">
      <div class="section-label-row">
        <h2>ردیف‌های هزینه</h2>
        <small>{{ filteredExpenses.length }} مورد</small>
      </div>

      <div class="stack-list">
        <article v-for="item in filteredExpenses" :key="item.id" class="list-row expense-row">
          <div class="list-row-main">
            <strong>{{ item.title }}</strong>
            <p>{{ item.category }} · {{ item.owner }} · {{ item.id }}</p>
            <div class="progress-shell">
              <span :style="{ width: `${item.progress}%` }"></span>
            </div>
          </div>
          <div class="list-row-meta">
            <span class="meta-pill strong">{{ item.amount }}</span>
            <span>{{ item.status }}</span>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup>
import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  state,
  expensePeople,
  filteredExpenses,
  openExpenseComposer,
  resetPageFilters,
  toggleSidebar,
  updatePageFilter,
} = useWorkflowHub()
</script>

<template>
  <section class="page-shell expenses-page">
    <PageHeader
      eyebrow="هزینه ها"
      title="ثبت و پیگیری هزینه"
      description="کارمندان فقط هزینه های خودشان را می بینند و مدیرها به کل سازمان دسترسی دارند."
      action-label="ثبت هزینه"
      action-icon="add"
      @action="openExpenseComposer"
      @menu="toggleSidebar"
    />

    <PageFilters
      :query="state.filters.expenses.query"
      :person="state.filters.expenses.person"
      :start-date="state.filters.expenses.startDate"
      :end-date="state.filters.expenses.endDate"
      :people="expensePeople"
      @update:query="updatePageFilter('expenses', 'query', $event)"
      @update:person="updatePageFilter('expenses', 'person', $event)"
      @update:start-date="updatePageFilter('expenses', 'startDate', $event)"
      @update:end-date="updatePageFilter('expenses', 'endDate', $event)"
      @reset="resetPageFilters('expenses')"
    />

    <section class="surface-block">
      <div class="section-label-row">
        <h2>فهرست هزینه ها</h2>
        <small>{{ filteredExpenses.length }} ردیف</small>
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>کد</th>
              <th>شرح</th>
              <th>ثبت کننده</th>
              <th>بخش</th>
              <th>تاریخ</th>
              <th>مبلغ</th>
              <th>وضعیت</th>
              <th>فاکتور</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredExpenses" :key="item.id">
              <td>{{ item.id }}</td>
              <td>
                <strong>{{ item.title }}</strong>
                <small>{{ item.description }}</small>
              </td>
              <td>{{ item.owner }}</td>
              <td>{{ item.department }}</td>
              <td>{{ item.submittedAt }}</td>
              <td>{{ item.amount }}</td>
              <td><span class="meta-pill">{{ item.status }}</span></td>
              <td>
                <a v-if="item.invoiceUrl" :href="item.invoiceUrl" target="_blank" class="table-link">مشاهده</a>
                <span v-else>ندارد</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

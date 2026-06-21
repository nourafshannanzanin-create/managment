<script setup>
import CompactStatRow from '../components/CompactStatRow.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state, toggleSidebar } = useWorkflowHub()
</script>

<template>
  <section class="page-shell dashboard-page">
    <PageHeader
      eyebrow="داشبورد"
      title="نمای کلی عملیات"
      :description="`نمای ${state.currentUser.organization || 'سازمان'} برای ${state.currentUser.name || 'کاربر'}`"
      @menu="toggleSidebar"
    />

    <section class="hero-panel compact-hero">
      <div>
        <h2>گردش کار سازمان</h2>
        <p>وضعیت جاری درخواست ها، هزینه ها و تاییدها در یک نگاه.</p>
      </div>
      <div class="hero-badges">
        <span>{{ state.currentUser.department || 'بدون واحد' }}</span>
        <span>{{ state.currentUser.role || 'کاربر' }}</span>
      </div>
    </section>

    <CompactStatRow :items="state.stats" />

    <div class="dashboard-grid">
      <section class="surface-block">
        <div class="section-label-row">
          <h2>روند هزینه ها</h2>
        </div>
        <div class="mini-chart">
          <div v-for="bar in state.chartData" :key="bar.day" class="mini-chart-column">
            <span :style="{ height: `${Math.max(bar.value, 10)}%` }"></span>
            <small>{{ bar.day }}</small>
          </div>
        </div>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>وضعیت درخواست ها</h2>
        </div>
        <div class="pipeline-grid">
          <article v-for="stage in state.pipeline" :key="stage.label" class="pipeline-card">
            <strong>{{ stage.count }}</strong>
            <p>{{ stage.label }}</p>
          </article>
        </div>
      </section>
    </div>

    <div class="dashboard-grid">
      <section class="surface-block">
        <div class="section-label-row">
          <h2>آخرین فعالیت ها</h2>
        </div>
        <div class="stack-list">
          <article v-for="item in state.activities" :key="item.id" class="list-row">
            <div class="list-row-main">
              <strong>{{ item.user }}</strong>
              <p>{{ item.action }}</p>
            </div>
            <div class="list-row-meta">
              <small>{{ item.time }}</small>
            </div>
          </article>
        </div>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>جمع هزینه</h2>
        </div>
        <div class="spotlight-metrics summary-metrics">
          <article v-for="item in state.expenseSummary" :key="item.label">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

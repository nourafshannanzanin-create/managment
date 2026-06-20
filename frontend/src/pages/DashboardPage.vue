<script setup>
import CompactStatRow from '../components/CompactStatRow.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state, toggleSidebar } = useWorkflowHub()
</script>

<template>
  <section class="page-shell dashboard-page">
    <PageHeader title="مرکز مدیریت کارومند" description="" @menu="toggleSidebar" />

    <section class="hero-panel">
      <h2>داشبورد</h2>
    </section>

    <CompactStatRow :items="state.stats" />

    <div class="content-grid content-grid-dashboard">
      <section class="surface-block chart-block">
        <div class="section-label-row">
          <h2>هزینه‌ها</h2>
        </div>
        <div class="mini-chart">
          <div v-for="bar in state.chartData" :key="bar.day" class="mini-chart-column">
            <span :style="{ height: `${bar.value}%` }"></span>
            <small>{{ bar.day }}</small>
          </div>
        </div>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>وضعیت</h2>
        </div>
        <div class="pipeline-grid">
          <article v-for="stage in state.pipeline" :key="stage.label" class="pipeline-card">
            <strong>{{ stage.count }}</strong>
            <p>{{ stage.label }}</p>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

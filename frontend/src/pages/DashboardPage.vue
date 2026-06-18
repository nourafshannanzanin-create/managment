<script setup>
import CompactStatRow from '../components/CompactStatRow.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state, toggleSidebar } = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader
      eyebrow="پیشخوان"
      title="نمای کلی گردش کار سازمان"
      description="نمایی فشرده از درخواست‌ها، هزینه‌ها، تأییدیه‌ها و فعالیت‌های اخیر."
      @menu="toggleSidebar"
    />

    <CompactStatRow :items="state.stats" />

    <div class="content-grid content-grid-dashboard">
      <section class="surface-block chart-block">
        <div class="section-label-row">
          <h2>روند هزینه هفتگی</h2>
          <small>۷ روز اخیر</small>
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
          <h2>وضعیت گردش کار</h2>
          <small>{{ state.pipeline.length }} مرحله</small>
        </div>
        <div class="inline-list">
          <article v-for="stage in state.pipeline" :key="stage.label" class="inline-row">
            <div>
              <strong>{{ stage.label }}</strong>
              <p>مرحله جاری</p>
            </div>
            <span>{{ stage.count }}</span>
          </article>
        </div>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>فعالیت‌های اخیر</h2>
          <small>آخرین تغییرات</small>
        </div>
        <div class="inline-list">
          <article v-for="item in state.activities" :key="item.id" class="activity-row">
            <span class="material-symbols-outlined activity-symbol">{{ item.icon }}</span>
            <div>
              <strong>{{ item.user }} {{ item.action }}</strong>
              <p>{{ item.detail }}</p>
            </div>
            <small>{{ item.time }}</small>
          </article>
        </div>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>بینش‌های سریع</h2>
          <small>خلاصه مدیریتی</small>
        </div>
        <div class="insight-stream">
          <article v-for="item in state.insights" :key="item" class="insight-row">
            <span class="material-symbols-outlined">flare</span>
            <p>{{ item }}</p>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

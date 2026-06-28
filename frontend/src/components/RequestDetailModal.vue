<script setup>
import BaseModal from './BaseModal.vue'

defineProps({
  open: { type: Boolean, default: false },
  request: { type: Object, default: null },
  timeline: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

defineEmits(['close'])
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div v-if="request" class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">جزئیات درخواست</p>
        <h2>{{ request.title }}</h2>
      </div>

      <section class="detail-meta-grid">
        <div class="detail-meta-item">
          <span>کد</span>
          <strong>{{ request.id }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>- ثبت‌کننده -</span>
          <strong>{{ request.owner }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>مدیر</span>
          <strong>{{ request.manager }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>مدیران</span>
          <strong>{{ request.managerAssignees?.length ? request.managerAssignees.join('، ') : 'تعیین نشده' }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>وضعیت</span>
          <strong>{{ request.status }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>اولویت</span>
          <strong>{{ request.priority }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>تاریخ</span>
          <strong>{{ request.deadline }}</strong>
        </div>
      </section>

      <section class="modal-section">
        <div class="section-label-row">
          <h3>گردش کار</h3>
          <small v-if="loading">در حال بارگذاری...</small>
        </div>
        <div class="timeline-rail">
          <article v-for="item in timeline" :key="`${item.step}-${item.title}`" class="timeline-node">
            <div class="timeline-index">{{ item.step }}</div>
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.note }}</p>
            </div>
          </article>
        </div>
      </section>
    </div>
  </BaseModal>
</template>

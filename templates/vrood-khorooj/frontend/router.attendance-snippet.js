// Add these routes to your Vue router.
export const attendanceRoutes = [
  {
    path: '/attendance/:token',
    name: 'worker-attendance-public',
    component: () => import('./src/views/attendance/WorkerAttendancePunchView.vue'),
    meta: { public: true },
  },
  {
    path: '/manager/attendance',
    name: 'manager-attendance',
    component: () => import('./src/views/manager/AttendanceView.vue'),
    meta: { roles: ['manager', 'admin'] },
  },
]

// Add this menu item for admin and manager navigation:
export const attendanceNavigationItem = {
  label: 'ورود و خروج',
  route: '/manager/attendance',
  iconName: 'calendar',
}

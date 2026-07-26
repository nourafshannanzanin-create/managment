export function createTemplateRouteGuard({
  authStore,
  authApi,
  routeConfig,
  notifyWarning = () => {}
}) {
  return async function templateGuard(to) {
    if (to.meta?.public) {
      return true
    }

    if (!authStore.initialized && !authStore.isAuthenticated) {
      try {
        await authStore.fetchMe(authApi)
      } catch {
        return routeConfig.publicRoutes[0] || '/login'
      }
    }

    if (!authStore.isAuthenticated) {
      return routeConfig.publicRoutes[0] || '/login'
    }

    if (authStore.isHq && to.meta?.tenantOnly) {
      return routeConfig.hqHome
    }

    if (authStore.isLicenseLocked && !routeConfig.licenseSafeRoutes.includes(to.path)) {
      notifyWarning(authStore.licenseStatus.notice || 'دسترسی نرم‌افزار موقتاً قفل شده است.')
      return '/manager/wallet'
    }

    const requiredRoles = Array.isArray(to.meta?.roles) ? to.meta.roles : []
    if (requiredRoles.length && !requiredRoles.includes(authStore.role)) {
      return routeConfig.tenantHomeByRole[authStore.role] || '/'
    }

    const requiredFeature = to.meta?.feature
    if (requiredFeature && authStore.menuAccess?.[requiredFeature] !== true) {
      notifyWarning('این قابلیت برای این کاربر یا این شعبه فعال نیست.')
      return routeConfig.tenantHomeByRole[authStore.role] || '/'
    }

    return true
  }
}

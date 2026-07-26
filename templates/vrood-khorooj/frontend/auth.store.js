import { defineStore } from 'pinia'

export const useTemplateAuthStore = defineStore('template-auth', {
  state: () => ({
    user: null,
    initialized: false
  }),
  getters: {
    role: (state) => state.user?.role || '',
    platformRole: (state) => state.user?.platform_role || '',
    isAuthenticated: (state) => Boolean(state.user?.id),
    isHq: (state) => state.user?.is_hq === true,
    menuAccess: (state) => state.user?.menu_access || {},
    licenseStatus: (state) => state.user?.license_status || {},
    isLicenseLocked: (state) => state.user?.license_status?.is_locked === true
  },
  actions: {
    setUser(user) {
      this.user = user || null
      this.initialized = true
    },
    clear() {
      this.user = null
      this.initialized = true
    },
    async fetchMe(authApi) {
      try {
        const { data } = await authApi.me()
        this.setUser(data)
        return data
      } catch (error) {
        this.clear()
        throw error
      }
    },
    async login(authApi, credentials) {
      const { data } = await authApi.login(credentials)
      this.setUser(data)
      return data
    },
    async logout(authApi) {
      try {
        await authApi.logout()
      } finally {
        this.clear()
      }
    }
  }
})

export function createSupportService(api, endpoints) {
  return {
    list() {
      return api.get(endpoints.list)
    },
    detail(id) {
      return api.get(endpoints.detail(id))
    },
    create(formData) {
      return api.post(endpoints.list, formData)
    },
    reply(id, payload) {
      return api.post(endpoints.reply(id), payload)
    },
    feedback(id, payload) {
      return api.post(endpoints.feedback(id), payload)
    }
  }
}

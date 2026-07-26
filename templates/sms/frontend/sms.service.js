export function createSmsService(api, endpoints) {
  return {
    dashboard() {
      return api.get(endpoints.dashboard)
    },
    listTemplates() {
      return api.get(endpoints.templates)
    },
    createTemplate(payload) {
      return api.post(endpoints.templates, payload)
    },
    sendCampaign(payload) {
      return api.post(endpoints.send, payload)
    },
    sendSimple(payload) {
      return api.post(endpoints.simpleSend, payload)
    }
  }
}

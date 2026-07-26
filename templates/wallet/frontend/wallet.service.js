export function createWalletService(api, endpoints) {
  return {
    dashboard(params = {}) {
      return api.get(endpoints.dashboard, { params })
    },
    options() {
      return api.get(endpoints.options)
    },
    deposit(payload) {
      return api.post(endpoints.deposit, payload)
    },
    startGatewayDeposit(payload) {
      return api.post(endpoints.depositStart, payload)
    },
    withdraw(payload) {
      return api.post(endpoints.withdraw, payload)
    }
  }
}

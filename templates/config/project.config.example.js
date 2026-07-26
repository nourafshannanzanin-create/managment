export const projectConfig = {
  project: {
    id: 'carwash-template',
    name: 'Shared Platform',
    shortName: 'Platform',
    locale: 'fa',
    direction: 'rtl',
    logo: '/assets/logo.svg'
  },
  branding: {
    primaryColor: '#0f5cc0',
    secondaryColor: '#1fb89b',
    dangerColor: '#c85b5b',
    borderRadius: '18px'
  },
  auth: {
    loginPath: '/login',
    meEndpoint: '/auth/me/',
    loginEndpoint: '/auth/login/',
    logoutEndpoint: '/auth/logout/',
    csrfEndpoint: '/auth/csrf/'
  },
  modules: {
    auth: true,
    wallet: true,
    support: true,
    sms: true
  },
  wallet: {
    dashboardEndpoint: '/payments/wallet/dashboard/',
    optionsEndpoint: '/payments/wallet/options/',
    depositEndpoint: '/payments/wallet/deposit/',
    depositStartEndpoint: '/payments/wallet/deposit/start/',
    withdrawEndpoint: '/payments/wallet/withdraw/',
    currencyLabel: 'تومان'
  },
  support: {
    listEndpoint: '/auth/support/tickets/',
    detailEndpoint: (id) => `/auth/support/tickets/${id}/`,
    replyEndpoint: (id) => `/auth/support/tickets/${id}/messages/`,
    feedbackEndpoint: (id) => `/auth/support/tickets/${id}/feedback/`
  },
  sms: {
    dashboardEndpoint: '/notifications/customer-club/',
    sendEndpoint: '/notifications/sms/send/',
    simpleSendEndpoint: '/notifications/sms/simple/',
    templatesEndpoint: '/notifications/sms/templates/',
    groupsEndpoint: '/notifications/customer-groups/'
  }
}

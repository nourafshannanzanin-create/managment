export const routeConfig = {
  publicRoutes: ['/login'],
  hqHome: '/hq',
  tenantHomeByRole: {
    accountant: '/manager/wallet',
    admin: '/',
    manager: '/',
    owner: '/',
    operator: '/',
    worker: '/'
  },
  licenseSafeRoutes: [
    '/login',
    '/support',
    '/manager/wallet',
    '/hq'
  ]
}

import axios from 'axios'

export function createApiClient({
  baseURL = '/api',
  withCredentials = true,
  onUnauthorized = null,
  resolveErrorMessage = null
} = {}) {
  const client = axios.create({
    baseURL,
    withCredentials,
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken'
  })

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = Number(error?.response?.status || 0)
      if ((status === 401 || status === 403) && typeof onUnauthorized === 'function') {
        onUnauthorized(error)
      }
      if (typeof resolveErrorMessage === 'function') {
        error.normalizedMessage = resolveErrorMessage(error)
      }
      return Promise.reject(error)
    }
  )

  return client
}

export async function ensureCsrfToken(client, csrfEndpoint = '/auth/csrf/') {
  await client.get(csrfEndpoint)
}

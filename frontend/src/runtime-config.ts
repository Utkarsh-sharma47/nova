export interface NovaRuntimeConfig {
  apiBaseUrl?: string
  apiAuthToken?: string
}

declare global {
  interface Window {
    __NOVA_RUNTIME__?: NovaRuntimeConfig
  }
}

export function getRuntimeConfig(): NovaRuntimeConfig {
  return window.__NOVA_RUNTIME__ ?? {}
}

export function getRuntimeAuthToken(): string | undefined {
  const runtime = getRuntimeConfig().apiAuthToken
  if (runtime) {
    return runtime
  }
  const buildTime = import.meta.env.VITE_API_AUTH_TOKEN
  return buildTime || undefined
}

export function getRuntimeApiBaseUrl(): string | undefined {
  const runtime = getRuntimeConfig().apiBaseUrl
  if (runtime !== undefined) {
    return runtime
  }
  return undefined
}

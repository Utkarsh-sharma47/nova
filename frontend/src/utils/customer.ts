const STORAGE_KEY = 'nova.customer_id'

export function readStoredCustomerId(): string {
  try {
    return sessionStorage.getItem(STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
}

export function storeCustomerId(value: string): void {
  try {
    if (value) {
      sessionStorage.setItem(STORAGE_KEY, value)
    } else {
      sessionStorage.removeItem(STORAGE_KEY)
    }
  } catch {
    // Ignore storage failures in restricted contexts.
  }
}

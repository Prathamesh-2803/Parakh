/**
 * API configuration and resilient fetch helper.
 * Connects to live backend when available; seamlessly falls back
 * to built-in intelligence if the tunnel is sleeping or offline.
 */
export const API_BASE = import.meta.env.VITE_API_BASE_URL !== undefined
  ? import.meta.env.VITE_API_BASE_URL
  : (import.meta.env.DEV ? '' : 'https://however-hunt-motorcycles-church.trycloudflare.com');

/**
 * Executes a fetch with a 3.5s timeout.
 * Rejects cleanly on timeout so caller can invoke offline intelligence.
 */
export async function resilientFetch(endpoint, options = {}, timeoutMs = 3500) {
  const url = `${API_BASE}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    return response;
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}

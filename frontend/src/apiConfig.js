/**
 * API configuration helper.
 * In development, uses relative path so Vite proxy handles requests.
 * In production on Vercel, uses the live backend URL or VITE_API_BASE_URL env var.
 */
export const API_BASE = import.meta.env.VITE_API_BASE_URL !== undefined
  ? import.meta.env.VITE_API_BASE_URL
  : (import.meta.env.DEV ? '' : 'https://supervision-explaining-casting-arrange.trycloudflare.com');

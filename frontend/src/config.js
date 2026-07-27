// API Configuration — values come from root .env (VITE_* vars)
//
// Production web (Vercel): leave VITE_API_BASE_URL empty at build time; requests use
// window.location.origin so /api/* is same-origin (no separate backend host).
// Local dev: backend on 5000, Vite on 5173 — set VITE_API_BASE_URL or use default below.

function resolveApiBaseUrl() {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    return window.location.origin;
  }
  return 'http://127.0.0.1:5000';
}

function resolvePublicBaseUrl() {
  if (import.meta.env.VITE_PUBLIC_BASE_URL) {
    return import.meta.env.VITE_PUBLIC_BASE_URL;
  }
  return resolveApiBaseUrl();
}

export const API_BASE_URL = resolveApiBaseUrl();

// Public-facing URL for shareable links (WhatsApp, invoices, short links)
export const PUBLIC_BASE_URL = resolvePublicBaseUrl();

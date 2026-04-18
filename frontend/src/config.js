// API Configuration
export const API_BASE_URL = 'https://saloon-management-system-895210689446.europe-west2.run.app';
// export const API_BASE_URL = 'http://127.0.0.1:5000';

// Public-facing URL for shareable links (WhatsApp, etc.)
// Set VITE_PUBLIC_BASE_URL env var to your public domain (e.g., ngrok URL for dev, Cloud Run URL for prod)
export const PUBLIC_BASE_URL = import.meta.env.VITE_PUBLIC_BASE_URL || API_BASE_URL;
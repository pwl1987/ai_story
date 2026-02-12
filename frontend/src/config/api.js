/**
 * Frontend API Configuration File
 *
 * Unified management of all API endpoints and WebSocket connection settings
 * Avoid hard-coding URLs and paths in code
 *
 * Epic: Story 12-6
 * Created: 2026-02-12
 * Fixed: 2026-02-12
 */

export const API_CONFIG = {
  baseURL: process.env.VUE_APP_API_URL || '/api/v1',
  wsURL: process.env.VUE_APP_WS_URL || 'ws://localhost:8000',
  polling: {
    interval: parseInt(process.env.VUE_APP_POLLING_INTERVAL) || 5000,
    maxRetries: parseInt(process.env.VUE_APP_POLLING_MAX_RETRIES) || 10,
    retryDelay: parseInt(process.env.VUE_APP_POLLING_RETRY_DELAY) || 1000,
  },
  endpoints: {
    chapters: '/artworks/chapters',
    scenes: '/artworks/scenes',
    workflow: '/artworks/chapters',
    frames: '/artworks/scenes/{id}/extract-frames',
  },
};

export function getAPIUrl(endpoint) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_CONFIG.baseURL}${cleanEndpoint}`;
}

export function getWebSocketURL(chapterId) {
  const protocol = API_CONFIG.wsURL.startsWith('wss://') ? 'wss:' : 'ws:';
  const host = API_CONFIG.wsURL.replace(`${protocol}//`, '').split('/')[2] || 'localhost:8000';
  return `${protocol}//${host}/ws/artworks/chapters/${chapterId}`;
}

export default {
  API_CONFIG,
  getAPIUrl,
  getWebSocketURL,
};

/**
 * API Client Abstraction Layer
 * ============================
 * 
 * Provides a unified API interface that works in both Electron and Web modes.
 * This enables the React app to be deployed as both:
 * - Electron desktop app (using IPC)
 * - Web app in Docker/Dokploy (using REST + WebSocket)
 */

import { createAPIClient } from './client';
import type { APIClient } from './types';

// Re-export types and client factory
export { createAPIClient, isWebMode } from './client';
export { TerminalWebSocket } from './terminal-client';
export type { APIClient, TerminalClient } from './types';

let _apiClient: APIClient | null = null;

export function getAPIClient(): APIClient {
  if (!_apiClient) {
    _apiClient = createAPIClient();
  }
  return _apiClient;
}

export function resetAPIClient(): void {
  _apiClient = null;
}

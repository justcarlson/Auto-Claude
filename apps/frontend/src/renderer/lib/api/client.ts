/**
 * API Client Factory
 * ==================
 * 
 * Creates the appropriate API client based on the runtime environment:
 * - Electron: Uses window.electronAPI (IPC)
 * - Web: Uses fetch (REST) + WebSocket
 */

import type { APIClient } from './types';

/**
 * Check if we're explicitly in web mode (Dokploy/Docker deployment).
 * This uses the IS_WEB environment variable set by vite.web.config.ts
 * to distinguish from browser-mock development mode.
 */
export function isWebMode(): boolean {
  // IS_WEB is only true in production web builds (Docker/Dokploy)
  // It's NOT set in Electron or browser-mock development
  return import.meta.env.IS_WEB === true || import.meta.env.IS_WEB === 'true';
}

/**
 * Check if running in Electron environment.
 * Note: browser-mock creates window.electronAPI for dev, so we also check IS_WEB.
 */
function isElectron(): boolean {
  // If explicitly web mode, never consider it Electron
  if (isWebMode()) {
    return false;
  }
  return typeof window !== 'undefined' && 
         'electronAPI' in window && 
         window.electronAPI !== undefined;
}

/**
 * Create an API client for the current environment.
 * 
 * @returns APIClient instance (ElectronAPIClient or WebAPIClient)
 */
export function createAPIClient(): APIClient {
  if (isElectron()) {
    // Dynamic import to avoid bundling issues
    const { ElectronAPIClient } = require('./electron-client');
    return new ElectronAPIClient();
  } else {
    const { WebAPIClient } = require('./web-client');
    return new WebAPIClient();
  }
}

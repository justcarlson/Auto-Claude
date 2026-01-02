import { create } from 'zustand';
import type { AppSettings } from '../../shared/types';
import { DEFAULT_APP_SETTINGS } from '../../shared/constants';
import { getAPIClient, isWebMode } from '../lib/api';

interface SettingsState {
  settings: AppSettings;
  isLoading: boolean;
  error: string | null;

  // Actions
  setSettings: (settings: AppSettings) => void;
  updateSettings: (updates: Partial<AppSettings>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: DEFAULT_APP_SETTINGS as AppSettings,
  isLoading: true,  // Start as true since we load settings on app init
  error: null,

  setSettings: (settings) => set({ settings }),

  updateSettings: (updates) =>
    set((state) => ({
      settings: { ...state.settings, ...updates }
    })),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error })
}));

/**
 * Check if settings need migration for onboardingCompleted flag.
 * Existing users (with tokens or projects configured) should have
 * onboardingCompleted set to true to skip the onboarding wizard.
 */
function migrateOnboardingCompleted(settings: AppSettings): AppSettings {
  // Only migrate if onboardingCompleted is undefined (not explicitly set)
  if (settings.onboardingCompleted !== undefined) {
    return settings;
  }

  // Check for signs of an existing user:
  // - Has a Claude OAuth token configured
  // - Has the auto-build source path configured
  const hasOAuthToken = Boolean(settings.globalClaudeOAuthToken);
  const hasAutoBuildPath = Boolean(settings.autoBuildPath);

  const isExistingUser = hasOAuthToken || hasAutoBuildPath;

  if (isExistingUser) {
    // Mark onboarding as completed for existing users
    return { ...settings, onboardingCompleted: true };
  }

  // New user - set to false to trigger onboarding wizard
  return { ...settings, onboardingCompleted: false };
}

export async function loadSettings(): Promise<void> {
  const store = useSettingsStore.getState();
  store.setLoading(true);

  try {
    if (isWebMode()) {
      const api = getAPIClient();
      const result = await api.getSettings() as { success: boolean; data?: AppSettings; error?: string };
      if (result.success && result.data) {
        store.setSettings(result.data);
      }
    } else {
      const result = await window.electronAPI.getSettings();
      if (result.success && result.data) {
        const migratedSettings = migrateOnboardingCompleted(result.data);
        store.setSettings(migratedSettings);

        if (migratedSettings.onboardingCompleted !== result.data.onboardingCompleted) {
          await window.electronAPI.saveSettings({
            onboardingCompleted: migratedSettings.onboardingCompleted
          });
        }
      }
    }
  } catch (error) {
    store.setError(error instanceof Error ? error.message : 'Failed to load settings');
  } finally {
    store.setLoading(false);
  }
}

export async function saveSettings(updates: Partial<AppSettings>): Promise<boolean> {
  const store = useSettingsStore.getState();

  try {
    if (isWebMode()) {
      const api = getAPIClient();
      const result = await api.saveSettings(updates);
      if (result.success) {
        store.updateSettings(updates);
        return true;
      }
      return false;
    } else {
      const result = await window.electronAPI.saveSettings(updates);
      if (result.success) {
        store.updateSettings(updates);
        return true;
      }
      return false;
    }
  } catch {
    return false;
  }
}

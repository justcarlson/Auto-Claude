/**
 * API Client Test Setup
 * =====================
 * 
 * Provides test utilities and RITE Way assertion helpers for API client tests.
 * RITE = Readable, Isolated, Thorough, Explicit
 */

import { vi, expect } from 'vitest';

// =============================================================================
// RITE WAY ASSERTION HELPER
// =============================================================================

interface AssertOptions<T> {
  /** Description of the test preconditions */
  given: string;
  /** Description of expected behavior */
  should: string;
  /** Actual value from test */
  actual: T;
  /** Expected value */
  expected: T;
}

/**
 * RITE Way assertion helper for explicit, readable test assertions.
 * 
 * @example
 * assert({
 *   given: 'a valid project path',
 *   should: 'return project with id',
 *   actual: result.id,
 *   expected: '123'
 * });
 */
export function assert<T>({ given, should, actual, expected }: AssertOptions<T>): void {
  const message = `Given: ${given}\nShould: ${should}`;
  expect(actual, message).toEqual(expected);
}

/**
 * RITE Way assertion for truthy values.
 */
export function assertTruthy<T>({ given, should, actual }: Omit<AssertOptions<T>, 'expected'>): void {
  const message = `Given: ${given}\nShould: ${should}`;
  expect(actual, message).toBeTruthy();
}

/**
 * RITE Way assertion for falsy values.
 */
export function assertFalsy<T>({ given, should, actual }: Omit<AssertOptions<T>, 'expected'>): void {
  const message = `Given: ${given}\nShould: ${should}`;
  expect(actual, message).toBeFalsy();
}

/**
 * RITE Way assertion for arrays containing specific items.
 */
export function assertContains<T>({ given, should, actual, expected }: { 
  given: string; 
  should: string; 
  actual: T[]; 
  expected: T 
}): void {
  const message = `Given: ${given}\nShould: ${should}`;
  expect(actual, message).toContain(expected);
}

/**
 * RITE Way assertion for thrown errors.
 */
export async function assertThrows({ given, should, fn, errorMatch }: {
  given: string;
  should: string;
  fn: () => Promise<unknown> | unknown;
  errorMatch?: string | RegExp;
}): Promise<void> {
  const message = `Given: ${given}\nShould: ${should}`;
  
  if (errorMatch) {
    await expect(fn, message).rejects.toThrow(errorMatch);
  } else {
    await expect(fn, message).rejects.toThrow();
  }
}

// =============================================================================
// MOCK HELPERS
// =============================================================================

/**
 * Create a mock fetch function for testing WebAPIClient.
 */
export function createMockFetch(responses: Map<string, { status: number; data: unknown }>) {
  return vi.fn().mockImplementation(async (url: string, options?: RequestInit) => {
    const key = `${options?.method || 'GET'} ${url}`;
    const response = responses.get(key) || responses.get(url);
    
    if (!response) {
      return {
        ok: false,
        status: 404,
        json: async () => ({ error: 'Not found' }),
      };
    }
    
    return {
      ok: response.status >= 200 && response.status < 300,
      status: response.status,
      json: async () => response.data,
    };
  });
}

/**
 * Create a mock WebSocket for testing TerminalWebSocket.
 */
export function createMockWebSocket() {
  const listeners: Map<string, Set<(event: unknown) => void>> = new Map();
  
  const mockWs = {
    readyState: 1, // OPEN
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn((event: string, callback: (event: unknown) => void) => {
      if (!listeners.has(event)) {
        listeners.set(event, new Set());
      }
      listeners.get(event)!.add(callback);
    }),
    removeEventListener: vi.fn((event: string, callback: (event: unknown) => void) => {
      listeners.get(event)?.delete(callback);
    }),
    // Test helper to simulate receiving a message
    simulateMessage: (data: unknown) => {
      const callbacks = listeners.get('message') || new Set();
      callbacks.forEach(cb => cb({ data: JSON.stringify(data) }));
    },
    // Test helper to simulate connection open
    simulateOpen: () => {
      const callbacks = listeners.get('open') || new Set();
      callbacks.forEach(cb => cb({}));
    },
    // Test helper to simulate error
    simulateError: (error: Error) => {
      const callbacks = listeners.get('error') || new Set();
      callbacks.forEach(cb => cb({ error }));
    },
    // Test helper to simulate close
    simulateClose: (code: number, reason: string) => {
      mockWs.readyState = 3; // CLOSED
      const callbacks = listeners.get('close') || new Set();
      callbacks.forEach(cb => cb({ code, reason }));
    },
  };
  
  return mockWs;
}

/**
 * Create a mock electronAPI for testing ElectronAPIClient.
 */
export function createMockElectronAPI() {
  return {
    getProjects: vi.fn(),
    addProject: vi.fn(),
    removeProject: vi.fn(),
    getTasks: vi.fn(),
    createTask: vi.fn(),
    updateTask: vi.fn(),
    deleteTask: vi.fn(),
    startTask: vi.fn(),
    stopTask: vi.fn(),
    getSettings: vi.fn(),
    saveSettings: vi.fn(),
    // Event listeners
    onTaskProgress: vi.fn(() => vi.fn()),
    onTaskError: vi.fn(() => vi.fn()),
    onTaskLog: vi.fn(() => vi.fn()),
    onTaskStatusChange: vi.fn(() => vi.fn()),
  };
}

// =============================================================================
// TEST DATA FACTORIES
// =============================================================================

/**
 * Create a mock project for testing.
 */
export function createMockProject(overrides: Partial<{ id: string; path: string; name: string }> = {}) {
  return {
    id: 'proj_123',
    path: '/projects/test-app',
    name: 'test-app',
    ...overrides,
  };
}

/**
 * Create a mock task for testing.
 */
export function createMockTask(overrides: Partial<{ 
  id: string; 
  projectId: string;
  title: string; 
  description: string;
  status: string;
}> = {}) {
  return {
    id: 'task_456',
    projectId: 'proj_123',
    title: 'Test Task',
    description: 'A task for testing',
    status: 'pending',
    ...overrides,
  };
}

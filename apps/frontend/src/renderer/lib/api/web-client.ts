/**
 * Web API Client
 * ==============
 * 
 * API client implementation for Web (Docker/Dokploy) environment.
 * Uses fetch for REST and WebSocket for real-time events.
 */

import type { 
  APIClient, 
  APIResult, 
  Project, 
  Task, 
  TaskCreateInput, 
  TaskUpdateInput, 
  TaskStatus,
  AppSettings 
} from './types';

/**
 * WebAPIClient implements the API interface using HTTP fetch and WebSocket.
 * Used when running as a web app in Docker/Dokploy.
 */
export class WebAPIClient implements APIClient {
  private baseUrl: string;
  private wsBaseUrl: string;
  private eventWs: WebSocket | null = null;
  private eventCallbacks: Map<string, Set<(data: unknown) => void>> = new Map();

  constructor(baseUrl = '/api', wsBaseUrl = '/ws') {
    this.baseUrl = baseUrl;
    this.wsBaseUrl = wsBaseUrl;
  }

  // ==========================================================================
  // Health Check
  // ==========================================================================

  async health(): Promise<APIResult<{ status: string; version: string }>> {
    return this.get('/health');
  }

  // ==========================================================================
  // Project Operations
  // ==========================================================================

  async getProjects(): Promise<APIResult<Project[]>> {
    return this.get('/projects');
  }

  async addProject(path: string): Promise<APIResult<Project>> {
    return this.post('/projects', { path });
  }

  async removeProject(projectId: string): Promise<APIResult<void>> {
    return this.delete(`/projects/${projectId}`);
  }

  // ==========================================================================
  // Task Operations
  // ==========================================================================

  async getTasks(projectId: string): Promise<APIResult<Task[]>> {
    return this.get(`/projects/${projectId}/tasks`);
  }

  async createTask(projectId: string, input: TaskCreateInput): Promise<APIResult<Task>> {
    return this.post(`/projects/${projectId}/tasks`, input);
  }

  async getTask(taskId: string): Promise<APIResult<Task>> {
    return this.get(`/tasks/${taskId}`);
  }

  async updateTask(taskId: string, input: TaskUpdateInput): Promise<APIResult<Task>> {
    return this.patch(`/tasks/${taskId}`, input);
  }

  async deleteTask(taskId: string): Promise<APIResult<void>> {
    return this.delete(`/tasks/${taskId}`);
  }

  // Task execution (via WebSocket or POST)
  startTask(taskId: string): void {
    this.post(`/tasks/${taskId}/start`, {}).catch(console.error);
  }

  stopTask(taskId: string): void {
    this.post(`/tasks/${taskId}/stop`, {}).catch(console.error);
  }

  // ==========================================================================
  // Settings
  // ==========================================================================

  async getSettings(): Promise<APIResult<AppSettings>> {
    return this.get('/settings');
  }

  async saveSettings(settings: Partial<AppSettings>): Promise<APIResult<void>> {
    return this.put('/settings', settings);
  }

  // ==========================================================================
  // Event Subscriptions (via WebSocket)
  // ==========================================================================

  onTaskProgress(callback: (taskId: string, progress: unknown) => void): () => void {
    return this.subscribeToEvent('task:progress', (data: unknown) => {
      const { taskId, progress } = data as { taskId: string; progress: unknown };
      callback(taskId, progress);
    });
  }

  onTaskError(callback: (taskId: string, error: string) => void): () => void {
    return this.subscribeToEvent('task:error', (data: unknown) => {
      const { taskId, error } = data as { taskId: string; error: string };
      callback(taskId, error);
    });
  }

  onTaskStatusChange(callback: (taskId: string, status: TaskStatus) => void): () => void {
    return this.subscribeToEvent('task:status', (data: unknown) => {
      const { taskId, status } = data as { taskId: string; status: TaskStatus };
      callback(taskId, status);
    });
  }

  // ==========================================================================
  // HTTP Methods
  // ==========================================================================

  private async get<T>(path: string): Promise<APIResult<T>> {
    return this.request('GET', path);
  }

  private async post<T>(path: string, data: unknown): Promise<APIResult<T>> {
    return this.request('POST', path, data);
  }

  private async put<T>(path: string, data: unknown): Promise<APIResult<T>> {
    return this.request('PUT', path, data);
  }

  private async patch<T>(path: string, data: unknown): Promise<APIResult<T>> {
    return this.request('PATCH', path, data);
  }

  private async delete<T>(path: string): Promise<APIResult<T>> {
    return this.request('DELETE', path);
  }

  private async request<T>(method: string, path: string, data?: unknown): Promise<APIResult<T>> {
    try {
      const options: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (data !== undefined) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(`${this.baseUrl}${path}`, options);
      
      if (!response.ok) {
        const error = await response.text();
        return {
          success: false,
          error: error || `HTTP ${response.status}`,
        };
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return { success: true };
      }

      const result = await response.json();
      return {
        success: true,
        data: result,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // ==========================================================================
  // WebSocket Event System
  // ==========================================================================

  private subscribeToEvent(event: string, callback: (data: unknown) => void): () => void {
    // Ensure WebSocket is connected
    this.ensureEventConnection();

    // Add callback
    if (!this.eventCallbacks.has(event)) {
      this.eventCallbacks.set(event, new Set());
    }
    this.eventCallbacks.get(event)!.add(callback);

    // Return cleanup function
    return () => {
      this.eventCallbacks.get(event)?.delete(callback);
    };
  }

  private ensureEventConnection(): void {
    if (this.eventWs && this.eventWs.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.eventWs = new WebSocket(`${protocol}//${host}${this.wsBaseUrl}/events`);

    this.eventWs.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const callbacks = this.eventCallbacks.get(message.type);
        callbacks?.forEach((cb) => cb(message.data));
      } catch (error) {
        console.error('Failed to parse event message:', error);
      }
    };

    this.eventWs.onclose = () => {
      // Reconnect after delay
      setTimeout(() => this.ensureEventConnection(), 3000);
    };

    this.eventWs.onerror = (error) => {
      console.error('Event WebSocket error:', error);
    };
  }
}

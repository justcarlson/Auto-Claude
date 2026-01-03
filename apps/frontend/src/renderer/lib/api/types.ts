/**
 * API Client Types
 * ================
 * 
 * TypeScript interfaces for the API client abstraction layer.
 * These types define the contract that both ElectronAPIClient and WebAPIClient must implement.
 */

import type { ProjectEnvConfig as SharedProjectEnvConfig } from '../../../shared/types/project';
import type { 
  WorktreeStatus, 
  WorktreeDiff, 
  WorktreeMergeResult, 
  WorktreeListResult 
} from '../../../shared/types/task';

export type ProjectEnvConfig = SharedProjectEnvConfig;
export type { WorktreeStatus, WorktreeDiff, WorktreeMergeResult, WorktreeListResult };

// =============================================================================
// RESULT TYPES
// =============================================================================

/**
 * Standard result wrapper for API responses.
 * Matches the existing IPCResult pattern from Electron.
 */
export interface APIResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

// =============================================================================
// PROJECT TYPES
// =============================================================================

export interface Project {
  id: string;
  path: string;
  name: string;
  settings?: ProjectSettings;
}

export interface ProjectSettings {
  mainBranch?: string;
  parallelAgents?: number;
  autoMerge?: boolean;
}

// =============================================================================
// TASK TYPES
// =============================================================================

export type TaskStatus = 
  | 'pending'
  | 'planning'
  | 'running'
  | 'review'
  | 'completed'
  | 'failed'
  | 'stopped';

export interface Task {
  id: string;
  projectId: string;
  title: string;
  description: string;
  status: TaskStatus;
  specPath?: string;
  createdAt: string;
  updatedAt: string;
}

export interface TaskCreateInput {
  title: string;
  description: string;
}

export interface TaskUpdateInput {
  title?: string;
  description?: string;
  status?: TaskStatus;
}

// =============================================================================
// TERMINAL TYPES
// =============================================================================

export interface TerminalCreateOptions {
  cwd?: string;
  cols?: number;
  rows?: number;
}

export interface TerminalMessage {
  type: 'input' | 'output' | 'resize' | 'connected' | 'error';
  data?: string;
  cols?: number;
  rows?: number;
  terminal_id?: string;
  error?: string;
}

// =============================================================================
// SETTINGS TYPES
// =============================================================================

export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  defaultModel?: string;
  graphitiEnabled?: boolean;
}

// =============================================================================
// API CLIENT INTERFACE
// =============================================================================

/**
 * API Client Interface
 * 
 * This interface defines all methods that must be implemented by both:
 * - ElectronAPIClient (for Electron IPC)
 * - WebAPIClient (for REST + WebSocket)
 * 
 * The interface is intentionally minimal for Phase 1.
 * More methods will be added as features are implemented.
 */
export interface APIClient {
  // Health check
  health(): Promise<APIResult<{ status: string; version: string }>>;
  
  // Project operations
  getProjects(): Promise<APIResult<Project[]>>;
  addProject(path: string): Promise<APIResult<Project>>;
  removeProject(projectId: string): Promise<APIResult<void>>;
  
  // Task operations
  getTasks(projectId: string): Promise<APIResult<Task[]>>;
  createTask(projectId: string, input: TaskCreateInput): Promise<APIResult<Task>>;
  getTask(taskId: string): Promise<APIResult<Task>>;
  updateTask(taskId: string, input: TaskUpdateInput): Promise<APIResult<Task>>;
  deleteTask(taskId: string): Promise<APIResult<void>>;
  
  // Task execution
  startTask(taskId: string, options?: { parallel?: boolean; workers?: number }): void;
  stopTask(taskId: string): void;
  submitReview(taskId: string, approved: boolean, feedback?: string): Promise<APIResult<{ success: boolean; status: string; feedback?: string }>>;
  updateTaskStatus(taskId: string, status: TaskStatus): Promise<APIResult<Task>>;
  checkTaskRunning(taskId: string): Promise<APIResult<boolean>>;
  recoverStuckTask(taskId: string, options?: { targetStatus?: TaskStatus; autoRestart?: boolean }): Promise<APIResult<{ success: boolean; newStatus: string; message: string; autoRestarted?: boolean }>>;
  
  // Settings
  getSettings(): Promise<APIResult<AppSettings>>;
  saveSettings(settings: Partial<AppSettings>): Promise<APIResult<void>>;
  
  // Project environment
  getProjectEnv(projectId: string): Promise<APIResult<ProjectEnvConfig>>;
  updateProjectEnv(projectId: string, config: Partial<ProjectEnvConfig>): Promise<APIResult<ProjectEnvConfig>>;
  
  // Worktree operations
  listWorktrees(projectId: string): Promise<APIResult<WorktreeListResult>>;
  getWorktreeStatus(taskId: string): Promise<APIResult<WorktreeStatus>>;
  getWorktreeDiff(taskId: string): Promise<APIResult<WorktreeDiff>>;
  mergeWorktreePreview(taskId: string): Promise<APIResult<WorktreeMergeResult>>;
  mergeWorktree(taskId: string, options?: { noCommit?: boolean }): Promise<APIResult<WorktreeMergeResult>>;
  discardWorktree(taskId: string): Promise<APIResult<{ success: boolean; message: string }>>;
  
  // Event subscriptions (return cleanup functions)
  onTaskProgress(callback: (taskId: string, progress: unknown) => void): () => void;
  onTaskError(callback: (taskId: string, error: string) => void): () => void;
  onTaskStatusChange(callback: (taskId: string, status: TaskStatus) => void): () => void;
}

// =============================================================================
// TERMINAL CLIENT INTERFACE
// =============================================================================

/**
 * Terminal WebSocket Client Interface
 * 
 * Separate from APIClient because terminal requires persistent WebSocket connection.
 */
export interface TerminalClient {
  readonly terminalId: string;
  readonly connected: boolean;
  
  connect(): void;
  disconnect(): void;
  
  sendInput(data: string): void;
  resize(cols: number, rows: number): void;
  setClaudeSession(sessionId: string): void;
  
  onOutput(callback: (data: string) => void): () => void;
  onConnected(callback: () => void): () => void;
  onDisconnected(callback: (reason?: string) => void): () => void;
  onError(callback: (error: string) => void): () => void;
  onTitle(callback: (title: string) => void): () => void;
  onClaudeSession(callback: (sessionId: string) => void): () => void;
}

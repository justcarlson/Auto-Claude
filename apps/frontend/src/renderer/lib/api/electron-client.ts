import type { 
  APIClient, 
  APIResult, 
  Project, 
  ProjectEnvConfig,
  Task, 
  TaskCreateInput, 
  TaskUpdateInput, 
  TaskStatus,
  AppSettings,
  WorktreeStatus,
  WorktreeDiff,
  WorktreeMergeResult,
  WorktreeListResult,
  GitBranchesResult,
  GitMainBranchResult,
  GitStatusResult,
  GitInitResult,
  DirectoryListResult,
  FileContentResult,
} from './types';

export class ElectronAPIClient implements APIClient {
  private api: typeof window.electronAPI;

  constructor() {
    if (typeof window === 'undefined' || !window.electronAPI) {
      throw new Error('ElectronAPIClient requires window.electronAPI');
    }
    this.api = window.electronAPI;
  }

  async health(): Promise<APIResult<{ status: string; version: string }>> {
    return {
      success: true,
      data: {
        status: 'ok',
        version: 'electron',
      },
    };
  }

  async getProjects(): Promise<APIResult<Project[]>> {
    const result = await this.api.getProjects();
    return this.mapResult<Project[]>(result);
  }

  async addProject(path: string): Promise<APIResult<Project>> {
    const result = await this.api.addProject(path);
    return this.mapResult<Project>(result);
  }

  async removeProject(projectId: string): Promise<APIResult<void>> {
    const result = await this.api.removeProject(projectId);
    return { success: result.success, error: result.error };
  }

  async getTasks(projectId: string): Promise<APIResult<Task[]>> {
    const result = await this.api.getTasks(projectId);
    return this.mapResult<Task[]>(result);
  }

  async createTask(projectId: string, input: TaskCreateInput): Promise<APIResult<Task>> {
    const result = await this.api.createTask(projectId, input.title, input.description);
    return this.mapResult<Task>(result);
  }

  async getTask(_taskId: string): Promise<APIResult<Task>> {
    return {
      success: false,
      error: 'getTask requires project context in Electron mode',
    };
  }

  async updateTask(taskId: string, input: TaskUpdateInput): Promise<APIResult<Task>> {
    if (input.title || input.description) {
      const result = await this.api.updateTask(taskId, { 
        title: input.title, 
        description: input.description 
      });
      return this.mapResult<Task>(result);
    }
    if (input.status) {
      type SharedTaskStatus = import('../../../shared/types').TaskStatus;
      const result = await this.api.updateTaskStatus(taskId, input.status as unknown as SharedTaskStatus);
      return this.mapResult<Task>(result);
    }
    return { success: false, error: 'No updates provided' };
  }

  async deleteTask(taskId: string): Promise<APIResult<void>> {
    const result = await this.api.deleteTask(taskId);
    return { success: result.success, error: result.error };
  }

  startTask(taskId: string, options?: { parallel?: boolean; workers?: number }): void {
    this.api.startTask(taskId, options);
  }

  stopTask(taskId: string): void {
    this.api.stopTask(taskId);
  }

  async submitReview(
    taskId: string, 
    approved: boolean, 
    feedback?: string
  ): Promise<APIResult<{ success: boolean; status: string; feedback?: string }>> {
    const result = await this.api.submitReview(taskId, approved, feedback);
    if (result.success) {
      return { 
        success: true, 
        data: { 
          success: true, 
          status: approved ? 'done' : 'in_progress',
          feedback 
        } 
      };
    }
    return { success: false, error: result.error };
  }

  async updateTaskStatus(taskId: string, status: TaskStatus): Promise<APIResult<Task>> {
    type SharedTaskStatus = import('../../../shared/types').TaskStatus;
    const result = await this.api.updateTaskStatus(taskId, status as unknown as SharedTaskStatus);
    return this.mapResult<Task>(result);
  }

  async checkTaskRunning(taskId: string): Promise<APIResult<boolean>> {
    const result = await this.api.checkTaskRunning(taskId);
    if (result.success) {
      return { success: true, data: result.data === true };
    }
    return { success: false, error: result.error };
  }

  async recoverStuckTask(
    taskId: string, 
    options?: { targetStatus?: TaskStatus; autoRestart?: boolean }
  ): Promise<APIResult<{ success: boolean; newStatus: string; message: string; autoRestarted?: boolean }>> {
    type SharedTaskStatus = import('../../../shared/types').TaskStatus;
    // Convert API TaskStatus to shared TaskStatus for the IPC call
    const ipcOptions = options ? {
      targetStatus: options.targetStatus as unknown as SharedTaskStatus | undefined,
      autoRestart: options.autoRestart
    } : undefined;
    const result = await this.api.recoverStuckTask(taskId, ipcOptions);
    if (result.success && result.data) {
      return { 
        success: true, 
        data: {
          success: true,
          newStatus: result.data.newStatus,
          message: result.data.message,
          autoRestarted: result.data.autoRestarted
        }
      };
    }
    return { success: false, error: result.error };
  }

  async getSettings(): Promise<APIResult<AppSettings>> {
    const result = await this.api.getSettings();
    return this.mapResult<AppSettings>(result);
  }

  async saveSettings(settings: Partial<AppSettings>): Promise<APIResult<void>> {
    const result = await this.api.saveSettings(settings as Record<string, unknown>);
    return { success: result.success, error: result.error };
  }

  async getProjectEnv(projectId: string): Promise<APIResult<ProjectEnvConfig>> {
    const result = await this.api.getProjectEnv(projectId);
    return this.mapResult<ProjectEnvConfig>(result);
  }

  async updateProjectEnv(projectId: string, config: Partial<ProjectEnvConfig>): Promise<APIResult<ProjectEnvConfig>> {
    const result = await this.api.updateProjectEnv(projectId, config as Record<string, unknown>);
    return this.mapResult<ProjectEnvConfig>(result);
  }

  onTaskProgress(callback: (taskId: string, progress: unknown) => void): () => void {
    return this.api.onTaskProgress(callback);
  }

  onTaskError(callback: (taskId: string, error: string) => void): () => void {
    return this.api.onTaskError(callback);
  }

  onTaskStatusChange(callback: (taskId: string, status: TaskStatus) => void): () => void {
    return this.api.onTaskStatusChange(callback as (taskId: string, status: unknown) => void);
  }

  async listWorktrees(projectId: string): Promise<APIResult<WorktreeListResult>> {
    const result = await this.api.listWorktrees(projectId);
    return this.mapResult<WorktreeListResult>(result);
  }

  async getWorktreeStatus(taskId: string): Promise<APIResult<WorktreeStatus>> {
    const result = await this.api.getWorktreeStatus(taskId);
    return this.mapResult<WorktreeStatus>(result);
  }

  async getWorktreeDiff(taskId: string): Promise<APIResult<WorktreeDiff>> {
    const result = await this.api.getWorktreeDiff(taskId);
    return this.mapResult<WorktreeDiff>(result);
  }

  async mergeWorktreePreview(taskId: string): Promise<APIResult<WorktreeMergeResult>> {
    const result = await this.api.mergeWorktreePreview(taskId);
    return this.mapResult<WorktreeMergeResult>(result);
  }

  async mergeWorktree(taskId: string, options?: { noCommit?: boolean }): Promise<APIResult<WorktreeMergeResult>> {
    const result = await this.api.mergeWorktree(taskId, options);
    return this.mapResult<WorktreeMergeResult>(result);
  }

  async discardWorktree(taskId: string): Promise<APIResult<{ success: boolean; message: string }>> {
    const result = await this.api.discardWorktree(taskId);
    return this.mapResult<{ success: boolean; message: string }>(result);
  }

  async getGitBranches(_projectId: string): Promise<APIResult<GitBranchesResult>> {
    return { success: false, error: 'Git branches not available in Electron mode yet' };
  }

  async getGitMainBranch(_projectId: string): Promise<APIResult<GitMainBranchResult>> {
    return { success: false, error: 'Git main branch detection not available in Electron mode yet' };
  }

  async getGitStatus(_projectId: string): Promise<APIResult<GitStatusResult>> {
    return { success: false, error: 'Git status not available in Electron mode yet' };
  }

  async initGitRepo(_projectId: string): Promise<APIResult<GitInitResult>> {
    return { success: false, error: 'Git init not available in Electron mode yet' };
  }

  async listDirectory(_projectId: string, _path?: string): Promise<APIResult<DirectoryListResult>> {
    return { success: false, error: 'Directory listing not available in Electron mode yet' };
  }

  async readFile(_projectId: string, _path: string): Promise<APIResult<FileContentResult>> {
    return { success: false, error: 'File reading not available in Electron mode yet' };
  }

  private mapResult<T>(result: { success: boolean; data?: unknown; error?: string }): APIResult<T> {
    return {
      success: result.success,
      data: result.data as T,
      error: result.error,
    };
  }
}

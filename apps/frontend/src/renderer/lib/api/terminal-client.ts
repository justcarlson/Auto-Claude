/**
 * Terminal WebSocket Client
 * =========================
 * 
 * WebSocket client for terminal sessions.
 * Connects to /ws/terminal/{terminal_id} and handles PTY communication.
 * 
 * Used in web mode (Docker/Dokploy) for terminal functionality.
 */

import type { TerminalClient } from './types';

/**
 * Message types sent to server
 */
interface InputMessage {
  type: 'input';
  data: string;
}

interface ResizeMessage {
  type: 'resize';
  cols: number;
  rows: number;
}

type OutgoingMessage = InputMessage | ResizeMessage;

/**
 * Message types received from server
 */
interface OutputMessage {
  type: 'output';
  data: string;
}

interface ConnectedMessage {
  type: 'connected';
  terminal_id: string;
}

interface ErrorMessage {
  type: 'error';
  data: string;
}

interface PongMessage {
  type: 'pong';
}

type IncomingMessage = OutputMessage | ConnectedMessage | ErrorMessage | PongMessage;

/**
 * TerminalWebSocket implements TerminalClient interface for WebSocket-based terminal access.
 * 
 * @example
 * ```typescript
 * const terminal = new TerminalWebSocket('term_123');
 * 
 * terminal.onOutput((data) => {
 *   console.log(data);
 * });
 * 
 * terminal.onConnected(() => {
 *   terminal.sendInput('ls -la\n');
 * });
 * 
 * terminal.connect();
 * ```
 */
export class TerminalWebSocket implements TerminalClient {
  private readonly _terminalId: string;
  private _connected = false;
  private ws: WebSocket | null = null;
  
  // Callback registrations
  private outputCallbacks: Set<(data: string) => void> = new Set();
  private connectedCallbacks: Set<() => void> = new Set();
  private disconnectedCallbacks: Set<(reason?: string) => void> = new Set();
  private errorCallbacks: Set<(error: string) => void> = new Set();
  
  // Message queue for messages sent before connection
  private messageQueue: OutgoingMessage[] = [];

  constructor(terminalId: string) {
    this._terminalId = terminalId;
  }

  // ==========================================================================
  // Readonly Properties
  // ==========================================================================

  get terminalId(): string {
    return this._terminalId;
  }

  get connected(): boolean {
    return this._connected;
  }

  // ==========================================================================
  // Connection Management
  // ==========================================================================

  connect(): void {
    // Ignore if already connected
    if (this._connected || this.ws) {
      return;
    }

    // Build WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/terminal/${this._terminalId}`;

    this.ws = new WebSocket(url);
    this.setupEventHandlers();
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
    }
  }

  // ==========================================================================
  // Message Sending
  // ==========================================================================

  sendInput(data: string): void {
    this.send({ type: 'input', data });
  }

  resize(cols: number, rows: number): void {
    this.send({ type: 'resize', cols, rows });
  }

  // ==========================================================================
  // Event Subscriptions
  // ==========================================================================

  onOutput(callback: (data: string) => void): () => void {
    this.outputCallbacks.add(callback);
    return () => {
      this.outputCallbacks.delete(callback);
    };
  }

  onConnected(callback: () => void): () => void {
    this.connectedCallbacks.add(callback);
    return () => {
      this.connectedCallbacks.delete(callback);
    };
  }

  onDisconnected(callback: (reason?: string) => void): () => void {
    this.disconnectedCallbacks.add(callback);
    return () => {
      this.disconnectedCallbacks.delete(callback);
    };
  }

  onError(callback: (error: string) => void): () => void {
    this.errorCallbacks.add(callback);
    return () => {
      this.errorCallbacks.delete(callback);
    };
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.addEventListener('open', this.handleOpen.bind(this));
    this.ws.addEventListener('message', this.handleMessage.bind(this));
    this.ws.addEventListener('close', this.handleClose.bind(this));
    this.ws.addEventListener('error', this.handleError.bind(this));
  }

  private handleOpen(): void {
    this._connected = true;
    
    // Notify connected callbacks
    this.connectedCallbacks.forEach((cb) => cb());
    
    // Send queued messages
    this.flushQueue();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data) as IncomingMessage;
      
      switch (message.type) {
        case 'output':
          this.outputCallbacks.forEach((cb) => cb(message.data));
          break;
          
        case 'connected':
          // Server confirmation - already handled by WebSocket open
          break;
          
        case 'error':
          this.errorCallbacks.forEach((cb) => cb(message.data));
          break;
          
        case 'pong':
          // Heartbeat response - no action needed
          break;
      }
    } catch {
      // Invalid JSON - ignore
      console.error('Failed to parse terminal message:', event.data);
    }
  }

  private handleClose(event: CloseEvent): void {
    this._connected = false;
    this.ws = null;
    
    this.disconnectedCallbacks.forEach((cb) => cb(event.reason || undefined));
  }

  private handleError(_event: Event): void {
    this.errorCallbacks.forEach((cb) => cb('WebSocket connection error'));
  }

  private send(message: OutgoingMessage): void {
    if (this._connected && this.ws) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue for later
      this.messageQueue.push(message);
    }
  }

  private flushQueue(): void {
    if (!this._connected || !this.ws) return;
    
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()!;
      this.ws.send(JSON.stringify(message));
    }
  }
}

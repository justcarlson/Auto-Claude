/**
 * TerminalWebSocket Tests
 * =======================
 * 
 * TDD tests for the WebSocket-based terminal client.
 * Tests the connection, messaging, and event handling for terminal sessions.
 */

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { assert, assertTruthy, assertFalsy } from './setup';

// Mock WebSocket instances array to track created instances
interface MockWebSocketInstance {
  url: string;
  readyState: number;
  send: ReturnType<typeof vi.fn>;
  close: ReturnType<typeof vi.fn>;
  addEventListener: ReturnType<typeof vi.fn>;
  removeEventListener: ReturnType<typeof vi.fn>;
  // Event handlers stored for simulation
  _listeners: Map<string, Set<(event: unknown) => void>>;
  // Test helpers
  simulateOpen: () => void;
  simulateMessage: (data: unknown) => void;
  simulateClose: (code: number, reason: string) => void;
  simulateError: (error: Error) => void;
}

const mockWebSocketInstances: MockWebSocketInstance[] = [];

// Create a proper mock WebSocket class
class MockWebSocket implements MockWebSocketInstance {
  url: string;
  readyState = 0; // CONNECTING
  send = vi.fn();
  close = vi.fn();
  addEventListener = vi.fn((event: string, callback: (event: unknown) => void) => {
    if (!this._listeners.has(event)) {
      this._listeners.set(event, new Set());
    }
    this._listeners.get(event)!.add(callback);
  });
  removeEventListener = vi.fn((event: string, callback: (event: unknown) => void) => {
    this._listeners.get(event)?.delete(callback);
  });
  _listeners: Map<string, Set<(event: unknown) => void>> = new Map();

  constructor(url: string) {
    this.url = url;
    mockWebSocketInstances.push(this);
  }

  simulateOpen(): void {
    this.readyState = 1; // OPEN
    const callbacks = this._listeners.get('open') || new Set();
    callbacks.forEach(cb => cb({}));
  }

  simulateMessage(data: unknown): void {
    const callbacks = this._listeners.get('message') || new Set();
    callbacks.forEach(cb => cb({ data: JSON.stringify(data) }));
  }

  simulateClose(code: number, reason: string): void {
    this.readyState = 3; // CLOSED
    const callbacks = this._listeners.get('close') || new Set();
    callbacks.forEach(cb => cb({ code, reason }));
  }

  simulateError(error: Error): void {
    const callbacks = this._listeners.get('error') || new Set();
    callbacks.forEach(cb => cb({ error }));
  }
}

vi.stubGlobal('WebSocket', MockWebSocket);

// Import after mocking
import { TerminalWebSocket } from '../terminal-client';

describe('TerminalWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockWebSocketInstances.length = 0;
    // Mock window.location for URL construction
    vi.stubGlobal('window', {
      location: {
        protocol: 'http:',
        host: 'localhost:8000',
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.stubGlobal('WebSocket', MockWebSocket); // Re-stub for next test
  });

  // ===========================================================================
  // Construction
  // ===========================================================================

  describe('construction', () => {
    test('stores terminal ID', () => {
      // Given: A terminal ID
      // Should: Store and expose it as readonly property
      
      const ws = new TerminalWebSocket('term_123');
      
      assert({
        given: 'a terminal ID on construction',
        should: 'expose terminalId as readonly property',
        actual: ws.terminalId,
        expected: 'term_123',
      });
    });

    test('initializes as not connected', () => {
      // Given: A new TerminalWebSocket instance
      // Should: Start in disconnected state
      
      const ws = new TerminalWebSocket('term_456');
      
      assertFalsy({
        given: 'a new TerminalWebSocket instance',
        should: 'be in disconnected state initially',
        actual: ws.connected,
      });
    });
  });

  // ===========================================================================
  // Connection
  // ===========================================================================

  describe('connect()', () => {
    test('creates WebSocket with correct URL', () => {
      // Given: Terminal ID
      // Should: Connect to /ws/terminal/{id}
      
      const ws = new TerminalWebSocket('term_123');
      ws.connect();
      
      assert({
        given: 'connect() called',
        should: 'create WebSocket to correct endpoint',
        actual: (mockWebSocketInstances[0] as unknown as { url: string }).url,
        expected: 'ws://localhost:8000/ws/terminal/term_123',
      });
    });

    test('uses wss protocol for https', () => {
      // Given: HTTPS location
      // Should: Use wss:// protocol
      
      vi.stubGlobal('window', {
        location: {
          protocol: 'https:',
          host: 'secure.example.com',
        },
      });
      
      const ws = new TerminalWebSocket('term_secure');
      ws.connect();
      
      assert({
        given: 'https protocol',
        should: 'use wss:// for WebSocket',
        actual: (mockWebSocketInstances[0] as unknown as { url: string }).url,
        expected: 'wss://secure.example.com/ws/terminal/term_secure',
      });
    });

    test('calls onConnected callback when WebSocket opens', () => {
      // Given: onConnected callback registered
      // Should: Call it when WebSocket 'open' event fires
      
      const ws = new TerminalWebSocket('term_123');
      const connectedCalls: void[] = [];
      
      ws.onConnected(() => connectedCalls.push(undefined));
      ws.connect();
      
      // Simulate WebSocket open
      mockWebSocketInstances[0].simulateOpen();
      
      assert({
        given: 'WebSocket open event',
        should: 'call onConnected callback once',
        actual: connectedCalls.length,
        expected: 1,
      });
    });

    test('sets connected to true after open', () => {
      // Given: WebSocket connects
      // Should: Set connected = true
      
      const ws = new TerminalWebSocket('term_123');
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      assertTruthy({
        given: 'WebSocket open event',
        should: 'set connected to true',
        actual: ws.connected,
      });
    });

    test('ignores connect() if already connected', () => {
      // Given: Already connected
      // Should: Not create new WebSocket
      
      const ws = new TerminalWebSocket('term_123');
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      ws.connect(); // Second call
      
      assert({
        given: 'connect() called twice',
        should: 'only create one WebSocket',
        actual: mockWebSocketInstances.length,
        expected: 1,
      });
    });
  });

  // ===========================================================================
  // Disconnection
  // ===========================================================================

  describe('disconnect()', () => {
    test('closes WebSocket connection', () => {
      // Given: Connected WebSocket
      // Should: Call close() on disconnect
      
      const ws = new TerminalWebSocket('term_123');
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      ws.disconnect();
      
      assertTruthy({
        given: 'disconnect() called',
        should: 'call WebSocket.close()',
        actual: mockWebSocketInstances[0].close.mock.calls.length > 0,
      });
    });

    test('calls onDisconnected callback', () => {
      // Given: onDisconnected registered, WebSocket closes
      // Should: Call callback with reason
      
      const ws = new TerminalWebSocket('term_123');
      const disconnectReasons: (string | undefined)[] = [];
      
      ws.onDisconnected((reason) => disconnectReasons.push(reason));
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      mockWebSocketInstances[0].simulateClose(1000, 'Normal closure');
      
      assert({
        given: 'WebSocket close event',
        should: 'call onDisconnected with reason',
        actual: disconnectReasons,
        expected: ['Normal closure'],
      });
    });

    test('sets connected to false after close', () => {
      // Given: Connected WebSocket
      // Should: Set connected = false after close
      
      const ws = new TerminalWebSocket('term_123');
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      mockWebSocketInstances[0].simulateClose(1000, '');
      
      assertFalsy({
        given: 'WebSocket close event',
        should: 'set connected to false',
        actual: ws.connected,
      });
    });

    test('handles disconnect when not connected', () => {
      // Given: Not connected
      // Should: Not throw
      
      const ws = new TerminalWebSocket('term_123');
      
      // Should not throw
      expect(() => ws.disconnect()).not.toThrow();
    });
  });

  // ===========================================================================
  // Input/Output
  // ===========================================================================

  describe('sendInput()', () => {
    test('sends input as JSON message', () => {
      // Given: Connected terminal
      // Should: Send { type: "input", data: "..." }
      
      const ws = new TerminalWebSocket('term_123');
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      ws.sendInput('ls -la\n');
      
      const sentData = JSON.parse(mockWebSocketInstances[0].send.mock.calls[0][0]);
      assert({
        given: 'sendInput() called',
        should: 'send JSON with type "input"',
        actual: sentData,
        expected: { type: 'input', data: 'ls -la\n' },
      });
    });

    test('queues input when not connected', () => {
      // Given: Not connected
      // Should: Queue and send after connect
      
      const ws = new TerminalWebSocket('term_123');
      
      ws.sendInput('queued command\n');
      
      // No send yet
      assert({
        given: 'sendInput before connect',
        should: 'not send immediately',
        actual: mockWebSocketInstances.length,
        expected: 0,
      });
      
      // Now connect
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      // Should have sent queued message
      assertTruthy({
        given: 'after connection established',
        should: 'send queued input',
        actual: mockWebSocketInstances[0].send.mock.calls.length > 0,
      });
    });
  });

  describe('onOutput()', () => {
    test('calls callback when output message received', () => {
      // Given: onOutput callback registered
      // Should: Call with data when server sends output
      
      const ws = new TerminalWebSocket('term_123');
      const outputs: string[] = [];
      
      ws.onOutput((data) => outputs.push(data));
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      mockWebSocketInstances[0].simulateMessage({ type: 'output', data: 'Hello World\n' });
      
      assert({
        given: 'output message from server',
        should: 'call onOutput callback with data',
        actual: outputs,
        expected: ['Hello World\n'],
      });
    });

    test('handles multiple outputs', () => {
      // Given: Multiple output messages
      // Should: Call callback for each
      
      const ws = new TerminalWebSocket('term_123');
      const outputs: string[] = [];
      
      ws.onOutput((data) => outputs.push(data));
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      mockWebSocketInstances[0].simulateMessage({ type: 'output', data: 'line1\n' });
      mockWebSocketInstances[0].simulateMessage({ type: 'output', data: 'line2\n' });
      mockWebSocketInstances[0].simulateMessage({ type: 'output', data: 'line3\n' });
      
      assert({
        given: 'multiple output messages',
        should: 'call onOutput for each',
        actual: outputs,
        expected: ['line1\n', 'line2\n', 'line3\n'],
      });
    });

    test('returns unsubscribe function', () => {
      // Given: onOutput with unsubscribe
      // Should: Stop receiving after unsubscribe
      
      const ws = new TerminalWebSocket('term_123');
      const outputs: string[] = [];
      
      const unsubscribe = ws.onOutput((data) => outputs.push(data));
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      mockWebSocketInstances[0].simulateMessage({ type: 'output', data: 'before\n' });
      
      unsubscribe();
      
      mockWebSocketInstances[0].simulateMessage({ type: 'output', data: 'after\n' });
      
      assert({
        given: 'unsubscribe called',
        should: 'stop receiving outputs',
        actual: outputs,
        expected: ['before\n'],
      });
    });
  });

  // ===========================================================================
  // Resize
  // ===========================================================================

  describe('resize()', () => {
    test('sends resize message', () => {
      // Given: Connected terminal
      // Should: Send { type: "resize", cols, rows }
      
      const ws = new TerminalWebSocket('term_123');
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      ws.resize(120, 40);
      
      const sentData = JSON.parse(mockWebSocketInstances[0].send.mock.calls[0][0]);
      assert({
        given: 'resize() called',
        should: 'send JSON with type "resize"',
        actual: sentData,
        expected: { type: 'resize', cols: 120, rows: 40 },
      });
    });
  });

  // ===========================================================================
  // Error Handling
  // ===========================================================================

  describe('error handling', () => {
    test('calls onError when WebSocket error occurs', () => {
      // Given: onError callback registered
      // Should: Call it when WebSocket error event fires
      
      const ws = new TerminalWebSocket('term_123');
      const errors: string[] = [];
      
      ws.onError((error) => errors.push(error));
      ws.connect();
      
      mockWebSocketInstances[0].simulateError(new Error('Connection failed'));
      
      assertTruthy({
        given: 'WebSocket error event',
        should: 'call onError callback',
        actual: errors.length > 0,
      });
    });

    test('calls onError when server sends error message', () => {
      // Given: Server sends error type message
      // Should: Call onError callback
      
      const ws = new TerminalWebSocket('term_123');
      const errors: string[] = [];
      
      ws.onError((error) => errors.push(error));
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      mockWebSocketInstances[0].simulateMessage({ type: 'error', data: 'Terminal not found' });
      
      assert({
        given: 'error message from server',
        should: 'call onError with error data',
        actual: errors,
        expected: ['Terminal not found'],
      });
    });
  });

  // ===========================================================================
  // Multiple Callbacks
  // ===========================================================================

  describe('multiple callbacks', () => {
    test('supports multiple onOutput callbacks', () => {
      // Given: Multiple onOutput callbacks
      // Should: Call all of them
      
      const ws = new TerminalWebSocket('term_123');
      const outputs1: string[] = [];
      const outputs2: string[] = [];
      
      ws.onOutput((data) => outputs1.push(data));
      ws.onOutput((data) => outputs2.push(data));
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      mockWebSocketInstances[0].simulateMessage({ type: 'output', data: 'test\n' });
      
      assert({
        given: 'multiple onOutput callbacks',
        should: 'call first callback',
        actual: outputs1,
        expected: ['test\n'],
      });
      
      assert({
        given: 'multiple onOutput callbacks',
        should: 'call second callback',
        actual: outputs2,
        expected: ['test\n'],
      });
    });
  });

  // ===========================================================================
  // Connected Message Handling
  // ===========================================================================

  describe('connected message', () => {
    test('handles connected message from server', () => {
      // Given: Server sends connected confirmation
      // Should: Update internal state
      
      const ws = new TerminalWebSocket('term_123');
      const connectedCalls: void[] = [];
      
      ws.onConnected(() => connectedCalls.push(undefined));
      ws.connect();
      mockWebSocketInstances[0].simulateOpen();
      
      // Server also sends connected message
      mockWebSocketInstances[0].simulateMessage({ type: 'connected', terminal_id: 'term_123' });
      
      // onConnected should have been called (from WebSocket open)
      assert({
        given: 'WebSocket open + connected message',
        should: 'call onConnected at least once',
        actual: connectedCalls.length >= 1,
        expected: true,
      });
    });
  });
});

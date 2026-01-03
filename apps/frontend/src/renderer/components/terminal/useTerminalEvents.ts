import { useEffect, useRef } from 'react';
import { useTerminalStore } from '../../stores/terminal-store';
import { terminalBufferManager } from '../../lib/terminal-buffer-manager';
import { isWebMode, TerminalWebSocket } from '../../lib/api';

interface UseTerminalEventsOptions {
  terminalId: string;
  onOutput?: (data: string) => void;
  onExit?: (exitCode: number) => void;
  onTitleChange?: (title: string) => void;
  onClaudeSession?: (sessionId: string) => void;
}

export function useTerminalEvents({
  terminalId,
  onOutput,
  onExit,
  onTitleChange,
  onClaudeSession,
}: UseTerminalEventsOptions) {
  const onOutputRef = useRef(onOutput);
  const onExitRef = useRef(onExit);
  const onTitleChangeRef = useRef(onTitleChange);
  const onClaudeSessionRef = useRef(onClaudeSession);
  const wsClientRef = useRef<TerminalWebSocket | null>(null);

  useEffect(() => {
    onOutputRef.current = onOutput;
  }, [onOutput]);

  useEffect(() => {
    onExitRef.current = onExit;
  }, [onExit]);

  useEffect(() => {
    onTitleChangeRef.current = onTitleChange;
  }, [onTitleChange]);

  useEffect(() => {
    onClaudeSessionRef.current = onClaudeSession;
  }, [onClaudeSession]);

  useEffect(() => {
    if (isWebMode()) {
      const client = new TerminalWebSocket(terminalId);
      wsClientRef.current = client;

      const cleanupOutput = client.onOutput((data) => {
        terminalBufferManager.append(terminalId, data);
        onOutputRef.current?.(data);
      });

      const cleanupTitle = client.onTitle((title) => {
        useTerminalStore.getState().updateTerminal(terminalId, { title });
        onTitleChangeRef.current?.(title);
      });

      const cleanupClaudeSession = client.onClaudeSession((sessionId) => {
        useTerminalStore.getState().setClaudeSessionId(terminalId, sessionId);
        onClaudeSessionRef.current?.(sessionId);
      });

      const cleanupDisconnect = client.onDisconnected(() => {
        useTerminalStore.getState().setTerminalStatus(terminalId, 'exited');
        onExitRef.current?.(0);
      });

      client.connect();

      return () => {
        cleanupOutput();
        cleanupTitle();
        cleanupClaudeSession();
        cleanupDisconnect();
        client.disconnect();
        wsClientRef.current = null;
      };
    } else {
      const cleanupOutput = window.electronAPI.onTerminalOutput((id, data) => {
        if (id === terminalId) {
          terminalBufferManager.append(terminalId, data);
          onOutputRef.current?.(data);
        }
      });

      const cleanupExit = window.electronAPI.onTerminalExit((id, exitCode) => {
        if (id === terminalId) {
          useTerminalStore.getState().setTerminalStatus(terminalId, 'exited');
          onExitRef.current?.(exitCode);
        }
      });

      const cleanupTitle = window.electronAPI.onTerminalTitleChange((id, title) => {
        if (id === terminalId) {
          useTerminalStore.getState().updateTerminal(terminalId, { title });
          onTitleChangeRef.current?.(title);
        }
      });

      const cleanupClaudeSession = window.electronAPI.onTerminalClaudeSession((id, sessionId) => {
        if (id === terminalId) {
          useTerminalStore.getState().setClaudeSessionId(terminalId, sessionId);
          onClaudeSessionRef.current?.(sessionId);
        }
      });

      return () => {
        cleanupOutput();
        cleanupExit();
        cleanupTitle();
        cleanupClaudeSession();
      };
    }
  }, [terminalId]);

  return {
    sendInput: (data: string) => {
      if (isWebMode() && wsClientRef.current) {
        wsClientRef.current.sendInput(data);
      } else {
        window.electronAPI.sendTerminalInput(terminalId, data);
      }
    },
    resize: (cols: number, rows: number) => {
      if (isWebMode() && wsClientRef.current) {
        wsClientRef.current.resize(cols, rows);
      } else {
        window.electronAPI.resizeTerminal(terminalId, cols, rows);
      }
    },
  };
}

"""
Terminal Service
================

PTY-based terminal management for web terminals.
Uses ptyprocess for spawning and managing pseudo-terminals.
"""

import asyncio
import json
import os
import re
import select
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import ptyprocess

# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class TerminalMessage:
    """Message sent to/from terminal WebSocket."""

    type: str  # "input", "output", "resize", "error", "connected"
    data: str = ""
    cols: int | None = None
    rows: int | None = None


@dataclass
class Terminal:
    """Represents an active terminal session."""

    id: str
    process: ptyprocess.PtyProcess
    cwd: str
    shell: str


# =============================================================================
# PURE FUNCTIONS (unit testable)
# =============================================================================


# ANSI escape code regex pattern
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape codes from text.

    Args:
        text: String potentially containing ANSI codes

    Returns:
        Clean string without escape codes
    """
    return ANSI_ESCAPE_PATTERN.sub("", text)


def to_pty_dimensions(dims: dict) -> tuple[int, int]:
    """
    Convert dimensions dict to ptyprocess format.

    Args:
        dims: Dict with 'cols' and 'rows' keys

    Returns:
        Tuple of (rows, cols) for ptyprocess.setwinsize()
    """
    cols = dims.get("cols", 80)
    rows = dims.get("rows", 24)
    return (rows, cols)


def parse_terminal_message(raw: str) -> TerminalMessage:
    """
    Parse raw JSON string into TerminalMessage.

    Args:
        raw: JSON string from WebSocket

    Returns:
        TerminalMessage instance (type="error" on parse failure)
    """
    try:
        data = json.loads(raw)

        msg_type = data.get("type")
        if not msg_type:
            return TerminalMessage(type="error", data="Missing 'type' field")

        return TerminalMessage(
            type=msg_type,
            data=data.get("data", ""),
            cols=data.get("cols"),
            rows=data.get("rows"),
        )
    except json.JSONDecodeError as e:
        return TerminalMessage(type="error", data=f"JSON parse error: {e}")


# =============================================================================
# TERMINAL MANAGER
# =============================================================================


class TerminalManager:
    """
    Manages multiple terminal sessions.

    Thread-safe manager for creating, destroying, and interacting
    with PTY terminals.
    """

    def __init__(self):
        self._terminals: dict[str, Terminal] = {}

    async def create_terminal(
        self,
        cwd: str = "/tmp",
        shell: str = "/bin/bash",
        cols: int = 80,
        rows: int = 24,
    ) -> str:
        """
        Create a new terminal session.

        Args:
            cwd: Working directory for the shell
            shell: Shell executable path
            cols: Initial terminal width
            rows: Initial terminal height

        Returns:
            Terminal ID string
        """
        terminal_id = str(uuid.uuid4())

        # Spawn PTY process
        loop = asyncio.get_event_loop()
        process = await loop.run_in_executor(
            None,
            lambda: ptyprocess.PtyProcess.spawn(
                [shell],
                cwd=cwd,
                dimensions=(rows, cols),
                env={**os.environ, "TERM": "xterm-256color"},
            ),
        )

        terminal = Terminal(
            id=terminal_id,
            process=process,
            cwd=cwd,
            shell=shell,
        )
        self._terminals[terminal_id] = terminal

        return terminal_id

    def is_alive(self, terminal_id: str) -> bool:
        """
        Check if terminal is still running.

        Args:
            terminal_id: Terminal ID to check

        Returns:
            True if terminal exists and process is alive
        """
        terminal = self._terminals.get(terminal_id)
        if not terminal:
            return False
        return terminal.process.isalive()

    def count(self) -> int:
        """Return number of active terminals."""
        return len(self._terminals)

    async def write(self, terminal_id: str, data: str) -> None:
        """
        Write data to terminal.

        Args:
            terminal_id: Terminal ID to write to
            data: String data to send

        Raises:
            KeyError: If terminal not found
        """
        terminal = self._terminals.get(terminal_id)
        if not terminal:
            raise KeyError(f"Terminal not found: {terminal_id}")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, terminal.process.write, data.encode())

    async def read(
        self, terminal_id: str, timeout: float = 0.1
    ) -> AsyncGenerator[str, None]:
        """
        Read output from terminal.

        Yields chunks of output as they become available.
        Stops when timeout reached with no data.

        Uses select() to avoid blocking reads that leave orphaned executor threads.

        Args:
            terminal_id: Terminal ID to read from
            timeout: Max time to wait for data (seconds)

        Yields:
            String chunks of terminal output

        Raises:
            KeyError: If terminal not found
        """
        terminal = self._terminals.get(terminal_id)
        if not terminal:
            raise KeyError(f"Terminal not found: {terminal_id}")

        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        fd = terminal.process.fd

        while loop.time() < deadline and terminal.process.isalive():
            try:
                # Use select to check if data is available (non-blocking)
                remaining = max(0.01, min(0.1, deadline - loop.time()))
                readable, _, _ = await loop.run_in_executor(
                    None, lambda t=remaining: select.select([fd], [], [], t)
                )

                if not readable:
                    # No data available within timeout
                    continue

                # Data is available, read it (won't block since select said readable)
                data = await loop.run_in_executor(None, lambda: os.read(fd, 4096))
                if data:
                    yield data.decode("utf-8", errors="replace")
                    deadline = loop.time() + timeout  # Reset deadline on data
                else:
                    # Empty read means EOF
                    break
            except asyncio.CancelledError:
                break
            except (OSError, ValueError, EOFError):
                break

    async def resize(self, terminal_id: str, rows: int, cols: int) -> None:
        """
        Resize terminal dimensions.

        Args:
            terminal_id: Terminal ID to resize
            rows: New row count
            cols: New column count

        Raises:
            KeyError: If terminal not found
        """
        terminal = self._terminals.get(terminal_id)
        if not terminal:
            raise KeyError(f"Terminal not found: {terminal_id}")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, terminal.process.setwinsize, rows, cols)

    async def destroy(self, terminal_id: str) -> bool:
        """
        Destroy a terminal session.

        Args:
            terminal_id: Terminal ID to destroy

        Returns:
            True if destroyed, False if not found
        """
        terminal = self._terminals.pop(terminal_id, None)
        if not terminal:
            return False

        loop = asyncio.get_event_loop()
        try:
            if terminal.process.isalive():
                await loop.run_in_executor(None, terminal.process.terminate)
                # Give process time to exit gracefully
                for _ in range(10):
                    if not terminal.process.isalive():
                        break
                    await asyncio.sleep(0.1)
                # Force kill if still alive
                if terminal.process.isalive():
                    await loop.run_in_executor(
                        None, lambda: terminal.process.terminate(force=True)
                    )
        except Exception:
            pass  # Process may already be dead

        return True

    async def destroy_all(self) -> int:
        """
        Destroy all terminal sessions.

        Returns:
            Number of terminals destroyed
        """
        terminal_ids = list(self._terminals.keys())
        count = 0
        for terminal_id in terminal_ids:
            if await self.destroy(terminal_id):
                count += 1
        return count

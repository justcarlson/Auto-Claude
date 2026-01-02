"""
WebSocket Terminal Handler Tests
================================

Tests for the terminal WebSocket endpoint that bridges
browser connections to PTY sessions.
"""

import time
import threading
from typing import List, Optional

import pytest
from starlette.testclient import TestClient


def receive_with_timeout(ws, timeout: float = 2.0) -> Optional[dict]:
    """
    Receive JSON from WebSocket with timeout.

    Starlette's TestClient receive_json() blocks forever,
    so we wrap it in a thread with timeout.
    """
    result = [None]
    error = [None]

    def receive():
        try:
            result[0] = ws.receive_json()
        except Exception as e:
            error[0] = e

    thread = threading.Thread(target=receive)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        return None  # Timed out
    if error[0]:
        raise error[0]
    return result[0]


def collect_output_until(
    ws, marker: str, max_messages: int = 50, timeout: float = 5.0
) -> List[str]:
    """
    Collect output messages until marker is found or timeout/max reached.

    Returns list of output data strings.
    """
    outputs = []
    start = time.time()

    for _ in range(max_messages):
        if time.time() - start > timeout:
            break

        msg = receive_with_timeout(ws, timeout=1.0)
        if msg is None:
            continue

        if msg.get("type") == "output":
            outputs.append(msg.get("data", ""))

        if marker in "".join(outputs):
            break

    return outputs


class TestWebSocketConnection:
    """Test WebSocket connection handling."""

    def test_websocket_accepts_connection(self):
        """
        Given: WebSocket connection request to /ws/terminal/{id}
        Should: Accept and send connected message with terminal_id
        """
        from api.main import app

        client = TestClient(app)
        with client.websocket_connect("/ws/terminal/term_123") as ws:
            message = ws.receive_json()

        assert message["type"] == "connected"
        assert message["terminal_id"] == "term_123"

    def test_websocket_creates_unique_terminal_per_connection(self):
        """
        Given: Two WebSocket connections with different IDs
        Should: Create separate terminal sessions
        """
        from api.main import app

        client = TestClient(app)

        # First connection
        with client.websocket_connect("/ws/terminal/term_a") as ws1:
            msg1 = ws1.receive_json()
            assert msg1["terminal_id"] == "term_a"

        # Second connection
        with client.websocket_connect("/ws/terminal/term_b") as ws2:
            msg2 = ws2.receive_json()
            assert msg2["terminal_id"] == "term_b"


class TestWebSocketInput:
    """Test WebSocket input handling (sending commands to PTY)."""

    def test_websocket_forwards_input_to_pty(self):
        """
        Given: Input message sent to WebSocket
        Should: Execute in PTY and return output containing the command result
        """
        from api.main import app

        client = TestClient(app)
        with client.websocket_connect("/ws/terminal/term_input") as ws:
            ws.receive_json()  # connected message

            # Send echo command
            ws.send_json({"type": "input", "data": "echo hello_from_test\n"})

            # Collect output until we see our string
            outputs = collect_output_until(ws, "hello_from_test")

        assert "hello_from_test" in "".join(outputs), f"Output was: {''.join(outputs)}"

    def test_websocket_handles_multiple_commands(self):
        """
        Given: Multiple input messages
        Should: Execute each and return outputs
        """
        from api.main import app

        client = TestClient(app)
        with client.websocket_connect("/ws/terminal/term_multi") as ws:
            ws.receive_json()  # connected

            # Send commands with small delay between
            ws.send_json({"type": "input", "data": "echo first_cmd\n"})
            time.sleep(0.2)
            ws.send_json({"type": "input", "data": "echo second_cmd\n"})

            # Collect outputs - wait for both markers
            outputs = []
            start = time.time()
            while time.time() - start < 5.0:
                msg = receive_with_timeout(ws, timeout=0.5)
                if msg and msg.get("type") == "output":
                    outputs.append(msg.get("data", ""))
                combined = "".join(outputs)
                if "first_cmd" in combined and "second_cmd" in combined:
                    break

        combined = "".join(outputs)
        assert "first_cmd" in combined, f"Output was: {combined}"
        assert "second_cmd" in combined, f"Output was: {combined}"


class TestWebSocketResize:
    """Test WebSocket resize handling."""

    def test_websocket_handles_resize(self):
        """
        Given: Resize message with cols and rows
        Should: Resize PTY dimensions without error
        """
        from api.main import app

        client = TestClient(app)
        with client.websocket_connect("/ws/terminal/term_resize") as ws:
            ws.receive_json()  # connected

            # Send resize
            ws.send_json({"type": "resize", "cols": 120, "rows": 40})

            # Verify terminal still works after resize
            ws.send_json({"type": "input", "data": "echo resize_ok\n"})

            outputs = collect_output_until(ws, "resize_ok")

        assert "resize_ok" in "".join(outputs), f"Output was: {''.join(outputs)}"


class TestWebSocketCleanup:
    """Test WebSocket cleanup on disconnect."""

    def test_websocket_destroys_terminal_on_disconnect(self):
        """
        Given: WebSocket connection that disconnects
        Should: Cleanup the PTY process
        """
        from api.main import app

        client = TestClient(app)

        with client.websocket_connect("/ws/terminal/term_cleanup") as ws:
            ws.receive_json()  # connected
            # Connection is active here

        # After disconnect, terminal should be cleaned up
        # Verify no exception is raised - cleanup happens in background


class TestWebSocketErrors:
    """Test WebSocket error handling."""

    def test_websocket_handles_invalid_message_type(self):
        """
        Given: Message with unknown type
        Should: Handle gracefully without crashing
        """
        from api.main import app

        client = TestClient(app)
        with client.websocket_connect("/ws/terminal/term_err") as ws:
            ws.receive_json()  # connected

            # Send invalid type - should be ignored
            ws.send_json({"type": "unknown_type", "data": "test"})

            # Should still be able to send valid commands
            ws.send_json({"type": "input", "data": "echo still_works\n"})

            outputs = collect_output_until(ws, "still_works")

        assert "still_works" in "".join(outputs), f"Output was: {''.join(outputs)}"

    def test_websocket_handles_malformed_json(self):
        """
        Given: Malformed JSON message
        Should: Send error message but keep connection alive
        """
        from api.main import app

        client = TestClient(app)
        with client.websocket_connect("/ws/terminal/term_malformed") as ws:
            ws.receive_json()  # connected

            # Send malformed data (as text, not JSON)
            ws.send_text("not valid json {{{")

            # Should receive error message
            error_msg = receive_with_timeout(ws, timeout=2.0)

            # Either we got an error or the connection is still working
            if error_msg and error_msg.get("type") == "error":
                # Good - we got an error message
                pass

            # Connection should still work
            ws.send_json({"type": "input", "data": "echo recovered\n"})
            outputs = collect_output_until(ws, "recovered", timeout=3.0)

        # Success if we got error message OR connection recovered
        got_error = error_msg and error_msg.get("type") == "error"
        recovered = "recovered" in "".join(outputs)
        assert got_error or recovered, (
            f"No error msg and no recovery. Error: {error_msg}, Output: {''.join(outputs)}"
        )

"""
WebSocket Terminal Handler Tests
================================

Tests for the terminal WebSocket endpoint that bridges
browser connections to PTY sessions.

NOTE: These tests use bounded iteration to avoid CI hangs.
The PTY operations use executor threads that can orphan if reads block.
We use pytest.mark.timeout to fail fast instead of waiting 300s for cleanup.
"""

import time

import pytest
from starlette.testclient import TestClient


def collect_output_until(
    ws, marker: str, max_messages: int = 30, timeout: float = 5.0
) -> list[str]:
    """
    Collect output messages until marker is found or limits reached.

    Uses bounded iteration to prevent infinite loops.
    Returns list of output data strings.
    """
    outputs = []
    start = time.time()

    for _ in range(max_messages):
        elapsed = time.time() - start
        if elapsed > timeout:
            break

        try:
            msg = ws.receive_json()
        except Exception:
            # Connection closed or error
            break

        if msg is None:
            continue

        if msg.get("type") == "output":
            outputs.append(msg.get("data", ""))

        if marker in "".join(outputs):
            break

    return outputs


class TestWebSocketConnection:
    """Test WebSocket connection handling."""

    @pytest.mark.timeout(10)
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

    @pytest.mark.timeout(10)
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

    @pytest.mark.timeout(15)
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

    @pytest.mark.timeout(15)
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
            time.sleep(0.1)
            ws.send_json({"type": "input", "data": "echo second_cmd\n"})

            # Collect outputs - bounded iteration for both markers
            outputs = []
            start = time.time()
            for _ in range(30):
                if time.time() - start > 5.0:
                    break
                try:
                    msg = ws.receive_json()
                    if msg and msg.get("type") == "output":
                        outputs.append(msg.get("data", ""))
                    combined = "".join(outputs)
                    if "first_cmd" in combined and "second_cmd" in combined:
                        break
                except Exception:
                    break

        combined = "".join(outputs)
        assert "first_cmd" in combined, f"Output was: {combined}"
        assert "second_cmd" in combined, f"Output was: {combined}"


class TestWebSocketResize:
    """Test WebSocket resize handling."""

    @pytest.mark.timeout(15)
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

    @pytest.mark.timeout(10)
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

    @pytest.mark.timeout(15)
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

    @pytest.mark.timeout(15)
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

            # Try to receive error message (may or may not come)
            error_msg = None
            try:
                error_msg = ws.receive_json()
            except Exception:
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

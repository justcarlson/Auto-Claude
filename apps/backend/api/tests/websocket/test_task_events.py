"""
Task Events WebSocket Tests
===========================

Tests for the task events WebSocket endpoint that streams
real-time task progress, status, and error events.
"""

import pytest
from starlette.testclient import TestClient


class TestTaskEventsConnection:
    """Test WebSocket connection handling for task events."""

    @pytest.mark.timeout(10)
    def test_websocket_connects(self):
        """
        Given: WebSocket connection request to /ws/tasks/{id}/events
        Should: Accept and send connected message
        """
        from api.main import app

        client = TestClient(app)
        with client.websocket_connect("/ws/tasks/task_123/events") as ws:
            message = ws.receive_json()

        assert message["type"] == "connected"
        assert message["taskId"] == "task_123"

    @pytest.mark.timeout(10)
    def test_websocket_supports_multiple_clients(self):
        """
        Given: Multiple WebSocket connections to same task
        Should: All clients receive events independently
        """
        from api.main import app

        client = TestClient(app)

        # First connection
        with client.websocket_connect("/ws/tasks/task_multi/events") as ws1:
            msg1 = ws1.receive_json()
            assert msg1["type"] == "connected"

        # Second connection
        with client.websocket_connect("/ws/tasks/task_multi/events") as ws2:
            msg2 = ws2.receive_json()
            assert msg2["type"] == "connected"


class TestTaskEventsProgress:
    """Test task progress event streaming."""

    @pytest.mark.timeout(10)
    def test_progress_events_streamed(self):
        """
        Given: Task with progress updates
        Should: Stream progress events to connected clients
        """
        from api.main import app
        from api.websocket.task_events import emit_progress

        client = TestClient(app)
        with client.websocket_connect("/ws/tasks/task_prog/events") as ws:
            ws.receive_json()  # connected message

            # Emit progress from service
            emit_progress("task_prog", {"phase": "planning", "percent": 25})

            # Should receive progress event
            msg = ws.receive_json()

        assert msg["type"] == "progress"
        assert msg["taskId"] == "task_prog"
        assert msg["data"]["phase"] == "planning"
        assert msg["data"]["percent"] == 25


class TestTaskEventsStatus:
    """Test task status change events."""

    @pytest.mark.timeout(10)
    def test_status_change_events(self):
        """
        Given: Task status change
        Should: Send status event to connected clients
        """
        from api.main import app
        from api.websocket.task_events import emit_status

        client = TestClient(app)
        with client.websocket_connect("/ws/tasks/task_status/events") as ws:
            ws.receive_json()  # connected

            # Emit status change
            emit_status("task_status", "in_progress")

            msg = ws.receive_json()

        assert msg["type"] == "status"
        assert msg["taskId"] == "task_status"
        assert msg["status"] == "in_progress"


class TestTaskEventsError:
    """Test task error events."""

    @pytest.mark.timeout(10)
    def test_error_events(self):
        """
        Given: Task error occurs
        Should: Send error event to connected clients
        """
        from api.main import app
        from api.websocket.task_events import emit_error

        client = TestClient(app)
        with client.websocket_connect("/ws/tasks/task_err/events") as ws:
            ws.receive_json()  # connected

            # Emit error
            emit_error("task_err", "Build failed: missing dependency")

            msg = ws.receive_json()

        assert msg["type"] == "error"
        assert msg["taskId"] == "task_err"
        assert "missing dependency" in msg["error"]


class TestTaskEventsLog:
    """Test task log events."""

    @pytest.mark.timeout(10)
    def test_log_events(self):
        """
        Given: Task produces log output
        Should: Stream log events to connected clients
        """
        from api.main import app
        from api.websocket.task_events import emit_log

        client = TestClient(app)
        with client.websocket_connect("/ws/tasks/task_log/events") as ws:
            ws.receive_json()  # connected

            # Emit log
            emit_log("task_log", "info", "Installing dependencies...")

            msg = ws.receive_json()

        assert msg["type"] == "log"
        assert msg["taskId"] == "task_log"
        assert msg["level"] == "info"
        assert "Installing dependencies" in msg["message"]


class TestTaskEventsBroadcast:
    """Test event broadcasting to multiple clients."""

    @pytest.mark.timeout(15)
    def test_multiple_clients_receive_events(self):
        """
        Given: Multiple clients connected to same task
        Should: All clients receive the same events
        """
        from api.main import app
        from api.websocket.task_events import emit_progress

        client = TestClient(app)

        # Connect both clients first, then emit
        with client.websocket_connect("/ws/tasks/task_bc/events") as ws1:
            ws1.receive_json()  # connected

            with client.websocket_connect("/ws/tasks/task_bc/events") as ws2:
                ws2.receive_json()  # connected

                # Emit progress
                emit_progress("task_bc", {"phase": "testing", "percent": 75})

                # Both should receive
                msg1 = ws1.receive_json()
                msg2 = ws2.receive_json()

        assert msg1["type"] == "progress"
        assert msg2["type"] == "progress"
        assert msg1["data"]["percent"] == 75
        assert msg2["data"]["percent"] == 75

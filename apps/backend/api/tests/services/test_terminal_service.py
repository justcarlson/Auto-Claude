#!/usr/bin/env python3
"""
Terminal Service Unit Tests
===========================

Pure function tests for terminal service utilities.
Fast tests (no real PTY spawning).
"""

import pytest

# =============================================================================
# ANSI STRIPPING
# =============================================================================


def test_strip_ansi_removes_escape_codes():
    """
    Given: String with ANSI escape codes
    Should: Return clean string
    """
    from api.services.terminal_service import strip_ansi

    input_data = "\x1b[32mHello\x1b[0m World"
    expected = "Hello World"
    actual = strip_ansi(input_data)

    assert actual == expected


def test_strip_ansi_handles_multiple_codes():
    """
    Given: String with multiple ANSI codes
    Should: Remove all codes
    """
    from api.services.terminal_service import strip_ansi

    input_data = "\x1b[1m\x1b[34mBold Blue\x1b[0m\x1b[31mRed\x1b[0m"
    expected = "Bold BlueRed"
    actual = strip_ansi(input_data)

    assert actual == expected


def test_strip_ansi_handles_no_codes():
    """
    Given: String without ANSI codes
    Should: Return unchanged string
    """
    from api.services.terminal_service import strip_ansi

    input_data = "Plain text"
    expected = "Plain text"
    actual = strip_ansi(input_data)

    assert actual == expected


def test_strip_ansi_handles_empty_string():
    """
    Given: Empty string
    Should: Return empty string
    """
    from api.services.terminal_service import strip_ansi

    assert strip_ansi("") == ""


# =============================================================================
# PTY DIMENSIONS CONVERSION
# =============================================================================


def test_to_pty_dimensions_converts_correctly():
    """
    Given: cols and rows dict
    Should: Return (rows, cols) tuple for ptyprocess
    """
    from api.services.terminal_service import to_pty_dimensions

    input_data = {"cols": 80, "rows": 24}
    expected = (24, 80)
    actual = to_pty_dimensions(input_data)

    assert actual == expected


def test_to_pty_dimensions_handles_different_values():
    """
    Given: Different dimension values
    Should: Return correctly ordered tuple
    """
    from api.services.terminal_service import to_pty_dimensions

    input_data = {"cols": 120, "rows": 40}
    expected = (40, 120)
    actual = to_pty_dimensions(input_data)

    assert actual == expected


def test_to_pty_dimensions_defaults_on_missing():
    """
    Given: Missing dimension values
    Should: Use defaults (80x24)
    """
    from api.services.terminal_service import to_pty_dimensions

    assert to_pty_dimensions({}) == (24, 80)
    assert to_pty_dimensions({"cols": 100}) == (24, 100)
    assert to_pty_dimensions({"rows": 30}) == (30, 80)


# =============================================================================
# TERMINAL MESSAGE PARSING
# =============================================================================


def test_parse_terminal_message_handles_input():
    """
    Given: JSON message with type 'input'
    Should: Return parsed TerminalMessage
    """
    from api.services.terminal_service import parse_terminal_message

    input_data = '{"type": "input", "data": "ls\\n"}'
    result = parse_terminal_message(input_data)

    assert result.type == "input"
    assert result.data == "ls\n"


def test_parse_terminal_message_handles_resize():
    """
    Given: JSON message with type 'resize'
    Should: Return parsed TerminalMessage with cols/rows
    """
    from api.services.terminal_service import parse_terminal_message

    input_data = '{"type": "resize", "cols": 120, "rows": 40}'
    result = parse_terminal_message(input_data)

    assert result.type == "resize"
    assert result.cols == 120
    assert result.rows == 40


def test_parse_terminal_message_handles_invalid_json():
    """
    Given: Invalid JSON
    Should: Return error message
    """
    from api.services.terminal_service import parse_terminal_message

    result = parse_terminal_message("not valid json")

    assert result.type == "error"
    assert "error" in result.data.lower() or result.data


def test_parse_terminal_message_handles_missing_type():
    """
    Given: JSON without type field
    Should: Return error message
    """
    from api.services.terminal_service import parse_terminal_message

    input_data = '{"data": "hello"}'
    result = parse_terminal_message(input_data)

    assert result.type == "error"


# =============================================================================
# TERMINAL MESSAGE MODEL
# =============================================================================


def test_terminal_message_model_validates():
    """
    Given: Valid message data
    Should: Create TerminalMessage with correct fields
    """
    from api.services.terminal_service import TerminalMessage

    msg = TerminalMessage(type="input", data="hello")

    assert msg.type == "input"
    assert msg.data == "hello"
    assert msg.cols is None
    assert msg.rows is None


def test_terminal_message_model_resize():
    """
    Given: Resize message data
    Should: Create TerminalMessage with dimensions
    """
    from api.services.terminal_service import TerminalMessage

    msg = TerminalMessage(type="resize", cols=100, rows=30)

    assert msg.type == "resize"
    assert msg.cols == 100
    assert msg.rows == 30

#!/usr/bin/env python3
"""
Terminal Service Integration Tests
==================================

Integration tests with real PTY spawning.
Marked with @pytest.mark.integration to skip in fast test runs.
"""

import pytest


# =============================================================================
# TERMINAL SPAWNING
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_spawns_shell():
    """
    Given: Request to create terminal
    Should: Spawn bash and return terminal_id
    """
    from api.services.terminal_service import TerminalManager

    manager = TerminalManager()
    terminal_id = await manager.create_terminal(cwd="/tmp")

    assert terminal_id is not None
    assert manager.is_alive(terminal_id)

    await manager.destroy(terminal_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_spawns_with_custom_shell():
    """
    Given: Request to create terminal with custom shell
    Should: Spawn specified shell
    """
    from api.services.terminal_service import TerminalManager

    manager = TerminalManager()
    terminal_id = await manager.create_terminal(cwd="/tmp", shell="/bin/sh")

    assert terminal_id is not None
    assert manager.is_alive(terminal_id)

    await manager.destroy(terminal_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_destroy_terminates_process():
    """
    Given: Active terminal
    Should: Terminate on destroy
    """
    from api.services.terminal_service import TerminalManager

    manager = TerminalManager()
    terminal_id = await manager.create_terminal(cwd="/tmp")

    assert manager.is_alive(terminal_id)

    await manager.destroy(terminal_id)

    assert not manager.is_alive(terminal_id)


# =============================================================================
# TERMINAL I/O
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_echoes_command():
    """
    Given: Terminal with echo command
    Should: Return command output
    """
    from api.services.terminal_service import TerminalManager

    manager = TerminalManager()
    terminal_id = await manager.create_terminal(cwd="/tmp")

    await manager.write(terminal_id, "echo hello_terminal\n")

    output = []
    async for chunk in manager.read(terminal_id, timeout=2.0):
        output.append(chunk)
        if "hello_terminal" in "".join(output):
            break

    assert "hello_terminal" in "".join(output)
    await manager.destroy(terminal_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_handles_multiple_commands():
    """
    Given: Terminal with multiple commands
    Should: Return output for each
    """
    from api.services.terminal_service import TerminalManager

    manager = TerminalManager()
    terminal_id = await manager.create_terminal(cwd="/tmp")

    await manager.write(terminal_id, "echo first_cmd\n")
    await manager.write(terminal_id, "echo second_cmd\n")

    output = []
    async for chunk in manager.read(terminal_id, timeout=3.0):
        output.append(chunk)
        combined = "".join(output)
        if "first_cmd" in combined and "second_cmd" in combined:
            break

    combined = "".join(output)
    assert "first_cmd" in combined
    assert "second_cmd" in combined

    await manager.destroy(terminal_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_write_to_nonexistent_raises():
    """
    Given: Non-existent terminal ID
    Should: Raise error on write
    """
    from api.services.terminal_service import TerminalManager

    manager = TerminalManager()

    with pytest.raises(KeyError):
        await manager.write("nonexistent-id", "hello")


# =============================================================================
# TERMINAL RESIZE
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_resize():
    """
    Given: Active terminal
    Should: Resize PTY dimensions
    """
    from api.services.terminal_service import TerminalManager

    manager = TerminalManager()
    terminal_id = await manager.create_terminal(cwd="/tmp")

    # Should not raise
    await manager.resize(terminal_id, rows=40, cols=120)

    await manager.destroy(terminal_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_resize_nonexistent_raises():
    """
    Given: Non-existent terminal ID
    Should: Raise error on resize
    """
    from api.services.terminal_service import TerminalManager

    manager = TerminalManager()

    with pytest.raises(KeyError):
        await manager.resize("nonexistent-id", rows=40, cols=120)


# =============================================================================
# TERMINAL CLEANUP
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_manager_tracks_terminals():
    """
    Given: Multiple terminals created
    Should: Track all terminals
    """
    from api.services.terminal_service import TerminalManager

    manager = TerminalManager()
    id1 = await manager.create_terminal(cwd="/tmp")
    id2 = await manager.create_terminal(cwd="/tmp")

    assert manager.is_alive(id1)
    assert manager.is_alive(id2)
    assert manager.count() == 2

    await manager.destroy(id1)
    assert manager.count() == 1

    await manager.destroy(id2)
    assert manager.count() == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_manager_destroy_all():
    """
    Given: Multiple active terminals
    Should: Destroy all on cleanup
    """
    from api.services.terminal_service import TerminalManager

    manager = TerminalManager()
    id1 = await manager.create_terminal(cwd="/tmp")
    id2 = await manager.create_terminal(cwd="/tmp")

    await manager.destroy_all()

    assert not manager.is_alive(id1)
    assert not manager.is_alive(id2)
    assert manager.count() == 0

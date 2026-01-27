import pytest
import discord
from discord.ext import commands
from main import bot

@pytest.mark.asyncio
async def test_ping_command_exists():
    # Check if the 'ping' command is registered
    command = bot.get_command('ping')
    assert command is not None
    assert command.name == 'ping'

@pytest.mark.asyncio
async def test_echo_command_exists():
    # Check if the 'echo' command is registered
    command = bot.get_command('echo')
    assert command is not None
    assert command.name == 'echo'

@pytest.mark.asyncio
async def test_roll_command_exists():
    # Check if the 'roll' command is registered
    command = bot.get_command('roll')
    assert command is not None
    assert command.name == 'roll'

@pytest.mark.asyncio
async def test_8ball_command_exists():
    # Check if the '8ball' command is registered
    command = bot.get_command('8ball')
    assert command is not None
    assert command.name == '8ball'

@pytest.mark.asyncio
async def test_setup_ticket_command_exists():
    # Check if the 'setup_ticket' command is registered
    command = bot.get_command('setup_ticket')
    assert command is not None
    assert command.name == 'setup_ticket'

@pytest.mark.asyncio
async def test_moderation_commands_exist():
    # Check if moderation commands are registered
    assert bot.get_command('mute') is not None
    assert bot.get_command('warn') is not None
    assert bot.get_command('warnings') is not None
    assert bot.get_command('ban') is not None
    assert bot.get_command('unban') is not None

@pytest.mark.asyncio
async def test_sync_command_exists():
    # Check if the 'sync' command is registered
    command = bot.get_command('sync')
    assert command is not None
    assert command.name == 'sync'

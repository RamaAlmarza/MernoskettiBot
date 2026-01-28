import pytest
import discord
from discord.ext import commands
from main import bot

@pytest.mark.asyncio
async def test_ping_command_exists():
    assert bot.get_command('ping') is not None

@pytest.mark.asyncio
async def test_echo_command_exists():
    assert bot.get_command('echo') is not None

@pytest.mark.asyncio
async def test_roll_command_exists():
    assert bot.get_command('roll') is not None

@pytest.mark.asyncio
async def test_8ball_command_exists():
    assert bot.get_command('8ball') is not None

@pytest.mark.asyncio
async def test_setup_ticket_command_exists():
    assert bot.get_command('setup_ticket') is not None

@pytest.mark.asyncio
async def test_moderation_commands_exist():
    assert bot.get_command('mute') is not None
    assert bot.get_command('duration') is not None
    assert bot.get_command('warn') is not None
    assert bot.get_command('warn-remove') is not None
    assert bot.get_command('warnings') is not None
    assert bot.get_command('ban') is not None
    assert bot.get_command('unban') is not None
    assert bot.get_command('kick') is not None
    assert bot.get_command('softban') is not None
    assert bot.get_command('lock') is not None
    assert bot.get_command('unlock') is not None
    assert bot.get_command('temprole') is not None

@pytest.mark.asyncio
async def test_note_commands_exist():
    assert bot.get_command('note') is not None
    assert bot.get_command('delnote') is not None
    assert bot.get_command('notes') is not None
    assert bot.get_command('clearnotes') is not None
    assert bot.get_command('editnote') is not None

@pytest.mark.asyncio
async def test_utility_commands_exist():
    assert bot.get_command('star') is not None
    assert bot.get_command('av') is not None
    assert bot.get_command('modlogs') is not None
    assert bot.get_command('modstats') is not None
    assert bot.get_command('moderations') is not None

@pytest.mark.asyncio
async def test_sync_command_exists():
    assert bot.get_command('sync') is not None

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

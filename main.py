import os
import random
import asyncio
import datetime
import discord
import csv
import json
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
from discord.ext import commands
from dotenv import load_dotenv
import database

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Role IDs for permissions
LOW_STAFF_ROLE_ID = int(os.getenv('LOW_STAFF_ROLE_ID', 0))
JR_MOD_ROLE_ID = int(os.getenv('JR_MOD_ROLE_ID', 0))
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', 0))
SR_MOD_ROLE_ID = int(os.getenv('SR_MOD_ROLE_ID', 0))
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID', 0))
SR_ADMIN_ROLE_ID = int(os.getenv('SR_ADMIN_ROLE_ID', 0))
STAR_THRESHOLD = int(os.getenv('STAR_THRESHOLD', 5))

def has_permission(min_role_name):
    async def predicate(ctx):
        # Define hierarchy
        hierarchy = [
            'LOW_STAFF_ROLE_ID',
            'JR_MOD_ROLE_ID',
            'MOD_ROLE_ID',
            'SR_MOD_ROLE_ID',
            'ADMIN_ROLE_ID',
            'SR_ADMIN_ROLE_ID'
        ]

        try:
            min_index = hierarchy.index(min_role_name)
        except ValueError:
            return False # Invalid role name passed

        # Get all allowed role variable names
        allowed_vars = hierarchy[min_index:]

        # Get actual IDs from global scope
        allowed_ids = []
        for var_name in allowed_vars:
            val = globals().get(var_name, 0)
            if val != 0:
                allowed_ids.append(val)

        if not allowed_ids:
            return False # No roles configured

        # Check if user has any of the allowed IDs
        if isinstance(ctx.author, discord.Member):
            user_role_ids = [r.id for r in ctx.author.roles]
            return any(role_id in user_role_ids for role_id in allowed_ids)
        return False
    return commands.check(predicate)

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

def get_prefix_for_bot(bot, message):
    if not message.guild:
        return '!'
    return database.get_config(message.guild.id)["prefix"]

# Initialize bot
bot = commands.Bot(command_prefix=get_prefix_for_bot, intents=intents)

class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.green, custom_id="ticket_claim", emoji="🙋")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You do not have permission to claim tickets.", ephemeral=True)
            return

        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        button.style = discord.ButtonStyle.grey

        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"{interaction.user.mention} has claimed this ticket!")

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="ticket_close", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing ticket in 5 seconds...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Select a ticket option...",
        custom_id="ticket_select",
        options=[
            discord.SelectOption(label="Roles", value="roles", description="Request or change roles", emoji="🎭"),
            discord.SelectOption(label="Report Staff", value="report_staff", description="Report a staff member", emoji="🛡️"),
            discord.SelectOption(label="Report User", value="report_user", description="Report a user", emoji="⚠️"),
            discord.SelectOption(label="Questions", value="questions", description="Ask a question", emoji="❓"),
            discord.SelectOption(label="Others", value="others", description="Other inquiries", emoji="📝"),
        ]
    )
    async def create_ticket(self, interaction: discord.Interaction, select: discord.ui.Select):
        ticket_type = select.values[0]
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")

        if not category:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }
            category = await guild.create_category("Tickets", overwrites=overwrites)

        # Sanitize username for channel name
        safe_username = "".join(c for c in interaction.user.name if c.isalnum() or c in "-_").lower()
        channel_name = f"ticket-{safe_username}-{ticket_type}"

        # Check if channel already exists
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name.lower())
        if existing_channel:
            await interaction.response.send_message(f"You already have a ticket open for this topic: {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title="Ticket Created",
            description=f"Hello {interaction.user.mention}, support will be with you shortly.\n\n**Topic:** {ticket_type.replace('_', ' ').title()}",
            color=discord.Color.green()
        )

        await channel.send(embed=embed, view=TicketControls())
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    # Register persistent views
    bot.add_view(TicketLauncher())
    bot.add_view(TicketControls())

    # Sync slash commands
    # try:
    #     synced = await bot.tree.sync()
    #     print(f"Synced {len(synced)} command(s)")
    # except Exception as e:
    #     print(f"Failed to sync commands: {e}")

    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You do not have the required permissions to run this command.", ephemeral=True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        await interaction.response.send_message("I do not have the required permissions to execute this command.", ephemeral=True)
    elif isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("You do not have permission to perform this action.", ephemeral=True)
    elif isinstance(error, app_commands.TransformerError):
        await interaction.response.send_message(f"Invalid input: {error}", ephemeral=True)
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"Command is on cooldown. Try again in {error.retry_after:.2f}s.", ephemeral=True)
    else:
        print(f"An error occurred: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message("An error occurred while executing the command.", ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) != '⭐':
        return

    STAR_CHANNEL_ID = int(os.getenv('STAR_CHANNEL_ID', 0))
    if not STAR_CHANNEL_ID:
        return

    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return

    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.NotFound:
        return

    # Count star reactions
    reaction = discord.utils.get(message.reactions, emoji='⭐')
    if not reaction:
        return

    count = reaction.count

    # Check DB
    entry = database.get_starboard_entry(message.id)

    if entry:
        star_message_id, _, _ = entry
        star_channel = bot.get_channel(STAR_CHANNEL_ID)
        if star_channel:
            try:
                star_message = await star_channel.fetch_message(star_message_id)
                await star_message.edit(content=f"⭐ {count} {channel.mention}")
                database.update_starboard_entry(message.id, count)
            except discord.NotFound:
                pass # Star message deleted manually?
    elif count >= STAR_THRESHOLD:
        star_channel = bot.get_channel(STAR_CHANNEL_ID)
        if not star_channel:
            return

        embed = discord.Embed(description=message.content, color=discord.Color.gold())
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="Source", value=f"[Jump!]({message.jump_url})")
        embed.set_footer(text=f"{message.id} • {message.created_at.strftime('%Y-%m-%d %H:%M')}")

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        sent_message = await star_channel.send(content=f"⭐ {count} {channel.mention}", embed=embed)
        database.add_starboard_entry(message.id, sent_message.id, STAR_CHANNEL_ID, count)

@bot.hybrid_command(description="Syncs commands (default: local guild). Args: global, clear, clearglobal")
@app_commands.describe(action="Action: 'global', 'clear', 'clearglobal', or empty")
@has_permission('ADMIN_ROLE_ID')
async def sync(ctx, action: str = None):
    """Syncs commands. Usage: !sync [global|clear|clearglobal]"""
    if action == "global":
        msg = await ctx.send("Syncing global commands... (This may take up to an hour to propagate)")
        try:
            synced = await bot.tree.sync()
            await msg.edit(content=f"Synced {len(synced)} global command(s).")
        except Exception as e:
            await msg.edit(content=f"Failed to sync global commands: {e}")

    elif action == "clearglobal":
        msg = await ctx.send("Clearing global commands... (This may take up to an hour to propagate)")
        try:
            bot.tree.clear_commands(guild=None)
            await bot.tree.sync()
            await msg.edit(content="Cleared global commands.")
        except Exception as e:
            await msg.edit(content=f"Failed to clear global commands: {e}")

    elif action == "clear":
        try:
            bot.tree.clear_commands(guild=ctx.guild)
            await bot.tree.sync(guild=ctx.guild)
            await ctx.send("Cleared guild-specific commands. (Global commands may still persist)")
        except Exception as e:
            await ctx.send(f"Failed to clear commands: {e}")

    else:
        # Default: Sync to current guild (Instant update for dev)
        try:
            bot.tree.clear_commands(guild=ctx.guild)
            bot.tree.copy_global_to(guild=ctx.guild)
            synced = await bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"Synced {len(synced)} command(s) to this guild. (Duplicates cleared)")
        except Exception as e:
            await ctx.send(f"Failed to sync commands: {e}")

@bot.hybrid_command(description="Changes the bot's prefix.")
@app_commands.describe(new_prefix="The new prefix")
@has_permission('ADMIN_ROLE_ID')
async def prefix(ctx, new_prefix: str):
    database.set_config(ctx.guild.id, prefix=new_prefix)
    await ctx.send(f"Prefix changed to: `{new_prefix}`")

@bot.hybrid_command(description="Makes an announcement.")
@app_commands.describe(channel="Channel to announce in", message="The announcement message")
@has_permission('SR_ADMIN_ROLE_ID')
async def announce(ctx, channel: discord.TextChannel, *, message: str):
    embed = discord.Embed(title="📢 Announcement", description=message, color=discord.Color.red(), timestamp=datetime.datetime.now())
    embed.set_footer(text=f"Announced by {ctx.author.display_name}")
    await channel.send(embed=embed)
    await ctx.send("Announcement sent.", ephemeral=True)

@bot.hybrid_command(description="Clears messages.")
@app_commands.describe(amount="Number of messages to clear (1-500)")
@has_permission('LOW_STAFF_ROLE_ID')
async def clear(ctx, amount: int):
    if amount < 1 or amount > 500:
        await ctx.send("Amount must be between 1 and 500.", ephemeral=True)
        return
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)

@bot.hybrid_command(description="Shows user info.")
@app_commands.describe(member="The member to show info for")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"User Info: {member.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"))
    embed.add_field(name="Created", value=member.created_at.strftime("%Y-%m-%d"))
    roles = [r.mention for r in member.roles if r.name != "@everyone"]
    embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles) if roles else "None", inline=False)
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Shows server info.")
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"Server Info: {guild.name}", color=discord.Color.blue())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Owner", value=guild.owner)
    embed.add_field(name="Members", value=guild.member_count)
    embed.add_field(name="Channels", value=len(guild.channels))
    embed.add_field(name="Roles", value=len(guild.roles))
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Shows server icon.")
async def servericon(ctx):
    if ctx.guild.icon:
        await ctx.send(ctx.guild.icon.url)
    else:
        await ctx.send("Server has no icon.")

@bot.hybrid_command(description="Sets up the ticket system panel.")
@has_permission('SR_ADMIN_ROLE_ID')
async def setup_ticket(ctx):
    """Sets up the ticket system panel."""
    embed = discord.Embed(
        title="Support Tickets",
        description="Click the button below to open a support ticket.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketLauncher())

def convert_duration(duration: str):
    """Converts a duration string (e.g., '10m', '1h') to timedelta."""
    try:
        unit = duration[-1]
        value = int(duration[:-1])
        if unit == 's':
            return datetime.timedelta(seconds=value)
        elif unit == 'm':
            return datetime.timedelta(minutes=value)
        elif unit == 'h':
            return datetime.timedelta(hours=value)
        elif unit == 'd':
            return datetime.timedelta(days=value)
    except (ValueError, IndexError):
        return None
    return None

async def send_dm_log(member: discord.Member, action: str, reason: str, case_id: int, guild_name: str):
    """Helper to send DM logs to users."""
    try:
        embed = discord.Embed(title=f"You have been {action}", color=discord.Color.red())
        embed.add_field(name="Server", value=guild_name, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Case ID", value=f"#{case_id}", inline=False)
        await member.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass  # User has DMs off or blocked the bot

@bot.hybrid_command(description="Mutes a member for the specified duration.")
@app_commands.describe(duration="Duration (e.g., 10m, 1h)", reason="Reason for the mute")
@has_permission('LOW_STAFF_ROLE_ID')
async def mute(ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
    delta = convert_duration(duration)
    if not delta:
        await ctx.send("Invalid duration format. Use s, m, h, or d (e.g., 10m).", ephemeral=True)
        return

    try:
        case_id = database.log_action("MUTE", member.id, ctx.author.id, reason, duration)
        await send_dm_log(member, "Muted", reason, case_id, ctx.guild.name)
        await member.timeout(delta, reason=reason)
        await ctx.send(f"{member.mention} has been muted for {duration}. Reason: {reason} (Case #{case_id})")
    except discord.Forbidden:
        await ctx.send("I do not have permission to perform this action on this user. They might have a higher role than me.", ephemeral=True)

@bot.hybrid_command(description="Modifies the mute duration for a user.")
@app_commands.describe(member="The member to modify", duration="New duration (e.g., 10m, 1h)")
@has_permission('LOW_STAFF_ROLE_ID')
async def duration(ctx, member: discord.Member, duration: str):
    delta = convert_duration(duration)
    if not delta:
        await ctx.send("Invalid duration format. Use s, m, h, or d (e.g., 10m).", ephemeral=True)
        return

    try:
        await member.timeout(delta, reason="Duration modified by staff")
        case_id = database.log_action("MUTE_DURATION_EDIT", member.id, ctx.author.id, "Modified duration", duration)
        await ctx.send(f"Updated mute duration for {member.mention} to {duration}. (Case #{case_id})")
    except discord.Forbidden:
        await ctx.send("I do not have permission to perform this action on this user. They might have a higher role than me.", ephemeral=True)

@bot.hybrid_command(description="Kicks a member from the server.")
@app_commands.describe(reason="Reason for the kick")
@has_permission('MOD_ROLE_ID')
async def kick(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    try:
        case_id = database.log_action("KICK", member.id, ctx.author.id, reason)
        await send_dm_log(member, "Kicked", reason, case_id, ctx.guild.name)
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} has been kicked. Reason: {reason} (Case #{case_id})")
    except discord.Forbidden:
        await ctx.send("I do not have permission to perform this action on this user. They might have a higher role than me.", ephemeral=True)

@bot.hybrid_command(description="Softbans a member (ban then unban) to delete messages.")
@app_commands.describe(reason="Reason for the softban")
@has_permission('SR_ADMIN_ROLE_ID')
async def softban(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    try:
        case_id = database.log_action("SOFTBAN", member.id, ctx.author.id, reason)
        await send_dm_log(member, "Softbanned", reason, case_id, ctx.guild.name)
        await member.ban(reason=reason, delete_message_seconds=86400)
        await member.unban(reason="Softban unban")
        await ctx.send(f"{member.mention} has been softbanned. (Case #{case_id})")
    except discord.Forbidden:
        await ctx.send("I do not have permission to perform this action on this user. They might have a higher role than me.", ephemeral=True)

@bot.hybrid_command(description="Locks the current channel.")
@has_permission('ADMIN_ROLE_ID')
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    database.log_action("LOCK", 0, ctx.author.id, "Channel locked", str(ctx.channel.id))
    await ctx.send(f"Channel {ctx.channel.mention} has been locked.")

@bot.hybrid_command(description="Unlocks the current channel.")
@has_permission('ADMIN_ROLE_ID')
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    database.log_action("UNLOCK", 0, ctx.author.id, "Channel unlocked", str(ctx.channel.id))
    await ctx.send(f"Channel {ctx.channel.mention} has been unlocked.")

@bot.hybrid_command(description="Gives a temporary role to a user.")
@app_commands.describe(member="The member", role="The role to give", duration="Duration (e.g. 10m)")
@has_permission('ADMIN_ROLE_ID')
async def temprole(ctx, member: discord.Member, role: discord.Role, duration: str):
    delta = convert_duration(duration)
    if not delta:
        await ctx.send("Invalid duration format.", ephemeral=True)
        return

    try:
        await member.add_roles(role)
        database.log_action("TEMPROLE_ADD", member.id, ctx.author.id, f"Added role {role.name}", duration)
        await ctx.send(f"Gave {role.name} to {member.mention} for {duration}.")

        # Non-persistent implementation for simplicity as requested plan
        await asyncio.sleep(delta.total_seconds())

        # Check if user still has role and remove it
        if role in member.roles:
            await member.remove_roles(role)
            database.log_action("TEMPROLE_REMOVE", member.id, bot.user.id, f"Removed role {role.name} (Expired)")
    except discord.Forbidden:
        await ctx.send("I do not have permission to perform this action on this user or role. I might be missing permissions or the role is higher than mine.", ephemeral=True)

@bot.hybrid_command(description="Warns a member.")
@app_commands.describe(reason="Reason for the warning")
@has_permission('JR_MOD_ROLE_ID')
async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    database.add_warning(member.id, reason, ctx.author.id)
    case_id = database.log_action("WARN", member.id, ctx.author.id, reason)
    await send_dm_log(member, "Warned", reason, case_id, ctx.guild.name)
    await ctx.send(f"{member.mention} has been warned. Reason: {reason} (Case #{case_id})")

@bot.hybrid_command(name="warn-remove", description="Removes a specific warning.")
@app_commands.describe(user="The user", warn_id="ID of the warning to remove")
@has_permission('MOD_ROLE_ID')
async def warn_remove(ctx, user: discord.User, warn_id: int):
    if database.remove_warning(warn_id, user.id):
        case_id = database.log_action("WARN_REMOVE", user.id, ctx.author.id, f"Removed warning {warn_id}")
        await ctx.send(f"Removed warning {warn_id} for user {user.mention}. (Case #{case_id})")
    else:
        await ctx.send(f"Warning {warn_id} not found for user {user.mention}.", ephemeral=True)

@bot.hybrid_command(description="Lists warnings for a specific member.")
@has_permission('JR_MOD_ROLE_ID')
async def warnings(ctx, member: discord.Member):
    warnings_list = database.get_warnings(member.id)
    if not warnings_list:
        await ctx.send(f"{member.mention} has no warnings.")
        return

    embed = discord.Embed(title=f"Warnings for {member.name}", color=discord.Color.orange())
    for warn_id, reason, staff_id, timestamp in warnings_list:
        staff_member = ctx.guild.get_member(staff_id)
        staff_name = staff_member.name if staff_member else f"ID: {staff_id}"
        embed.add_field(
            name=f"ID: {warn_id} | Date: {timestamp[:10]}",
            value=f"**Reason:** {reason}\n**Staff:** {staff_name}",
            inline=False
        )
    await ctx.send(embed=embed)

# --- Notes Commands ---

@bot.hybrid_command(description="Adds a note to a user.")
@app_commands.describe(user="The user", text="The note content")
@has_permission('LOW_STAFF_ROLE_ID')
async def note(ctx, user: discord.User, *, text: str):
    database.add_note(user.id, text, ctx.author.id)
    database.log_action("NOTE_ADD", user.id, ctx.author.id, "Added note", text)
    await ctx.send(f"Note added for user {user.mention}.")

@bot.hybrid_command(description="Deletes a specific note.")
@app_commands.describe(user="The user", note_id="ID of the note to delete")
@has_permission('LOW_STAFF_ROLE_ID')
async def delnote(ctx, user: discord.User, note_id: int):
    if database.delete_note(note_id, user.id):
        database.log_action("NOTE_DELETE", user.id, ctx.author.id, f"Deleted note {note_id}")
        await ctx.send(f"Deleted note {note_id} for user {user.mention}.")
    else:
        await ctx.send(f"Note {note_id} not found for user {user.mention}.", ephemeral=True)

@bot.hybrid_command(description="Shows all notes for a user.")
@app_commands.describe(user="The user")
@has_permission('LOW_STAFF_ROLE_ID')
async def notes(ctx, user: discord.User):
    notes_list = database.get_notes(user.id)
    if not notes_list:
        await ctx.send(f"No notes found for user {user.mention}.")
        return

    embed = discord.Embed(title=f"Notes for User {user.name}", color=discord.Color.blue())
    for note_id, text, staff_id, timestamp in notes_list:
        staff_member = ctx.guild.get_member(staff_id)
        staff_name = staff_member.name if staff_member else f"ID: {staff_id}"
        embed.add_field(
            name=f"ID: {note_id} | Date: {timestamp[:10]}",
            value=f"**Note:** {text}\n**Staff:** {staff_name}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Clears all notes for a user.")
@app_commands.describe(user="The user")
@has_permission('SR_MOD_ROLE_ID')
async def clearnotes(ctx, user: discord.User):
    database.clear_notes(user.id)
    database.log_action("NOTE_CLEAR", user.id, ctx.author.id, "Cleared all notes")
    await ctx.send(f"Cleared all notes for user {user.mention}.")

@bot.hybrid_command(description="Edits a note.")
@app_commands.describe(user="The user", note_id="ID of the note", new_text="New note content")
@has_permission('SR_MOD_ROLE_ID')
async def editnote(ctx, user: discord.User, note_id: int, *, new_text: str):
    if database.edit_note(note_id, new_text, user.id):
        database.log_action("NOTE_EDIT", user.id, ctx.author.id, f"Edited note {note_id}", new_text)
        await ctx.send(f"Edited note {note_id} for user {user.mention}.")
    else:
        await ctx.send(f"Note {note_id} not found for user {user.mention}.", ephemeral=True)

@bot.hybrid_command(description="Bans a user from the server (even if not in server).")
@app_commands.describe(user="The user to ban", reason="Reason for the ban")
@has_permission('MOD_ROLE_ID')
async def ban(ctx, user: discord.User, *, reason: str = "No reason provided"):
    try:
        case_id = database.log_action("BAN", user.id, ctx.author.id, reason)
        # Try to send DM if user shares a server, otherwise pass
        await send_dm_log(user, "Banned", reason, case_id, ctx.guild.name)
        await ctx.guild.ban(user, reason=reason)
        await ctx.send(f"{user.mention} has been banned. Reason: {reason} (Case #{case_id})")
    except discord.Forbidden:
        await ctx.send("I do not have permission to ban this user.", ephemeral=True)

@bot.hybrid_command(description="Unbans a user from the server.")
@app_commands.describe(user="The user to unban (ID or mention)", reason="Reason for the unban")
@has_permission('MOD_ROLE_ID')
async def unban(ctx, user: discord.User, *, reason: str = "No reason provided"):
    try:
        await ctx.guild.unban(user, reason=reason)
        case_id = database.log_action("UNBAN", user.id, ctx.author.id, reason)
        await ctx.send(f"{user.mention} has been unbanned. Reason: {reason} (Case #{case_id})")
    except discord.NotFound:
        await ctx.send("User not found or not banned.", ephemeral=True)
    except discord.Forbidden:
        await ctx.send("I do not have permission to unban users.", ephemeral=True)
    except discord.HTTPException:
        await ctx.send("Failed to unban user.", ephemeral=True)

@bot.hybrid_command(description="Star a message (send content/embed to a channel).")
@app_commands.describe(message_id="ID of the message to star")
@has_permission('LOW_STAFF_ROLE_ID')
async def star(ctx, message_id: str):
    # Retrieve target channel from env or config. Using placeholder for now as requested.
    STAR_CHANNEL_ID = int(os.getenv('STAR_CHANNEL_ID', 0))
    if not STAR_CHANNEL_ID:
         await ctx.send("Star channel ID not set in environment variables.", ephemeral=True)
         return

    try:
        msg_id_int = int(message_id)
        # Fetch message from current channel
        message = await ctx.channel.fetch_message(msg_id_int)

        channel = bot.get_channel(STAR_CHANNEL_ID)
        if not channel:
            await ctx.send("Star channel not found.", ephemeral=True)
            return

        embed = discord.Embed(description=message.content, color=discord.Color.gold())
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="Original", value=f"[Jump to message]({message.jump_url})")

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        await channel.send(embed=embed)
        await ctx.send(f"Starred message {message_id} to {channel.mention}.")

    except ValueError:
        await ctx.send("Invalid Message ID format.", ephemeral=True)
    except discord.NotFound:
        await ctx.send("Message not found.", ephemeral=True)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}", ephemeral=True)

@bot.hybrid_command(description="Displays a user's avatar.")
@app_commands.describe(user="The user")
async def av(ctx, user: discord.User):
    embed = discord.Embed(title=f"Avatar for {user.name}", color=discord.Color.blue())
    embed.set_image(url=user.display_avatar.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Shows moderation logs (warns, mutes) for a user.")
@app_commands.describe(user="The user")
@has_permission('SR_MOD_ROLE_ID')
async def modlogs(ctx, user: discord.User):
    logs = database.get_mod_logs(user.id)

    if not logs:
        await ctx.send(f"No moderation logs found for user {user.mention}.")
        return

    embed = discord.Embed(title=f"Mod Logs for {user.name}", color=discord.Color.red())
    # Discord embed fields have limits, so we slice if too many, or just show last 10
    for case_id, action, staff_id, reason, timestamp, extra in logs[-10:]:
        staff_member = ctx.guild.get_member(staff_id)
        staff_name = staff_member.name if staff_member else f"ID: {staff_id}"
        value_str = f"**Staff:** {staff_name}\n**Reason:** {reason}"
        if extra:
            value_str += f"\n**Extra:** {extra}"
        embed.add_field(name=f"Case #{case_id} | {action} | {timestamp[:10]}", value=value_str, inline=False)

    await ctx.send(embed=embed)

@bot.hybrid_command(description="Shows stats for a moderator.")
@app_commands.describe(user="The moderator")
@has_permission('SR_ADMIN_ROLE_ID')
async def modstats(ctx, user: discord.User):
    stats = database.get_mod_stats(user.id)

    if not stats:
        await ctx.send(f"No stats found for staff {user.mention}.")
        return

    embed = discord.Embed(title=f"Mod Stats for {user.name}", color=discord.Color.purple())
    for action, count in stats:
        embed.add_field(name=action, value=str(count), inline=True)

    await ctx.send(embed=embed)

@bot.hybrid_command(description="Shows recent moderation actions.")
@has_permission('SR_ADMIN_ROLE_ID')
async def moderations(ctx):
    logs = database.get_recent_moderations(limit=10) # Showing 10 to fit in one embed easily

    if not logs:
        await ctx.send("No recent moderations found.")
        return

    embed = discord.Embed(title="Recent Moderations", color=discord.Color.dark_red())
    for action, user_id, staff_id, reason, timestamp in logs:
        staff_member = ctx.guild.get_member(staff_id)
        staff_name = staff_member.name if staff_member else f"ID: {staff_id}"
        embed.add_field(
            name=f"{action} | {timestamp[:19]}",
            value=f"**User:** {user_id}\n**Staff:** {staff_name}\n**Reason:** {reason}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Responds with Pong!")
async def ping(ctx):
    await ctx.send('Pong!')

@bot.hybrid_command(description="Repeats the provided message.")
@app_commands.describe(message="The message to repeat")
async def echo(ctx, *, message: str):
    await ctx.send(message)

@bot.hybrid_command(description="Rolls a dice.")
@app_commands.describe(sides="Number of sides on the dice")
async def roll(ctx, sides: int = 6):
    result = random.randint(1, sides)
    await ctx.send(str(result))

@bot.hybrid_command(name='8ball', description="Ask the magic 8-ball a question.")
@app_commands.describe(question="The question to ask")
async def eight_ball(ctx, *, question: str):
    responses = [
        "It is certain.",
        "It is decidedly so.",
        "Without a doubt.",
        "Yes - definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    await ctx.send(f'Question: {question}\nAnswer: {random.choice(responses)}')

@bot.hybrid_command(description="Shows details of a specific moderation case.")
@app_commands.describe(case_id="ID of the case to look up")
@has_permission('ADMIN_ROLE_ID')
async def case(ctx, case_id: int):
    log = database.get_case(case_id)
    if not log:
        await ctx.send(f"Case #{case_id} not found.")
        return

    # log structure: (id, action, user_id, staff_id, reason, timestamp, extra_data)
    _, action, user_id, staff_id, reason, timestamp, extra_data = log

    staff_member = ctx.guild.get_member(staff_id)
    staff_name = staff_member.name if staff_member else f"ID: {staff_id}"

    embed = discord.Embed(title=f"Case #{case_id} | {action}", color=discord.Color.gold())
    embed.add_field(name="User", value=f"<@{user_id}> ({user_id})", inline=True)
    embed.add_field(name="Staff", value=f"{staff_name} ({staff_id})", inline=True)
    embed.add_field(name="Timestamp", value=f"{timestamp[:19]}", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)

    if extra_data:
        embed.add_field(name="Extra Data", value=extra_data, inline=False)

    await ctx.send(embed=embed)

@bot.hybrid_command(description="Unmutes a member.")
@app_commands.describe(member="The member to unmute")
@has_permission('LOW_STAFF_ROLE_ID')
async def unmute(ctx, member: discord.Member):
    try:
        await member.timeout(None, reason="Unmuted by staff")
        case_id = database.log_action("UNMUTE", member.id, ctx.author.id, "Unmuted by staff")
        await ctx.send(f"{member.mention} has been unmuted. (Case #{case_id})")
    except discord.Forbidden:
        await ctx.send("I do not have permission to perform this action on this user. They might have a higher role than me.", ephemeral=True)

# Config
CSV_FILE = "devoluciones.csv"
# Users allowed to use CSV commands (IDs from user input)
CSV_ALLOWED_USERS = [984268053141409813, 1345943525069553714, 556428548735238155]

# ---------- CSV HELPER ----------
def inicializar_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='|')
            writer.writerow(['ID', 'Usuario', 'ID_Usuario', 'Rol', 'Dinero_Devuelto', 'Numero_Devolucion', 'Fecha'])

def agregar_fila_csv(usuario, id_usuario, rol, dinero_devuelto, numero_devolucion, fecha):
    try:
        inicializar_csv()
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if len(lines) <= 1:
                next_id = 1
            else:
                last_line = lines[-1].split('|')
                try:
                    next_id = int(last_line[0].strip()) + 1
                except ValueError:
                    next_id = 1

        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='|')
            writer.writerow([f' {next_id} ', f' {usuario} ', f' {id_usuario} ', f' {rol} ', f' {dinero_devuelto} ', f' {numero_devolucion} ', f' {fecha} '])
        return True, "Datos agregados correctamente al CSV"
    except Exception as e:
        return False, f"Error al agregar datos al CSV: {str(e)}"

def obtener_csv_como_archivo():
    if os.path.exists(CSV_FILE):
        return discord.File(CSV_FILE, filename="devoluciones.csv")
    return None

def eliminar_fila_csv_por_id(fila_id):
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        if len(lines) <= 1:
            return False, "El archivo CSV está vacío"

        encontrado = False
        nuevas_lineas = [lines[0]]

        for i, line in enumerate(lines[1:], 1):
            partes = line.split('|')
            if len(partes) > 0:
                try:
                    id_actual = int(partes[0].strip())
                except ValueError:
                    continue
                if id_actual == fila_id:
                    encontrado = True
                else:
                    nuevas_lineas.append(line)

        if encontrado:
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
                file.writelines(nuevas_lineas)
            return True, f"Fila con ID {fila_id} eliminada correctamente"
        else:
            return False, f"No se encontró ninguna fila con ID {fila_id}"
    except Exception as e:
        return False, f"Error al eliminar fila del CSV: {str(e)}"

def reset_csv_file():
    try:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='|')
            writer.writerow(['ID', 'Usuario', 'ID_Usuario', 'Rol', 'Dinero_Devuelto', 'Numero_Devolucion', 'Fecha'])
        return True, "CSV reseteado correctamente"
    except Exception as e:
        return False, f"Error al resetear CSV: {str(e)}"

class ResetCSVView(View):
    def __init__(self, ctx):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label="✅", style=discord.ButtonStyle.success, custom_id="confirm_csv")
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("These buttons are not for you.", ephemeral=True)
            return

        self.value = True
        self.stop()
        success, message = reset_csv_file()
        if success:
            embed = discord.Embed(title="✅ CSV Reset", description="CSV file has been successfully reset.", color=discord.Color.green())
        else:
            embed = discord.Embed(title="❌ Error", description=f"Error resetting CSV: {message}", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger, custom_id="cancel_csv")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("These buttons are not for you.", ephemeral=True)
            return
        self.value = False
        self.stop()
        embed = discord.Embed(title="❌ Cancelled", description="CSV reset has been cancelled.", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=None)

# ---------- NEW FEATURES COMMANDS ----------

@bot.hybrid_command(description="Sets the role to be given on member join.")
@app_commands.describe(role="The role to give")
@has_permission('ADMIN_ROLE_ID')
async def autorole(ctx, subcommand: str, role: discord.Role = None, member: discord.Member = None):
    # Subcommands via arguments for simplicity in hybrid commands
    if subcommand.lower() == "set":
        if not role:
            await ctx.send("Please specify a role.", ephemeral=True)
            return
        database.set_config(ctx.guild.id, autorole_id=role.id)
        await ctx.send(f"✅ Autorole set to {role.mention}")
    elif subcommand.lower() == "give" and member and role:
        await member.add_roles(role)
        await ctx.send(f"✅ Gave {role.mention} to {member.mention}")
    elif subcommand.lower() == "giveall" and role:
        await ctx.send(f"⏳ Giving {role.mention} to all members... This may take a while.")
        count = 0
        for m in ctx.guild.members:
            if not m.bot and role not in m.roles:
                try:
                    await m.add_roles(role)
                    count += 1
                    await asyncio.sleep(1) # Rate limit protection
                except:
                    pass
        await ctx.send(f"✅ Gave {role.mention} to {count} members.")
    else:
        await ctx.send("Usage: `/autorole set <role>`, `/autorole give <member> <role>`, `/autorole giveall <role>`", ephemeral=True)

@bot.event
async def on_member_join(member):
    config = database.get_config(member.guild.id)
    role_id = config["autorole_id"]
    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except:
                pass

# Ranking System
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Cooldown check (simple in-memory for now)
    # Using a dict {user_id: timestamp}
    if not hasattr(bot, 'ranking_cooldowns'):
        bot.ranking_cooldowns = {}

    last_msg = bot.ranking_cooldowns.get(message.author.id)
    now = datetime.datetime.now()

    if not last_msg or (now - last_msg).total_seconds() > 60:
        database.update_points(message.author.id, message.author.name, 1)
        bot.ranking_cooldowns[message.author.id] = now

    await bot.process_commands(message)

@bot.hybrid_command(description="Add points to a user.")
@app_commands.describe(member="The user", amount="Points to add")
@has_permission('LOW_STAFF_ROLE_ID')
async def addpoints(ctx, member: discord.Member, amount: int):
    database.update_points(member.id, member.name, amount)
    await ctx.send(f"✅ Added {amount} points to {member.mention}")

@bot.hybrid_command(description="Remove points from a user.")
@app_commands.describe(member="The user", amount="Points to remove")
@has_permission('LOW_STAFF_ROLE_ID')
async def removepoints(ctx, member: discord.Member, amount: int):
    database.update_points(member.id, member.name, -amount)
    await ctx.send(f"✅ Removed {amount} points from {member.mention}")

@bot.hybrid_command(description="Get points of a user.")
@app_commands.describe(member="The user")
async def getpoints(ctx, member: discord.Member = None):
    member = member or ctx.author
    points = database.get_points(member.id)
    await ctx.send(f"📊 {member.mention} has {points} points.")

@bot.hybrid_command(description="Show ranking leaderboard.")
async def ranking(ctx):
    top = database.get_ranking()
    if not top:
        await ctx.send("Ranking empty.")
        return

    embed = discord.Embed(title="🏆 Ranking", color=discord.Color.gold())
    for i, (user_id, username, points) in enumerate(top[:10], start=1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "⭐"
        embed.add_field(name=f"{i}. {medal} {username}", value=f"{points} points", inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Show all server warnings.")
@has_permission('JR_MOD_ROLE_ID')
async def allwarnings(ctx):
    warns = database.get_all_warnings()
    if not warns:
        await ctx.send("No warnings found.")
        return

    embed = discord.Embed(title="⚠️ All Warnings (Last 10)", color=discord.Color.orange())
    for warn_id, user_id, reason, staff_id, timestamp in warns[:10]:
        staff = ctx.guild.get_member(staff_id)
        staff_name = staff.name if staff else f"ID:{staff_id}"
        embed.add_field(name=f"ID: {warn_id} | User: {user_id}", value=f"Reason: {reason}\nBy: {staff_name}", inline=False)
    await ctx.send(embed=embed)

# CSV Commands
@bot.hybrid_command(name="csv", description="Create CSV file.")
async def csv_create(ctx):
    if ctx.author.id not in CSV_ALLOWED_USERS:
        await ctx.send("❌ No permission.", ephemeral=True)
        return
    inicializar_csv()
    await ctx.send("✅ CSV file initialized.")

@bot.hybrid_command(name="addcsv", description="Add info to CSV.")
@app_commands.describe(usuario="User", id_usuario="User ID", rol="Role", dinero_devuelto="Money", numero_devolucion="Return #", fecha="Date")
async def addcsv(ctx, usuario: str, id_usuario: str, rol: str, dinero_devuelto: str, numero_devolucion: str, fecha: str):
    if ctx.author.id not in CSV_ALLOWED_USERS:
        await ctx.send("❌ No permission.", ephemeral=True)
        return
    success, msg = agregar_fila_csv(usuario, id_usuario, rol, dinero_devuelto, numero_devolucion, fecha)
    await ctx.send(f"{'✅' if success else '❌'} {msg}")

@bot.hybrid_command(name="removecsv", description="Remove info from CSV.")
@app_commands.describe(fila_id="Row ID")
async def removecsv(ctx, fila_id: int):
    if ctx.author.id not in CSV_ALLOWED_USERS:
        await ctx.send("❌ No permission.", ephemeral=True)
        return
    success, msg = eliminar_fila_csv_por_id(fila_id)
    await ctx.send(f"{'✅' if success else '❌'} {msg}")

@bot.hybrid_command(name="resetcsv", description="Reset CSV file.")
async def resetcsv(ctx):
    if ctx.author.id not in CSV_ALLOWED_USERS:
        await ctx.send("❌ No permission.", ephemeral=True)
        return
    view = ResetCSVView(ctx)
    await ctx.send("⚠️ Reset CSV?", view=view)

if __name__ == '__main__':
    if TOKEN:
        try:
            bot.run(TOKEN)
        except discord.errors.LoginFailure:
            print("Error: Invalid Discord Token. Please check your .env file and ensure DISCORD_TOKEN is correct.")
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")
        print("Please create a .env file (you can copy .env.example) and add your DISCORD_TOKEN.")
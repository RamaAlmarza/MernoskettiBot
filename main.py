import os
import random
import asyncio
import datetime
import discord
from discord import app_commands
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

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=intents)

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
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

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

@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Syncs commands to the current guild for instant updates."""
    try:
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(synced)} command(s) to this guild.")
    except Exception as e:
        await ctx.send(f"Failed to sync commands: {e}")

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
@app_commands.describe(user_id="ID of the user", warn_id="ID of the warning to remove")
@has_permission('MOD_ROLE_ID')
async def warn_remove(ctx, user_id: str, warn_id: int):
    try:
        user_id_int = int(user_id)
        if database.remove_warning(warn_id, user_id_int):
            case_id = database.log_action("WARN_REMOVE", user_id_int, ctx.author.id, f"Removed warning {warn_id}")
            await ctx.send(f"Removed warning {warn_id} for user {user_id}. (Case #{case_id})")
        else:
            await ctx.send(f"Warning {warn_id} not found for user {user_id}.", ephemeral=True)
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)

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
@app_commands.describe(user_id="ID of the user", text="The note content")
@has_permission('LOW_STAFF_ROLE_ID')
async def note(ctx, user_id: str, *, text: str):
    try:
        user_id_int = int(user_id)
        database.add_note(user_id_int, text, ctx.author.id)
        database.log_action("NOTE_ADD", user_id_int, ctx.author.id, "Added note", text)
        await ctx.send(f"Note added for user {user_id}.")
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)

@bot.hybrid_command(description="Deletes a specific note.")
@app_commands.describe(user_id="ID of the user", note_id="ID of the note to delete")
@has_permission('LOW_STAFF_ROLE_ID')
async def delnote(ctx, user_id: str, note_id: int):
    try:
        user_id_int = int(user_id)
        if database.delete_note(note_id, user_id_int):
            database.log_action("NOTE_DELETE", user_id_int, ctx.author.id, f"Deleted note {note_id}")
            await ctx.send(f"Deleted note {note_id} for user {user_id}.")
        else:
             await ctx.send(f"Note {note_id} not found for user {user_id}.", ephemeral=True)
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)

@bot.hybrid_command(description="Shows all notes for a user.")
@app_commands.describe(user_id="ID of the user")
@has_permission('LOW_STAFF_ROLE_ID')
async def notes(ctx, user_id: str):
    try:
        user_id_int = int(user_id)
        notes_list = database.get_notes(user_id_int)
        if not notes_list:
            await ctx.send(f"No notes found for user {user_id}.")
            return

        embed = discord.Embed(title=f"Notes for User {user_id}", color=discord.Color.blue())
        for note_id, text, staff_id, timestamp in notes_list:
            staff_member = ctx.guild.get_member(staff_id)
            staff_name = staff_member.name if staff_member else f"ID: {staff_id}"
            embed.add_field(
                name=f"ID: {note_id} | Date: {timestamp[:10]}",
                value=f"**Note:** {text}\n**Staff:** {staff_name}",
                inline=False
            )
        await ctx.send(embed=embed)
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)

@bot.hybrid_command(description="Clears all notes for a user.")
@app_commands.describe(user_id="ID of the user")
@has_permission('SR_MOD_ROLE_ID')
async def clearnotes(ctx, user_id: str):
    try:
        user_id_int = int(user_id)
        database.clear_notes(user_id_int)
        database.log_action("NOTE_CLEAR", user_id_int, ctx.author.id, "Cleared all notes")
        await ctx.send(f"Cleared all notes for user {user_id}.")
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)

@bot.hybrid_command(description="Edits a note.")
@app_commands.describe(user_id="ID of the user", note_id="ID of the note", new_text="New note content")
@has_permission('SR_MOD_ROLE_ID')
async def editnote(ctx, user_id: str, note_id: int, *, new_text: str):
    try:
        user_id_int = int(user_id)
        if database.edit_note(note_id, new_text, user_id_int):
            database.log_action("NOTE_EDIT", user_id_int, ctx.author.id, f"Edited note {note_id}", new_text)
            await ctx.send(f"Edited note {note_id} for user {user_id}.")
        else:
             await ctx.send(f"Note {note_id} not found for user {user_id}.", ephemeral=True)
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)

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

@bot.hybrid_command(description="Unbans a user from the server using their ID.")
@app_commands.describe(user_id="The ID of the user to unban", reason="Reason for the unban")
@has_permission('MOD_ROLE_ID')
async def unban(ctx, user_id: str, *, reason: str = "No reason provided"):
    try:
        user_id_int = int(user_id)
        user = await bot.fetch_user(user_id_int)
        await ctx.guild.unban(user, reason=reason)
        case_id = database.log_action("UNBAN", user_id_int, ctx.author.id, reason)
        await ctx.send(f"{user.mention} has been unbanned. Reason: {reason} (Case #{case_id})")
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)
    except discord.NotFound:
        await ctx.send("User not found.", ephemeral=True)
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
@app_commands.describe(user_id="ID of the user")
async def av(ctx, user_id: str):
    try:
        user_id_int = int(user_id)
        user = await bot.fetch_user(user_id_int)
        embed = discord.Embed(title=f"Avatar for {user.name}", color=discord.Color.blue())
        embed.set_image(url=user.display_avatar.url)
        await ctx.send(embed=embed)
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)
    except discord.NotFound:
         await ctx.send("User not found.", ephemeral=True)

@bot.hybrid_command(description="Shows moderation logs (warns, mutes) for a user.")
@app_commands.describe(user_id="ID of the user")
@has_permission('SR_MOD_ROLE_ID')
async def modlogs(ctx, user_id: str):
    try:
        user_id_int = int(user_id)
        logs = database.get_mod_logs(user_id_int)

        if not logs:
            await ctx.send(f"No moderation logs found for user {user_id}.")
            return

        embed = discord.Embed(title=f"Mod Logs for {user_id}", color=discord.Color.red())
        # Discord embed fields have limits, so we slice if too many, or just show last 10
        for case_id, action, staff_id, reason, timestamp, extra in logs[-10:]:
             staff_member = ctx.guild.get_member(staff_id)
             staff_name = staff_member.name if staff_member else f"ID: {staff_id}"
             value_str = f"**Staff:** {staff_name}\n**Reason:** {reason}"
             if extra:
                 value_str += f"\n**Extra:** {extra}"
             embed.add_field(name=f"Case #{case_id} | {action} | {timestamp[:10]}", value=value_str, inline=False)

        await ctx.send(embed=embed)
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)

@bot.hybrid_command(description="Shows stats for a moderator.")
@app_commands.describe(user_id="ID of the moderator")
@has_permission('SR_ADMIN_ROLE_ID')
async def modstats(ctx, user_id: str):
    try:
        user_id_int = int(user_id)
        stats = database.get_mod_stats(user_id_int)

        if not stats:
            await ctx.send(f"No stats found for staff {user_id}.")
            return

        embed = discord.Embed(title=f"Mod Stats for {user_id}", color=discord.Color.purple())
        for action, count in stats:
            embed.add_field(name=action, value=str(count), inline=True)

        await ctx.send(embed=embed)
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)

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

if __name__ == '__main__':
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")
        print("Please create a .env file (you can copy .env.example) and add your DISCORD_TOKEN.")

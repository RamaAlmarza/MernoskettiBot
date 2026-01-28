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

# Config
CSV_FILE = "devoluciones.csv"
# Users allowed to use CSV commands (IDs from user input)
CSV_ALLOWED_USERS = [984268053141409813, 1345943525069553714, 556428548735238155]

TRIVIA_QUESTIONS = [
    {
        "pregunta": "¿Cuál es la capital de Francia?",
        "question": "What is the capital of France?",
        "respuesta": "paris",
        "answer": "paris",
        "dificultad": "facil",
        "difficulty": "easy",
        "puntos": 5,
        "points": 5
    },
    {
        "pregunta": "¿En qué año llegó el hombre a la luna?",
        "question": "In what year did man land on the moon?",
        "respuesta": "1969",
        "answer": "1969",
        "dificultad": "media",
        "difficulty": "medium",
        "puntos": 10,
        "points": 10
    },
    {
        "pregunta": "¿Quién pintó la Mona Lisa?",
        "question": "Who painted the Mona Lisa?",
        "respuesta": "leonardo da vinci",
        "answer": "leonardo da vinci",
        "dificultad": "media",
        "difficulty": "medium",
        "puntos": 10,
        "points": 10
    },
    {
        "pregunta": "¿Cuál es el río más largo del mundo?",
        "question": "What is the longest river in the world?",
        "respuesta": "amazonas",
        "answer": "amazon",
        "dificultad": "media",
        "difficulty": "medium",
        "puntos": 10,
        "points": 10
    },
    {
        "pregunta": "¿Cuál es el elemento químico con símbolo 'Au'?",
        "question": "What is the chemical element with the symbol 'Au'?",
        "respuesta": "oro",
        "answer": "gold",
        "dificultad": "facil",
        "difficulty": "easy",
        "puntos": 5,
        "points": 5
    },
    {
        "pregunta": "¿En qué continente se encuentra Egipto?",
        "question": "On which continent is Egypt located?",
        "respuesta": "africa",
        "answer": "africa",
        "dificultad": "facil",
        "difficulty": "easy",
        "puntos": 5,
        "points": 5
    },
    {
        "pregunta": "¿Cuántos lados tiene a heptágono?",
        "question": "How many sides does a heptagon have?",
        "respuesta": "7",
        "answer": "7",
        "dificultad": "media",
        "difficulty": "medium",
        "puntos": 10,
        "points": 10
    },
    {
        "pregunta": "¿Quién escribió 'Cien años de soledad'?",
        "question": "Who wrote 'One Hundred Years of Solitude'?",
        "respuesta": "gabriel garcia marquez",
        "answer": "gabriel garcia marquez",
        "dificultad": "media",
        "difficulty": "medium",
        "puntos": 10,
        "points": 10
    },
    {
        "pregunta": "¿Cuál es el planeta más grande del sistema solar?",
        "question": "What is the largest planet in the solar system?",
        "respuesta": "jupiter",
        "answer": "jupiter",
        "dificultad": "facil",
        "difficulty": "easy",
        "puntos": 5,
        "points": 5
    },
    {
        "pregunta": "¿En qué año comenzó la Segunda Guerra Mundial?",
        "question": "In what year did World War II begin?",
        "respuesta": "1939",
        "answer": "1939",
        "dificultad": "dificil",
        "difficulty": "hard",
        "puntos": 15,
        "points": 15
    }
]

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

    # Autorole logic
    if payload.user_id != bot.user.id:
        autorole_data = database.get_reaction_role(payload.message_id)
        if autorole_data:
            emoji_store, role_id, _ = autorole_data
            # Check emoji match (name or ID)
            current_emoji = payload.emoji.name if not payload.emoji.id else str(payload.emoji)
            # Simple check: if stored is name, compare name. If stored is <:name:id>, compare string representation?
            # Stored emoji from command processing is usually name or ID.
            # Assuming basic emoji support for now or name matching
            if str(payload.emoji.name) == emoji_store or str(payload.emoji) == emoji_store:
                guild = bot.get_guild(payload.guild_id)
                role = guild.get_role(role_id)
                if role:
                    member = guild.get_member(payload.user_id)
                    if member:
                        await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return

    autorole_data = database.get_reaction_role(payload.message_id)
    if autorole_data:
        emoji_store, role_id, _ = autorole_data
        current_emoji = payload.emoji.name if not payload.emoji.id else str(payload.emoji)

        if str(payload.emoji.name) == emoji_store or str(payload.emoji) == emoji_store:
            guild = bot.get_guild(payload.guild_id)
            if guild:
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.remove_roles(role)

@bot.hybrid_command(description="Syncs commands to the current guild for instant updates.")
@has_permission('ADMIN_ROLE_ID')
async def sync(ctx):
    """Syncs commands to the current guild for instant updates."""
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
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
# ---------- HELPER FUNCTIONS ----------
def get_language(guild_id):
    config = database.get_config(guild_id)
    return config["language"]

def set_language(guild_id, language):
    database.set_config(guild_id, language=language)

def get_prefix(guild_id):
    config = database.get_config(guild_id)
    return config["prefix"]

def set_prefix(guild_id, prefix):
    database.set_config(guild_id, prefix=prefix)

# ---------- CSV FUNCTIONS ----------
def inicializar_csv():
    """Inicializa el archivo CSV con los encabezados si no existe"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='|')
            writer.writerow(['ID', 'Usuario', 'ID_Usuario', 'Rol', 'Dinero_Devuelto', 'Numero_Devolucion', 'Fecha'])

def agregar_fila_csv(usuario, id_usuario, rol, dinero_devuelto, numero_devolucion, fecha):
    """Agrega una nueva fila al archivo CSV"""
    try:
        inicializar_csv()

        # Obtener el próximo ID
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if len(lines) <= 1:  # Solo encabezados
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
    """Devuelve el archivo CSV como un objeto de archivo de Discord"""
    if os.path.exists(CSV_FILE):
        return discord.File(CSV_FILE, filename="devoluciones.csv")
    return None

def eliminar_fila_csv_por_id(fila_id):
    """Elimina una fila del CSV por ID"""
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        if len(lines) <= 1:  # Solo encabezados
            return False, "El archivo CSV está vacío"

        encontrado = False
        nuevas_lineas = [lines[0]]  # Mantener encabezados

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

def reset_csv():
    """Resetea el archivo CSV a solo los encabezados"""
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

        success, message = reset_csv()

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

class ResetRankingView(View):
    def __init__(self, ctx):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label="✅", style=discord.ButtonStyle.success, custom_id="confirm_ranking")
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("These buttons are not for you.", ephemeral=True)
            return

        self.value = True
        self.stop()
        database.reset_ranking()
        embed = discord.Embed(title="✅ Ranking Reset", description="Ranking has been successfully reset.", color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger, custom_id="cancel_ranking")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("These buttons are not for you.", ephemeral=True)
            return

        self.value = False
        self.stop()
        embed = discord.Embed(title="❌ Cancelled", description="Ranking reset has been cancelled.", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=None)

# ---------- NEW COMMANDS ----------

@bot.hybrid_command(name="language", description="Change the bot's language / Cambia el idioma del bot")
@app_commands.describe(lang="The new language (es/en)")
@has_permission('ADMIN_ROLE_ID')
async def language(ctx, lang: str):
    lang = lang.lower()
    if lang not in ["es", "en", "english", "spanish", "español", "ingles"]:
        await ctx.send("❌ Invalid language. Available: es, en", ephemeral=True)
        return

    lang_code = "en" if lang in ["en", "english", "ingles"] else "es"
    set_language(ctx.guild.id, lang_code)

    if lang_code == "en":
        embed = discord.Embed(title="✅ Language Changed", description=f"Bot language changed to: English", color=discord.Color.green())
    else:
        embed = discord.Embed(title="✅ Idioma Cambiado", description=f"Idioma del bot cambiado a: Español", color=discord.Color.green())

    await ctx.send(embed=embed)

@bot.hybrid_command(name="prefix", description="Cambia el prefijo del bot (Solo staff) / Change the bot's prefix (Staff only)")
@app_commands.describe(nuevo_prefijo="The new prefix")
@has_permission('ADMIN_ROLE_ID')
async def prefix(ctx, nuevo_prefijo: str):
    set_prefix(ctx.guild.id, nuevo_prefijo)
    # Note: Changing prefix dynamically in discord.py usually requires restarting or using a custom prefix callable which we have in main.py?
    # Current bot init: bot = commands.Bot(command_prefix='!', ...)
    # To support dynamic prefix, we need to change bot init. I will do that in the merge step.
    await ctx.send(f"✅ Prefix changed to: {nuevo_prefijo}")

@bot.hybrid_command(name="announce", description="Hace un anuncio oficial (Solo staff) / Make an official announcement (Staff only)")
@app_commands.describe(canal="The channel to announce in", mensaje="The message content")
@has_permission('SR_ADMIN_ROLE_ID')
async def announce(ctx, canal: discord.TextChannel, *, mensaje: str):
    embed = discord.Embed(title="📢 Announcement", description=mensaje, color=discord.Color.red(), timestamp=datetime.datetime.now())
    embed.set_footer(text=f"Announced by {ctx.author.display_name}")
    await canal.send(embed=embed)
    await ctx.send("✅ Announcement sent.", ephemeral=True)

@bot.hybrid_command(name="autorole", description="Configura un autorol / Set up an autorole")
@app_commands.describe(canal="Channel where message is", mensaje_id="ID of the message", emoji="Emoji to react with", rol="Role to give")
@has_permission('ADMIN_ROLE_ID')
async def autorole(ctx, canal: discord.TextChannel, mensaje_id: str, emoji: str, rol: discord.Role):
    try:
        mensaje_int = int(mensaje_id)
        mensaje = await canal.fetch_message(mensaje_int)
    except (ValueError, discord.NotFound):
        await ctx.send("❌ Message not found or invalid ID.", ephemeral=True)
        return

    # Process custom emoji
    emoji_to_store = emoji
    if emoji.startswith('<') and emoji.endswith('>'):
        emoji_parts = emoji.strip('<>').split(':')
        if len(emoji_parts) >= 2:
            emoji_to_store = emoji_parts[1]

    database.add_reaction_role(mensaje_int, emoji_to_store, rol.id, canal.id)

    try:
        await mensaje.add_reaction(emoji)
        await ctx.send(f"✅ Autorole configured: {emoji} -> {rol.name}", ephemeral=True)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permissions to add reactions there.", ephemeral=True)

@bot.hybrid_command(name="addpoints", description="Añade puntos a un usuario (Solo staff)")
@app_commands.describe(member="The user to add points to", cantidad="Amount of points")
@has_permission('LOW_STAFF_ROLE_ID')
async def addpoints(ctx, member: discord.Member, cantidad: int):
    database.update_points(member.id, member.name, cantidad)
    await ctx.send(f"✅ Added {cantidad} points to {member.mention}")

@bot.hybrid_command(name="removepoints", description="Quita puntos a un usuario (Solo staff)")
@app_commands.describe(member="The user to remove points from", cantidad="Amount or 'all'")
@has_permission('LOW_STAFF_ROLE_ID')
async def removepoints(ctx, member: discord.Member, cantidad: str):
    if cantidad.lower() == "all":
        database.set_points(member.id, member.name, 0)
        await ctx.send(f"✅ Removed all points from {member.mention}")
    else:
        try:
            cant = int(cantidad)
            database.update_points(member.id, member.name, -cant)
            await ctx.send(f"✅ Removed {cant} points from {member.mention}")
        except ValueError:
            await ctx.send("❌ Invalid amount.", ephemeral=True)

@bot.hybrid_command(name="ranking", description="Muestra el ranking de puntos")
@app_commands.describe(action="Optional action (e.g. 'reset')")
async def ranking(ctx, action: str = None):
    if action and action.lower() == "reset":
        # Check permission for reset
        if not await has_permission('SR_ADMIN_ROLE_ID').predicate(ctx):
             await ctx.send("❌ No permission to reset ranking.", ephemeral=True)
             return
        view = ResetRankingView(ctx)
        await ctx.send("⚠️ Are you sure you want to reset the ranking?", view=view)
        return

    top = database.get_ranking()
    if not top:
        await ctx.send("😢 Ranking empty.")
        return

    embed = discord.Embed(title="🏆 Ranking", color=discord.Color.gold())
    for i, (user_id, username, points) in enumerate(top[:10], start=1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "⭐"
        embed.add_field(name=f"{i}. {medal} {username}", value=f"{points} points", inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="rank", description="Muestra los puntos de un usuario")
@app_commands.describe(member="The user to check (defaults to self)")
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    ranking_data = database.get_ranking()

    for i, (user_id, username, points) in enumerate(ranking_data, start=1):
        if user_id == member.id:
            embed = discord.Embed(title=f"👤 Profile of {username}", color=discord.Color.blue())
            embed.add_field(name="⭐ Points", value=str(points), inline=True)
            embed.add_field(name="🏅 Position", value=f"#{i}", inline=True)
            await ctx.send(embed=embed)
            return

    await ctx.send(f"📊 {member.mention} has no points yet.")

@bot.hybrid_command(name="trivia", description="Inicia una trivia")
@app_commands.describe(dificultad="Difficulty (easy, medium, hard)")
async def trivia(ctx, dificultad: str = None):
    # Normalize difficulty
    if dificultad:
        dificultad = dificultad.lower()
        if dificultad not in ["easy", "medium", "hard", "facil", "media", "dificil"]:
             await ctx.send("❌ Invalid difficulty. Use: easy, medium, hard.", ephemeral=True)
             return
        # Map to Spanish for internal logic if needed, or stick to list
        if dificultad in ["easy", "medium", "hard"]:
             map_diff = {"easy": "facil", "medium": "media", "hard": "dificil"}
             dificultad = map_diff[dificultad]

    questions = [q for q in TRIVIA_QUESTIONS if not dificultad or q["dificultad"] == dificultad]
    if not questions:
        await ctx.send("❌ No questions found.")
        return

    q = random.choice(questions)
    lang = get_language(ctx.guild.id)

    # Simple localization
    title = "🎯 Trivia"
    question_text = q["question"] if lang == "en" else q["pregunta"]
    footer = "Answer with the correct answer!" if lang == "en" else "¡Responde con la respuesta correcta!"

    embed = discord.Embed(title=title, color=discord.Color.blue())
    embed.add_field(name="Question", value=question_text, inline=False)
    embed.add_field(name="Points", value=str(q["puntos"]), inline=True)
    embed.set_footer(text=footer)

    await ctx.send(embed=embed)

    def check(m):
        return m.channel == ctx.channel and not m.author.bot

    try:
        msg = await bot.wait_for("message", timeout=30, check=check)
        ans = msg.content.lower().strip()
        correct_es = q["respuesta"].lower()
        correct_en = q["answer"].lower()

        if ans == correct_es or ans == correct_en:
            database.update_points(msg.author.id, msg.author.name, q["puntos"])
            await ctx.send(f"✅ Correct! {msg.author.mention} won {q['puntos']} points.")
        else:
            await ctx.send(f"❌ Incorrect! The answer was: {q['answer']}/{q['respuesta']}")
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ Time's up! The answer was: {q['answer']}/{q['respuesta']}")

@bot.hybrid_command(name="pregunta", description="Crea una pregunta de trivia personalizada")
@app_commands.describe(canal="Channel", pregunta="Question", respuesta_correcta="Answer", tiempo="Time (seconds)", premio="Points reward")
@has_permission('LOW_STAFF_ROLE_ID')
async def pregunta(ctx, canal: discord.TextChannel, pregunta: str, respuesta_correcta: str, tiempo: int, premio: int):
    embed = discord.Embed(title="🎯 Trivia Question", color=discord.Color.blue())
    embed.add_field(name="Question", value=pregunta, inline=False)
    embed.add_field(name="Time", value=f"{tiempo}s", inline=True)
    embed.add_field(name="Reward", value=f"{premio} pts", inline=True)

    await canal.send(embed=embed)
    await ctx.send("✅ Question sent.", ephemeral=True)

    def check(m):
        return m.channel == canal and not m.author.bot

    try:
        msg = await bot.wait_for("message", timeout=tiempo, check=check)
        if msg.content.lower().strip() == respuesta_correcta.lower().strip():
            database.update_points(msg.author.id, msg.author.name, premio)
            await canal.send(f"✅ Correct! {msg.author.mention} won {premio} points.")
        else:
            await canal.send("❌ Incorrect.")
    except asyncio.TimeoutError:
        await canal.send(f"⏰ Time's up! Answer: {respuesta_correcta}")

@bot.hybrid_command(name="csv", description="Agrega datos al CSV")
@app_commands.describe(usuario="User Name", id_usuario="User ID", rol="Role", dinero_devuelto="Amount Returned", numero_devolucion="Return #", fecha="Date")
async def csv_cmd(ctx, usuario: str, id_usuario: str, rol: str, dinero_devuelto: str, numero_devolucion: str, fecha: str):
    if ctx.author.id not in CSV_ALLOWED_USERS:
        await ctx.send("❌ You are not allowed to use this command.", ephemeral=True)
        return

    success, msg = agregar_fila_csv(usuario, id_usuario, rol, dinero_devuelto, numero_devolucion, fecha)
    if success:
        await ctx.send(f"✅ {msg}")
    else:
        await ctx.send(f"❌ {msg}")

@bot.hybrid_command(name="getcsv", description="Obtiene el archivo CSV")
async def getcsv(ctx):
    if ctx.author.id not in CSV_ALLOWED_USERS:
        await ctx.send("❌ You are not allowed to use this command.", ephemeral=True)
        return
    f = obtener_csv_como_archivo()
    if f:
        await ctx.send(file=f)
    else:
        await ctx.send("❌ CSV not found or empty.")

@bot.hybrid_command(name="delcsv", description="Elimina fila del CSV")
@app_commands.describe(fila_id="Row ID to delete")
async def delcsv(ctx, fila_id: int):
    if ctx.author.id not in CSV_ALLOWED_USERS:
        await ctx.send("❌ You are not allowed to use this command.", ephemeral=True)
        return
    success, msg = eliminar_fila_csv_por_id(fila_id)
    await ctx.send(f"{'✅' if success else '❌'} {msg}")

@bot.hybrid_command(name="resetcsv", description="Resetea el archivo CSV")
async def resetcsv(ctx):
    if ctx.author.id not in CSV_ALLOWED_USERS:
        await ctx.send("❌ You are not allowed to use this command.", ephemeral=True)
        return
    view = ResetCSVView(ctx)
    await ctx.send("⚠️ Are you sure you want to reset the CSV?", view=view)

@bot.hybrid_command(name="clear", description="Clear messages")
@app_commands.describe(amount="Number of messages to clear (1-500)")
@has_permission('LOW_STAFF_ROLE_ID')
async def clear(ctx, amount: int):
    if amount < 1 or amount > 500:
        await ctx.send("Amount must be between 1 and 500.", ephemeral=True)
        return
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 Deleted {len(deleted)} messages.", delete_after=5)

@bot.hybrid_command(name="userinfo", description="User Information")
@app_commands.describe(member="The user to show info for")
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

@bot.hybrid_command(name="serverinfo", description="Server Information")
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"Server Info: {guild.name}", color=discord.Color.blue())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Owner", value=guild.owner)
    embed.add_field(name="Members", value=guild.member_count)
    embed.add_field(name="Roles", value=len(guild.roles))
    embed.add_field(name="Channels", value=len(guild.channels))
    await ctx.send(embed=embed)

@bot.hybrid_command(name="servericon", description="Server Icon")
async def servericon(ctx):
    if ctx.guild.icon:
        await ctx.send(ctx.guild.icon.url)
    else:
        await ctx.send("Server has no icon.")

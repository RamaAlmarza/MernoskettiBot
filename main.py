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

@bot.hybrid_command(description="Mutes a member for the specified duration.")
@app_commands.describe(duration="Duration (e.g., 10m, 1h)", reason="Reason for the mute")
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
    delta = convert_duration(duration)
    if not delta:
        await ctx.send("Invalid duration format. Use s, m, h, or d (e.g., 10m).", ephemeral=True)
        return

    await member.timeout(delta, reason=reason)
    await ctx.send(f"{member.mention} has been muted for {duration}. Reason: {reason}")

@bot.hybrid_command(description="Warns a member.")
@app_commands.describe(reason="Reason for the warning")
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    database.add_warning(member.id, reason, ctx.author.id)
    try:
        await member.send(f"You have been warned in {ctx.guild.name}. Reason: {reason}")
    except discord.Forbidden:
        pass
    await ctx.send(f"{member.mention} has been warned. Reason: {reason}")

@bot.hybrid_command(description="Lists warnings for a specific member.")
@commands.has_permissions(manage_messages=True)
async def warnings(ctx, member: discord.Member):
    warnings_list = database.get_warnings(member.id)
    if not warnings_list:
        await ctx.send(f"{member.mention} has no warnings.")
        return

    embed = discord.Embed(title=f"Warnings for {member.name}", color=discord.Color.orange())
    for reason, staff_id, timestamp in warnings_list:
        staff_member = ctx.guild.get_member(staff_id)
        staff_name = staff_member.name if staff_member else f"ID: {staff_id}"
        embed.add_field(
            name=f"Date: {timestamp[:10]}",
            value=f"**Reason:** {reason}\n**Staff:** {staff_name}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Bans a member from the server.")
@app_commands.describe(reason="Reason for the ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned. Reason: {reason}")

@bot.hybrid_command(description="Unbans a user from the server using their ID.")
@app_commands.describe(user_id="The ID of the user to unban", reason="Reason for the unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: str, *, reason: str = "No reason provided"):
    try:
        user_id_int = int(user_id)
        user = await bot.fetch_user(user_id_int)
        await ctx.guild.unban(user, reason=reason)
        await ctx.send(f"{user.mention} has been unbanned. Reason: {reason}")
    except ValueError:
        await ctx.send("Invalid User ID format.", ephemeral=True)
    except discord.NotFound:
        await ctx.send("User not found.", ephemeral=True)
    except discord.HTTPException:
        await ctx.send("Failed to unban user.", ephemeral=True)

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

if __name__ == '__main__':
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")
        print("Please create a .env file (you can copy .env.example) and add your DISCORD_TOKEN.")

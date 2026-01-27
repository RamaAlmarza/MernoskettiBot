import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
async def echo(ctx, *, message: str):
    await ctx.send(message)

@bot.command()
async def roll(ctx, sides: int = 6):
    result = random.randint(1, sides)
    await ctx.send(str(result))

@bot.command(name='8ball')
async def eight_ball(ctx, *, question):
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

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from utility.guild import Database

load_dotenv("variables.env")
TOKEN = os.environ.get('DISCORD_TOKEN')
intents = discord.Intents.all()
intents.message_content = True 
bot = commands.Bot(command_prefix='m?', description="Bot commands for moderation and convenience!", intents=intents, case_insensitive=True,strip_after_prefix=True)

@bot.event
async def on_ready():
    """Loads the bot, the associated Database, and the extensions/cogs, then attempts to setup the default configuration for servers if necessary"""
    global database
    database = Database(bot)
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Loading extensions...')
    await bot.load_extension("cogs.config")
    await bot.load_extension("cogs.moderation")
    await bot.load_extension("cogs.welcome")
    print('Extensions loaded.')
    print('------')
    print(bot.cogs)
    for guild in bot.guilds:
        await database.setup_default_config(guild.id)

bot.run(TOKEN)
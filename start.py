from discord.ext import commands
from dotenv import load_dotenv
from utility.guild import Database
import discord
import os

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
    await bot.load_extension("cogs.automod")
    await bot.load_extension("cogs.config")
    await bot.load_extension("cogs.custom")
    #await bot.load_extension("cogs.giveaway")
    await bot.load_extension("cogs.level")
    await bot.load_extension("cogs.logs")
    await bot.load_extension("cogs.moderation")
    #await bot.load_extension("cogs.reminder")
    #await bot.load_extension("cogs.roles")
    #await bot.load_extension("cogs.starboard")
    #await bot.load_extension("cogs.tnb")
    #await bot.load_extension("cogs.utility")
    #await bot.load_extension("cogs.voicelink")
    #await bot.load_extension("cogs.welcome")
    print('Extensions loaded.')
    print('------')
    for guild in bot.guilds:
        await database.setup_default_config(guild.id)

bot.run(TOKEN)
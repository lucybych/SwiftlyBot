import discord
from discord.ext import commands
from utility.finder import find_channel, find_str
from utility.guild import Database

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Welcome module"""
        self.bot = bot
        self.database = Database(self.bot)
    
    def format_msg(self, message: str, member: discord.Member):
        """Formats a message for joins/leaves/bans"""
        return message.replace("{mention}", member.mention) \
                      .replace("{server}", member.guild.name) \
                      .replace("{user(proper)}", member.name)
    
    async def send_welcome_message(self, guild: discord.Guild, member: discord.Member, config_key: str):
        """Fetches and sends a configured welcome message if available"""
        channel = await find_channel(guild, self.database, "welcome_channel")
        message_template = await find_str(guild, self.database, config_key)
        if channel and message_template:
            await channel.send(self.format_msg(message_template, member))

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, member: discord.Member):
        """Sends a message to the welcome channel if a user is banned"""
        if member in guild.members:
            await self.send_welcome_message(guild, member, "ban_message")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Sends a message to the welcome channel when a user joins"""
        await self.send_welcome_message(member.guild, member, "join_message")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Sends a message to the welcome channel when a user leaves"""
        await self.send_welcome_message(member.guild, member, "leave_message")

async def setup(bot: commands.Bot): 
    """Sets up the Welcome Cog"""
    await bot.add_cog(Welcome(bot))
from discord import Guild, Member, Thread
from discord.abc import GuildChannel
from discord.ext import commands
from utility.finder import find_channel, find_str
from utility.guild import Database

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the Welcome module"""
        self.bot: commands.Bot = bot
        self.database = Database(self.bot)
    
    def format_msg(self, text: str, member: Member) -> str:
        """Formats a message for joins/leaves/bans"""
        return text.replace("{mention}", member.mention) \
                      .replace("{server}", member.guild.name) \
                      .replace("{user(proper)}", member.name)
    
    async def send_welcome_message(self, guild: Guild, member: Member, type: str) -> None:
        """Fetches and sends a configured welcome message if available"""
        welcome_channel: GuildChannel | Thread = await find_channel(guild, self.database, self.database.welcome_channel)
        text: str = await find_str(guild, self.database, type)
        if welcome_channel and text:
            await welcome_channel.send(self.format_msg(text, member))

    @commands.Cog.listener()
    async def on_member_ban(self, guild: Guild, member: Member) -> None:
        """Sends a message to the welcome channel if a user is banned"""
        if member in guild.members:
            await self.send_welcome_message(guild, member, self.database.ban_message)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        """Sends a message to the welcome channel when a user joins"""
        await self.send_welcome_message(member.guild, member, self.database.join_message)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: Member) -> None:
        """Sends a message to the welcome channel when a user leaves"""
        await self.send_welcome_message(member.guild, member, self.database.leave_message)

async def setup(bot: commands.Bot) -> None: 
    """Sets up the Welcome Cog"""
    await bot.add_cog(Welcome(bot))
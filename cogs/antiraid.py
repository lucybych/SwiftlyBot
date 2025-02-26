from collections import deque
from discord.ext import commands
from utility.guild import Database
import discord
import time

join_limit = 10
time_limit = "60s"

class Antiraid(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Antiraid module"""
        self.bot = bot
        self.database = Database(self.bot)
        self.recent_joins = {}
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id
        if guild_id not in self.recent_joins:
            self.recent_joins[guild_id] = deque()
        join_queue = self.recent_joins[guild_id]
        current_time = time.time()
        join_queue.append((current_time, member))
        while join_queue and join_queue[0][0] < current_time - 60:
            join_queue.popleft()
        if len(join_queue) >= 10:
            for _, member in list(join_queue):
                try:
                    await member.ban(reason="Automatic action due to antiraid trigger (10 joins in 60 seconds.)")
                except Exception:
                    pass
            join_queue.clear()

async def setup(bot: commands.Bot): 
    """Sets up the Antiraid Cog"""
    await bot.add_cog(Antiraid(bot))
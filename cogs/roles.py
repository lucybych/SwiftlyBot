from discord.ext import commands
from typing import List
from utility.finder import has_valid_id
from utility.guild import Database
import discord

ROLE_IDS = "role_ids"
USER_ID = "user_id"

class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Roles module"""
        self.bot = bot
        self.database = Database(self.bot)
            
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """When a member rejoins the server, they receive previously held roles if not blacklisted."""
        if not await self.database.get_config(member.guild.id, self.database.stickyroles):
            return
        roles_collection = await self.database.get_guild_collection(member.guild.id, self.database.roles)
        entry = await roles_collection.find_one({USER_ID: member.id})
        if entry:
            role_ids = entry.get(ROLE_IDS, [])
            roles: List[discord.Role] = []
            for role_id in role_ids:
                role = member.guild.get_role(role_id)
                if role and not await has_valid_id(member, role, member.guild, self.database, self.database.sticky_blacklist):
                    roles.append(role)
            if roles:
                try:
                    await member.add_roles(*roles, reason="Restoring sticky roles")
                except Exception:
                    pass
            await roles_collection.delete_one({USER_ID: member.id})
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """When a member leaves the server, the database will store the user's ID and a list of IDs for roles that the user had before leaving"""
        if not await self.database.get_config(member.guild.id, self.database.stickyroles):
            return
        roles_collection = await self.database.get_guild_collection(member.guild.id, self.database.roles)
        role_ids = [role.id for role in member.roles if role != member.guild.default_role]
        if not role_ids:
            return
        entry = {USER_ID: member.id, ROLE_IDS: role_ids}
        print(entry)
        await roles_collection.update_one({USER_ID: member.id},{"$set": entry},upsert=True)
        
async def setup(bot: commands.Bot): 
    """Sets up the Roles Cog"""
    await bot.add_cog(Roles(bot))
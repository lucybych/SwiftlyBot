from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Any, List
from utility.finder import has_valid_id
from utility.guild import Database
import discord

ROLE_IDS = "role_ids"
USER_ID = "user_id"

class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the Roles module"""
        self.bot: commands.Bot = bot
        self.database = Database(self.bot)
            
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """When a member rejoins the server, they receive previously held roles if not blacklisted."""
        if not await self.database.get_config(member.guild.id, self.database.stickyroles):
            return
        roles_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(member.guild.id, self.database.roles)
        entry: Any = await roles_collection.find_one({USER_ID: member.id})
        if entry:
            role_ids: List[int] = entry.get(ROLE_IDS, [])
            roles: List[discord.Role] = []
            for role_id in role_ids:
                role: discord.Role = member.guild.get_role(role_id)
                if role and not await has_valid_id(member, role, member.guild, self.database, self.database.sticky_blacklist):
                    roles.append(role)
            if roles:
                try:
                    await member.add_roles(*roles, reason="Restoring sticky roles")
                except Exception:
                    pass
            await roles_collection.delete_one({USER_ID: member.id})
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """When a member leaves the server, the database will store the user's ID and a list of IDs for roles that the user had before leaving"""
        if not await self.database.get_config(member.guild.id, self.database.stickyroles):
            return
        roles_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(member.guild.id, self.database.roles)
        role_ids: list[int] = [role.id for role in member.roles if role != member.guild.default_role]
        if not role_ids:
            return
        entry: dict[str, list[int]] = {USER_ID: member.id, ROLE_IDS: role_ids}
        await roles_collection.update_one({USER_ID: member.id},{"$set": entry},upsert=True)
        
async def setup(bot: commands.Bot) -> None: 
    """Sets up the Roles Cog"""
    await bot.add_cog(Roles(bot))
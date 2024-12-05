import discord
from discord.ext import commands
from utility.finder import has_valid_id
from utility.guild import Database

class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Roles module"""
        self.bot = bot
        self.database = Database(self.bot)
            
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """When a member rejoins the server, they receive previously held roles if not blacklisted."""
        if not await self.database.get_config(member.guild.id, "stickyroles"):
            return
        roles_collection = await self.database.get_guild_collection(member.guild.id, "roles")
        result = await roles_collection.find_one({"user_id": member.id})
        if result:
            role_ids = result.get("role_ids", [])
            roles_to_add = []
            for role_id in role_ids:
                role = member.guild.get_role(role_id)
                if role and await has_valid_id(member, role, member.guild, self.database, "sticky_blacklist"):
                    roles_to_add.append(role)
            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason="Restoring sticky roles")
                except Exception:
                    pass
            await roles_collection.delete_one({"user_id": member.id})
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """When a member leaves the server, the database will store the user's ID and a list of IDs for roles that the user had before leaving"""
        if not await self.database.get_config(member.guild.id, "stickyroles"):
            return
        roles = await self.database.get_guild_collection(member.guild.id, "roles")
        role_ids = [role.id for role in member.roles if role != member.guild.default_role]
        if not role_ids:
            return
        document = {"user_id": member.id,"role_ids": role_ids}
        await roles.update_one({"user_id": member.id},{"$set": document},upsert=True)
        
async def setup(bot: commands.Bot): 
    """Sets up the Roles Cog"""
    await bot.add_cog(Roles(bot))
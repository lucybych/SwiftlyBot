import discord
from discord.ext import commands
from typing import List
from utility.guild import Database

class VoiceLink(commands.Cog):
    def __init__(self, bot):
        """Initializes the VoiceLink module"""
        self.bot = bot
        self.database = Database(self.bot)
    
    async def update_vl(self, ctx: commands.Context, guild_id, channel: discord.VoiceChannel, role: discord.Role, action: str):
        """Updates the database with roles linked to a voice channel."""
        voicelink = await self.database.get_guild_collection(guild_id, "voicelink")
        result = await voicelink.find_one({"channel_id": channel.id})
        if result:
            role_list: List[int] = result["role_ids"]
            if action == "add" and role.id not in role_list:
                role_list.append(role.id)
            elif action == "remove" and role.id in role_list:
                role_list.remove(role.id)
        else:
            role_list = [role.id] if action == "add" else []
        if role_list:
            update = await voicelink.update_one({"channel_id": channel.id}, {"$set": {"role_ids": role_list}}, upsert=True)
            if not result or update.modified_count > 0:
                await ctx.send(f"Successfully added **{role.name}** to **{channel.name}**.")
            else:
                await ctx.send("Failed to add voicelink (Is this role already added?)")
        else:
            delete = await voicelink.delete_one({"channel_id": channel.id})
            if delete.deleted_count > 0:
                await ctx.send(f"Successfully removed **{role.name}** from **{channel.name}**.")
            else:
                await ctx.send(f"Failed to remove voicelink (Is the role currently not a voicelink for that channel?)")
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def addvoicelink(self, ctx: commands.Context, channel: discord.VoiceChannel, role: discord.Role):
        """ Connects a role to a voice channel, that will be controlled based on when the user joins/leaves/moves from a voice channel. """
        await self.update_vl(ctx, ctx.guild.id, channel, role, "add")
    @addvoicelink.error
    async def on_addvoicelink_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel and role.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to add a voice link.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel and role found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def removevoicelink(self, ctx: commands.Context, channel: discord.VoiceChannel, role: discord.Role):
        """ Disconnects a role from a voice channel, meaning it will no longer be used when a user interacts with a voice channel. """
        await self.update_vl(ctx, ctx.guild.id, channel, role, "remove")
    @removevoicelink.error
    async def on_removevoicelink_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel and role.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to remove a voice link.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel and role found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Determines if a user has joined, left, or moved from a voice channel, and does the following:
        Joining a voice channel - Grabbing the list of roles linked to that channel and adds them to the user if possible
        Leaving a voice channel - Grabbing the list of roles linked to that channel and removing them from the user if possible
        Moving from one voice channel to another - Grabbing the list of roles linked to both channels, removing the ones that are only linked to the previous voice channel and adding the ones that are only linked to the new channel"""
        voicelink = await self.database.get_guild_collection(member.guild.id, "voicelink")
        async def update_roles(channel_id: int, add_roles: bool):
            result = await voicelink.find_one({"channel_id": channel_id})
            if result:
                for role_id in result["role_ids"]:
                    role = member.guild.get_role(role_id)
                    if role:
                        if add_roles:
                            await member.add_roles(role)
                        else:
                            await member.remove_roles(role)
        if not before.channel and after.channel:
            await update_roles(after.channel.id, add_roles=True)
        elif before.channel and not after.channel:
            await update_roles(before.channel.id, add_roles=False)
        elif before.channel and after.channel:
            result_before = await voicelink.find_one({"channel_id": before.channel.id})
            result_after = await voicelink.find_one({"channel_id": after.channel.id})
            if result_before:
                for role_id in result_before["role_ids"]:
                    if not result_after or (result_after and role_id not in result_after["role_ids"]):
                        role = member.guild.get_role(role_id)
                        if role:
                            await member.remove_roles(role)
            if result_after:
                for role_id in result_after["role_ids"]:
                    role = member.guild.get_role(role_id)
                    if role:
                        await member.add_roles(role)

async def setup(bot: commands.Bot): 
    """Sets up the VoiceLink Cog"""
    await bot.add_cog(VoiceLink(bot))
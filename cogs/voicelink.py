from discord.ext import commands
from typing import List
from utility.guild import Database
import discord

ADD = "add"
CHANNEL_ID = "channel_id"
REMOVE = "remove"
ROLE_IDS = "role_ids"

class VoiceLink(commands.Cog):
    def __init__(self, bot):
        """Initializes the VoiceLink module"""
        self.bot = bot
        self.database = Database(self.bot)
    
    async def update_vl(self, ctx: commands.Context, guild_id: int, channel: discord.VoiceChannel, role: discord.Role, action: str):
        """Updates the database with roles linked to a voice channel."""
        voicelink_collection = await self.database.get_guild_collection(guild_id, self.database.voicelink)
        voice_link = await voicelink_collection.find_one({CHANNEL_ID: channel.id})
        if voice_link:
            role_ids: List[int] = voice_link[ROLE_IDS]
            if action == ADD and role.id not in role_ids:
                role_ids.append(role.id)
            elif action == REMOVE and role.id in role_ids:
                role_ids.remove(role.id)
        else:
            role_ids = [role.id] if action == ADD else []
        if role_ids:
            update = await voicelink_collection.update_one({CHANNEL_ID: channel.id}, {"$set": {ROLE_IDS:role_ids}}, upsert=True)
            if not voice_link or update.modified_count > 0:
                await ctx.send(f"Successfully added **{role.name}** to **{channel.name}**.")
            else:
                await ctx.send("Failed to add voicelink (Is this role already added?)")
        else:
            delete = await voicelink_collection.delete_one({CHANNEL_ID: channel.id})
            if delete.deleted_count > 0:
                await ctx.send(f"Successfully removed **{role.name}** from **{channel.name}**.")
            else:
                await ctx.send(f"Failed to remove voicelink (Is the role currently not a voicelink for that channel?)")
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def addvoicelink(self, ctx: commands.Context, channel: discord.VoiceChannel, role: discord.Role):
        """Connects a role to a voice channel, that will be controlled based on when the user joins/leaves/moves from a voice channel."""
        await self.update_vl(ctx, ctx.guild.id, channel, role, ADD)
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
        """Disconnects a role from a voice channel, meaning it will no longer be used when a user interacts with a voice channel."""
        await self.update_vl(ctx, ctx.guild.id, channel, role, REMOVE)
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
        voicelink_collection = await self.database.get_guild_collection(member.guild.id, self.database.voicelink)
        async def update_roles(channel_id: int, add_roles: bool):
            entry = await voicelink_collection.find_one({CHANNEL_ID: channel_id})
            if entry:
                for role_id in entry[ROLE_IDS]:
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
            before_entry = await voicelink_collection.find_one({CHANNEL_ID: before.channel.id})
            after_entry = await voicelink_collection.find_one({CHANNEL_ID: after.channel.id})
            if before_entry:
                for role_id in before_entry[ROLE_IDS]:
                    if not after_entry or (after_entry and role_id not in after_entry[ROLE_IDS]):
                        role = member.guild.get_role(role_id)
                        if role:
                            await member.remove_roles(role)
            if after_entry:
                for role_id in after_entry[ROLE_IDS]:
                    role = member.guild.get_role(role_id)
                    if role:
                        await member.add_roles(role)

async def setup(bot: commands.Bot): 
    """Sets up the VoiceLink Cog"""
    await bot.add_cog(VoiceLink(bot))
from datetime import timedelta
from discord.ext import commands
from typing import Optional, Union
from utility.finder import has_valid_id, find_bool
from utility.guild import Database
import discord
import math
import pytz
import random
import sys

LAST_MESSAGE = "last_message"
LEVEL = "level"
MESSAGE_ID = "message_id"
TOTAL_XP = "total_xp"
USER_ID = "user_id"
XP_AT_LEVEL = "xp_at_level"
XP_FOR_NEXT_LEVEL = "xp_for_next_level"

class Level(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Level module"""
        self.bot = bot
        self.database = Database(self.bot)
    
    async def award_message(self, guild: discord.Guild, level: int) -> str:
        """Determines the message to send when a user has leveled up"""
        level_messages = await self.database.get_config(guild.id, self.database.level_messages)
        if level_messages and str(level) in level_messages:
            return level_messages[str(level)]
        return await self.database.get_config(guild.id, self.database.default_level_message)
    
    async def award_role(self, guild: discord.Guild, level: int) -> discord.Role:
        """Determines the role to give when a user has leveled up, if any"""
        level_roles = await self.database.get_config(guild.id, self.database.level_roles)
        if level_roles and str(level) in level_roles:
            return guild.get_role(level_roles[str(level)])
        return None
    
    def calculate_xp(self, level) -> int:
        """Calculates the XP to the next level"""
        return int(5 * math.pow(level, 2) + 50 * level + 100)
    
    async def determine_level(self, xp: int) -> int:
        """Determines level based on given XP"""
        level = 0
        while True:
            if await self.determine_cumulative_xp(level) <= xp < await self.determine_cumulative_xp(level + 1):
                return level
            level += 1
    
    async def determine_role(self, guild: discord.Guild, level: int) -> discord.Role:
        while level != 0:
            role = await self.award_role(guild, level)
            if role:
                return role
            level -= 1
        return None
    
    async def determine_cumulative_xp(self, level: int) -> int:
        """Determines the total amount of XP needed for a level"""
        xp = 0
        for lvl in range (0, level):
            xp += self.calculate_xp(lvl)
        return xp
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def givexp(self, ctx: commands.Context, xp: int, user: Optional[Union[discord.Member, discord.User]]):
        """Gives the number of experience to the given user, or the command user if no user is specified."""
        if xp < 0 or xp >= sys.maxsize:
            raise commands.UserInputError
        user = user if user else ctx.author
        level_collection = await self.database.get_guild_collection(ctx.guild.id, self.database.level)
        entry = await level_collection.find_one({USER_ID: user.id})
        total_xp = entry[TOTAL_XP] + xp if entry else xp
        last_message = entry[LAST_MESSAGE] if entry else None
        level = entry[LEVEL] if entry else 0
        new_level = await self.determine_level(total_xp)
        xp_at_level = await self.determine_cumulative_xp(new_level)
        new_xp_at_level = total_xp - xp_at_level
        xp_at_next_level = await self.determine_cumulative_xp(new_level+1)
        new_xp_at_next_level = xp_at_next_level - total_xp
        update = await level_collection.update_one({USER_ID: user.id},{"$set": {LEVEL: new_level,TOTAL_XP: total_xp,XP_AT_LEVEL: new_xp_at_level,XP_FOR_NEXT_LEVEL: new_xp_at_next_level,LAST_MESSAGE: last_message,}},upsert=True)
        if not entry or update.modified_count > 0:
            await ctx.send(f"Successfully added {xp} XP to user **{user.name}**.")
        else:
            await ctx.send(f"Failed to add {xp} XP to user **{user.name}**")
        max_lvl_role = await self.determine_role(ctx.guild, level)
        new_max_lvl_role = await self.determine_role(ctx.guild, new_level)
        if new_max_lvl_role:
            try:
                await user.add_roles(new_max_lvl_role)
            except Exception:
                pass
        if max_lvl_role:
            try:
                await user.remove_roles(max_lvl_role)
            except Exception:
                pass
    @givexp.error
    async def on_givexp_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid number and user, or omit it to add XP to yourself.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to give users XP.")
        elif isinstance(error, commands.UserInputError):
            await ctx.send(f"Invalid XP input. Make sure that the XP value is positive and does not exceed {sys.maxsize}.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid XP number and user.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command(aliases=['lb'])
    async def leaderboard(self, ctx: commands.Context, page: int = 1):
        """Displays the users with the most XP, each page contains 20 entries (Page 1 is 1-20, 2 is 21-40, etc)"""
        per_page = 20
        start_position = (page - 1) * per_page
        end_position = start_position + per_page
        level_collection = await self.database.get_guild_collection(ctx.guild.id, self.database.level)
        cursor = level_collection.find().sort(TOTAL_XP, -1)
        users = await cursor.to_list(None)
        total_users = len(users)
        if total_users <= 0:
            raise commands.UserNotFound(["experience"])
        total_pages = (total_users + per_page - 1) // per_page
        if page < 1 or page > total_pages:
            await ctx.send(f"Invalid page number. Please select a page between 1 and {total_pages}, inclusive.")
            return
        embed = discord.Embed(title=f"Leaderboard for {ctx.guild.name}", color=discord.Color.blurple())
        for idx, user_entry in enumerate(users[start_position:end_position], start=start_position + 1):
            user = self.bot.get_user(user_entry[USER_ID])
            if user:
                embed.add_field(name="",value=f"{idx}. {user.mention} {user_entry[TOTAL_XP]}xp lvl {user_entry[LEVEL]}",inline=False)
        await ctx.send(embed=embed)
    @leaderboard.error
    async def on_leaderboard_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid page number, or omit it to get the first page of results.")
        elif isinstance(error, commands.UserNotFound):
            await ctx.send("No users with level data found.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid number.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command(aliases=['lvl'])
    async def level(self, ctx: commands.Context, user: Optional[Union[discord.User,discord.Member]]):
        """Checks the level for the given user, or the command user"""
        user = user if user else ctx.author
        level_collection = await self.database.get_guild_collection(ctx.guild.id, self.database.level)
        entry = await level_collection.find_one({USER_ID: user.id})
        if entry:
            level = entry[LEVEL]
            cursor = level_collection.find().sort(TOTAL_XP, -1)
            users = await cursor.to_list(None)
            rank = next((index + 1 for index, entry in enumerate(users) if entry[USER_ID] == user.id), None)
            xp_at_level = await self.determine_cumulative_xp(level)
            xp_at_next_level = await self.determine_cumulative_xp(level+1)
            xp_next_level = xp_at_next_level - xp_at_level
            embed = discord.Embed(color=user.color, title="",description=f"Level card for {user.mention}:")
            embed.add_field(name="", value=f"**Level:** {level}", inline=False)
            embed.add_field(name="", value=f"**XP:** {entry[XP_AT_LEVEL]}/{xp_next_level}", inline=False)
            embed.add_field(name="", value=f"**Rank:** {rank}/{len(users)}", inline=False)
            await ctx.send(embed=embed)
        else:
            raise commands.UserNotFound(["experience"])
    @level.error
    async def on_level_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only provide a valid user or omit it to get your own stats.")
        elif isinstance(error, commands.UserNotFound) or isinstance(error, commands.CommandInvokeError):
            await ctx.send("User cannot be found or has no level data in the server.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid user.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def removexp(self, ctx: commands.Context, xp: int, user: Optional[Union[discord.User, discord.Member]]):
        """Takes away the given number of XP away from the given user or the command user."""
        if xp < 0 or xp >= sys.maxsize:
            raise commands.UserInputError
        xp_user = user if user else ctx.author
        level_collection = await self.database.get_guild_collection(ctx.guild.id, self.database.level)
        entry = await level_collection.find_one({USER_ID: xp_user.id})
        if entry:
            total_xp = entry[TOTAL_XP] - xp if entry[TOTAL_XP] - xp >= 0 else 0
            last_message = entry[LAST_MESSAGE]
            level = entry[LEVEL]
        else:
            raise commands.UserNotFound(["experience"])
        new_level = await self.determine_level(total_xp)
        xp_at_level = await self.determine_cumulative_xp(new_level)
        new_xp_at_level = total_xp - xp_at_level
        xp_at_next_level = await self.determine_cumulative_xp(new_level+1)
        new_xp_at_next_level = xp_at_next_level - total_xp
        update = await level_collection.update_one({USER_ID: xp_user.id},{"$set": {LEVEL: new_level,TOTAL_XP: total_xp,XP_AT_LEVEL: new_xp_at_level,XP_FOR_NEXT_LEVEL: new_xp_at_next_level,LAST_MESSAGE: last_message,}},upsert=True)
        if not entry or update.modified_count > 0:
            await ctx.send(f"Successfully removed {xp} XP from user **{xp_user.name}**.")
        else:
            await ctx.send(f"Failed to remove {xp} XP from user **{xp_user.name}**.")
        max_lvl_role = await self.determine_role(ctx.guild, level)
        new_max_lvl_role = await self.determine_role(ctx.guild, new_level)
        if new_max_lvl_role:
            try:
                await xp_user.add_roles(new_max_lvl_role)
            except Exception:
                pass
        if max_lvl_role:
            try:
                await xp_user.remove_roles(max_lvl_role)
            except Exception:
                pass
    @removexp.error
    async def on_removexp_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid number and user, or omit it to remove your own XP.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to remove XP from users.")
        elif isinstance(error, commands.UserNotFound):
            await ctx.send("User has no experience in server or cannot be found, therefore they cannot have any XP removed.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid number and user.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def resetxp(self, ctx: commands.Context, user: Optional[Union[discord.User, discord.Member]]):
        """Resets the experience of the given user or command user to 0 (Deletes their level entry)"""
        user = user if user else ctx.author
        level_collection = await self.database.get_guild_collection(ctx.guild.id, self.database.level)
        entry = await level_collection.find_one({USER_ID: user.id})
        if entry:
            level = entry[LEVEL]
            role = await self.determine_role(ctx.guild, level)
            if role and user in ctx.guild.members:
                try:
                    await user.remove_roles(role)
                except Exception:
                    pass
        result = await level_collection.delete_many({USER_ID: user.id})
        if result.deleted_count > 0:
            await ctx.send(f"Successfully removed all XP from user **{user.name}**.")
        else:
            await ctx.send(f"Failed to reset XP on {user.name}. Make sure that they have level data.")
    @resetxp.error
    async def on_resetxp_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid user, or omit it to reset your own XP.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to reset users' XP.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid user.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """When a user sends a message, it checks if the user is blacklisted from gaining XP. If not, they will be awarded xp between 15 and 25. If they level up, they will be alerted if such a level messages exists"""
        if message.author.bot:
            return
        if message.content.startswith(self.bot.command_prefix):
            return
        if not await find_bool(message.guild, self.database, self.database.levels_enabled):
            return
        blacklisted = await has_valid_id(message.author, message.channel, message.guild, self.database, self.database.level_blacklist)
        if blacklisted:
            return
        current_time = discord.utils.utcnow()
        level_collection = await self.database.get_guild_collection(message.guild.id, self.database.level)
        entry = await level_collection.find_one({USER_ID: message.author.id})
        xp = random.randint(15, 25)
        if not entry:
            xp_for_next_level = await self.determine_cumulative_xp(1)
            entry = {
                USER_ID: message.author.id,
                LEVEL: 0,
                TOTAL_XP: xp, 
                XP_AT_LEVEL: xp, 
                XP_FOR_NEXT_LEVEL: xp_for_next_level - xp, 
                LAST_MESSAGE: current_time,
            }
            level_collection.insert_one(entry)
        else:
            entry_date = None if not entry[LAST_MESSAGE] else pytz.timezone("UTC").localize(entry[LAST_MESSAGE])
            if not entry_date or (current_time - entry_date) >= timedelta(seconds=60):
                total_xp = entry[TOTAL_XP] + xp
                if xp >= entry[XP_FOR_NEXT_LEVEL]:
                    new_level = entry[LEVEL] + 1
                    xp_at_level = total_xp - await self.determine_cumulative_xp(new_level)
                    xp_for_next_level = await self.determine_cumulative_xp(new_level+1) - total_xp
                    award_message = await self.award_message(message.guild, new_level)
                    if award_message:
                        award_message = award_message.replace("{lvl}", str(new_level))
                        award_message = award_message.replace("{mention}", message.author.mention)
                        await message.channel.send(award_message)
                    role = await self.award_role(message.guild, new_level)
                    if role:
                        await message.author.add_roles(role)
                else:
                    new_level = entry[LEVEL]
                    xp_at_level = total_xp - await self.determine_cumulative_xp(new_level)
                    xp_for_next_level = await self.determine_cumulative_xp(new_level+1) - total_xp
                await level_collection.update_one({USER_ID: message.author.id},{"$set": {LEVEL: new_level,TOTAL_XP: total_xp,XP_AT_LEVEL: xp_at_level,XP_FOR_NEXT_LEVEL: xp_for_next_level,LAST_MESSAGE: current_time}})

async def setup(bot: commands.Bot): 
    """Sets up the Level Cog"""
    await bot.add_cog(Level(bot))
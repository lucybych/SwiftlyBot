from datetime import timedelta
import discord
from discord.ext import commands
import math
import pytz
import random
import sys
from typing import Optional, Union
from utility.finder import has_valid_id, find_bool
from utility.guild import Database

class Level(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Level module"""
        self.bot = bot
        self.database = Database(self.bot)
    
    async def award_message(self, guild: discord.Guild, level: int) -> str:
        """Determines the message to send when a user has leveled up"""
        level_messages = await self.database.get_config(guild.id, "level_messages")
        if level_messages and str(level) in level_messages:
            return level_messages[str(level)]
        return await self.database.get_config(guild.id, "default_level_message")
    
    async def award_role(self, guild: discord.Guild, level: int) -> discord.Role:
        """Determines the role to give when a user has leveled up, if any"""
        level_roles = await self.database.get_config(guild.id, "level_roles")
        if level_roles and str(level) in level_roles:
            return guild.get_role(level_roles[str(level)])
        return None
    
    def calculate_xp(self, level):
        """Calculates the XP to the next level"""
        return int(5 * math.pow(level, 2) + 50 * level + 100)
    
    async def determine_level(self, xp: int):
        """Determines level based on given XP"""
        level = 0
        while True:
            if await self.determine_cumulative_xp(level) <= xp < await self.determine_cumulative_xp(level + 1):
                return level
            level += 1
    
    async def determine_role(self, guild: discord.Guild, level: int):
        while level != 0:
            role = await self.award_role(guild, level)
            if role:
                return role
            level -= 1
        return None
    
    async def determine_cumulative_xp(self, level: int):
        """Determines the total amount of XP needed for a level"""
        xp = 0
        for i in range (0, level):
            xp += self.calculate_xp(i)
        return xp
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def givexp(self, ctx: commands.Context, xp: int, user: Optional[Union[discord.Member, discord.User]]):
        """Gives the number of experience to the given user"""
        if xp < 0 or xp >= sys.maxsize:
            raise commands.UserInputError
        xp_user = user if user else ctx.author
        level_collection = await self.database.get_guild_collection(ctx.guild.id, "level")
        level_entry = await level_collection.find_one({"user_id": xp_user.id})
        new_total_xp = level_entry["total_xp"] + xp if level_entry else xp
        last_message = level_entry["last_message"] if level_entry else None
        old_lvl = level_entry["level"] if level_entry else 0
        new_level = await self.determine_level(new_total_xp)
        cumulative_xp_at_level = await self.determine_cumulative_xp(new_level)
        new_xp_at_level = new_total_xp - cumulative_xp_at_level
        cumulative_xp_at_next_level = await self.determine_cumulative_xp(new_level+1)
        new_xp_to_next_level = cumulative_xp_at_next_level - new_total_xp
        update = await level_collection.update_one({"user_id": xp_user.id},{"$set": {"level": new_level,"total_xp": new_total_xp,"xp_at_level": new_xp_at_level,"xp_for_next_level": new_xp_to_next_level,"last_message": last_message,}},upsert=True)
        if not level_entry or update.modified_count > 0:
            await ctx.send(f"Successfully added {xp} XP to user **{xp_user.name}**.")
        else:
            await ctx.send(f"Failed to add {xp} XP to user **{xp_user.name}**")
        old_max_lvl_role = await self.determine_role(ctx.guild, old_lvl)
        max_lvl_role = await self.determine_role(ctx.guild, new_level)
        if max_lvl_role:
            try:
                await xp_user.add_roles(max_lvl_role)
            except Exception:
                pass
        if old_max_lvl_role:
            try:
                await xp_user.remove_roles(old_max_lvl_role)
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
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        level_collection = await self.database.get_guild_collection(ctx.guild.id, "level")
        all_users_cursor = level_collection.find().sort("total_xp", -1)
        all_users = await all_users_cursor.to_list(None)
        total_users = len(all_users)
        if total_users <= 0:
            raise commands.UserNotFound
        total_pages = (total_users + per_page - 1) // per_page
        if page < 1 or page > total_pages:
            await ctx.send(f"Invalid page number. Please select a page between 1 and {total_pages}, inclusive.")
            return
        embed = discord.Embed(title=f"Leaderboard for {ctx.guild.name}", color=discord.Color.blurple())
        for idx, user_entry in enumerate(all_users[start_index:end_index], start=start_index + 1):
            user = self.bot.get_user(user_entry["user_id"])
            if user:
                embed.add_field(name="",value=f"{idx}. {user.mention} {user_entry['total_xp']}xp lvl {user_entry['level']}",inline=False)
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
        check_user = user if user else ctx.author
        level_collection = await self.database.get_guild_collection(ctx.guild.id, "level")
        level_entry = await level_collection.find_one({"user_id": check_user.id})
        if level_entry:
            level = level_entry["level"]
            all_users_cursor = level_collection.find().sort("total_xp", -1)
            all_users = await all_users_cursor.to_list(None)
            rank = next((index + 1 for index, entry in enumerate(all_users) if entry["user_id"] == check_user.id), None)
            xp_at_level = await self.determine_cumulative_xp(level)
            xp_at_next_level = await self.determine_cumulative_xp(level+1)
            xp_next_level = xp_at_next_level - xp_at_level
            embed = discord.Embed(color=check_user.color, title="",description=f"Level card for {check_user.mention}:")
            embed.add_field(name="", value=f"**Level:** {level}", inline=False)
            embed.add_field(name="", value=f"**XP:** {level_entry['xp_at_level']}/{xp_next_level}", inline=False)
            embed.add_field(name="", value=f"**Rank:** {rank}/{len(all_users)}", inline=False)
            await ctx.send(embed=embed)
        else:
            raise commands.UserNotFound
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
        """Takes away the given number of XP away from the given user"""
        if xp < 0 or xp >= sys.maxsize:
            raise commands.UserInputError
        xp_user = user if user else ctx.author
        level_collection = await self.database.get_guild_collection(ctx.guild.id, "level")
        level_entry = await level_collection.find_one({"user_id": xp_user.id})
        if level_entry:
            new_total_xp = level_entry["total_xp"] - xp
            if new_total_xp < 0:
                new_total_xp = 0
            last_message = level_entry["last_message"]
            old_lvl = level_entry["level"]
        else:
            raise commands.UserNotFound
        new_level = await self.determine_level(new_total_xp)
        cumulative_xp_at_level = await self.determine_cumulative_xp(new_level)
        new_xp_at_level = new_total_xp - cumulative_xp_at_level
        cumulative_xp_at_next_level = await self.determine_cumulative_xp(new_level+1)
        new_xp_to_next_level = cumulative_xp_at_next_level - new_total_xp
        update = await level_collection.update_one({"user_id": xp_user.id},{"$set": {"level": new_level,"total_xp": new_total_xp,"xp_at_level": new_xp_at_level,"xp_for_next_level": new_xp_to_next_level,"last_message": last_message,}},upsert=True)
        if not level_entry or update.modified_count > 0:
            await ctx.send(f"Successfully removed {xp} XP from user **{xp_user.name}**.")
        else:
            await ctx.send(f"Failed to remove {xp} XP from user **{xp_user.name}**.")
        old_max_lvl_role = await self.determine_role(ctx.guild, old_lvl)
        max_lvl_role = await self.determine_role(ctx.guild, new_level)
        if max_lvl_role:
            try:
                await xp_user.add_roles(max_lvl_role)
            except Exception:
                pass
        if old_max_lvl_role:
            try:
                await xp_user.remove_roles(old_max_lvl_role)
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
        """Resets the experience of the given user to 0 (Deletes their level entry)"""
        reset_user = user if user else ctx.author
        level_collection = await self.database.get_guild_collection(ctx.guild.id, "level")
        level_entry_og = await level_collection.find_one({"user_id": reset_user.id})
        if level_entry_og:
            old_lvl = level_entry_og["level"]
            old_role = await self.determine_role(ctx.guild, old_lvl)
            if old_role and user in ctx.guild.members:
                try:
                    await user.remove_roles(old_role)
                except Exception:
                    pass
        level_entry = await level_collection.delete_many({"user_id": reset_user.id})
        if level_entry.deleted_count > 0:
            await ctx.send(f"Successfully removed all XP from user **{reset_user.name}**.")
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
        time = discord.utils.utcnow()
        if message.author.bot:
            return
        if not await find_bool(message.guild, self.database, "levels_enabled"):
            return
        can_gain_xp = await has_valid_id(message.author, message.channel, message.guild, self.database, "level_blacklist")
        if not can_gain_xp:
            return
        level_collection = await self.database.get_guild_collection(message.guild.id, "level")
        level_entry = await level_collection.find_one({"user_id": message.author.id})
        xp = random.randint(15, 25)
        if not level_entry:
            xp_for_next_level = await self.determine_cumulative_xp(1)
            level_entry = {
                "user_id": message.author.id,
                "level": 0,
                "total_xp": xp, 
                "xp_at_level": xp, 
                "xp_for_next_level": xp_for_next_level - xp, 
                "last_message": time,
            }
            level_collection.insert_one(level_entry)
        else:
            utc = pytz.timezone("UTC")
            entry_date = utc.localize(level_entry["last_message"])
            if (time - entry_date) >= timedelta(seconds=60):
                new_total_xp = level_entry['total_xp'] + xp
                new_xp_at_level = level_entry['xp_at_level'] + xp 
                if xp >= level_entry['xp_for_next_level']:
                    new_level = level_entry['level'] + 1
                    xp_at_level = await self.determine_cumulative_xp(new_level)
                    xp_at_next_level = new_total_xp - xp_at_level
                    xp_at_level_next = await self.determine_cumulative_xp(new_level+1)
                    xp_for_next_level = xp_at_level_next - new_total_xp
                    award_message = await self.award_message(message.guild, new_level)
                    if award_message:
                        award_message = award_message.replace("{lvl}", str(new_level))
                        award_message = award_message.replace("{mention}", message.author.mention)
                        await message.channel.send(award_message)
                    role = await self.award_role(message.guild, new_level)
                    if role:
                        await message.author.add_roles(role)
                else:
                    new_level = level_entry['level']
                    xp_to_next_level = await self.determine_cumulative_xp(new_level+1)
                    xp_at_next_level = new_xp_at_level
                    xp_for_next_level = xp_to_next_level - new_total_xp
                await level_collection.update_one({"user_id": message.author.id},{"$set": {"level": new_level,"total_xp": new_total_xp,"xp_at_level": xp_at_next_level,"xp_for_next_level": xp_for_next_level,"last_message": time,}})

async def setup(bot: commands.Bot): 
    """Sets up the Level Cog"""
    await bot.add_cog(Level(bot))
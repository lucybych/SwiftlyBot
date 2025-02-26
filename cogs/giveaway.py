from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Any, AsyncIterator, Union
from utility.finder import has_valid_id
from utility.guild import Database, parse_time_string
import asyncio
import discord
import random

CHANNEL_ID = "channel_id"
ENDED = "ended"
END_TIME = "end_time"
HOST_ID = "host_id"
MESSAGE_ID = "message_id"
PARTICIPANTS = "participants"
PRIZE = "prize"
WINNERS_LIST = "winners_list"
WINNERS_NUM = "winners_num"

class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the giveaway module"""
        self.bot: commands.Bot = bot
        self.database = Database(self.bot)
        self.update_giveaways.start()

    async def reset_giveaways(self) -> None:
        """Purges expired giveaways from the database (Meaning giveaways that ended over 2 weeks ago)"""
        two_weeks_ago: datetime = discord.utils.utcnow() - timedelta(weeks=2)
        server_ids: list[str] = await self.database.mongo_client.list_database_names()
        for server_id in server_ids:
            giveaway_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(server_id, self.database.giveaway)
            async for giveaway in giveaway_collection.find():
                ended: bool = giveaway.get(ENDED, False)
                end_time: datetime | str = giveaway.get(END_TIME)
                if ended and end_time:
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time)
                    if end_time < two_weeks_ago:
                        await giveaway_collection.delete_one({"_id": giveaway["_id"]})
    
    async def schedule_giveaway_end(self, message_id: int, guild_id: int, duration_seconds: float):
        """Waits for a giveaway to end and announces the winners, if possible"""
        giveaway_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(guild_id, self.database.giveaway)
        await asyncio.sleep(duration_seconds)
        giveaway: Any = await giveaway_collection.find_one({MESSAGE_ID: message_id})
        if giveaway and not giveaway[ENDED]:
            channel: discord.abc.GuildChannel | discord.Thread = self.bot.get_channel(giveaway[CHANNEL_ID])
            if channel:
                message: discord.Message = await channel.fetch_message(message_id)
                if message:
                    users: AsyncIterator[discord.Member | discord.User] = message.reactions[0].users()
                    users: list[discord.Member | discord.User] = [user async for user in users if not user.bot]
                    host: discord.User = self.bot.get_user(giveaway[HOST_ID])
                    winners_num: int = giveaway[WINNERS_NUM]
                    winners: list[discord.Member | discord.User] = users if len(users) < winners_num else random.sample(users, winners_num)
                    user_ids: list[int] = [user.id for user in users]
                    winner_ids: list[int] = [winner.id for winner in winners]
                    await giveaway_collection.update_one({MESSAGE_ID: message_id}, {"$set": {ENDED: True, PARTICIPANTS: user_ids, WINNERS_NUM: len(winners), WINNERS_LIST: winner_ids}})
                    if winners:
                        winner_mentions: str = ", ".join([user.mention for user in winners])
                        await channel.send(f"Congratulations {winner_mentions}! You won the **{giveaway[PRIZE]}**!")
                    else:
                        winner_mentions = "None"
                        await channel.send(f"No valid winners could be selected for **{giveaway[PRIZE]}**.")
                    current_time: datetime = discord.utils.utcnow()
                    embed = discord.Embed(color=discord.Color.dark_gray(),title=giveaway[PRIZE],timestamp=current_time)
                    embed.add_field(name="Ended: ",value=f"{discord.utils.format_dt(current_time, 'R')}")
                    embed.add_field(name="Hosted by: ",value=host.mention if host else "Unknown Host")
                    embed.add_field(name="Entries: ",value=f"**{len(users)}**")
                    embed.add_field(name="Winners: ",value=winner_mentions)
                    await message.edit(embed=embed)

    @tasks.loop(hours=24)
    async def update_giveaways(self) -> None:
        """Loop that attempts to purge giveaways every day at 12 AM UTC"""
        current_time: datetime = discord.utils.utcnow()
        if current_time.hour == 0 and current_time.minute == 0:
            await self.reset_giveaways()

    @update_giveaways.before_loop
    async def before_update_giveaways(self) -> None:
        """Waits until 12 AM UTC before updating giveaways"""
        target_time: datetime = (discord.utils.utcnow() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await discord.utils.sleep_until(target_time)

    @commands.command()
    async def greroll(self, ctx: commands.Context, message_id: int):
        """Rerolls a giveaway, if said giveaway exists and has ended"""
        if not await has_valid_id(ctx.author, ctx.channel, ctx.guild, self.database, self.database.giveaway_hosts):
            raise commands.MissingPermissions(["Non-host/staff"])
        giveaway_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(ctx.guild.id, self.database.giveaway)
        giveaway: Any = await giveaway_collection.find_one({MESSAGE_ID: message_id})
        if giveaway and giveaway[ENDED]:
            channel: discord.abc.GuildChannel | discord.Thread = ctx.guild.get_channel(giveaway[CHANNEL_ID])
            if channel and ctx.author.id == giveaway[HOST_ID] or ctx.author.guild_permissions.manage_guild:
                message: discord.Message = await channel.fetch_message(message_id)
                winners_list: list[int] = giveaway[WINNERS_LIST]
                reactions: list[discord.Reaction] = [reaction for reaction in message.reactions if reaction.emoji == "🎉"]
                users: AsyncIterator[discord.Member | discord.User] = reactions[0].users()
                users: list[discord.Member | discord.User] = [user async for user in users if not user.bot and user.id not in winners_list]
                winners_num: int = giveaway[WINNERS_NUM]
                host: discord.User = self.bot.get_user(giveaway[HOST_ID])
                winners: list[discord.Member | discord.User] = users if len(users) < winners_num else random.sample(users, winners_num)
                user_ids: list[int] = [user.id for user in users]
                winner_ids: list[int] = [winner.id for winner in winners]
                await giveaway_collection.update_one({MESSAGE_ID: message_id}, {"$set": {ENDED: True, PARTICIPANTS: user_ids, WINNERS_NUM: len(winners), WINNERS_LIST: winner_ids}})
                if winners:
                    winner_mentions: str = ", ".join([user.mention for user in winners])
                    await channel.send(f"Congratulations {winner_mentions}! You won the **{giveaway[PRIZE]}**!")
                else:
                    winner_mentions = "None"
                    await channel.send(f"No winners could be rerolled for **{giveaway[PRIZE]}**.")
                new_embed = discord.Embed(color=discord.Color.dark_gray(),title=giveaway[PRIZE],timestamp=discord.utils.utcnow())
                new_embed.add_field(name="Ended: ",value=f"{discord.utils.format_dt(discord.utils.utcnow(), 'R')}")
                new_embed.add_field(name="Hosted by: ",value=host.mention if host else "Unknown Host")
                new_embed.add_field(name="Entries: ",value=f"**{len(users)}**")
                new_embed.add_field(name="Winners: ",value=winner_mentions)
                await message.edit(embed=new_embed)
            else:
                raise commands.MissingPermissions(["Non-host/staff"])
        else:
            raise commands.CommandInvokeError
    @greroll.error
    async def on_greroll_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid message/giveaway ID.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You are not listed as a giveaway host for this giveaway, or do not have the proper staff permissions. Please ensure that you are added to the host list, if you feel this is a mistake.")
        elif isinstance(error, discord.HTTPException) or isinstance(error, discord.NotFound) or isinstance(error, discord.InvalidData):
            await ctx.send("Error retrieving the giveaway message or channel or message reactions or editing the giveaway message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to reteive the giveaway channel and/or message and/or edit the giveaway message.")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("No inactive giveaway found. Ensure that the message ID is valid and exists, and/or the giveaway channel is valid and exists.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid message ID/number.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    async def gstart(self, ctx: commands.Context, time: Union[str, float], num_winners: int, *, prize: str) -> None:
        """Starts a giveaway that will end in the given time, have the given number of winners, and is for the given prize"""
        if not await has_valid_id(ctx.author, ctx.channel, ctx.guild, self.database, self.database.giveaway_hosts):
            raise commands.MissingPermissions(["Non-host/staff"])
        if num_winners <= 0:
            raise commands.UserInputError
        giveaway_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(ctx.guild.id, self.database.giveaway)
        duration: timedelta | datetime = await parse_time_string(time) if isinstance(time, str) else datetime.fromtimestamp(time, timezone.utc)
        if not duration:
            raise commands.UserInputError
        current_time: datetime = discord.utils.utcnow()
        end_time: datetime = current_time + duration
        embed = discord.Embed(title=prize, color=discord.Color.dark_gray(),timestamp=current_time)
        embed.add_field(name="Ends in: ", value=f"{discord.utils.format_dt(end_time, 'R')}")
        embed.add_field(name="Hosted by: ", value=ctx.author.mention)
        embed.add_field(name="Entires: ", value="**0**")
        embed.add_field(name="Winners: ",value=num_winners)
        message: discord.Message = await ctx.send(embed=embed)
        try:
            await message.add_reaction("🎉")
        except Exception as e:
            try:
                message.delete()
            except Exception:
                pass
            raise e
        giveaway_doc: dict[str, Any] = {
            MESSAGE_ID: message.id,
            CHANNEL_ID: ctx.channel.id,
            END_TIME: end_time,
            PRIZE: prize,
            HOST_ID: ctx.author.id,
            WINNERS_NUM: num_winners,
            WINNERS_LIST: [],
            PARTICIPANTS: [], 
            ENDED: False
        }
        giveaway_collection.insert_one(giveaway_doc)
        self.bot.loop.create_task(self.schedule_giveaway_end(message.id, ctx.guild.id, duration.total_seconds()))
    @gstart.error
    async def on_gstart_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid time, number of winners, and prize.")
        elif isinstance(error, commands.UserInputError):
            await ctx.send("Invalid number of winners or duration time. The number must be 1 or more, and the time must be in the format of a timestamp or number followed by time type (Ex. 4w or 2mo3d).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You are not listed as a giveaway host. Please ensure that you are added to the host list, if you feel this is a mistake.")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Failed to add the reaction to the giveaway message, the giveaway message is now invalid.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel or add reactions. Giveaway message is invalid.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that the time is a time string or timestamp, and the winners is a number.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Adds a user to the giveaway entries list, if the message is a valid giveaway and the user is not blacklisted"""
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        user: discord.Member = payload.member
        if not user or user.bot:
            return
        if payload.emoji.name == "🎉":
            channel: discord.abc.GuildChannel | discord.Thread = self.bot.get_channel(payload.channel_id)
            message: discord.Message = await channel.fetch_message(payload.message_id)
            if await has_valid_id(user, channel, guild, self.database, self.database.giveaway_blacklist):
                await message.remove_reaction("🎉", user)
                await user.send(f"You cannot enter this giveaway in {guild.name} due to being blacklisted from entering giveaways.")
                return
            giveaway_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(payload.guild_id, self.database.giveaway)
            giveaway: Any = await giveaway_collection.find_one({MESSAGE_ID: payload.message_id})
            if giveaway and not giveaway[ENDED]:
                if user and not user.bot:
                    await giveaway_collection.update_one({MESSAGE_ID: payload.message_id},{"$addToSet": {PARTICIPANTS: payload.user_id}})
                    participants: list[int] = giveaway.get(PARTICIPANTS, [])
                    embed: discord.Embed = message.embeds[0]
                    embed.set_field_at(2, name="Entries:",value=f"**{str(len(participants) + 1)}**")
                    await message.edit(embed=embed)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Removes the user from the giveaway entries list, if the message is a valid giveaway"""
        user: discord.User = self.bot.get_user(payload.user_id)
        if not user or user.bot:
            return
        if payload.emoji.name == "🎉":
            giveaway_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(payload.guild_id, self.database.giveaway)
            giveaway: Any = await giveaway_collection.find_one({MESSAGE_ID: payload.message_id})
            if giveaway and not giveaway[ENDED]:
                guild: discord.Guild = self.bot.get_guild(payload.guild_id)
                user = guild.get_member(payload.user_id)
                if user and not user.bot:
                    await giveaway_collection.update_one({MESSAGE_ID: payload.message_id},{"$pull": {PARTICIPANTS: payload.user_id}})
                    participants: list[int] = giveaway.get(PARTICIPANTS, [])
                    channel: discord.abc.GuildChannel | discord.Thread = self.bot.get_channel(payload.channel_id)
                    message: discord.Message = await channel.fetch_message(payload.message_id)
                    embed: discord.Embed = message.embeds[0]
                    num_p: int = len(participants) if len(participants) - 1 > 0 else 0
                    embed.set_field_at(2, name="Entries:", value=f"**{num_p}**")
                    await message.edit(embed=embed)

async def setup(bot: commands.Bot): 
    """Sets up the Giveaway Cog"""
    await bot.add_cog(Giveaway(bot))

import asyncio
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks
import random
from typing import Union
from utility.finder import has_valid_id
from utility.guild import Database, parse_time_string

class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the giveaway module"""
        self.bot = bot
        self.database = Database(self.bot)
        self.update_giveaways.start()

    async def reset_giveaways(self):
        """Purges expired giveaways from the database (Meaning giveaways that ended over 2 weeks ago)"""
        now_utc = discord.utils.utcnow()
        two_weeks_ago = now_utc - timedelta(weeks=2)
        server_ids = self.database.mongo_client.list_database_names()
        for server_id in server_ids:
            config_collection = await self.database.get_guild_collection(server_id, "giveaway")
            async for giveaway in config_collection.find():
                ended = giveaway.get("ended", False)
                end_time = giveaway.get("end_time")
                if ended and end_time:
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time)
                    if end_time < two_weeks_ago:
                        await config_collection.delete_one({"_id": giveaway["_id"]})
    
    async def schedule_giveaway_end(self, message_id: int, guild_id: int, duration_seconds: float):
        """Waits for a giveaway to end and announces the winners, if possible"""
        giveaway_collection = await self.database.get_guild_collection(guild_id, "giveaway")
        await asyncio.sleep(duration_seconds)
        giveaway = await giveaway_collection.find_one({"message_id": message_id})
        if giveaway and not giveaway["ended"]:
            channel = self.bot.get_channel(giveaway["channel_id"])
            if channel:
                giveaway_message = await channel.fetch_message(message_id)
                if giveaway_message:
                    users = giveaway_message.reactions[0].users()
                    users = [user async for user in users if not user.bot]
                    host = self.bot.get_user(giveaway["host_id"])
                    winners_count = giveaway["winners_num"]
                    if len(users) < winners_count:
                        winners = users
                    else:
                        winners = random.sample(users, winners_count)
                    users_list = [user.id for user in users]
                    winners_list = [winner.id for winner in winners]
                    await giveaway_collection.update_one({"message_id": message_id}, {"$set": {"ended": True, "participants": users_list, "winners_num": len(winners), "winners_list": winners_list}})
                    if winners:
                        winner_mentions = ", ".join([user.mention for user in winners])
                        await channel.send(f"Congratulations {winner_mentions}! You won the **{giveaway['prize']}**!")
                    else:
                        winner_mentions = "None"
                        await channel.send(f"No valid winners could be selected for **{giveaway['prize']}**.")
                    new_embed = discord.Embed(color=discord.Color.dark_gray(),title=giveaway["prize"],timestamp=discord.utils.utcnow())
                    new_embed.add_field(name="Ended: ",value=f"{discord.utils.format_dt(discord.utils.utcnow(), 'R')}")
                    new_embed.add_field(name="Hosted by: ",value=host.mention if host else "Unknown Host")
                    new_embed.add_field(name="Entries: ",value=f"**{len(users)}**")
                    new_embed.add_field(name="Winners: ",value=winner_mentions)
                    await giveaway_message.edit(embed=new_embed)

    @tasks.loop(hours=24)
    async def update_giveaways(self):
        """Loop that attempts to purge giveaways every day at 12 AM UTC"""
        now_utc = discord.utils.utcnow()
        if now_utc.hour == 0 and now_utc.minute == 0:
            await self.reset_giveaways()

    @update_giveaways.before_loop
    async def before_update_giveaways(self):
        """Waits until 12 AM UTC before updating giveaways"""
        now = discord.utils.utcnow()
        target_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_time = (target_time - now).total_seconds()
        await discord.utils.sleep_until(target_time)

    @commands.command()
    async def greroll(self, ctx: commands.Context, id: int):
        """Rerolls a giveaway, if said giveaway exists and has ended"""
        if not await has_valid_id(ctx.author, ctx.channel, ctx.guild, self.database, "giveaway_hosts"):
            raise commands.MissingPermissions
        giveaway = await self.database.get_guild_collection(ctx.guild.id, "giveaway")
        document = await giveaway.find_one({"message_id": id})
        if document and document["ended"]:
            channel = ctx.guild.get_channel(document["channel_id"])
            if channel and ctx.author.id == document["host_id"] or ctx.author.guild_permissions.manage_guild:
                giveaway_message = await channel.fetch_message(id)
                winners_list_db = document["winners_list"]
                reactions = [reaction for reaction in giveaway_message.reactions if reaction.emoji == "🎉"]
                users = reactions[0].users()
                users = [user async for user in users if not user.bot and user.id not in winners_list_db]
                winners_count = document["winners_num"]
                host = self.bot.get_user(document["host_id"])
                winners = users if len(users) < winners_count else random.sample(users, winners_count)
                users_list = [user.id for user in users]
                winners_list = [winner.id for winner in winners]
                await giveaway.update_one({"message_id": id}, {"$set": {"ended": True, "participants": users_list, "winners_num": len(winners), "winners_list": winners_list}})
                if winners:
                    winner_mentions = ", ".join([user.mention for user in winners])
                    await channel.send(f"Congratulations {winner_mentions}! You won the **{document['prize']}**!")
                else:
                    winner_mentions = "None"
                    await channel.send(f"No winners could be rerolled for **{document['prize']}**.")
                new_embed = discord.Embed(color=discord.Color.dark_gray(),title=document['prize'],timestamp=discord.utils.utcnow())
                new_embed.add_field(name="Ended: ",value=f"{discord.utils.format_dt(discord.utils.utcnow(), 'R')}")
                new_embed.add_field(name="Hosted by: ",value=host.mention if host else "Unknown Host")
                new_embed.add_field(name="Entries: ",value=f"**{len(users)}**")
                new_embed.add_field(name="Winners: ",value=winner_mentions)
                await giveaway_message.edit(embed=new_embed)
            else:
                raise commands.MissingPermissions
        else:
            raise commands.CommandInvokeError
    @greroll.error
    async def on_greroll_error(self, ctx: commands.Context, error):
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
    async def gstart(self, ctx: commands.Context, time: Union[str, float], winners: int, *, prize: str):
        """Starts a giveaway that will end in the given time, have the given number of winners, and is for the given prize"""
        if not await has_valid_id(ctx.author, ctx.channel, ctx.guild, self.database, "giveaway_hosts"):
            raise commands.MissingPermissions
        if winners <= 0:
            raise commands.UserInputError
        guild_id = ctx.guild.id
        giveaway_collection = await self.database.get_guild_collection(guild_id, "giveaway")
        if isinstance(time, str):
            duration = await parse_time_string(time)
            if not duration:
                raise commands.UserInputError
        else:
            duration = datetime.fromtimestamp(time,timezone.utc)
        end_time = discord.utils.utcnow() + duration
        embed = discord.Embed(title=prize, color=discord.Color.dark_gray(),timestamp=discord.utils.utcnow())
        embed.add_field(name="Ends in: ", value=f"{discord.utils.format_dt(end_time, 'R')}")
        embed.add_field(name="Hosted by: ", value=ctx.author.mention)
        embed.add_field(name="Entires: ", value="**0**")
        embed.add_field(name="Winners: ",value=winners)
        giveaway_message = await ctx.send(embed=embed)
        try:
            await giveaway_message.add_reaction("🎉")
        except Exception as e:
            try:
                giveaway_message.delete()
            except Exception:
                pass
            raise e
        giveaway_doc = {
            "message_id": giveaway_message.id,
            "channel_id": ctx.channel.id,
            "end_time": end_time,
            "prize": prize,
            "host_id": ctx.author.id,
            "winners_num": winners,
            "winners_list": [],
            "participants": [], 
            "ended": False
        }
        giveaway_collection.insert_one(giveaway_doc)
        self.bot.loop.create_task(self.schedule_giveaway_end(giveaway_message.id, ctx.guild.id, duration.total_seconds()))
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
        if payload.emoji.name == "🎉":
            channel = self.bot.get_channel(payload.channel_id)
            guild = self.bot.get_guild(payload.guild_id)
            user = self.bot.get_user(payload.user_id)
            message = await channel.fetch_message(payload.message_id)
            allowed = await has_valid_id(user, channel, guild, self.database, "giveaway_blacklist")
            if not allowed:
                await message.remove_reaction("🎉", user)
                await user.send(f"You cannot enter this giveaway in {guild.name} due to being blacklisted from entering giveaways.")
                return
            collection_name = "giveaway"
            giveaway_collection = await self.database.get_guild_collection(payload.guild_id, collection_name)
            giveaway = await giveaway_collection.find_one({"message_id": payload.message_id})
            if giveaway and not giveaway["ended"]:
                if user and not user.bot:
                    await giveaway_collection.update_one({"message_id": payload.message_id},{"$addToSet": {"participants": payload.user_id}})
                    participants = giveaway.get("participants", [])
                    embed = message.embeds[0]
                    embed.set_field_at(2, name="Entries:",value=f"**{str(len(participants) + 1)}**")
                    await message.edit(embed=embed)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Removes the user from the giveaway entries list, if the message is a valid giveaway"""
        if payload.emoji.name == "🎉":
            collection_name = "giveaway"
            giveaway_collection = await self.database.get_guild_collection(payload.guild_id, collection_name)
            giveaway = await giveaway_collection.find_one({"message_id": payload.message_id})
            if giveaway and not giveaway["ended"]:
                guild = self.bot.get_guild(payload.guild_id)
                user = guild.get_member(payload.user_id)
                if user and not user.bot:
                    await giveaway_collection.update_one({"message_id": payload.message_id},{"$pull": {"participants": payload.user_id}})
                    participants = giveaway.get("participants", [])
                    channel = self.bot.get_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    embed = message.embeds[0]
                    num_p = len(participants)
                    if num_p - 1 <= 0:
                        num_p = 0
                    embed.set_field_at(2, name="Entries:", value=f"**{num_p}**")
                    await message.edit(embed=embed)

async def setup(bot: commands.Bot): 
    """Sets up the Giveaway Cog"""
    await bot.add_cog(Giveaway(bot))

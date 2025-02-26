from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor
from pymongo.results import DeleteResult, UpdateResult
from typing import Any, Tuple
from utility.guild import Database, expand_time_string, parse_time_string
import discord
import re

CHANNEL_ID = "channel_id"
DM_REMINDER = "dm_reminder"
MESSAGE = "message"
MESSAGE_ID = "message_id"
REPEAT = "repeat"
REPEAT_INTERVAL = "repeat_interval"
TARGET_TIME = "target_time"
USER_ID = "user_id"

class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the Reminders module"""
        self.bot: commands.Bot = bot
        self.database = Database(self.bot)
        self.check_reminders.start()
    
    async def calculate_time(self, time_format, time: datetime) -> datetime:
        """Parses the time argument and determines how much time a reminder should last before activating"""
        if isinstance(time_format, float):
            return datetime.fromtimestamp(time_format, timezone.utc)
        time_map: dict[str, int] = {"mo": 30 * 24 * 3600, "w": 7 * 24 * 3600, "d": 24 * 3600, "h": 3600, "m": 60, "s": 1}
        total_seconds = 0
        matches: list[Any] = re.findall(r"(\d+)([smhdwmo]+)", time_format)
        for amount, unit in matches:
            seconds: int = time_map.get(unit, 0) * int(amount)
            total_seconds += seconds
        return time + timedelta(seconds=total_seconds)
    
    async def parse_reminder_args(self, args: str) -> Tuple[str, str, str, str]:
        """Parses the arguments of a reminder command, checking the format, dm vs channel, reminder message, and interval for repeating reminders"""
        match: re.Match[str] = re.match(r"(\d+[smhdwmo]+)\s+(dm|channel)\s+(.+?)(?:\s+(\d+[smhdwmo]+))?$", args)
        if match:
            time_format, dm_channel, message, interval = match.groups()
            return time_format, dm_channel, message.strip('"'), interval
        else:
            return None, None, None, None 
    
    async def schedule_reminder(self, user_id: int, channel_id: int, message_id: int, guild_id: int, reminder_msg: str, target_time: datetime, dm_reminder: bool, repeat: bool = False, repeat_interval=None) -> None:
        """Schedules a reminder by storing the reminder data into the database"""
        reminders: AsyncIOMotorCollection = await self.database.get_guild_collection(guild_id, self.database.reminders)
        reminder: dict[str, Any] = {
            USER_ID: user_id,
            CHANNEL_ID: channel_id,
            MESSAGE_ID: message_id,
            MESSAGE: reminder_msg,
            TARGET_TIME: target_time,
            DM_REMINDER: dm_reminder,
            REPEAT: repeat,
            REPEAT_INTERVAL: repeat_interval
        }
        await reminders.insert_one(reminder)
    
    @tasks.loop(seconds=10)
    async def check_reminders(self) -> None:
        """Checks every reminder once per 10 seconds and determines if the reminder should be activated and/or removed"""
        current_time: datetime = discord.utils.utcnow()
        for guild in self.bot.guilds:
            reminders_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(guild.id, self.database.reminders)
            reminders: AsyncIOMotorCursor = reminders_collection.find({TARGET_TIME: {"$lte": current_time}})
            async for reminder in reminders:
                user: discord.User = self.bot.get_user(reminder[USER_ID])
                if reminder[DM_REMINDER] and user:
                    try:
                        if reminder[REPEAT_INTERVAL]:
                            interval: datetime = await self.calculate_time(reminder[REPEAT_INTERVAL], current_time)
                            await user.send(f"Reminder from {guild.name}: {reminder[MESSAGE]}. Set to repeat at {discord.utils.format_dt(interval, 'R')}")
                        else:
                            await user.send(f"Reminder from {guild.name}: {reminder[MESSAGE]}")
                    except Exception:
                        pass
                else:
                    channel: discord.abc.GuildChannel | discord.Thread = self.bot.get_channel(reminder[CHANNEL_ID])
                    if channel and user:
                        if reminder[REPEAT_INTERVAL]:
                            interval = await self.calculate_time(reminder[REPEAT_INTERVAL], current_time)
                            await channel.send(f"{user.mention}, reminder: {reminder[MESSAGE]}. Set to repeat at {discord.utils.format_dt(interval, 'R')}")
                        else:
                            await channel.send(f"{user.mention}, reminder: {reminder[MESSAGE]}")
                if reminder[REPEAT]:
                    repeat_interval: timedelta = await parse_time_string(reminder[REPEAT_INTERVAL])
                    new_target_time: datetime = reminder[TARGET_TIME] + repeat_interval
                await reminders_collection.update_one({MESSAGE_ID: reminder[MESSAGE_ID]}, {"$set": {TARGET_TIME: new_target_time}}) if reminder[REPEAT] else await reminders_collection.delete_one({MESSAGE_ID: reminder[MESSAGE_ID]})  

    @commands.command()
    async def remind(self, ctx: commands.Context, *, args: str) -> discord.Message | None:
        """Creates a reminder for the command user, with the arguments of the time to remind the user, dm/channel specification, reminder message, and interval time for repeating reminders"""
        time_format, dm_channel, message, interval = await self.parse_reminder_args(args)
        if not time_format:
            return await ctx.send("Invalid time format. Please provide a valid timestamp or duration (e.g., '1m', '2h').")
        if dm_channel is None:
            return await ctx.send("Please specify either 'dm' or 'channel' for reminder location.")
        if not message:
            return await ctx.send("Please provide a message for the reminder.")
        if interval:
            interval_format: timedelta = await parse_time_string(interval)
            if not interval_format:
                return await ctx.send("Invalid time format. Please provide a valid timestamp or duration (e.g., '1m', '2h').")
        set_interval: bool = True if interval else False
        target_time: datetime = await self.calculate_time(time_format, discord.utils.utcnow())
        await self.schedule_reminder(ctx.author.id, ctx.channel.id, ctx.message.id, ctx.guild.id, message, target_time, dm_channel == "dm", set_interval, repeat_interval=interval)
        reminder_location: str = "DMs" if dm_channel == "dm" else ctx.channel.mention
        interval: str = await expand_time_string(interval) if interval else None
        await ctx.send(f"Reminder set for {discord.utils.format_dt(target_time, 'R')} in {reminder_location}!{' Repeating every ' + interval if interval else ''}")
    @remind.error
    async def on_remind_error(self, ctx: commands.Context, error) -> None:
        await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    async def reminddelete(self, ctx: commands.Context, reminder_id: int) -> None:
        """Deletes a reminder for the user with the given reminder ID"""
        reminders_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(ctx.guild.id, self.database.reminders)
        result: DeleteResult = await reminders_collection.delete_one({MESSAGE_ID: reminder_id, USER_ID: ctx.author.id})
        await ctx.send("Reminder deleted successfully.") if result.deleted_count > 0 else await ctx.send("Could not find the reminder or you don't have permission to delete it.")
    @reminddelete.error
    async def on_reminddelete_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a message/reminder ID.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid reminder/message ID.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    async def remindedit(self, ctx: commands.Context, reminder_id: int, *, new_message: str) -> None:
        """Edits a reminder for the user with the given ID, if they created the reminder"""
        reminders_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(ctx.guild.id, self.database.reminders)
        result: UpdateResult = await reminders_collection.update_one({MESSAGE_ID: reminder_id, USER_ID: ctx.author.id},{"$set": {MESSAGE: new_message}})
        await ctx.send("Reminder updated successfully.") if result.modified_count > 0 else await ctx.send("Could not update the reminder. Make sure the reminder exists and you own it.")
    @remindedit.error
    async def on_remindedit_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid message/reminder ID and message.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid reminder/message ID and message.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def remindlist(self, ctx: commands.Context) -> None:
        """List all active reminders for the command user"""
        reminders_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(ctx.guild.id, self.database.reminders)
        reminders: AsyncIOMotorCursor = reminders_collection.find({USER_ID: ctx.author.id})
        active_reminders: list[str] = []
        async for reminder in reminders:
            target_time: datetime = reminder[TARGET_TIME]
            target_time = target_time.replace(tzinfo=timezone.utc)
            active_reminders.append(f"ID: {reminder[MESSAGE_ID]}, Message: {reminder[MESSAGE]}, Time: {discord.utils.format_dt(target_time, 'R')}")
        await ctx.send("You don't have any active reminders.") if not active_reminders else await ctx.send(f"Your reminders:\n" + "\n".join(active_reminders))
            
    @remindlist.error
    async def on_remindlist_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?remindlist")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
async def setup(bot: commands.Bot) -> None:
    """Sets up the Reminder Cog"""
    await bot.add_cog(Reminder(bot))
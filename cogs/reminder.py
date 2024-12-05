from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks
import re
from utility.guild import Database, parse_time_string

class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Reminders module"""
        self.bot = bot
        self.database = Database(self.bot)
        self.check_reminders.start()
    
    async def calculate_time(self, time_format, time: datetime):
        """Parses the time argument and determines how much time a reminder should last before activating"""
        if isinstance(time_format, float):
            return datetime.fromtimestamp(time_format, timezone.utc)
        time_map = {"mo": 30 * 24 * 3600, "w": 7 * 24 * 3600, "d": 24 * 3600, "h": 3600, "m": 60, "s": 1}
        total_seconds = 0
        matches = re.findall(r"(\d+)([smhdwmo]+)", time_format)
        for amount, unit in matches:
            seconds = time_map.get(unit, 0) * int(amount)
            total_seconds += seconds
        return time + timedelta(seconds=total_seconds)
    
    async def parse_reminder_args(self, args: str):
        """Parses the arguments of a reminder command, checking the format, dm vs channel, reminder message, and interval for repeating reminders"""
        match = re.match(r"(\d+[smhdwmo]+)\s+(dm|channel)\s+(.+?)(?:\s+(\d+[smhdwmo]+))?$", args)
        if match:
            time_format, dm_channel, message, interval = match.groups()
            return time_format, dm_channel, message.strip('"'), interval
        else:
            return None, None, None, None 
    
    async def schedule_reminder(self, user_id: int, channel_id: int, message_id: int, guild_id: int, reminder_msg: str, target_time: datetime, dm_reminder: bool, repeat: bool = False, repeat_interval=None):
        """Schedules a reminder by storing the reminder data into the database"""
        reminders = await self.database.get_guild_collection(guild_id, "reminders")
        reminder = {
            "user_id": user_id,
            "channel_id": channel_id,
            "message_id": message_id,
            "message": reminder_msg,
            "target_time": target_time,
            "dm_reminder": dm_reminder,
            "repeat": repeat,
            "repeat_interval": repeat_interval
        }
        await reminders.insert_one(reminder)
    
    @tasks.loop(seconds=10)
    async def check_reminders(self):
        """Checks every reminder once per 10 seconds and determines if the reminder should be activated and/or removed"""
        current_time = discord.utils.utcnow()
        for guild in self.bot.guilds:
            reminders = await self.database.get_guild_collection(guild.id, "reminders")
            reminders_list = reminders.find({"target_time": {"$lte": current_time}})
            async for reminder in reminders_list:
                user = self.bot.get_user(reminder["user_id"])
                if reminder["dm_reminder"]:
                    if user:
                        await user.send(f"Reminder: {reminder['message']}")
                else:
                    channel = self.bot.get_channel(reminder["channel_id"])
                    if channel and user:
                        await channel.send(f"{user.mention}, reminder: {reminder['message']}")
                if reminder["repeat"]:
                    repeat_interval_format = await parse_time_string(reminder["repeat_interval"])
                    new_target_time = reminder["target_time"] + repeat_interval_format
                    await reminders.update_one({"_id": reminder["_id"]}, {"$set": {"target_time": new_target_time}})
                else:
                    await reminders.delete_one({"_id": reminder["_id"]})

    @commands.command()
    async def remind(self, ctx: commands.Context, *, args: str):
        """Creates a reminder for the command user, with the arguments of the time to remind the user, dm/channel specification, reminder message, and interval time for repeating reminders"""
        time = discord.utils.utcnow()
        time_format, dm_channel, message, interval = await self.parse_reminder_args(args)
        if not time_format:
            await ctx.send("Invalid time format. Please provide a valid timestamp or duration (e.g., '1m', '2h').")
            return
        if dm_channel is None:
            await ctx.send("Please specify either 'dm' or 'channel' for reminder location.")
            return
        if not message:
            await ctx.send("Please provide a message for the reminder.")
            return
        if interval:
            set_interval = True
            interval_format = await parse_time_string(interval)
            if not interval_format:
                await ctx.send("Invalid time format. Please provide a valid timestamp or duration (e.g., '1m', '2h').")
                return
        else:
            set_interval = False
        target_time = await self.calculate_time(time_format, time)
        await self.schedule_reminder(
            ctx.author.id, ctx.channel.id, ctx.message.id, ctx.guild.id,
            message, target_time, dm_channel == "dm", set_interval, repeat_interval=interval
        )
        reminder_location = "DMs" if dm_channel == "dm" else ctx.channel.mention
        await ctx.send(f"Reminder set for {discord.utils.format_dt(target_time, 'R')} in {reminder_location}!{' Repeating every ' + interval if interval else ''}")
    @remind.error
    async def on_remind_error(self, ctx: commands.Context, error):
        await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
        print(type(error))

    @commands.command()
    async def reminddelete(self, ctx: commands.Context, reminder_id: int):
        """Deletes a reminder for the user with the given reminder ID"""
        reminders = await self.database.get_guild_collection(ctx.guild.id, "reminders")
        result = await reminders.delete_one({"message_id": reminder_id, "user_id": ctx.author.id})
        if result.deleted_count > 0:
            await ctx.send("Reminder deleted successfully.")
        else:
            await ctx.send("Could not find the reminder or you don't have permission to delete it.")
    @reminddelete.error
    async def on_reminddelete_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a message/reminder ID.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid reminder/message ID.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    async def remindedit(self, ctx: commands.Context, reminder_id: int, *, new_message: str):
        """Edits a reminder for the user with the given ID, if they created the reminder"""
        reminders = await self.database.get_guild_collection(ctx.guild.id, "reminders")
        result = await reminders.update_one(
            {"message_id": reminder_id, "user_id": ctx.author.id},
            {"$set": {"message": new_message}}
        )
        if result.modified_count > 0:
            await ctx.send("Reminder updated successfully.")
        else:
            await ctx.send("Could not update the reminder. Make sure the reminder exists and you own it.")
    @remindedit.error
    async def on_remindedit_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid message/reminder ID and message.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid reminder/message ID and message.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def remindlist(self, ctx: commands.Context):
        """List all active reminders for the command user"""
        reminders_collection = await self.database.get_guild_collection(ctx.guild.id, "reminders")
        reminders = reminders_collection.find({"user_id": ctx.author.id})
        reminder_list = []
        async for r in reminders:
            target_time: datetime = r['target_time']
            target_time = target_time.replace(tzinfo=timezone.utc)
            reminder_list.append(f"ID: {r['message_id']}, Message: {r['message']}, Time: {discord.utils.format_dt(target_time, 'R')}")
        if not reminder_list:
            await ctx.send("You don't have any active reminders.")
        else:
            await ctx.send(f"Your reminders:\n" + "\n".join(reminder_list))
    @remindlist.error
    async def on_remindlist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?remindlist")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
async def setup(bot: commands.Bot):
    """Sets up the Reminder Cog"""
    await bot.add_cog(Reminder(bot))
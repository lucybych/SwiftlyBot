from datetime import datetime, timedelta, date
from discord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorClient, AsyncIOMotorCursor, AsyncIOMotorDatabase
from typing import Annotated, Any, List, Optional, Tuple, Union
from pymongo.results import DeleteResult
from utility.finder import find_channel, find_int, find_role
from utility.guild import Database, expand_time_string, get_channel, get_user, ordinal, parse_time_string
import asyncio
import datetime
import discord
import io
import math
import pytz
import shlex

BANSYNC_REASON = "Bansync across EMD servers"
EMD_SERVERS: list[int] = [385956732888678402,575829746961874963,667526492963602449,673735253143060481,715103013395759147,722922843616313447,788582109425565736,667527355048132623,667527442633850900,667527490667020292,667527539735920640,667527591183253514,667546269530718223,667897780659945512,667897887086346271,667897923584917505,667897969588305922,668594992104865810,668595061994553344,668595128398774293,668595207499022365,668595312012820491,668595505965826049,668595586458451997,668595639139041281,668595716418961415,668995723957633037,668995839838126080,668995890823954443,668995943928168478,668995991789371402,668996048857071616,668996095707447306,668996136853307412,668996185813417985,668996230415908885,669303632088268830,669303709544742913,669303797339914242,669303861491662850,669303936322109457,669304003653271556,670357952468746251,670358004834500649,670358055606681610,670358110145347603,670358161206542338,670358221084688466,670358263442964510,670358306929508383,670358347882561542,670358392623202335,669304054442098698,669304108246761494,669304217349128192,669654192352264192,669654244688658452,669654290549309442,669654328516280325,669654375739949120,669654417544445982,669654455339319347,669654495596249116,669654552399577098,669654593084456986,670023267452715058,670023313887592490,670023349014888488,670023384620466267,670023417885622278,670023453037953064,670023490702671881,670023524769071104,670023564522553375,670023595954667561,671488653528399882,671488700185575432,671488733975150613,671488763381284866,671489031653031956,671489098250190875,671489129220931604,671489154219114558,671489177938034718,672265556711309350,672266112192217110,672266184355348483,672266227393232899,672266264877465600,672266298553663498,672266334456905739,672266369466761216,672266402446704640,672266508931694593,672584940789039106,672584977409638440,672585035034918932,672585079456792596,672585122247344138,672585165524041767,672585208775704596,672585245421338634,672585338300137482,672585380217880609,672934859127390228,672934894124662794,672934922742267968,672934951011876894,672934983827980300,672935017848242206,672935052187009057,672935087372763147,672935124962246677,672935164237840435,673059226045775882,673059255158308864,673059287307911184,673059315367673877,673059350562078721,673059378722766854,673059425568686081,673059455650496542,673059487044599809,673059520469270568,673069260842729483,673069297316265985,672947122026315776,672947162547486750,672947189491826690,672947221163147316,672947246681292801,672947267883237416,672947303501398018,672947345075470343,672947380441841693,672947415296376882,673285360771530798,673285388277645315,673285422532526095,673285451259576331,673285477792743444,673285506615738368,673285529533677580,673285553877418004,673285576799289378,673285605936988172,673285631920570400,673285659263238164,673288617963159593,673288650242392113,673288678126387230,673288715581521934,673288739589586957,673288761517408306,673288796036399125,673288817859493929,673391852053069842,673391894868525057,673391918339850259,673391945560752154,673391975801552909,673392005048434688,673392034291384350,673392061965402184,673392084547403787,673392115077742595,673392146212061185,673392178134777867,673392211345408018,673392237958397962,673392271047262228,700845513204826133,736693732358881351,736693781281374279,700845165648019588,700845322494017581,700845338449412176,700845352810446930,700845371194081291,701877065376333866,701877079444160564,701877094266699806,701877112948391956,701877132095127801,701877149132652676,701877169336615018,701877188328423524,701877208431460455,701877236629766144,701877254430654545,671185402073317380,672677496596070401,673056866309373953,673442194421448737,677727489371668510,696494688823148685,677723036715188283,673414993630461983,673415041340407818,673415067781562368,673415092678950964,800180724639465563]
RATE_LIMIT = 2000
RBAN_REASON = "Silent or requested ban"
RKICK_REASON = "Silent or requested kick"
RMUTE_EXPIRY_REASON = "Expiry of silent or requested unmute"
RMUTE_REASON = "Silent or requested mute"
RQUARANTINE_REASON = "Silent or requested quarantine"
RTEMPBAN_EXPIRY_REASON = "Expiry of silent or requested tempban"
RTEMPBAN_REASON = "Silent or requested tempban"
RTIMEOUT_EXPIRY_REASON = "Expiry of silent or requested untimeout"
RTIMEOUT_REASON = "Silent or requested timeout"
RUNBAN_REASON = "Silent or requested unban"
RUNMUTE_REASON = "Silent or requested unmute"
RUNQUARANTINE_REASON = "Silent or requested unquarantine"
RUNTIMEOUT_REASON = "Silent or requested untimeout"
SILENT_REASONS: list[str] = [RBAN_REASON, RKICK_REASON, RMUTE_EXPIRY_REASON, RMUTE_REASON, RQUARANTINE_REASON, RTEMPBAN_REASON, RTEMPBAN_EXPIRY_REASON, RTIMEOUT_EXPIRY_REASON, RTIMEOUT_REASON, RUNBAN_REASON, RUNMUTE_REASON, RUNQUARANTINE_REASON, RUNTIMEOUT_REASON]

DURATION = "duration"
ID = "id"
LOG_CHANNEL_ID = "log_channel_id"
MESSAGE_LOG_ID = "message_log_id"
OFFENDER = "offender"
REASON = "reason"
RESPONSIBLE_MODERATOR = "responsible_moderator"
TIMESTAMP = "timestamp"
TYPE = "type"

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the Moderation module"""
        self.bot: commands.Bot = bot 
        self.database = Database(self.bot)
        self.update_ban_limit.start()
    
    async def can_unmute(self, guild: discord.Guild, user: Union[discord.Member, discord.User], timestamp: datetime) -> bool:
        """Determines if a user can be unmuted by checking if they have a more recent mute."""
        moderation: AsyncIOMotorClient = await self.database.get_guild_collection(guild.id, self.database.moderation)
        mutes: AsyncIOMotorDatabase = moderation.find({TYPE: "mute", OFFENDER: user.id})
        async for mute in mutes:
            if pytz.timezone("UTC").localize(mute[TIMESTAMP])  > timestamp:
                return False
        return True
    
    async def check_ban_limit(self, guild: discord.Guild) -> bool:
        """Checks how many bans the server has made for the day and if the rate limit has been reached"""
        ban_limit: int = await self.database.get_config(guild.id, self.database.ban_limit)
        return bool(ban_limit and ban_limit >= RATE_LIMIT)

    async def create_log_entry(self, guild: discord.Guild, mod_log: discord.TextChannel, color: discord.Color, type: str, offender: Union[discord.User,discord.Member], reason: str, responsible: discord.Member, duration: Optional[str], evidence: List[discord.Attachment] = None):
        """Creates an embed with the necessary information from a punishment (offender, duration, reason, responsible moderator, etc.)"""
        current_time: datetime = discord.utils.utcnow()
        id: int = await self.database.get_next_id(guild.id)
        moderation: AsyncIOMotorCollection = await self.database.get_guild_collection(guild.id, self.database.moderation)
        embed = discord.Embed(color=color, title=f"{type} | case {id}", timestamp=current_time)
        offender_id: int = offender.id if isinstance(offender, Union[discord.Member, discord.User]) else 0
        embed.add_field(name="Offender: ", value=offender.mention,inline=False)
        if (type == "mute" or type == "timeout") and duration:
            embed.add_field(name="Duration: ",value=duration,inline=False)
        embed.add_field(name="Reason: ",value=reason,inline=False)
        embed.add_field(name="Responsible Moderator: ",value=responsible.name,inline=False)
        embed.set_footer(text=f"ID: {offender.id}")
        log_message: discord.Message = await mod_log.send(embed=embed)
        if evidence:
            files: List[discord.File] = [await attachment.to_file() for attachment in evidence]
            await mod_log.send(content=f"Evidence for Case {id}:", files=files)
        entry: dict[str, Any] = {
            ID: id,
            TYPE: type,
            OFFENDER: offender_id,
            REASON:  reason,
            RESPONSIBLE_MODERATOR: responsible.id,
            MESSAGE_LOG_ID: log_message.id,
            LOG_CHANNEL_ID: mod_log.id,
            TIMESTAMP: current_time,
        }
        if duration:
            entry[DURATION] = duration
        moderation.insert_one(entry)

    async def generic_ban(self, ctx: commands.Context, users: List[Union[discord.Member, discord.User]], reason: str, toggle: Optional[str], evidence: List[discord.Attachment]) -> discord.Message | None:
        """Generic banning function that handles all ban commands (ab, sb, tb, uau, ban, rban)"""
        if await self.check_ban_limit(ctx.guild):
            return await ctx.send("The ban rate limit of 2,000 has been reached for the server. Please try again after 12 AM UTC.")
        s_bans, f_bans = await self.punishment_steps(ctx.guild, "ban", users, reason, ctx.author, None, None, None, evidence)
        if toggle:
            if toggle.startswith("Bansync"):
                if len(s_bans) > 0:
                    await ctx.send(f"Successfully banned **{len(s_bans)}** users.")
                if len(f_bans) > 0:
                    await ctx.send(f"Failed to ban the following IDs: {', '.join(user.mention for user in f_bans)}")
            else:
                if len(s_bans) > 0:
                        await ctx.send(f"{', '.join(user.mention for user in s_bans)} {'was' if len(s_bans) == 1 else 'were'} banned.\n**Reason:** {toggle}.")
                if len(f_bans) > 0:
                    await ctx.send(f"Failed to ban {', '.join(user.mention for user in f_bans)}")
        else:
            if len(s_bans) > 0:
                await ctx.send(f"Banned {', '.join(user.mention for user in s_bans)}")
            if len(f_bans) > 0:
                await ctx.send(f"Failed to ban {', '.join(x.mention for x in f_bans)}")
    
    async def get_messages(self, guild: discord.Guild, num: int, message: discord.Message, user: Optional[Union[discord.User, discord.Member]], channel: Optional[discord.TextChannel]) -> List[discord.Message]:
        """Gets the num most recent messages in the server, optionally filtered by user or channel."""
        messages: List[discord.Message] = []
        channels_to_search: List[discord.TextChannel] = [channel] if channel else guild.text_channels
        for channel2 in channels_to_search:
            async for msg in channel2.history(limit=num+1):
                if (msg.id != message.id) and (user and msg.author.id == user.id):
                    messages.append(msg)
        messages.sort(key=lambda msg: msg.created_at, reverse=True)
        return messages[:num]
    
    async def get_num_warnings(self, user: discord.User, guild: discord.Guild) -> int:
        """Grabs the number of warnings for a given user in a given server"""
        moderation: AsyncIOMotorCollection = await self.database.get_guild_collection(guild.id, self.database.moderation)
        return await moderation.count_documents({TYPE: "warn", OFFENDER: user.id})
    
    async def log_punishment(self, type: str, guild: discord.Guild, offender: Union[discord.User,discord.Member], reason: str, responsible: discord.Member, duration: Optional[str], evidence: List[discord.Attachment] = None):
        """Sends a message in the moderation log that logs the following information:
        Mutes - Offender's name and ID, duration of mute, reason for mute, person who performed the mute's name
        Unmutes - Offender's name and ID, reason for unmute, person who performed the unmute's name
        Quarantine - Offender's name and ID, reason for quarantine, person who performed the quarantine's name
        Unquarantine - Offender's name and ID, reason for unquarantine, person who performed the quarantine's name
        Warning - Offender's name and ID, reason for warn, person who performed the warn's name"""
        mod_log: discord.abc.GuildChannel | discord.Thread = await find_channel(guild, self.database, self.database.mod_log)
        if not mod_log or reason in SILENT_REASONS:
            return
        if type == "mute":
            await self.create_log_entry(guild, mod_log, discord.Color.orange(), "mute", offender, reason, responsible, duration, evidence)
        elif type == "unmute":
            await self.create_log_entry(guild, mod_log, discord.Color.green(), "unmute", offender, reason, responsible, duration, evidence)
        elif type == "quarantine":
            await self.create_log_entry(guild, mod_log, discord.Color.light_gray(), "quarantine", offender, reason, responsible, duration, evidence)
        elif type == "unquarantine":
            await self.create_log_entry(guild, mod_log, discord.Color.brand_green(), "unquarantine", offender, reason, responsible, duration, evidence)
        elif type == "warn":
            await self.create_log_entry(guild, mod_log, discord.Color.yellow(), "warn", offender, reason, responsible, duration, evidence)
        elif type == "delete":
            await self.create_log_entry(guild, mod_log, discord.Color(000000), "Message deleted", offender, reason, responsible, duration, evidence)

    async def perform_punishment(self, guild: discord.Guild, type: Annotated[str, lambda s: s.lower()], user: Union[discord.Member, discord.User], reason: str, until: Optional[timedelta] , role: Optional[discord.Role]) -> bool:
        """Performs the given type of punishment, then indicates if it was successfully applied."""
        if type == "ban":
            ban_limit: int = await self.database.get_config(guild.id, self.database.ban_limit)
            ban_limit = ban_limit if ban_limit else 0
            try:
                if ban_limit + 1 < RATE_LIMIT:
                    await guild.ban(user, reason=reason)
                    ban_limit += 1
                    await self.database.update_config(guild.id, {"$set": {self.database.ban_limit: ban_limit}})
                    return True
                else:
                    return False
            except Exception:
                return False
        elif type == "unban":
            try:
                await guild.unban(user, reason=reason)
                return True
            except Exception:
                return False
        elif type == "kick":
            try:
                await guild.kick(user, reason=reason)
                return True
            except Exception:
                return False
        elif type == "timeout":
            try:
                await user.timeout(until, reason=reason)
                return True
            except Exception:
                return False
        elif type == "untimeout":
            try:
                await user.timeout(None, reason=reason)
                return True
            except Exception:
                return False
        elif type == "mute" and role:
            try:
                await user.add_roles(role, reason=reason)
                return True
            except Exception:
                return False
        elif type == "unmute" and role:
            try:
                await user.remove_roles(role, reason=reason)
                return True
            except Exception:
                return False
        elif type == "quarantine" and role:
            quarantine_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(role.guild.id, self.database.quarantine)
            try:
                user_roles: list[discord.Role] = [user_role for user_role in user.roles if user_role != user.guild.default_role]
                role_ids: list[int] = [user_role.id for user_role in user_roles] if len(user_roles) > 0 else []
                await user.add_roles(role, reason=reason)
                if len(role_ids) > 0:
                    await user.remove_roles(*user_roles, reason="Removing roles for quarantine")
                    await quarantine_collection.update_one({"user_id": user.id},  {"$set": {"user_id": user.id,"role_ids": role_ids}},upsert=True)
                return True
            except Exception:
                return False
        elif type == "unquarantine" and role:
            quarantine_collection = await self.database.get_guild_collection(role.guild.id, "quarantine")
            try:
                entry: Any = await quarantine_collection.find_one({"user_id": user.id})
                await user.remove_roles(role, reason=reason)
                if entry:
                    user_roles = entry.get("role_ids", [])
                    user_roles = [role.guild.get_role(user_role) for user_role in user_roles if role.guild.get_role(user_role) is not None]
                    await quarantine_collection.delete_one({"user_id": user.id})
                    if len(user_roles) > 0:
                        await user.add_roles(*user_roles, reason="Removing user from quarantine and readding roles they previously had")
                return True
            except Exception:
                return False
        elif type == "warn":
            num_warnings: int = await self.get_num_warnings(user, guild)
            num_warnings += 1
            warn_threshold: int = await find_int(guild, self.database, "warn_threshold")
            if warn_threshold and warn_threshold > 0 and num_warnings >= warn_threshold:
                ordinal_num: str = await ordinal(num_warnings)
                await guild.ban(user, reason=f"Automatic action carried out after their {ordinal_num} warning.")
            return True
        
    async def punishment_steps(self, guild: discord.Guild, type: Annotated[str, lambda s: s.lower()], users: List[Union[discord.Member, discord.User]], reason: str, responsible: Union[discord.Member, discord.User], duration: Optional[str], role: Optional[discord.Role], until: Optional[timedelta], evidence: List[discord.Attachment] = None) -> Tuple[List[Union[discord.Member, discord.User]], List[Union[discord.Member, discord.User]]]: 
        """Applies the three steps of punishments:
        \n1. Performs the punishment
        \n2. Logs the punishment
        \n3. Sends the user a DM with the punishment information
        \nSteps 2 and 3 will only occur if the punishment was successfully applied"""
        s_punishments: list[Union[discord.User, discord.Member]] = []
        f_punishments: list[Union[discord.User, discord.Member]] = []
        for user in users:
            sf: bool = await self.perform_punishment(guild, type, user, reason, until, role)
            if sf:
                s_punishments.append(user)
                if not reason in SILENT_REASONS:
                    await self.log_punishment(type, guild, user, reason, responsible, duration, evidence)
                await self.send_offender_msg(guild, type, user, reason, responsible, duration)
            else:
                f_punishments.append(user)
        return s_punishments, f_punishments

    async def reset_ban_limits(self) -> None:
        """Resets the ban limit for a server (Since rate limits disappear over time)"""
        server_ids: list[str] = await self.database.mongo_client.list_database_names()
        for server_id in server_ids:
            await self.database.update_config(server_id, {"$set": {self.database.ban_limit: 0}})
    
    async def schedule_unmute(self, members: List[discord.Member], role: discord.Role, time_in_seconds: timedelta, reason: str, timestamp: datetime, responsible: Union[discord.User, discord.Member]):
        """Waits until a mute should be expired, determines if the user can be unmuted, and if they can, unmutes the user and logs it if it was not a requested mute"""
        await asyncio.sleep(time_in_seconds.total_seconds())
        unmuted_users: list[Union[discord.User, discord.Member]] = []
        for member in members:
            if await self.can_unmute(member.guild, member, timestamp):
                sf: bool = await self.perform_punishment(role.guild, "unmute", member, f"Automatic unmute from mute made {int(time_in_seconds.total_seconds())} seconds ago by {responsible.name}. (ID: {responsible.id})", None, role)
                if sf:
                    unmuted_users.append(member)
        if reason != RMUTE_EXPIRY_REASON:
            for unmuted_user in unmuted_users:
                await self.log_punishment("unmute", role.guild, unmuted_user, f"Automatic unmute from mute made {int(time_in_seconds.total_seconds())} seconds ago by {responsible.name}. (ID: {responsible.id})", responsible, None, None)
    
    async def schedule_untimeout(self, guild: discord.Guild, member: discord.Member, time_in_seconds: timedelta, reason: str, responsible: Union[discord.User, discord.Member]):
        """Waits until a timeout supposedly expires, and untimeouts those users after that time"""
        await asyncio.sleep(time_in_seconds.total_seconds())
        await self.punishment_steps(guild, "untimeout", member, reason, responsible, None, None, None, None)
    
    async def send_offender_msg(self, server: discord.Guild, type: Annotated[str, lambda s: s.lower()], user: Union[discord.User, discord.Member], reason: str, responsible: Union[discord.Member, discord.User], duration: Optional[str]) -> None:
        """DMs a punished user with the punishment information (type, duration, reason, responsible moderator, etc.)"""
        if reason in SILENT_REASONS:
            return
        if type == "mute" or type == "unmute" or type == "quarantine" or type == "unquarantine":
            punishment: str = type + "d"
        elif type == "ban" or type == "unban":
            punishment = type + "ned"
        elif type == "kick":
            punishment = type + "ed"
        elif type == "timeout":
            punishment = "timed out"
        elif type == "untimeout":
            punishment = "removed from timeout"
        else:
            return
        message: str = f"You have been {punishment} in {server.name} for {duration}. Reason: {reason}. Responsible Moderator: {responsible.name} (ID: {responsible.id}.)" if duration else f"You have been {punishment} in {server.name}. Reason: {reason}. Responsible Moderator: {responsible.name} (ID: {responsible.id})"
        try:
            await user.send(message)
        except Exception:
            pass
    
    async def set_permissions_in_channels(self, guild: discord.Guild, mute_role: discord.Role) -> None:
        """Sets the permissions for mutes in every channel of the server"""
        for channel in guild.channels:
            try:
                if isinstance(channel, discord.TextChannel) or isinstance(channel, discord.CategoryChannel):
                    await channel.set_permissions(mute_role, send_messages=False, add_reactions=False, send_messages_in_threads=False, create_public_threads=False, create_private_threads=False)
                elif isinstance(channel, discord.VoiceChannel):
                    await channel.set_permissions(mute_role, connect=False, speak=False, send_messages=False, add_reactions=False,)
            except Exception:
                pass
    
    async def set_quarantine_permissions(self, guild: discord.Guild, quarantine_role: discord.Role) -> None:
        """Sets the permissions for quarantines in every channel of the server"""
        for channel in guild.channels:
            try:
                await channel.set_permissions(quarantine_role, read_messages=False)
            except Exception:
                pass

    @tasks.loop(hours=24)
    async def update_ban_limit(self) -> None:
        """Resets the number of bans at 12 AM UTC"""
        current_time: datetime = discord.utils.utcnow()
        if current_time.hour == 0 and current_time.minute == 0:
            await self.reset_ban_limits()

    @update_ban_limit.before_loop
    async def before_update_ban_limit(self) -> None:
        """Sets the time for when the bans should be reset (12 AM UTC the next day)"""
        target_time: datetime = (discord.utils.utcnow() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await discord.utils.sleep_until(target_time) 

    #Done 
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ab(self, ctx: commands.Context, users: commands.Greedy[Union[discord.User, discord.Member]]) -> None:
        """Bans the given user(s) if possible with the reason of advertising"""
        await self.generic_ban(ctx, users, "Advertising their junk", "For advertising stuff (either in DMs or in the server).", ctx.message.attachments)
    @ab.error
    async def on_ab_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, users: commands.Greedy[Union[discord.User, discord.Member]], *, reason: str = "No reason given") -> None:
        """Bans the given user(s) if possible, with the given reason (if applicable)"""
        await self.generic_ban(ctx, users, reason, None, ctx.message.attachments)
    @ban.error
    async def on_ban_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def banlist(self, ctx: commands.Context) -> None:
        """Produces a .txt file of a list of banned user IDs in the server"""
        banned_users: list[discord.BanEntry] = [entry async for entry in ctx.guild.bans()]
        if len(banned_users) == 0:
            raise commands.UserNotFound(["Unknown user"])
        user_ids: str = "\n".join([str(ban_entry.user.id) for ban_entry in banned_users])
        file = io.BytesIO(user_ids.encode('utf-8'))
        filename = "banned_users.txt"
        await ctx.send("Here is the ban list of user IDs:", file=discord.File(file, filename))
    @banlist.error
    async def on_banlist_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?banlist")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view the list of banned users.")
        elif isinstance(error, commands.UserNotFound) or isinstance(error, commands.CommandInvokeError):
            await ctx.send("No banned users found for the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def bansync(self, ctx: commands.Context, file: discord.Attachment) -> discord.Message | None:
        """Bans users based on a list of IDs provided in a .txt file"""
        if not file.filename.endswith('.txt'):
            raise commands.BadArgument
        file_data: bytes = await file.read() 
        user_ids: List[str] = file_data.decode('utf-8').splitlines()
        users: List[discord.User] = [self.bot.get_user(int(user_id)) for user_id in user_ids if self.bot.get_user(int(user_id)) is not None]
        if len(users) <= 0:
            return await ctx.send("Failed to gather any banned users. Make sure that the .txt file is properly configured to have valid user IDs.")
        await self.generic_ban(ctx, users, f"Bansync performed by {ctx.author.name}", None, ctx.message.attachments)
    @bansync.error
    async def on_bansync_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid .txt file.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure it is a valid .txt file.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done        
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def clearpunishment(self, ctx: commands.Context, users: commands.Greedy[discord.User]) -> None:
        """Clears all punishments for given user(s)"""
        moderation_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(ctx.guild.id, self.database.moderation)
        for user in users:
            results: DeleteResult = await moderation_collection.delete_many({OFFENDER: user.id})
            num_deleted: int = results.deleted_count
            await ctx.send(f"Removed {num_deleted} {'punishment' if num_deleted == 1 else 'punishments'} from **{user.name}**")
    @clearpunishment.error
    async def on_clearpunishment_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to clear user punishments.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def clearwarn(self, ctx: commands.Context, users: commands.Greedy[discord.User]) -> None:
        """Clears all warnings for given user(s)"""
        moderation_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(ctx.guild.id, self.database.moderation)
        for user in users:
            results: DeleteResult = await moderation_collection.delete_many({OFFENDER: user.id, TYPE: "warn"})
            num_deleted: int = results.deleted_count
            await ctx.send(f"Removed {num_deleted} {'warning' if num_deleted == 1 else 'warnings'} from **{user.name}**")
    @clearwarn.error
    async def on_clearwarn_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to clear user warns.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, members: commands.Greedy[discord.Member], *, reason = "No reason provided") -> None:
        """Kicks the given user(s) if possible, with the given reason"""
        s_kicks, f_kicks = await self.punishment_steps(ctx.guild, "kick", members, reason, ctx.author, None, None, None, ctx.message.attachments)
        if len(s_kicks) > 0:
            await ctx.send(f"Kicked **{','.join(user.name for user in s_kicks)}**.")
        if len(f_kicks) > 0:
            await ctx.send(f"Failed to kick **{','.join(user.name for user in f_kicks)}**.")
    @kick.error
    async def on_kick_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to kick users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def modlog(self, ctx: commands.Context, users: commands.Greedy[discord.User]) -> None:
        """Grabs all moderation logs for user(s)"""
        moderation_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(ctx.guild.id, self.database.moderation)
        for user in users:
            entries: AsyncIOMotorCursor = moderation_collection.find({OFFENDER: user.id})
            embed = discord.Embed(title=f"Mod logs", color=discord.Color.blurple())
            embed.set_author(name=user.name, url=user.avatar.url)
            async for entry in entries:
                modlog_id: int = entry.get(ID)
                action: str = entry.get(TYPE)
                reason: str = entry.get(REASON, "No reason provided.")
                timestamp: datetime = entry.get(TIMESTAMP)
                mod_timestamp: date = timestamp.date()
                responsible_id: int = entry.get(RESPONSIBLE_MODERATOR)
                responsible: discord.User = self.bot.get_user(responsible_id)
                responsible_name: str = responsible.name if responsible else "Unknown Moderator"
                embed.add_field(name=f"#{modlog_id} | {action} | {mod_timestamp}",value=(f"**Responsible Moderator**: {responsible_name}\n"f"**Reason**: {reason}"),inline=True)
            await ctx.send(embed=embed) if len(embed.fields) > 0 else await ctx.send(f"No modlog entries found for **{user.name}**.")
    @modlog.error
    async def on_modlog_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view user modlogs.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context, members: commands.Greedy[discord.Member], *, args: Optional[str]) -> None:
        """Mutes the given user(s) if possible, for the given time and reason (Indefinite if no time is provided)"""
        mute_role: discord.Role = await find_role(ctx.guild, self.database, self.database.mute_role)
        if not mute_role:
            return await ctx.send("Cannot mute user(s). Make sure that the mute role is in-server and properly configured.")
        time_val = None
        duration = None
        reason = "No reason provided"
        if args:
            args_list: List[str] = shlex.split(args)
            potential_time: str = args_list[0]
            parsed_duration: timedelta = await parse_time_string(potential_time)
            if parsed_duration:
                time_val: str = potential_time
                duration: timedelta = parsed_duration
                reason = " ".join(args_list[1:]) if len(args_list) > 1 else "No reason provided"
            else:
                reason: str = args
        if duration:
            expanded: str = await expand_time_string(time_val)
            time_str: str = "for " + expanded
        else:
            expanded = None
            time_str = "indefinitely"
        s_mutes, f_mutes = await self.punishment_steps(ctx.guild, "mute", members, reason, ctx.author, expanded, mute_role, None, ctx.message.attachments)
        if s_mutes:
            await ctx.send(f"{ctx.author.name} muted {'**, **'.join(s_mute.name for s_mute in s_mutes)} {time_str}. Reason: {reason}")
        if f_mutes:
            await ctx.send(f"Failed to mute {'**, **'.join(f_mute.name for f_mute in f_mutes)}")
        if duration:
            await self.schedule_unmute(s_mutes, mute_role, duration, f"Automatic unmute made {duration} ago by {ctx.author.name} (ID: {ctx.author.id})", discord.utils.utcnow(), ctx.author)
    @mute.error
    async def on_mute_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid duration and reason, omit the duration & reason to have an indefinite mute with no reason, or omit the reason to have an indefinite mute with a reason.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to mute users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        elif isinstance(error, commands.UserInputError):
            await ctx.send("Invalid duration. Ensure that the duration is a valid time string (Ex. 4w or 2mo3d).")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def muted(self, ctx: commands.Context) -> discord.Message | None:
        """Produces a .txt file that contains the name and ID of all users who are currently muted"""
        mute_role: discord.Role = await find_role(ctx.guild, self.database, self.database.mute_role)
        if not mute_role:
            return await ctx.send("Cannot mute role. Make sure that the mute role is in-server and properly configured.")
        if len(mute_role.members) == 0:
            return await ctx.send("No members to dump.")
        user_list: str = "\n".join([f"{index + 1}. {member.name} ({member.id})"
                               for index, member in enumerate(mute_role.members)])
        file = io.BytesIO(user_list.encode('utf-8'))
        file_name: str = f"{mute_role.name}_members.txt"
        await ctx.send(file=discord.File(file, file_name))
    @muted.error
    async def on_muted_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?muted")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view all muted users.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def muterolecr(self, ctx: commands.Context) -> discord.Message | None:
        """Creates a new mute role, sets the database configuration to that role, and updates the permissions"""
        guild: discord.Guild = ctx.guild
        if await find_role(guild, self.database, self.database.mute_role):
            return await ctx.send(f"Mute role already exists in server.")
        mute_role: discord.Role = await guild.create_role(name="Muted", reason="Created for muting users", color=discord.Color.red())
        await self.set_permissions_in_channels(guild, mute_role)
        await self.database.update_config(guild.id, {"$set": {self.database.mute_role: mute_role.id}})
        await ctx.send("Muted role created and updated.")
    @muterolecr.error
    async def on_muterolecr_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?muterolecr")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to create a mute role.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
        
    #Done
    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def muteroleup(self, ctx: commands.Context) -> None:
        """Updates the existing mute role in the database by editing its permissions"""
        guild: discord.Guild = ctx.guild
        mute_role: discord.Role = await find_role(ctx.guild, self.database, self.database.mute_role)
        if not mute_role:
            return await ctx.send("Cannot find mute role. Make sure that the mute role is in-server and properly configured.")
        await self.set_permissions_in_channels(guild, mute_role)
        await ctx.send("Muted role updated.")
    @muteroleup.error
    async def on_muteroleup_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?muteroleup")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to update a mute role.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Purge
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, num: int, *, args: Optional[str]) -> discord.Message | None:
        """Purges num messages from the server, with specifications for the channel and user to purge from"""
        if not args:
            num_purged = 0
            messages = await self.get_messages(ctx.guild, num, ctx.message, None, None)
            for msg in messages:
                try:
                    await msg.delete()
                    num_purged += 1
                except Exception:
                    continue
            return await ctx.send("Failed to purge any messages.") if num_purged == 0 else await ctx.send(f"Purged {num_purged} messages from the entire server.")
        args_list: List[str] = shlex.split(args)
        if len(args_list) == 2:
            channel1: discord.abc.GuildChannel | discord.Thread = await get_channel(args_list[0], ctx.guild)
            user1: discord.User | discord.Member = await get_user(args_list[0], ctx.guild)
            channel2: discord.abc.GuildChannel | discord.Thread = await get_channel(args_list[1], ctx.guild)
            user2: discord.User | discord.Member = await get_user(args_list[1], ctx.guild)
            if channel1 and isinstance(channel1, discord.TextChannel):
                purge_channel = channel1
                if isinstance(user2, discord.Member) or isinstance(user2, discord.User):
                    purge_user = user2
                else:
                    raise commands.UserInputError
            elif user1 and (isinstance(user1, discord.Member) or isinstance(user1, discord.User)):
                purge_user = user1
                if isinstance(channel2, discord.TextChannel):
                    purge_channel = channel2
                else:
                    raise commands.UserInputError
            else:
                raise commands.UserInputError
            def check_msg(msg: discord.Message) -> bool:
                return msg.author == purge_user and msg.id != ctx.message.id
            adjusted_limit = num + 1 if purge_channel == ctx.channel else num
            messages = await purge_channel.purge(limit=adjusted_limit, check=check_msg)
            await ctx.send("Failed to purge any messages.") if len(messages) == 0 else await ctx.send(f"Purged {len(messages)} messages from {purge_channel.name}/{purge_user.name}") 
        elif len(args_list) == 1:
            channel: discord.abc.GuildChannel | discord.Thread  = await get_channel(args, ctx.guild)
            user: Union[discord.Member, discord.User] = await get_user(args, ctx.guild)
            if channel and isinstance(channel, discord.TextChannel):
                purge_channel: discord.abc.GuildChannel | discord.Thread = channel
                def check_msg_2(msg: discord.Message) -> bool:
                    return msg.id != ctx.message.id
                adjusted_limit: int = num + 1 if purge_channel == ctx.channel else num
                messages: List[discord.Message] = await purge_channel.purge(limit=adjusted_limit, check=check_msg_2)
                await ctx.send("Failed to purge any messages") if num_purged == 0 else await ctx.send(f"Purged {len(messages)} messages from {purge_channel.name}")
            elif user and (isinstance(user, discord.Member) or isinstance(user, discord.User)):
                purge_user: Union[discord.Member, discord.User] = user
                purge_channel = None
                messages = await self.get_messages(ctx.guild, num, ctx.message, purge_user, purge_channel)
                num_purged = 0
                for msg in messages:
                    try:
                        await msg.delete()
                        num_purged += 1
                    except Exception:
                        continue
                await ctx.send("Failed to purge any messages.") if num_purged == 0 else await ctx.send(f"Purged {num_purged} messages from {purge_user.name}.")
            else:
                raise commands.UserInputError
        else:
            raise commands.TooManyArguments
    @purge.error
    async def on_purge_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid number, channel, and user. Omit the channel & user to purge the entire server, omit the channel or user to only purge from a specific channel or user.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to purge messages.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that the purge number is a valid number.")
        elif isinstance(error, commands.UserInputError):
            await ctx.send("Invalid arguments provided. Must provide a valid user and/or channel. Provide just a channel or user to purge from a specific channel/user, or no inputs to purge an entire server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")    
    
    #Done
    @commands.command(aliases=['q'])
    @commands.has_permissions(manage_roles=True)
    async def quarantine(self, ctx: commands.Context, members: commands.Greedy[discord.Member], *, reason = "No reason provided") -> discord.Message | None:
        """Puts user(s) into quarantine if possible, with the given reason"""
        quarantine_role: discord.Role = await find_role(ctx.guild, self.database, self.database.quarantine_role)
        if not quarantine_role:
            return await ctx.send("Cannot quarantine user(s). Make sure that the quarantine role is in-server and properly configured.")
        s_quarantines, f_quarantines = await self.punishment_steps(ctx.guild, "quarantine", members, reason, ctx.author, None, quarantine_role, None, ctx.message.attachments)
        if len(s_quarantines) > 0:
            await ctx.send(f"{ctx.author.mention} put {', '.join(user.mention for user in s_quarantines)} in quarantine. :lock:")
        if len(f_quarantines) > 0:
            await ctx.send(f"Failed to put {', '.join(user.mention for user in f_quarantines) } in quarantine")
    @quarantine.error
    async def on_quarantine_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to quarantine users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done  
    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def quarantinecreate(self, ctx: commands.Context) -> discord.Message | None:
        """Creates a new quarantine role, sets the database configuration to that role, and updates the permissions"""
        guild: discord.Guild = ctx.guild
        if await find_role(ctx.guild, self.database, self.database.quarantine_role):
            return await ctx.send(f"Quarantine role already exists in server.")
        quarantine_role: discord.Role = await guild.create_role(name="Quarantine", reason="Created for quarantining users", color=discord.Color.darker_gray())
        await self.set_quarantine_permissions(guild, quarantine_role)
        await self.database.update_config(ctx.guild.id, {"$set": {self.database.quarantine_role: quarantine_role.id}})
        await ctx.send("Quarantine role created and updated.")
    @quarantinecreate.error
    async def on_quarantinecreate_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?quarantinecreate")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to create a quarantine role.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def quarantineup(self, ctx: commands.Context) -> discord.Message | None:
        """Updates the existing quarantine role in the database by editing its permissions"""
        guild: discord.Guild = ctx.guild
        quarantine_role: discord.Role = await find_role(ctx.guild, self.database, self.database.quarantine_role)
        if not quarantine_role:
            return await ctx.send("Cannot find quarantine role. Make sure that the quarantine role is in-server and properly configured.")
        await self.set_quarantine_permissions(guild, quarantine_role)
        await ctx.send("Quarantine role updated.")
    @quarantineup.error
    async def on_quarantineup_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?quarantineup")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to update a quarantine role.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def rban(self, ctx: commands.Context, users: commands.Greedy[Union[discord.Member, discord.User]]) -> None:
        """Bans the given user(s) if possible, without producing a moderation log"""
        await self.generic_ban(ctx, users, RBAN_REASON, None, ctx.message.attachments)
    @rban.error
    async def on_rban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def reason(self, ctx: commands.Context, ids: commands.Greedy[int], *, reason: str) -> None:
        """Changes the reason of moderation log entries with given id(s)"""
        moderation_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(ctx.guild.id, self.database.moderation)
        for id in ids:
            entry: Any = await moderation_collection.find_one({ID: id})
            if not entry:
                await ctx.send(f"No modlog entry found with ID {id}.")
                continue
            await moderation_collection.update_one({ID: id},{"$set": {REASON: reason}})
            channel_id: int = entry.get(LOG_CHANNEL_ID)
            message_id: int = entry.get( MESSAGE_LOG_ID)
            channel: discord.abc.GuildChannel | discord.Thread = self.bot.get_channel(channel_id)
            if not channel:
                await ctx.send(f"Modlog channel not found for id {id}.")
                continue
            try:
                message: discord.Message = await channel.fetch_message(message_id)
            except discord.NotFound:
                await ctx.send(f"Modlog message not found for id {id}.")
                continue
            if message.embeds:
                embed: discord.Embed = message.embeds[0]
                if embed.fields:
                    for field in embed.fields:
                        if field.name.startswith("Reason:"):
                            embed.set_field_at(embed.fields.index(field),name=field.name,value=reason,inline=field.inline)
                else:
                    embed.add_field(name=REASON, value=reason, inline=False)
                await message.edit(embed=embed)
                if ctx.channel == channel:
                    await ctx.message.delete()
                else:
                    await ctx.send(f"Updated the reason for modlog entry ID **{id}**.\n\n**Changed By:** {ctx.author}\n\n**New Reason:** {reason}")
            else:
                await ctx.send(f"Modlog message does not contain an embed for id {id}.")
    @reason.error
    async def on_reason_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid mod log ID(s) and reason.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to change reasons for user modlogs.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all mod log IDs are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def removepunishment(self, ctx: commands.Context, ids: commands.Greedy[int]) -> None:
        """Removes a punishment with the given ID"""
        moderation_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(ctx.guild.id, self.database.moderation)
        for id in ids:
            entry: Any = await moderation_collection.find_one({ID: id})
            if entry:
                channel_id: int = entry.get(LOG_CHANNEL_ID)
                message_id: int = entry.get( MESSAGE_LOG_ID)
                channel: discord.abc.GuildChannel | discord.Thread = self.bot.get_channel(channel_id)
                if not channel:
                    await ctx.send(f"Modlog channel not found for id {id}.")
                    continue
                try:
                    message: discord.Message = await channel.fetch_message(message_id)
                except discord.NotFound:
                    await ctx.send(f"Modlog message not found for id {id}.")
                    continue
                await message.delete()
            result: DeleteResult = await moderation_collection.delete_one({ID: id})
            await ctx.send(f"Removed punishment #{id}") if result.deleted_count > 0 else await ctx.send("No punishment found with that ID.")
    @removepunishment.error
    async def on_removepunishment_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid mod log ID(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to remove punishments.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all mod log IDs are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command(aliases=['rn'])
    @commands.has_permissions(manage_nicknames=True)
    async def resetnick(self, ctx: commands.Context, members: commands.Greedy[discord.Member]) -> None:
        """Resets the nickname of user(s)"""
        successful_nick: List[discord.Member] = []
        failed_nick: List[discord.Member] = []
        for member in members:
            try:
                await member.edit(nick=None)
                successful_nick.append(member)
            except Exception:
                failed_nick.append(member)
                pass
        if len(successful_nick) > 0:
            await ctx.send(f"Reset nickname for {', '.join(x.name for x in successful_nick)}") 
        if len(failed_nick) > 0:
            await ctx.send(f"Failed to reset nickname for {', '.join(x.name for x in failed_nick)}")
    @resetnick.error
    async def on_resetnick_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to reset user nicknames.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def rkick(self, ctx: commands.Context, members: commands.Greedy[discord.Member]) -> None:
        """Kicks the given user(s) if possible, without producing a moderation log"""
        s_kicks, f_kicks = await self.punishment_steps(ctx.guild, "kick", members, RKICK_REASON, ctx.author, None, None, None, ctx.message.attachments)
        if len(s_kicks) > 0:
            await ctx.send(f"Kicked **{','.join(user.name for user in s_kicks)}**.")
        if len(f_kicks) > 0:
            await ctx.send(f"Failed to kick **{','.join(user.name for user in f_kicks)}**.")
    @rkick.error
    async def on_rkick_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to kick users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rmute(self, ctx: commands.Context, members: commands.Greedy[discord.Member], duration: Optional[str]) -> discord.Message | None:
        """Mutes the given user(s) if possible for the given time (Indefinite if no time provided), without producing a moderation log"""
        mute_role: discord.Role = await find_role(ctx.guild, self.database, self.database.mute_role)
        if not mute_role:
            return await ctx.send("Cannot mute user(s). Make sure that the mute role is in-server and properly configured.")
        if duration:
            time_in_seconds: timedelta = await parse_time_string(duration)
            if not time_in_seconds:
                return await ctx.send("Invalid duration input. Please make sure it is a valid time (Ex. 4w or 2mo).")
            expanded: str = await expand_time_string(duration)
            time_str: str = "for " + expanded
        else:
            time_in_seconds = None
            expanded = None
            time_str = "indefinitely"
        s_mutes, f_mutes = await self.punishment_steps(ctx.guild, "mute", members, RMUTE_REASON, ctx.author, expanded, mute_role, None, ctx.message.attachments)
        if len(s_mutes) > 0:
            await ctx.send(f"{', '.join(s_mute.mention for s_mute in s_mutes)} muted {time_str}. If an unmute is required, contact a staff member.")
        if len(f_mutes) > 0:
            await ctx.send(f"Failed to mute {', '.join(f_mute.mention for f_mute in f_mutes)}")
        if time_in_seconds:
            await self.schedule_unmute(s_mutes, mute_role, time_in_seconds, RMUTE_EXPIRY_REASON,discord.utils.utcnow(),ctx.author)
    @rmute.error
    async def on_rmute_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid user(s) and duration. Omit the duration to have an indefinite mute")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to mute users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command(aliases=['rq'])
    @commands.has_permissions(manage_roles=True)
    async def rquarantine(self, ctx: commands.Context, members: commands.Greedy[discord.Member]):
        """Puts user(s) into quarantine, without producing a moderation log"""
        quarantine_role: discord.Role = await find_role(ctx.guild, self.database, self.database.quarantine_role)
        if not quarantine_role:
            return await ctx.send("Cannot quarantine user(s). Make sure that the quarantine role is in-server and properly configured.")
        s_quarantines, f_quarantines = await self.punishment_steps(ctx.guild, "quarantine", members, RQUARANTINE_REASON, ctx.author, None, quarantine_role, None, ctx.message.attachments)
        if len(s_quarantines) > 0:
            await ctx.send(f"{', '.join(user.mention for user in s_quarantines)} put in quarantine. If an unquarantine is required, contact a staff member.")
        if len(f_quarantines) > 0:
            await ctx.send(f"Failed to put {', '.join(user.mention for user in f_quarantines) } in quarantine")
    @rquarantine.error
    async def on_rquarantine_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to quarantine users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def rtempban(self, ctx: commands.Context, users: commands.Greedy[Union[discord.User, discord.Member]], duration: str) -> discord.Message | None:
        time_val: timedelta = await parse_time_string(duration)
        if not time_val:
            return await ctx.send("Invalid duration input. Please make sure it is a valid time (Ex. 4w or 2mo). (Note that for permanent bans, use m?ban)")
        time_str: str = await expand_time_string(duration)
        s_bans, f_bans = await self.punishment_steps(ctx.guild, "ban", users, RTEMPBAN_REASON, ctx.author, duration, None, time_val, ctx.message.attachments)
        if len(s_bans) > 0:
            await ctx.send(f"Banned {', '.join(user.name for user in s_bans)} for {time_str}.")
        if len(f_bans) > 0:
            await ctx.send(f"Failed to ban {', '.join(user.name for user in f_bans)}.")
        if s_bans:
            await asyncio.sleep(time_val.total_seconds())
            await self.punishment_steps(ctx.guild, "unban", s_bans, RTEMPBAN_EXPIRY_REASON, ctx.author, None, None, None, None)
    
    #Done
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def rtimeout(self, ctx: commands.Context, members: commands.Greedy[discord.Member], duration: str = "27d") -> discord.Message | None:
        """Times out user(s) if possible, for the given time (27 days max if time exceeds that or no time is provided), without producing a moderation log"""
        time_in_seconds: timedelta = await parse_time_string(duration)
        if not time_in_seconds:
            return await ctx.send("Invalid duration input. Please make sure it is a valid time (Ex. 4w or 2mo). (Note that the maximum for a timeout is 27 days)")
        elif int(time_in_seconds.total_seconds()) >= 2332800:
            time_in_seconds = timedelta(days=27)
            duration = "27d"
        time_str: str = await expand_time_string(duration)
        s_timeouts, f_timeouts = await self.punishment_steps(ctx.guild, "timeout", members, RTIMEOUT_REASON, ctx.author, None, None, time_in_seconds, ctx.message.attachments)
        if len(s_timeouts) > 0:
            await ctx.send(f"Timed out **{','.join(user.name for user in s_timeouts)}** for {time_str}.")
        if len(f_timeouts) > 0:
            await ctx.send(f"Failed to timeout **{','.join(user.name for user in f_timeouts)}**.")
        await self.schedule_untimeout(ctx.guild, members, time_in_seconds, RTIMEOUT_EXPIRY_REASON, ctx.author)
    @rtimeout.error
    async def on_rtimeout_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to timeout users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def runban(self, ctx: commands.Context, users: commands.Greedy[Union[discord.Member, discord.User]]) -> None:
        """Unbans the given user(s) if possible, without producing a moderation log"""
        s_unbans, f_unbans = await self.punishment_steps(ctx.guild, "unban", users, RUNBAN_REASON, ctx.author, None, None, None, ctx.message.attachments)
        if len(s_unbans) > 0:
            await ctx.send(f"**{','.join(user.name for user in s_unbans)}** successfully unbanned.")
        if len(f_unbans) > 0:
            await ctx.send(f"Failed to unban **{','.join(user.name for user in f_unbans)}**.")
    @runban.error
    async def on_runban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to unban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def runmute(self, ctx: commands.Context, members: commands.Greedy[discord.Member]) -> None:
        """Unmutes the given user(s) if possible, without producing a moderation log"""
        mute_role: discord.Role = await find_role(ctx.guild, self.database, self.database.mute_role)
        if not mute_role:
            return await ctx.send("Cannot unmute user(s). Make sure that the mute role is in-server and properly configured.")
        s_unmutes, f_unmutes = await self.punishment_steps(ctx.guild, "unmute", members, RUNMUTE_REASON, ctx.author, None, mute_role, None, ctx.message.attachments)
        if len(s_unmutes) > 0:
            await ctx.send(f"{', '.join(user.mention for user in s_unmutes)} {'has' if len(s_unmutes) == 1 else 'have'} been unmuted!")
        if len(f_unmutes) > 0:
            await ctx.send(f"Failed to unmute {', '.join(user.mention for user in f_unmutes) }")
    @runmute.error
    async def on_runmute_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to unmute users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command(aliases=['ruq'])
    @commands.has_permissions(manage_roles=True)
    async def runquarantine(self, ctx: commands.Context, members: commands.Greedy[discord.Member]) -> discord.Message | None:
        """Removes user(s) from quarantine, without producing a moderation log"""
        quarantine_role: discord.Role = await find_role(ctx.guild, self.database, self.database.quarantine_role)
        if not quarantine_role:
            return await ctx.send("Cannot unquarantine user(s). Make sure that the quarantine role is in-server and properly configured.")
        s_unquarantines, f_unquarantines = await self.punishment_steps(ctx.guild, "unquarantine", members, RUNQUARANTINE_REASON, ctx.author, None, quarantine_role, None, ctx.message.attachments)
        if len(s_unquarantines) > 0:
            await ctx.send(f"{', '.join(user.mention for user in s_unquarantines)} removed from quarantine!")
        if len(f_unquarantines) > 0:
            await ctx.send(f"Failed to remove {', '.join(user.mention for user in f_unquarantines) } from quarantine (Make sure the user is in server and has the role)")
    @runquarantine.error
    async def on_runquarantine_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to unquarantine users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def runtimeout(self, ctx: commands.Context, members: commands.Greedy[discord.Member]) -> None:
        """Removes user(s) from timeout if possible, without producing a moderation log"""
        s_untimeouts, f_untimeouts = await self.punishment_steps(ctx.guild, "untimeout", members, RUNTIMEOUT_REASON, ctx.author, None, None, None, ctx.message.attachments)
        if len(s_untimeouts) > 0:
            await ctx.send(f"**{','.join(user.name for user in s_untimeouts)}** {'has' if len(s_untimeouts) == 1 else 'have'} been removed from timeout.")
        if len(f_untimeouts) > 0:
            await ctx.send(f"Failed to untimeout **{','.join(user.name for user in f_untimeouts)}**.")
    @runtimeout.error
    async def on_runtimeout_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to untimeout users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def sb(self, ctx: commands.Context, users: commands.Greedy[Union[discord.Member, discord.User]]):
        """Bans the given user(s) if possible with the reason of scamming"""
        await self.generic_ban(ctx, users, "Scammer and/or compromised account", "For trying to scam people.", ctx.message.attachments)
    @sb.error
    async def on_sb_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command(aliases=['sn'])
    @commands.has_permissions(manage_nicknames=True)
    async def setnick(self, ctx: commands.Context, members: commands.Greedy[discord.Member], name="Request New Nickname") -> None:
        """Changes the nickname of user(s), setting it to \"Request New Nickname\" if the default is used"""
        s_nick: List[discord.Member] = []
        f_nick: List[discord.Member] = []
        for member in members:
            try:
                await member.edit(nick=name)
                s_nick.append(member)
            except Exception:
                f_nick.append(member)
                pass
        if len(s_nick) > 0:
            await ctx.send(f"Set new nickname to **{name}** for {', '.join(x.name for x in s_nick)}") 
        if len(f_nick) > 0:
            await ctx.send(f"Failed to set nickname for {', '.join(x.name for x in f_nick)}")
    @setnick.error
    async def on_setnick_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and name. Omit the name to use the default \"Request New Nickname\" nickname.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to change user nicknames.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def tb(self, ctx: commands.Context, users: commands.Greedy[Union[discord.Member, discord.User]]) -> None:
        """Bans the given user(s) if possible with the reason of trolling or raiding"""
        await self.generic_ban(ctx, users, "Troll/raider", "For trolling/raiding.", ctx.message.attachments)
    @tb.error
    async def on_tb_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx: commands.Context, users: commands.Greedy[Union[discord.Member, discord.User]], duration: str, *, reason: str = "No reason provided") -> discord.Message | None:
        time_val: timedelta = await parse_time_string(duration)
        if not time_val:
            return await ctx.send("Invalid duration input. Please make sure it is a valid time (Ex. 4w or 2mo). (Note that for permanent bans, use m?ban)")
        time_str: str = await expand_time_string(duration)
        s_bans, f_bans = await self.punishment_steps(ctx.guild, "ban", users, reason, ctx.author, duration, None, time_val, ctx.message.attachments)
        if len(s_bans) > 0:
            await ctx.send(f"Banned {', '.join(user.name for user in s_bans)} for {time_str}.")
        if len(f_bans) > 0:
            await ctx.send(f"Failed to ban {', '.join(user.name for user in f_bans)}.")
        if s_bans:
            await asyncio.sleep(time_val.total_seconds())
            await self.punishment_steps(ctx.guild, "unban", s_bans, f"Expiry of temporary ban made {time_str} ago by {ctx.author.name} (ID: {ctx.author.id}).", ctx.author, None, None, None, None)

    #Done
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, members: commands.Greedy[discord.Member], *, args: Optional[str]) -> None:
        """Times out user(s) if possible for the given time and reason (Maximum of 27 days if time exceeds that or no time is provided)"""
        time_val = "27d"
        duration = timedelta(days=27)
        reason = "No reason provided"
        if args:
            args_list: List[str] = shlex.split(args)
            potential_time: str = args_list[0]
            parsed_duration: timedelta = await parse_time_string(potential_time)
            if parsed_duration:
                time_val: str = potential_time
                duration: timedelta = parsed_duration
                reason: str = " ".join(args_list[1:]) if len(args_list) > 1 else "No reason provided"
            else:
                reason = args
        expanded: str = await expand_time_string(time_val)
        s_timeouts, f_timeouts = await self.punishment_steps(ctx.guild, "timeout", members, reason, ctx.author, None, None, duration, ctx.message.attachments)
        if len(s_timeouts) > 0:
            await ctx.send(f"Successfully timed out **{', '.join(user.name for user in s_timeouts)}** for {expanded}. Reason: {reason}")
        if len(f_timeouts) > 0:
            await ctx.send(f"Failed to ban **{', '.join(user.name for user in f_timeouts)}**.")
        await self.schedule_untimeout(ctx.guild, members, duration, f"Expiry of timeout made {expanded} ago by {ctx.author.name} (ID: {ctx.author.id})", ctx.author)
    @timeout.error
    async def on_timeout_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s), duration, and reason. Omit duration & reason to have a max duration mute (27 days) with no reason, omit reason to have just a duration with no reason.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to timeout users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def uau(self, ctx: commands.Context, users: commands.Greedy[Union[discord.Member, discord.User]]) -> None:
        """Bans the given user(s) if possible with the reason of being underaged"""
        await self.generic_ban(ctx, users, "Since you're under the age of 13, you're not allowed to be on Discord. This violates the Children's Online Privacy Protection Act (COPPA), which requires members of a service like Discord to be over the age of 13 if any personal info (including emails) is collected. Discord also punishes servers for knowingly harboring underage users. In light of that, I have to ban you. Come back later when you're over-age.", "For being an underage user, i.e. <13 years old", ctx.message.attachments)
    @uau.error
    async def on_uau_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, users: commands.Greedy[discord.User], *, reason = "No reason provided") -> None:
        """Unbans the given user(s) if possible, with the given reason"""
        s_unbans, f_unbans = await self.punishment_steps(ctx.guild, "unban", users, reason, ctx.author, None, None, None, ctx.message.attachments)
        if len(s_unbans) > 0:
            await ctx.send(f"**{','.join(user.name for user in s_unbans)}** successfully unbanned. Reason: {reason}")
        if len(f_unbans) > 0:
            await ctx.send(f"Failed to unban **{','.join(user.name for user in f_unbans)}**.")
    @unban.error
    async def on_unban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to unban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, members: commands.Greedy[discord.Member], *, reason = "No reason provided") -> discord.Message | None:
        """Unmutes the given user(s) if possible, with the given reason"""
        mute_role: discord.Role = await find_role(ctx.guild, self.database, self.database.mute_role)
        if not mute_role:
            return await ctx.send("Cannot mute user(s). Make sure that the mute role is in-server and properly configured.")
        s_unmutes, f_unmutes = await self.punishment_steps(ctx.guild, "unmute", members, reason, ctx.author, None, mute_role, None, ctx.message.attachments)
        if len(s_unmutes) > 0:
            await ctx.send(f"Successfully unmuted {'**, **'.join(user.name for user in s_unmutes)}")
        if len(f_unmutes) > 0:
            await ctx.send(f"Failed to unmute {'**, **'.join(user.name for user in f_unmutes) }")
    @unmute.error
    async def on_unmute_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to unmute users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    #Done       
    @commands.command(aliases=['uq'])
    @commands.has_permissions(manage_roles=True)
    async def unquarantine(self, ctx: commands.Context, members: commands.Greedy[discord.Member], *, reason = "No reason provided") -> None:
        """Removes user(s) from quarantine if possible, with the given reason"""
        quarantine_role: discord.Role = await find_role(ctx.guild, self.database, self.database.quarantine_role)
        if not quarantine_role:
            return await ctx.send("Cannot unquarantine user(s). Make sure that the quarantine role is in-server and properly configured.")
        s_unquarantines, f_unquarantines = await self.punishment_steps(ctx.guild, "unquarantine", members, reason, ctx.author, None, quarantine_role, None, ctx.message.attachments)
        if len(s_unquarantines) > 0:
            await ctx.send(f"{ctx.author.mention} removed {', '.join(user.mention for user in s_unquarantines)} from quarantine. :unlock:")
        if len(f_unquarantines) > 0:
            await ctx.send(f"Failed to remove {', '.join(user.mention for user in f_unquarantines) } from quarantine (Make sure the user is in server and has the role)")
    @unquarantine.error
    async def on_unquarantine_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to unquarantine users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.") 
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx: commands.Context, members: commands.Greedy[discord.Member], *, reason="No reason given") -> None:
        """Removes user(s) from timeout if possible, with the given reason"""
        s_untimeouts, f_untimeouts = await self.punishment_steps(ctx.guild, "untimeout", members, reason, ctx.author, None, None, None, ctx.message.attachments)
        if len(s_untimeouts) > 0:
            await ctx.send(f"**{','.join(user.name for user in s_untimeouts)}** {'has' if len(s_untimeouts) == 1 else 'have'} been removed from timeout. Reason: {reason}")
        if len(f_untimeouts) > 0:
            await ctx.send(f"Failed to ban **{','.join(user.name for user in f_untimeouts)}**.")
    @untimeout.error
    async def on_untimeout_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to untimeout users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    #Done
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def warn(self, ctx: commands.Context, users:commands.Greedy[Union[discord.Member,discord.User]], *, reason: str = "No reason provided"):
        """Warns user(s) with the given reason"""
        await self.punishment_steps(ctx.guild, "warn", users, reason, ctx.author, None, None, None, ctx.message.attachments)
        for user in users:
            warnings: int = await self.get_num_warnings(user, ctx.guild)
            warnings += 1
            ordinal_num: str = await ordinal(warnings)
            await ctx.send(f"{user.name} has been warned, this is their {ordinal_num} warning.")
    @warn.error
    async def on_warn_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to warn users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
              
    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry) -> None:
        """When a user gets kicked, timed out, or removed from timeout, the moderation log will log the following:
        Kicked users - User's name, mention, ID, reason for kick, user who performed kick's name
        Timeout - User's name, mention, ID, reason for timeout, duration of the timeout, user who performed timeout's name
        Untimeout - User's name, mention, ID, reason for untimeout, user who performed untimeout's name"""
        if entry.user and entry.user == entry.user.bot:
            return
        time: datetime = discord.utils.utcnow()
        guild: discord.Guild = entry.guild
        mod_log: discord.abc.GuildChannel | discord.Thread | None = await find_channel(guild, self.database, self.database.mod_log)
        id: int = await self.database.get_next_id(guild.id)
        if not mod_log:
            return
        target = entry.target
        user: discord.User = self.bot.get_user(target.id)
        reason: str = entry.reason if entry.reason else f"no reason given, use m?reason {id} <text> to add one"
        if entry.action == discord.AuditLogAction.kick and entry.reason not in SILENT_REASONS:
            await self.create_log_entry(guild, mod_log, discord.Color.blue(), "kick", user, reason, entry.user, None, None)
        elif entry.action == discord.AuditLogAction.member_update:
            timed_out_before: datetime = None
            timed_out_after: datetime = None
            for attr, value in entry.before:
                if attr == "timed_out_until":
                    timed_out_before = value
                    break
            for attr, value in entry.after:
                if attr == "timed_out_until":
                    timed_out_after = value
                    break
            responsible: discord.User = self.bot.get_user(responsible.id)
            if not timed_out_before and timed_out_after and entry.reason not in SILENT_REASONS:
                duration: datetime = timed_out_after - time
                duration_seconds: int = math.ceil(int(duration.total_seconds()))
                await self.create_log_entry(guild, mod_log, discord.Color.orange(), "timeout", user, reason, responsible, f"{duration_seconds} seconds", None)
            if timed_out_before and not timed_out_after and entry.reason not in SILENT_REASONS:
                await self.create_log_entry(guild, mod_log, discord.Color.green(), "untimeout", user, reason, responsible, None, None)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.Member, discord.User]) -> None:
        """When a user gets banned, the moderation log will log the user's name, mention, ID, the reason for the ban, the name of the user who performed the ban. 
        The bot will also perform the ban on that same user if the ban occurred on an EMD server"""
        ban_limit: int = await self.database.get_config(guild.id, self.database.ban_limit)
        ban_limit = ban_limit if ban_limit else 0
        await self.database.update_config(guild.id, {"$set": {self.database.ban_limit: ban_limit + 1}})
        mod_log: discord.abc.GuildChannel | discord.Thread = await find_channel(guild, self.database, self.database.mod_log)
        if not mod_log:
            return
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            if entry.user and entry.user == self.bot.user:
                return
            id: int = await self.database.get_next_id(guild.id)
            if entry.target.id == user.id and entry.reason not in SILENT_REASONS:
                reason: str = entry.reason if entry.reason else f"no reason given, use m?reason {id} <text> to add one"
                await self.create_log_entry(guild, mod_log, discord.Color.red(), "ban", user, reason, entry.user, None, None)
        if guild.id in EMD_SERVERS and reason != BANSYNC_REASON:
            for server_id in EMD_SERVERS:
                if server_id != guild.id:
                    try:
                        server: discord.Guild = self.bot.get_guild(server_id)
                        if server:
                            await self.perform_punishment(server, "ban", user, BANSYNC_REASON)
                    except Exception:
                        pass
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: Union[discord.Member, discord.User]) -> None:
        """When a user gets unbanned, the moderation log will log the user's name, mention, ID, the reason for the unban, the name of the user who performed the unban. 
        The bot will also perform the unban on that same user if the ban occurred on an EMD server"""
        mod_log: discord.abc.GuildChannel | discord.Thread = await find_channel(guild, self.database, self.database.mod_log)
        if not mod_log:
            return
        async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=1):
            if entry.user and entry.user == self.bot.user:
                return
            id: int = await self.database.get_next_id(guild.id)
            if entry.target.id == user.id and entry.reason not in SILENT_REASONS:
                reason: str = entry.reason if entry.reason else f"no reason given, use m?reason {id} <text> to add one"
                await self.create_log_entry(guild, mod_log, discord.Color.green(), "unban", user, reason, entry.user, None)
        if guild.id in EMD_SERVERS and reason != BANSYNC_REASON:
            for server_id in EMD_SERVERS:
                if server_id != guild.id:
                    try:
                        server: discord.Guild = self.bot.get_guild(server_id)
                        if server:
                            await self.perform_punishment(server, "unban", user, BANSYNC_REASON)
                    except Exception:
                        pass

async def setup(bot: commands.Bot) -> None:
    """Sets up the Moderation Cog"""
    await bot.add_cog(Moderation(bot))
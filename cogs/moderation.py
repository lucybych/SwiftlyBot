import asyncio
import datetime
from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks
import io
import pytz
from typing import List, Optional, Tuple, Union
from utility.finder import find_channel, find_role
from utility.guild import Database, expand_time_string, get_channel, get_user, ordinal, parse_time_string

EMD_SERVERS = [385956732888678402,575829746961874963,667526492963602449,673735253143060481,715103013395759147,722922843616313447,788582109425565736,667527355048132623,667527442633850900,667527490667020292,667527539735920640,667527591183253514,667546269530718223,667897780659945512,667897887086346271,667897923584917505,667897969588305922,668594992104865810,668595061994553344,668595128398774293,668595207499022365,668595312012820491,668595505965826049,668595586458451997,668595639139041281,668595716418961415,668995723957633037,668995839838126080,668995890823954443,668995943928168478,668995991789371402,668996048857071616,668996095707447306,668996136853307412,668996185813417985,668996230415908885,669303632088268830,669303709544742913,669303797339914242,669303861491662850,669303936322109457,669304003653271556,670357952468746251,670358004834500649,670358055606681610,670358110145347603,670358161206542338,670358221084688466,670358263442964510,670358306929508383,670358347882561542,670358392623202335,669304054442098698,669304108246761494,669304217349128192,669654192352264192,669654244688658452,669654290549309442,669654328516280325,669654375739949120,669654417544445982,669654455339319347,669654495596249116,669654552399577098,669654593084456986,670023267452715058,670023313887592490,670023349014888488,670023384620466267,670023417885622278,670023453037953064,670023490702671881,670023524769071104,670023564522553375,670023595954667561,671488653528399882,671488700185575432,671488733975150613,671488763381284866,671489031653031956,671489098250190875,671489129220931604,671489154219114558,671489177938034718,672265556711309350,672266112192217110,672266184355348483,672266227393232899,672266264877465600,672266298553663498,672266334456905739,672266369466761216,672266402446704640,672266508931694593,672584940789039106,672584977409638440,672585035034918932,672585079456792596,672585122247344138,672585165524041767,672585208775704596,672585245421338634,672585338300137482,672585380217880609,672934859127390228,672934894124662794,672934922742267968,672934951011876894,672934983827980300,672935017848242206,672935052187009057,672935087372763147,672935124962246677,672935164237840435,673059226045775882,673059255158308864,673059287307911184,673059315367673877,673059350562078721,673059378722766854,673059425568686081,673059455650496542,673059487044599809,673059520469270568,673069260842729483,673069297316265985,672947122026315776,672947162547486750,672947189491826690,672947221163147316,672947246681292801,672947267883237416,672947303501398018,672947345075470343,672947380441841693,672947415296376882,673285360771530798,673285388277645315,673285422532526095,673285451259576331,673285477792743444,673285506615738368,673285529533677580,673285553877418004,673285576799289378,673285605936988172,673285631920570400,673285659263238164,673288617963159593,673288650242392113,673288678126387230,673288715581521934,673288739589586957,673288761517408306,673288796036399125,673288817859493929,673391852053069842,673391894868525057,673391918339850259,673391945560752154,673391975801552909,673392005048434688,673392034291384350,673392061965402184,673392084547403787,673392115077742595,673392146212061185,673392178134777867,673392211345408018,673392237958397962,673392271047262228,700845513204826133,736693732358881351,736693781281374279,700845165648019588,700845322494017581,700845338449412176,700845352810446930,700845371194081291,701877065376333866,701877079444160564,701877094266699806,701877112948391956,701877132095127801,701877149132652676,701877169336615018,701877188328423524,701877208431460455,701877236629766144,701877254430654545,671185402073317380,672677496596070401,673056866309373953,673442194421448737,677727489371668510,696494688823148685,677723036715188283,673414993630461983,673415041340407818,673415067781562368,673415092678950964,800180724639465563]
RATE_LIMIT = 2000
RBAN_REASON = "Silent or requested ban"
RKICK_REASON = "Silent or requested kick"
RMUTE_EXPIRY_REASON = "Expiry of silent or requested unmute"
RMUTE_REASON = "Silent or requested mute"
RQUARANTINE_REASON = "Silent or requested quarantine"
RTIMEOUT_EXPIRY_REASON = "Expiry of silent or requested untimeout"
RTIMEOUT_REASON = "Silent or requested timeout"
RUNBAN_REASON = "Silent or requested unban"
RUNMUTE_REASON = "Silent or requested unmute"
RUNQUARANTINE_REASON = "Silent or requested unquarantine"
RUNTIMEOUT_REASON = "Silent or requested untimeout"

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Moderation module"""
        self.bot = bot 
        self.database = Database(self.bot)
        self.update_ban_limit.start()
    
    async def can_unmute(self, guild: discord.Guild, user: Union[discord.Member, discord.User], timestamp: datetime):
        """Determines if a user can be unmuted by viewing if they have a more recent mute"""
        moderation = await self.database.get_guild_collection(guild.id, "moderation")
        entries = moderation.find({"type": "mute", "offender": user.id})
        async for entry in entries:
            return bool(pytz.timezone("UTC").localize(entry["timestamp"]) > timestamp)
        return True
    
    async def check_ban_limit(self, guild: discord.Guild):
        """Checks how many bans the server has made for the day and if the rate limit has been reached"""
        return bool(await self.database.get_config(guild.id, "ban_limit") >= RATE_LIMIT)

    async def generic_ban(self, ctx: commands.Context, users: List[Union[discord.Member, discord.User]], reason: str, toggle: str = None):
        """Generic banning function that handles all ban commands (ab, sb, tb, uau, ban, rban)"""
        if await self.check_ban_limit(ctx.guild):
            await ctx.send("The ban rate limit of 2,000 has been reached for the server. Please try again after 12 AM UTC.")
            return
        banned_users, failed_bans = await self.perform_ban(ctx.guild, users, ctx.author, reason)
        if toggle:
            if toggle.startswith("Bansync"):
                if len(banned_users) > 0:
                    await ctx.send(f"Successfully banned **{len(banned_users)}** users.")
                if len(failed_bans) > 0:
                    await ctx.send(f"Failed to ban the following IDs: {', '.join(x.mention for x in failed_bans)}")
            else:
                s_m = "was" if len(banned_users) == 1 else "were"
                if len(banned_users) > 0:
                        await ctx.send(f"{', '.join(x.mention for x in banned_users)} {s_m} banned.\n**Reason:** {toggle}.")
                if len(failed_bans) > 0:
                    await ctx.send(f"Failed to ban {', '.join(x.mention for x in failed_bans)}")
        else:
            if len(banned_users) > 0:
                await ctx.send(f"Banned {', '.join(x.mention for x in banned_users)}")
            if len(failed_bans) > 0:
                await ctx.send(f"Failed to ban {', '.join(x.mention for x in failed_bans)}")
    
    async def get_messages(self, guild: discord.Guild, num: int, command_message: discord.Message, user: Union[discord.User, discord.Member] = None, channel: discord.abc.GuildChannel = None) -> List[discord.Message]:
        """Gets a list of the num most recent messages, with specifications of it coming from a specific user or channel"""
        purge_messages: List[discord.Message] = []
        for channel2 in guild.channels:
            if not isinstance(channel2, discord.CategoryChannel) and not isinstance(channel2, discord.ForumChannel):
                if not channel:
                    purge_messages = [msg async for msg in channel2.history(limit=num+1) if msg.id != command_message.id and (not user or (msg.author.id == user.id and msg.id != command_message.id))]
                else:
                    purge_messages = [msg async for msg in channel2.history(limit=num+1) if msg.id != command_message and (not user or (user and msg.author.id == user.id))]
        sorted_messages = sorted(purge_messages, key=lambda msg: msg.created_at, reverse=True)
        return sorted_messages[:num]
    
    async def get_num_warnings(self, user: discord.User, guild: discord.Guild):
        """Grabs the number of warnings for a given user in a given server"""
        moderation = await self.database.get_guild_collection(guild.id, "moderation")
        warnings = moderation.find({"type": "warn", "offender": user.id})
        return len(warnings.to_list())
    
    async def create_log_entry(self, guild: discord.Guild, mod_log: discord.TextChannel, color: discord.Color, type: str, offender: Union[discord.User,discord.Member], reason: str, responsible: discord.Member, duration: str = None):
        time = discord.utils.utcnow()
        id = await self.database.get_next_id(guild.id)
        moderation = await self.database.get_guild_collection(guild.id, "moderation")
        embed = discord.Embed(color=color, title=f"{type} | case {id}", timestamp=time)
        offender_info = offender.id if isinstance(offender, Union[discord.Member, discord.User]) else 0
        embed.add_field(name="Offender: ", value=offender.mention,inline=False)
        if type == "mute" and duration:
            duration_words = await expand_time_string(duration)
            embed.add_field(name="Duration: ",value=duration_words,inline=False)
        embed.add_field(name="Reason: ",value=reason,inline=False)
        embed.add_field(name="Responsible Moderator: ",value=responsible.name,inline=False)
        embed.set_footer(text=f"ID: {offender.id}")
        log_entry = await mod_log.send(embed=embed)
        db_entry = {
            "id": id,
            "type": type,
            "offender": offender_info,
            "reason":  reason,
            "responsible_moderator": responsible.id,
            "message_log_id": log_entry.id,
            "log_channel_id": mod_log.id,
            "timestamp": time,
        }
        if type == "mute" or type == "timeout":
            db_entry["duration"] = duration if duration else "Infinite",
        moderation.insert_one(db_entry)
    
    async def log_punishment(self, type: str, guild: discord.Guild, offender: Union[discord.User,discord.Member], reason: str, responsible: discord.Member, duration: str = None):
        """Sends a message in the moderation log that logs the following information:
        Mutes - Offender's name and ID, duration of mute, reason for mute, person who performed the mute's name
        Unmutes - Offender's name and ID, reason for unmute, person who performed the unmute's name
        Quarantine - Offender's name and ID, reason for quarantine, person who performed the quarantine's name
        Unquarantine - Offender's name and ID, reason for unquarantine, person who performed the quarantine's name
        Warning - Offender's name and ID, reason for warn, person who performed the warn's name"""
        mod_log = await find_channel(guild, self.database, "mod_log")
        if not mod_log:
            return
        if type == "mute" and reason != RMUTE_REASON:
            await self.create_log_entry(guild, mod_log, discord.Color.orange(), "mute", offender, reason, responsible, duration)
        elif type == "unmute" and reason != RUNMUTE_REASON and reason != RMUTE_EXPIRY_REASON:
            await self.create_log_entry(guild, mod_log, discord.Color.green(), "unmute", offender, reason, responsible, duration)
        elif type == "quarantine" and reason != RQUARANTINE_REASON:
            await self.create_log_entry(guild, mod_log, discord.Color.light_gray(), "quarantine", offender, reason, responsible, duration)
        elif type == "unquarantine" and reason != RUNQUARANTINE_REASON:
            await self.create_log_entry(guild, mod_log, discord.Color.brand_green(), "unquarantine", offender, reason, responsible, duration)
        elif type == "warn":
            await self.create_log_entry(guild, mod_log, discord.Color.yellow(), "warn", offender, reason, responsible, duration)

    async def perform_ban(self, guild: discord.Guild, users: List[Union[discord.Member, discord.User]], responsible: discord.Member, reason: str) -> tuple[List[discord.User], List[discord.User]]:
        """Bans users, then returns the list of users who were successfully and unsuccessfully banned"""
        banned_users = []
        failed_bans = []
        ban_limit = await self.database.get_config(guild.id, "ban_limit")
        for user in users:
            try:
                if ban_limit + 1 < RATE_LIMIT:
                    await guild.ban(user, reason=reason)
                    banned_users.append(user)
                    ban_limit += 1
                    try:
                        if reason != RBAN_REASON:
                            await user.send(f"You have been banned from {guild.name} for: {reason}. Responsible moderator: {responsible.name} (ID: {responsible.id})")
                    except Exception:
                        pass
                else:
                    failed_bans.append(user)
            except Exception:
                failed_bans.append(user)
                pass
        await self.database.update_config(guild.id, {"$set": {"ban_limit": ban_limit}})
        return banned_users, failed_bans
    
    async def perform_kick(self, guild: discord.Guild, members: List[Union[discord.Member, discord.User]], responsible: discord.Member, reason: str) -> tuple[List[discord.User], List[discord.User]]:
        """Kicks users, then returns the list of users who were successfully and unsuccessfully kicked"""
        kicked_users = []
        failed_kicks = []
        for member in members:
            try:
                await guild.kick(member, reason=reason)
                kicked_users.append(member)
                try:
                    if reason != RKICK_REASON:
                        await member.send(f"You have been kicked from {guild.name} for: {reason}. Responsible moderator: {responsible.name} (ID: {responsible.id})")
                except Exception:
                    pass
            except Exception:
                failed_kicks.append(member)
                pass
        return kicked_users, failed_kicks
    
    async def perform_mute(self, guild: discord.Guild, members: List[discord.Member], role: discord.Role, responsible: discord.Member, reason: str, duration: str = None) -> tuple[List[discord.Member], List[discord.Member]]:
        """Mutes users, then returns the list of users who were successfully and unsuccessfully muted"""
        muted_users = []
        failed_mutes = []
        for member in members:
            try:
                await member.add_roles(role, reason=reason)
                muted_users.append(member)
                try:
                    if duration:
                        time_str = await expand_time_string(duration)
                        time_s = "for " + time_str
                    else:
                        time_s = "indefinitely"
                    if reason != RMUTE_REASON:
                        await member.send(f"You have been muted in {guild.name} {time_s} for: {reason}. Responsible moderator: {responsible.name} (ID: {responsible.id})")
                except Exception:
                    pass
            except Exception:
                failed_mutes.append(member)
                pass
        return muted_users, failed_mutes
    
    async def perform_quarantine(self, members: List[discord.Member], role: discord.Role, reason) -> List[Tuple[(discord.Member, discord.Member)]]:
        """Puts users into quarantine, inserts the quarantine entry into the database, then returns the list of users who were successfully and unsuccessfully quarantined"""
        quarantined_users = []
        failed_quarantines = []
        quarantine = await self.database.get_guild_collection(role.guild.id, "quarantine")
        role_ids = []
        for member in members:
            try:
                for mrole in member.roles:
                    if mrole.name != "@everyone":
                        await member.remove_roles(mrole, reason="Removing roles for quarantine")
                        role_ids.append(mrole.id)
                await member.add_roles(role, reason=reason)
                quarantined_users.append(member)
                if len(role_ids) > 0:
                    document = {"user_id": member.id,"role_ids": role_ids}
                    await quarantine.update_one({"user_id": member.id},  {"$set": document},upsert=True)
            except Exception:
                failed_quarantines.append(member)
                pass
        return quarantined_users, failed_quarantines
    
    async def perform_timeout(self, guild: discord.Guild, members: List[discord.Member], time_in_seconds: timedelta, responsible: discord.Member, reason: str, duration: str) -> List[Tuple[(discord.Member, discord.Member)]]:
        """Times out users, then returns the list of users who were succesfully and unsuccessfully timed out"""
        time = discord.utils.utcnow()
        timedout_users = []
        failed_timeouts = []
        for member in members:
            try:
                time_a = time + time_in_seconds
                await member.timeout(time_a, reason=reason)
                timedout_users.append(member)
                try:
                    time_str = await expand_time_string(duration)
                    if reason != RTIMEOUT_REASON:
                        await member.send(f"You have been timed out in {guild.name} for {time_str} for: {reason}. Responsible moderator: {responsible.name} (ID: {responsible.id})")
                except Exception:
                    pass
            except Exception as e:
                failed_timeouts.append(member)
        return timedout_users, failed_timeouts
    
    async def perform_unban(self, guild: discord.Guild, users: List[Union[discord.Member, discord.User]], responsible: discord.Member, reason: str) -> tuple[List[discord.User], List[discord.User]]:
        """Unbans users, then returns the list of users who were successfully and unsuccessfully unbanned"""
        unbanned_users = []
        failed_unbans = []
        for user in users:
            try:
                await guild.unban(user, reason=reason)
                unbanned_users.append(user)
                try:
                    if reason != RUNBAN_REASON:
                        await user.send(f"You have been unbanned from {guild.name} for: {reason}. Responsible moderator: {responsible.name} (ID: {responsible.id})")
                except Exception:
                    pass
            except Exception:
                failed_unbans.append(user)
                pass
        return unbanned_users, failed_unbans

    async def perform_unmute(self, guild: discord.Guild, members: List[discord.Member], role: discord.Role, responsible: discord.Member, reason) -> tuple[List[discord.Member], List[discord.Member]]:
        """Unmutes users, then returns the list of users who were successfully and unsuccessfully unmuted"""
        unmuted_users = []
        failed_unmutes = []
        for member in members:
            try:
                await member.remove_roles(role, reason=reason)
                unmuted_users.append(member)
                try:
                    if reason != RUNMUTE_REASON and reason != RMUTE_EXPIRY_REASON:
                        await member.send(f"You have been unmuted from {guild.name} for: {reason}. Responsible moderator: {responsible.name} (ID: {responsible.id})")
                except Exception:
                    pass
            except Exception:
                failed_unmutes.append(member)
                pass
        return unmuted_users, failed_unmutes
    
    async def perform_untimeout(self, guild: discord.Guild, members: List[discord.Member], responsible: discord.Member, reason: str) -> List[Tuple[(discord.Member, discord.Member)]]:
        """Removes users from timeout, then returns the list of users who were successfully and unsuccessfully removed from timeout"""
        untimedout_users = []
        failed_untimeouts = []
        for member in members:
            try:
                await member.edit(timed_out_until=None, reason=reason)
                untimedout_users.append(member)
                try:
                    if reason != RUNTIMEOUT_REASON and reason != RTIMEOUT_EXPIRY_REASON:
                        await member.send(f"You have been removed from timeout in {guild.name} for: {reason}. Responsible moderator: {responsible.name} (ID: {responsible.id})")
                except Exception:
                    pass
            except Exception:
                failed_untimeouts.append(member)
                pass
        return untimedout_users, failed_untimeouts
    
    async def perform_unquarantine(self, members: List[discord.Member], role: discord.Role, reason) -> List[Tuple[(discord.Member, discord.Member)]]:
        """Removes users from quarantine, removes the quarantine entry, returns the user their roles, then returns the list of users who were successfully and unsuccessfully unquarantined"""
        unquarantined_users = []
        failed_unquarantines = []
        quarantine = await self.database.get_guild_collection(role.guild.id, "quarantine")
        for member in members:
            document = await quarantine.find_one({"user_id": member.id})
            if not document:
                pass
            mroles = document.get("role_ids", [])
            try:
                for mrole in mroles:
                    try:
                        rrole = role.guild.get_role(mrole)
                        await member.add_roles(rrole, reason="Removing user from quarantine and readding roles they previously had")
                    except Exception:
                        pass
                await member.remove_roles(role, reason=reason)
                unquarantined_users.append(member)
                await quarantine.delete_one({"user_id": member.id})
            except Exception:
                failed_unquarantines.append(member)
                pass
        return unquarantined_users, failed_unquarantines
    
    async def perform_warn(self, guild: discord.Guild, members: List[discord.Member], responsible: discord.Member, reason):
        """Warns users by messaging them the warning, logs the warning. If the user has passed the warn threshold, they will be automatically banned"""
        for member in members:
            try:
                await member.send(f"You have been warned in {guild.name} for: {reason}. Responsible moderator: {responsible.name}")
            except Exception:
                continue
            warnings = await self.get_num_warnings(member, guild)
            number = warnings + 1
            await self.log_punishment("warn", guild, member, reason, responsible)
            warn_threshold = await self.database.get_config(guild.id, "warn_threshold")
            if warn_threshold > 0 and number >= warn_threshold:
                ordinaln = await ordinal(number)
                await member.ban(reason=f"Automatic action carried out after their {ordinaln} warning.")

    async def reset_ban_limits(self):
        """Resets the ban limit for a server (Since rate limits disappear over time)"""
        server_ids = self.database.mongo_client.list_database_names()
        for server_id in server_ids:
            await self.database.update_config(server_id, {"$set": {"ban_limit": 0}})
    
    async def schedule_unmute(self, users: List[discord.Member], role: discord.Role, time_in_seconds: timedelta, reason: str, timestamp: datetime, responsible: Union[discord.User, discord.Member]):
        """Waits until a mute should be expired, determines if the user can be unmuted, and if they can, unmutes the user and logs it if it was not a requested mute"""
        await asyncio.sleep(time_in_seconds.total_seconds())
        unmute_users = []
        for user in users:
            if await self.can_unmute(user.guild, user, timestamp):
                unmute_users.append(user)
        unmuted_users, failed_unmutes = await self.perform_unmute(role.guild, unmute_users, role, responsible, reason)
        if reason != RMUTE_EXPIRY_REASON:
            for unmute in unmuted_users:
                await self.log_punishment("unmute", role.guild, unmute, f"Automatic unmute from mute made {int(time_in_seconds.total_seconds())} seconds ago by {responsible.name}. (ID: {responsible.id})", responsible)
    
    async def schedule_untimeout(self, users: List[discord.Member], time_in_seconds: timedelta, responsible: Union[discord.Member, discord.User], reason: str):
        """Waits until a timeout supposedly expires, and untimeouts those users after that time"""
        await asyncio.sleep(time_in_seconds.total_seconds())
        await self.perform_untimeout(users[0].guild, users, responsible, reason)
    
    async def set_permissions_in_channels(self, guild: discord.Guild, muted_role: discord.Role):
        """Sets the permissions for mutes in every channel of the server"""
        for channel in guild.channels:
            try:
                if isinstance(channel, discord.TextChannel) or isinstance(channel, discord.CategoryChannel):
                    await channel.set_permissions(muted_role, send_messages=False, add_reactions=False, send_messages_in_threads=False, create_public_threads=False, create_private_threads=False)
                elif isinstance(channel, discord.VoiceChannel):
                    await channel.set_permissions(muted_role, connect=False, speak=False, send_messages=False, add_reactions=False,)
            except Exception:
                pass
    
    async def set_quarantine_permissions(self, guild: discord.Guild, quarantine_role: discord.Role):
        """Sets the permissions for quarantines in every channel of the server"""
        for channel in guild.channels:
            try:
                await channel.set_permissions(quarantine_role, read_messages=False)
            except Exception:
                pass

    @tasks.loop(hours=24)
    async def update_ban_limit(self):
        """Resets the number of bans at 12 AM UTC"""
        now_utc = discord.utils.utcnow()
        if now_utc.hour == 0 and now_utc.minute == 0:
            await self.reset_ban_limits()

    @update_ban_limit.before_loop
    async def before_update_ban_limit(self):
        """Sets the time for when the bans should be reset (12 AM UTC the next day)"""
        now = discord.utils.utcnow()
        target_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await discord.utils.sleep_until(target_time) 

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ab(self, ctx: commands.Context, users: commands.Greedy[discord.User]):
        """Bans the given user(s) if possible with the reason of advertising"""
        await self.generic_ban(ctx, users, "Advertising their junk", "For advertising stuff (either in DMs or in the server)")
    @ab.error
    async def on_ab_error(self, ctx: commands.Context, error):
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
    async def ban(self, ctx: commands.Context, users: commands.Greedy[discord.User], *, reason = "No reason provided"):
        """Bans the given user(s) if possible, with the given reason (if applicable)"""
        await self.generic_ban(ctx, users, reason, None)
    @ban.error
    async def on_ban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def banlist(self, ctx: commands.Context):
        """Produces a .txt file of a list of banned user IDs in the server"""
        banned_users = [entry async for entry in ctx.guild.bans()]
        if len(banned_users) == 0:
            raise commands.UserNotFound
        user_ids = "\n".join([str(ban_entry.user.id) for ban_entry in banned_users])
        file = io.BytesIO(user_ids.encode('utf-8'))
        file_name = "banned_users.txt"
        await ctx.send("Here is the ban list of user IDs:", file=discord.File(file, file_name))
    @banlist.error
    async def on_banlist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?banlist")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view the list of banned users.")
        elif isinstance(error, commands.UserNotFound) or isinstance(error, commands.CommandInvokeError):
            await ctx.send("No banned users found for the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def bansync(self, ctx: commands.Context, file: discord.Attachment):
        """Bans users based on a list of IDs provided in a .txt file"""
        if not file.filename.endswith('.txt'):
            raise commands.BadArgument
        file_data = await file.read() 
        user_ids = file_data.decode('utf-8').splitlines()
        users = []
        for user_id in user_ids:
            user = self.bot.get_user(int(user_id))
            if user:
                users.append(user)
        if len(users) <= 0:
            await ctx.send("Failed to gather any banned users. Make sure that the .txt file is properly configured to have valid user IDs.")
            return
        await self.generic_ban(ctx, users, f"Bansync performed by {ctx.author.name}", )
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
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def clearpunishment(self, ctx: commands.Context, users: commands.Greedy[discord.User]):
        """Clears all punishments for given user(s)"""
        moderation = await self.database.get_guild_collection(ctx.guild.id, "moderation")
        for user in users:
            results = await moderation.delete_many({"offender": user.id})
            number = results.deleted_count
            count = "punishment" if number == 1 else "punishments"
            await ctx.send(f"Removed {number} {count} from **{user.name}**")
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
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def clearwarn(self, ctx: commands.Context, users: commands.Greedy[discord.User]):
        """Clears all warnings for given user(s)"""
        moderation = await self.database.get_guild_collection(ctx.guild.id, "moderation")
        for user in users:
            results = await moderation.delete_many({"offender": user.id, "type": "warn"})
            number = results.deleted_count
            count = "warning" if number == 1 else "warnings"
            await ctx.send(f"Removed {number} {count} from **{user.name}**")
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
            
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, users: commands.Greedy[discord.Member], *, reason = "No reason provided"):
        """Kicks the given user(s) if possible, with the given reason"""
        kicked_users, failed_kicks = await self.perform_kick(ctx.guild, users, ctx.author, reason)
        if len(kicked_users) > 0:
            await ctx.send(f"Kicked {'**, **'.join(x.name for x in kicked_users)}")
        if len(failed_kicks) > 0:
            await ctx.send(f"Failed to kick {'**, **'.join(x.name for x in failed_kicks)}")
    @kick.error
    async def on_kick_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to kick users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def modlog(self, ctx: commands.Context, users: commands.Greedy[discord.User]):
        """Grabs all moderation logs for user(s)"""
        moderation = await self.database.get_guild_collection(ctx.guild.id, "moderation")
        for user in users:
            modlog_entries = moderation.find({"offender": user.id})
            embed = discord.Embed(title=f"Mod logs", color=discord.Color.blurple())
            embed.set_author(name=user.name, url=user.avatar.url)
            async for entry in modlog_entries:
                modlog_id = entry.get("id")
                action = entry.get("type")
                reason = entry.get("reason", "No reason provided.")
                timestamp: datetime = entry.get("timestamp")
                mod_timestamp = timestamp.date()
                moderator_id = entry.get("responsible_moderator")
                moderator = self.bot.get_user(moderator_id)
                moderator_name = moderator.name if moderator else "Unknown Moderator"
                embed.add_field(name=f"#{modlog_id} | {action} | {mod_timestamp}",value=(f"**Responsible Moderator**: {moderator_name}\n"f"**Reason**: {reason}"),inline=False)
            await ctx.send(embed=embed) if len(embed.fields) > 0 else await ctx.send(f"No modlog entries found for **{user.name}**.")
    @modlog.error
    async def on_modlog_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view user modlogs.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context, users: commands.Greedy[discord.Member], *, args: str = None):
        """Mutes the given user(s) if possible, for the given time and reason (Indefinite if no time is provided)"""
        time = discord.utils.utcnow()
        mute_role = await find_role(ctx.guild, self.database, "mute_role")
        if not mute_role:
            await ctx.send("Cannot mute user(s). Make sure that the mute role is in-server and properly configured.")
            return
        if not args:
            time_val = None
            duration = None
            reason = "No reason provided"
        else:
            args_list = args.split(" ")
            if len(args_list) == 1:
                time_val = args_list[0]
                duration = await parse_time_string(args_list[0])
                if not duration:
                    raise commands.UserInputError
                reason = "No reason provided"
            elif len(args_list) == 2:
                time_val = args_list[0]
                duration = await parse_time_string(args_list[0])
                if not duration:
                    raise commands.UserInputError
                reason = args_list[1]
            else:
                raise commands.TooManyArguments
        muted_users, failed_mutes = await self.perform_mute(ctx.guild, users, mute_role, ctx.author, reason, time_val)
        if duration:
            time_str = await expand_time_string(time_val)
            time_str = "for " + time_str
        else:
            time_str = "indefinitely"
        if len(muted_users) > 0:
            await ctx.send(f"{ctx.author.name} muted {'**, **'.join(x.name for x in muted_users)} {time_str}. Reason: {reason}")
        if len(failed_mutes) > 0:
            await ctx.send(f"Failed to mute {'**, **'.join(x.name for x in failed_mutes) }")
        for member in muted_users:
            await self.log_punishment("mute", ctx.guild, member, reason, ctx.author, time_val)
        if duration:
            await self.schedule_unmute(muted_users, mute_role, duration, f"Automatic unmute made {duration} ago by {ctx.author.name} (ID: {ctx.author.id})",time,ctx.author)   
    @mute.error
    async def on_mute_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid duration and reason, omit the duration & reason to have an indefinite mute with no reason, or omit the reason to have a indefinite mute with a reason.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to mute users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        elif isinstance(error, commands.UserInputError):
            await ctx.send("Invalid duration. Ensure that the duration is a valid time string (Ex. 4w or 2mo3d).")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def muted(self, ctx: commands.Context):
        """Produces a .txt file that contains the name and ID of all users who are currently muted"""
        mute_role = await find_role(ctx.guild, self.database, "mute_role")
        if not mute_role:
            await ctx.send("Cannot mute role. Make sure that the mute role is in-server and properly configured.")
            return
        members: List[discord.Member]= [member for member in ctx.guild.members if mute_role in member.roles]
        if len(members) == 0:
            await ctx.send("No members to dump.")
            return
        user_list = "\n".join([f"{index + 1}. {member.name} ({member.id})"
                               for index, member in enumerate(members)])
        file = io.BytesIO(user_list.encode('utf-8'))
        file_name = f"{mute_role.name}_members.txt"
        await ctx.send(file=discord.File(file, file_name))
    @muted.error
    async def on_muted_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?muted")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view all muted users.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def muterolecr(self, ctx: commands.Context):
        """Creates a new mute role, sets the database configuration to that role, and updates the permissions"""
        guild = ctx.guild
        if await find_role(ctx.guild, self.database, "mute_role"):
            await ctx.send(f"Mute role already exists in server.")
            return
        mute_role = await guild.create_role(name="Muted", reason="Created for muting users", color=discord.Color.red())
        await self.set_permissions_in_channels(guild, mute_role)
        await self.database.update_config(ctx.guild.id, {"$set": {"mute_role": mute_role.id}})
        await ctx.send("Muted role created and updated.")
    @muterolecr.error
    async def on_muterolecr_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?muterolecr")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to create a mute role.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def muteroleup(self, ctx: commands.Context):
        """Updates the existing mute role in the database by editing its permissions"""
        guild = ctx.guild
        mute_role = await find_role(ctx.guild, self.database, "mute_role")
        if not mute_role:
            await ctx.send("Cannot find mute role. Make sure that the mute role is in-server and properly configured.")
            return
        await self.set_permissions_in_channels(guild, mute_role)
        await ctx.send("Muted role updated.")
    @muteroleup.error
    async def on_muteroleup_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?muteroleup")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to update a mute role.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, num: int, *, args: Optional[str]):
        """Purges num messages from the server, with specifications for the channel and user to purge from"""
        if not args:
            num_purged = 0
            messages = await self.get_messages(ctx.guild, num, ctx.message)
            for msg in messages:
                try:
                    await msg.delete()
                    num_purged += 1
                except Exception:
                    continue
            if num_purged == 0:
                await ctx.send("Failed to purge any messages.")
                return
            await ctx.send(f"Purged {num_purged} messages from the entire server.")
            return
        args_list = args.split(" ")
        if len(args_list) == 2:
            channel1 = await get_channel(args_list[0], ctx.guild)
            user1 = await get_user(args_list[0], ctx.guild)
            channel2 = await get_channel(args_list[1], ctx.guild)
            user2 = await get_user(args_list[1], ctx.guild)
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
            def check_msg(msg: discord.Message):
                return msg.author == purge_user and msg.id != ctx.message.id
            adjusted_limit = num + 1 if purge_channel == ctx.channel else num
            messages = await purge_channel.purge(limit=adjusted_limit, check=check_msg)
            if len(messages) == 0:
                await ctx.send("Failed to purge any messages.")
            else:
                await ctx.send(f"Purged {len(messages)} messages from {purge_channel.name}/{purge_user.name}")
        elif len(args_list) == 1:
            channel = await get_channel(args, ctx.guild)
            user = await get_user(args, ctx.guild)
            if channel and isinstance(channel, discord.TextChannel):
                purge_channel = channel
                def check_msg_2(msg: discord.Message):
                    return msg.id != ctx.message.id
                adjusted_limit = num + 1 if purge_channel == ctx.channel else num
                messages = await purge_channel.purge(limit=adjusted_limit, check=check_msg_2)
                if len(messages) == 0:
                    await ctx.send("Failed to purge any messages")
                else:
                    await ctx.send(f"Purged {len(messages)} messages from {purge_channel.name}")
            elif user and (isinstance(user, discord.Member) or isinstance(user, discord.User)):
                purge_user = user
                purge_channel = None
                messages = await self.get_messages(ctx.guild, num, ctx.message, purge_user, purge_channel)
                num_purged = 0
                for msg in messages:
                    try:
                        await msg.delete()
                        num_purged += 1
                    except Exception:
                        continue
                if num_purged == 0:
                    await ctx.send("Failed to purge any messages.")
                else:
                    await ctx.send(f"Purged {num_purged} messages from {purge_user.name}.")
            else:
                raise commands.UserInputError
        else:
            raise commands.TooManyArguments
    @purge.error
    async def on_purge_error(self, ctx: commands.Context, error):
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
            
    @commands.command(aliases=['q'])
    @commands.has_permissions(manage_roles=True)
    async def quarantine(self, ctx: commands.Context, users: commands.Greedy[discord.Member], *, reason = "No reason provided"):
        """Puts user(s) into quarantine if possible, with the given reason"""
        quarantine_role = await find_role(ctx.guild, self.database, "quarantine_role")
        if not quarantine_role:
            await ctx.send("Cannot quarantine user(s). Make sure that the quarantine role is in-server and properly configured.")
            return
        quarantined_users, failed_quarantines = await self.perform_quarantine(users, quarantine_role, reason)
        if len(quarantined_users) > 0:
            await ctx.send(f"{ctx.author.mention} put {', '.join(x.mention for x in quarantined_users)} in quarantine. :lock:")
        if len(failed_quarantines) > 0:
            await ctx.send(f"Failed to put {', '.join(x.mention for x in failed_quarantines) } in quarantine")
        for member in quarantined_users:
            await self.log_punishment("quarantine", ctx.guild, member, reason, ctx.author)
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
             
    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def quarantinecreate(self, ctx: commands.Context):
        """Creates a new quarantine role, sets the database configuration to that role, and updates the permissions"""
        guild = ctx.guild
        if await find_role(ctx.guild, self.database, "quarantine_role"):
            await ctx.send(f"Quarantine role already exists in server.")
            return
        quarantine_role = await guild.create_role(name="Quarantine", reason="Created for quarantining users", color=discord.Color.darker_gray())
        await self.set_quarantine_permissions(guild, quarantine_role)
        await self.database.update_config(ctx.guild.id, {}, {"$set": {"mute_role": quarantine_role.id}})
        await ctx.send("Quarantine role created and updated.")
    @quarantinecreate.error
    async def on_quarantinecreate_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?quarantinecreate")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to create a quarantine role.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def quarantineup(self, ctx: commands.Context):
        """Updates the existing quarantine role in the database by editing its permissions"""
        guild = ctx.guild
        quarantine_role = await find_role(ctx.guild, self.database, "quarantine_role")
        if not quarantine_role:
            await ctx.send("Cannot find quarantine role. Make sure that the quarantine role is in-server and properly configured.")
            return
        await self.set_quarantine_permissions(guild, quarantine_role)
        await ctx.send("Quarantine role updated.")
    @quarantineup.error
    async def on_quarantineup_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?quarantineup")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to update a quarantine role.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def rban(self, ctx: commands.Context, users: commands.Greedy[Union[discord.User, discord.Member]]):
        """Bans the given user(s) if possible, without producing a moderation log"""
        await self.generic_ban(ctx, users, RBAN_REASON)
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
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def reason(self, ctx: commands.Context, ids: commands.Greedy[int], *, reason: str):
        """Changes the reason of moderation log entries with given id(s)"""
        moderation = await self.database.get_guild_collection(ctx.guild.id, "moderation")
        for id in ids:
            result = await moderation.find_one({"id": id})
            if not result:
                await ctx.send(f"No modlog entry found with ID {id}.")
                pass
            await moderation.update_one({"id": id},{"$set": {"reason": reason}})
            channel_id = result.get("log_channel_id")
            message_id = result.get("message_log_id")
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await ctx.send(f"Modlog channel not found for id {id}.")
                pass
            try:
                modlog_message = await channel.fetch_message(message_id)
            except discord.NotFound:
                await ctx.send(f"Modlog message not found for id {id}.")
                pass
            if modlog_message.embeds:
                embed = modlog_message.embeds[0]
                if embed.fields:
                    for field in embed.fields:
                        if "Reason" in field.name:
                            embed.set_field_at(embed.fields.index(field),name=field.name,value=reason,inline=field.inline)
                else:
                    embed.add_field(name="Reason", value=reason, inline=False)
                await modlog_message.edit(embed=embed)
                await ctx.send(f"Updated the reason for modlog entry ID {id}.")
            else:
                await ctx.send(f"Modlog message does not contain an embed for id {id}.")
    @reason.error
    async def on_reason_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid mod log ID(s) and reason.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to change reasons for user modlogs.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all mod log IDs are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def removepunishment(self, ctx: commands.Context, ids: commands.Greedy[int]):
        """Removes a punishment with the given ID"""
        moderation = await self.database.get_guild_collection(ctx.guild.id, "moderation")
        for id in ids:
            entry = await moderation.find_one({"id": id})
            if entry:
                channel_id = entry.get("log_channel_id")
                message_id = entry.get("message_log_id")
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    await ctx.send(f"Modlog channel not found for id {id}.")
                    pass
                try:
                    modlog_message = await channel.fetch_message(message_id)
                except discord.NotFound:
                    await ctx.send(f"Modlog message not found for id {id}.")
                    return
                await modlog_message.delete()
            result = await moderation.delete_one({"id": id})
            if result.deleted_count > 0:
                await ctx.send(f"Removed punishment #{id}")
            else:
                await ctx.send("No punishment found with that ID.")
    @removepunishment.error
    async def on_removepunishment_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid mod log ID(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to remove punishments.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all mod log IDs are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['rn'])
    @commands.has_permissions(manage_nicknames=True)
    async def resetnick(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        """Resets the nickname of user(s)"""
        successful_nick: List[discord.Member] = []
        failed_nick: List[discord.Member] = []
        for user in users:
            try:
                await user.edit(nick=None)
                successful_nick.append(user)
            except Exception:
                failed_nick.append(user)
                pass
        if len(successful_nick) > 0:
            await ctx.send(f"Reset nickname for {', '.join(x.name for x in successful_nick)}") 
        if len(failed_nick) > 0:
            await ctx.send(f"Failed to reset nickname for {', '.join(x.name for x in failed_nick)}")
    @resetnick.error
    async def on_resetnick_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to reset user nicknames.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def rkick(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        """Kicks the given user(s) if possible, without producing a moderation log"""
        kicked_users, failed_kicks = await self.perform_kick(ctx.guild, users, ctx.author, RKICK_REASON)
        if len(kicked_users) > 0:
            await ctx.send(f"Kicked {'**, **'.join(x.name for x in failed_kicks)}")
        if len(failed_kicks) > 0:
            await ctx.send(f"Failed to kick {'**, **'.join(x.name for x in kicked_users)}")
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
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rmute(self, ctx: commands.Context, users: commands.Greedy[discord.Member], duration: Optional[str]):
        """Mutes the given user(s) if possible for the given time (Indefinite if no time provided), without producing a moderation log"""
        timestamp = discord.utils.utcnow()
        mute_role = await find_role(ctx.guild, self.database, "mute_role")
        if not mute_role:
            await ctx.send("Cannot mute user(s). Make sure that the mute role is in-server and properly configured.")
            return
        if duration:
            time_in_seconds = await parse_time_string(duration)
            if not time_in_seconds:
                await ctx.send("Invalid duration input. Please make sure it is a valid time (Ex. 4w or 2mo).")
                return
            time_str = await expand_time_string(duration)
            time_str = "for " + time_str
        else:
            time_in_seconds = None
            time_str = "indefinitely"
        muted_users, failed_mutes = await self.perform_mute(ctx.guild, users, mute_role, ctx.author, RMUTE_REASON, duration)
        if len(muted_users) > 0:
            await ctx.send(f"{', '.join(x.mention for x in muted_users)} muted {time_str}. If an unmute is required, contact a staff member.")
        if len(failed_mutes) > 0:
            await ctx.send(f"Failed to mute {', '.join(x.mention for x in failed_mutes)}")
        if time_in_seconds:
            await self.schedule_unmute(muted_users, mute_role, time_in_seconds, RMUTE_EXPIRY_REASON,timestamp,ctx.author)
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
            
    @commands.command(aliases=['rq'])
    @commands.has_permissions(manage_roles=True)
    async def rquarantine(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        """Puts user(s) into quarantine, without producing a moderation log"""
        quarantine_role = await find_role(ctx.guild, self.database, "quarantine_role")
        if not quarantine_role:
            await ctx.send("Cannot quarantine user(s). Make sure that the quarantine role is in-server and properly configured.")
            return
        quarantined_users, failed_quarantines = await self.perform_quarantine(users, quarantine_role, RQUARANTINE_REASON)
        if len(quarantined_users) > 0:
            await ctx.send(f"{', '.join(x.mention for x in quarantined_users)} put in quarantine. If an unquarantine is required, contact a staff member.")
        if len(failed_quarantines) > 0:
            await ctx.send(f"Failed to put {', '.join(x.mention for x in failed_quarantines) } in quarantine")
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
    @commands.has_permissions(moderate_members=True)
    async def rtimeout(self, ctx: commands.Context, users: commands.Greedy[discord.Member], duration: str = "27d"):
        """Times out user(s) if possible, for the given time (27 days max if time exceeds that or no time is provided), without producing a moderation log"""
        time_in_seconds = await parse_time_string(duration)
        if not time_in_seconds:
            await ctx.send("Invalid duration input. Please make sure it is a valid time (Ex. 4w or 2mo). (Note that the maximum for a timeout is 27 days)")
            return
        elif int(time_in_seconds.total_seconds()) >= 2332800:
            time_in_seconds = timedelta(days=27)
        time_str = await expand_time_string(duration)
        timedout_users, failed_timeouts = await self.perform_timeout(ctx.guild, users, time_in_seconds, ctx.author, RTIMEOUT_REASON, duration)
        if len(timedout_users) > 0:
            await ctx.send(f"Timed out {', '.join(x.mention for x in timedout_users)} for {time_str}. If an untimeout is required, contact a staff member.")
        if len(failed_timeouts) > 0:
            await ctx.send(f"Failed to timeout {', '.join(x.mention for x in failed_timeouts) }")
        await self.schedule_untimeout(timedout_users, time_in_seconds, ctx.author, RTIMEOUT_EXPIRY_REASON)
    @rtimeout.error
    async def on_rtimeout_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to timeout users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def runban(self, ctx: commands.Context, users: commands.Greedy[discord.User]):
        """Unbans the given user(s) if possible, without producing a moderation log"""
        unbanned_users, failed_unbans = await self.perform_unban(ctx.guild, users, ctx.author, RUNBAN_REASON)
        if len(unbanned_users) > 0:
            await ctx.send(f"{'**, **'.join(x.name for x in unbanned_users)} successfully unbanned.")
        if len(failed_unbans) > 0:
            await ctx.send(f"Failed to unban {'**, **'.join(x.name for x in failed_unbans)}")
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
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def runmute(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        """Unmutes the given user(s) if possible, without producing a moderation log"""
        mute_role = await find_role(ctx.guild, self.database, "mute_role")
        if not mute_role:
            await ctx.send("Cannot unmute user(s). Make sure that the mute role is in-server and properly configured.")
            return
        unmuted_users, failed_unmutes = await self.perform_unmute(ctx.guild, users, mute_role, ctx.author, RUNMUTE_REASON)
        s_m = "has" if len(unmuted_users) == 1 else "have"
        if len(unmuted_users) > 0:
            await ctx.send(f"{', '.join(x.mention for x in unmuted_users)} {s_m} been unmuted!")
        if len(failed_unmutes) > 0:
            await ctx.send(f"Failed to unmute {', '.join(x.mention for x in failed_unmutes) }")
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
            
    @commands.command(aliases=['ruq'])
    @commands.has_permissions(manage_roles=True)
    async def runquarantine(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        """Removes user(s) from quarantine, without producing a moderation log"""
        quarantine_role = await find_role(ctx.guild, self.database, "quarantine_role")
        if not quarantine_role:
            await ctx.send("Cannot unquarantine user(s). Make sure that the quarantine role is in-server and properly configured.")
            return
        unquarantined_users, failed_unquarantines = await self.perform_unquarantine(users, quarantine_role, RUNQUARANTINE_REASON)
        if len(unquarantined_users) > 0:
            await ctx.send(f"{', '.join(x.mention for x in unquarantined_users)} removed from quarantine!")
        if len(failed_unquarantines) > 0:
            await ctx.send(f"Failed to remove {', '.join(x.mention for x in failed_unquarantines) } from quarantine (Make sure the user is in server and has the role)")
    @runquarantine.error
    async def on_runquarantine_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to unquarantine users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def runtimeout(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        """Removes user(s) from timeout if possible, without producing a moderation log"""
        untimedout_users, failed_untimeouts = await self.perform_untimeout(ctx.guild, users, ctx.author, RUNTIMEOUT_REASON)
        s_m = "was" if len(untimedout_users) == 1 else "were"
        if len(untimedout_users) > 0:
            await ctx.send(f"{', '.join(x.mention for x in untimedout_users)} {s_m} been removed from timeout!")
        if len(failed_untimeouts) > 0:
            await ctx.send(f"Failed to untimeout {', '.join(x.mention for x in failed_untimeouts)}")
    @runtimeout.error
    async def on_runtimeout_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to untimeout users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def sb(self, ctx: commands.Context, users: commands.Greedy[discord.User]):
        """Bans the given user(s) if possible with the reason of scamming"""
        await self.generic_ban(ctx, users, "Scammer and/or compromised account", "For trying to scam people.")
    @sb.error
    async def on_sb_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['sn'])
    @commands.has_permissions(manage_nicknames=True)
    async def setnick(self, ctx: commands.Context, users: commands.Greedy[discord.Member], name="Request New Nickname"):
        """Changes the nickname of user(s), setting it to \"Request New Nickname\" if the default is used"""
        successful_nick: List[discord.Member] = []
        failed_nick: List[discord.Member] = []
        for user in users:
            try:
                await user.edit(nick=name)
                successful_nick.append(user)
            except Exception:
                failed_nick.append(user)
                pass
        if len(successful_nick) > 0:
            await ctx.send(f"Set new nickname to {name} for {', '.join(x.name for x in successful_nick)}") 
        if len(failed_nick) > 0:
            await ctx.send(f"Failed to set nickname for {', '.join(x.name for x in failed_nick)}")
    @setnick.error
    async def on_setnick_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and name. Omit the name to use the default \"Request New Nickname\" nickname.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to change user nicknames.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def tb(self, ctx: commands.Context, users: commands.Greedy[Union[discord.User, discord.Member]]):
        """Bans the given user(s) if possible with the reason of trolling or raiding"""
        await self.generic_ban(ctx, users, "Troll/raider", "For trolling/raiding")
    @tb.error
    async def on_tb_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, users: commands.Greedy[discord.Member], *, args: str = None):
        """Times out user(s) if possible for the given time and reason (Maximum of 27 days if time exceeds that or no time is provided)"""
        if not args:
            time_val = None
            duration = None
            reason = "No reason provided"
        else:
            args_list = args.split(" ")
            if len(args_list) == 1:
                time_val = args_list[0]
                duration = await parse_time_string(args_list[0])
                if not duration:
                    await ctx.send("Invalid duration input. Please make sure it is a valid time (Ex. 4w or 2mo). Make sure the duration is first. (Max duration for a timeout is 27d)")
                    return
                elif duration.total_seconds() > 2419200:
                    duration = timedelta(days=27)
                reason = "No reason provided"
            elif len(args_list == 2):
                time_val = args_list[0]
                duration = await parse_time_string(args_list[0])
                if not duration:
                    await ctx.send("Invalid duration input. Please make sure it is a valid time (Ex. 4w or 2mo). Make sure the duration is first. (Max duration for a timeout is 27d)")
                    return
                elif duration.total_seconds() > 2419200:
                    time_val = "27d"
                    duration = timedelta(days=27)
                reason = args_list[1]
            else:
                raise commands.TooManyArguments
        timedout_users, failed_timeouts = await self.perform_timeout(ctx.guild, users, duration, ctx.author, reason, time_val)
        time_str = await expand_time_string(time_val)
        time_str = "for " + time_str
        if len(timedout_users) > 0:
            await ctx.send(f"Successfully timed out {'**, **'.join(x.name for x in timedout_users)} {time_str}. Reason: {reason}")
            await self.schedule_untimeout(timedout_users, duration, ctx.author, f"Automatic untimeout from timeout made {duration} ago by {ctx.author.name} (ID: {ctx.author.id})")
        if len(failed_timeouts) > 0:
            await ctx.send(f"Failed to timeout {'**, **'.join(x.name for x in failed_timeouts) }")
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
            
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def uau(self, ctx: commands.Context, users: commands.Greedy[Union[discord.User, discord.Member]]):
        """Bans the given user(s) if possible with the reason of being underaged"""
        await self.generic_ban(ctx, users, "Since you're under the age of 13, you're not allowed to be on Discord. This violates the Children's Online Privacy Protection Act (COPPA), which requires members of a service like Discord to be over the age of 13 if any personal info (including emails) is collected. Discord also punishes servers for knowingly harboring underage users. In light of that, I have to ban you. Come back later when you're over-age.", "For being an underage user, i.e. <13 years old")
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
            
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, users: commands.Greedy[discord.User], *, reason = "No reason provided"):
        """Unbans the given user(s) if possible, with the given reason"""
        unbanned_users, failed_unbans = await self.perform_unban(ctx.guild, users, ctx.author, reason)
        if len(unbanned_users) > 0:
            await ctx.send(f"{'**, **'.join(x.name for x in unbanned_users)} successfully unbanned. Reason: {reason}")
        if len(failed_unbans) > 0:
            await ctx.send(f"Failed to unban {'**, **'.join(x.name for x in failed_unbans)}")
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
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, users: commands.Greedy[discord.Member], *, reason = "No reason provided"):
        """Unmutes the given user(s) if possible, with the given reason"""
        mute_role = await find_role(ctx.guild, self.database, "mute_role")
        if not mute_role:
            await ctx.send("Cannot mute user(s). Make sure that the mute role is in-server and properly configured.")
            return
        unmuted_users, failed_unmutes = await self.perform_unmute(ctx.guild, users, mute_role, ctx.author, reason)
        if len(unmuted_users) > 0:
            await ctx.send(f"Successfully unmuted {'**, **'.join(x.name for x in unmuted_users)}")
        if len(failed_unmutes) > 0:
            await ctx.send(f"Failed to unmute {'**, **'.join(x.name for x in failed_unmutes) }")
        for member in unmuted_users:
            await self.log_punishment("unmute", ctx.guild, member, reason, ctx.author)
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
            
    @commands.command(aliases=['uq'])
    @commands.has_permissions(manage_roles=True)
    async def unquarantine(self, ctx: commands.Context, users: commands.Greedy[discord.Member], *, reason = "No reason provided"):
        """Removes user(s) from quarantine if possible, with the given reason"""
        quarantine_role = await find_role(ctx.guild, self.database, "quarantine_role")
        if not quarantine_role:
            await ctx.send("Cannot unquarantine user(s). Make sure that the quarantine role is in-server and properly configured.")
            return
        unquarantined_users, failed_unquarantines = await self.perform_unquarantine(users, quarantine_role, reason)
        if len(unquarantined_users) > 0:
            await ctx.send(f"{ctx.author.mention} removed {', '.join(x.mention for x in unquarantined_users)} from quarantine. :unlock:")
        if len(failed_unquarantines) > 0:
            await ctx.send(f"Failed to remove {', '.join(x.mention for x in failed_unquarantines) } from quarantine (Make sure the user is in server and has the role)")
        for member in unquarantined_users:
            await self.log_punishment("unquarantine", ctx.guild, member, reason, ctx.author)
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
            
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx: commands.Context, users: commands.Greedy[discord.Member], *, reason="No reason given"):
        """Removes user(s) from timeout if possible, with the given reason"""
        untimedout_users, failed_untimeouts = await self.perform_untimeout(ctx.guild, users, ctx.author, reason)
        if len(untimedout_users) > 0:
            await ctx.send(f"Successfully removed {'**, **'.join(x.name for x in untimedout_users)} from timeout. Reason: {reason}")
        if len(failed_untimeouts) > 0:
            await ctx.send(f"Failed to untimeout {'**, **'.join(x.name for x in failed_untimeouts)}")
    @untimeout.error
    async def on_untimeout_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s) and reason, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to untimeout users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def warn(self, ctx: commands.Context, users:commands.Greedy[discord.Member], *, reason):
        """Warns user(s) with the given reason"""
        await self.perform_warn(ctx.guild, users, ctx.author, reason)
        for user in users:
            warnings = await self.get_num_warnings(user, ctx.guild)
            ordinaln = await ordinal(warnings)
            await ctx.send(f"{user.name} has been warned, this is their {ordinaln} warning.")
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
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        """When a user gets kicked, timed out, or removed from timeout, the moderation log will log the following:
        Kicked users - User's name, mention, ID, reason for kick, user who performed kick's name
        Timeout - User's name, mention, ID, reason for timeout, duration of the timeout, user who performed timeout's name
        Untimeout - User's name, mention, ID, reason for untimeout, user who performed untimeout's name"""
        time = discord.utils.utcnow()
        guild = entry.guild
        mod_log = await find_channel(guild, self.database, "mod_log")
        if not mod_log:
            return
        if entry.reason:
            real_reason = entry.reason
        else:
            real_reason = f"no reason given, use m?reason {id} <text> to add one"
        if entry.action == discord.AuditLogAction.kick and entry.reason != RKICK_REASON:
            id = await self.database.get_next_id(guild.id)
            obj = entry.target
            try:
                user = self.bot.get_user(obj.id)
                if user:
                    user_name = f"{user.name} {user.mention}"
                else:
                    user_name = f"Unknown User {obj.id}"
            except Exception:
                user_name = f"Unknown User {obj.id}"
            await self.create_log_entry(guild, mod_log, discord.Color.blue(), "kick", id, user_name, real_reason, entry.user)
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
            if not timed_out_before and timed_out_after and entry.reason != RTIMEOUT_REASON:
                id = await self.database.get_next_id(guild.id)
                user = entry.target
                duration = timed_out_after - time
                duration_seconds = int(duration.total_seconds())
                await self.create_log_entry(guild, mod_log, discord.Color.orange(), "timeout", id, user, real_reason, entry.user, f"{duration_seconds} seconds")
            if timed_out_before and not timed_out_after and entry.reason != RUNTIMEOUT_REASON and entry.reason != RTIMEOUT_EXPIRY_REASON:
                id = await self.database.get_next_id(guild.id)
                user = entry.target
                await self.create_log_entry(guild, mod_log, discord.Color.green(), "untimeout", id, user, real_reason, user)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.Member, discord.User]):
        """When a user gets banned, the moderation log will log the user's name, mention, ID, the reason for the ban, the name of the user who performed the ban. 
        The bot will also perform the ban on that same user if the ban occurred on an EMD server"""
        ban_limit = await self.database.get_config(guild.id, "ban_limit")
        await self.database.update_config(guild.id, {"$set": {"ban_limit": ban_limit + 1}})
        mod_log = await find_channel(guild, self.database, "mod_log")
        if not mod_log:
            return
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            id = await self.database.get_next_id(guild.id)
            if entry.target.id == user.id and entry.reason != RBAN_REASON:
                if entry.reason:
                    real_reason = entry.reason
                else:
                    real_reason = f"no reason given, use m?reason {id} <text> to add one"
                await self.create_log_entry(guild, mod_log, discord.Color.red(), "ban", id, user, real_reason, entry.user)
        if guild.id in EMD_SERVERS and real_reason != "Ban-Sync across EMD servers":
            for server_id in EMD_SERVERS:
                if server_id != guild.id:
                    try:
                        server = self.bot.get_guild(server_id)
                        if server:
                            await self.perform_ban(server, [user], self.bot.user, "Ban-Sync across EMD servers")
                    except Exception:
                        pass
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: Union[discord.Member, discord.User]):
        """When a user gets unbanned, the moderation log will log the user's name, mention, ID, the reason for the unban, the name of the user who performed the unban. 
        The bot will also perform the unban on that same user if the ban occurred on an EMD server"""
        mod_log = await find_channel(guild, self.database, "mod_log")
        if not mod_log:
            return
        async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=1):
            id = await self.database.get_next_id(guild.id)
            if entry.target.id == user.id and entry.reason != RUNBAN_REASON:
                if entry.reason:
                    real_reason = entry.reason
                else:
                    real_reason = f"no reason given, use m?reason {id} <text> to add one"
                await self.create_log_entry(guild, mod_log, discord.Color.green(), "unban", id, user, real_reason, entry.user)
        if guild.id in EMD_SERVERS and real_reason != "Ban-Sync across EMD servers":
            for server_id in EMD_SERVERS:
                if server_id != guild.id:
                    try:
                        server = self.bot.get_guild(server_id)
                        if server:
                            await self.perform_unban(server, [user], self.bot.user, "Ban-Sync across EMD servers")
                    except Exception:
                        pass

async def setup(bot: commands.Bot): 
    """Sets up the Moderation Cog"""
    await bot.add_cog(Moderation(bot))
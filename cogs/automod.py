from cogs.moderation import Moderation
from datetime import datetime, timedelta, timezone
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Any, List, LiteralString, Union 
from utility.finder import find_channel, find_int, find_list, find_role, find_time
from utility.guild import Database
import asyncio
import discord
import re

AUTOMOD_EMOTES: list[str] = ["⏲️", "🔨", "🔇", "🔊", "👢", "🗑️", "1️⃣", "2️⃣", "3️⃣", "❌"]
DRAMA_CHANNEL = "drama_channel"
DRAMA_MESSAGE = "drama_message"
MESSAGE_ID = "message_id"
CHANNEL_ID = "channel_id"
USER = "user"

class Automod(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the Automod module"""
        self.bot: commands.Bot = bot
        self.database = Database(self.bot)
    
    async def account_age(self, guild: discord.Guild, member: discord.Member) -> bool:
        """Checks the minimum account age for a server and if an account matches that criteria"""
        min_account_age, _= await find_time(guild, self.database, self.database.min_account_age)
        return False if not min_account_age else bool(member.created_at >= discord.utils.utcnow() - min_account_age)
    
    async def automod_mute(self, moderation: Moderation, guild: discord.Guild, members: List[discord.Member], mute_role: discord.Role, responsible: Union[discord.User,discord.Member], reason: str, time: timedelta = None, text: str = None):
        """Performs the mute based on the reaction given in the automod"""
        await moderation.punishment_steps(guild, "mute", members, reason, responsible, text, mute_role, None)
        if time:
            await asyncio.sleep(time.total_seconds())
            await moderation.punishment_steps(guild, "unmute", members, f"Automatic unmute from mute made {text} ago by {responsible.name} (ID: {responsible.id})", responsible, mute_role, None, None)
    
    async def check_link(self, content: str, guild: discord.Guild) -> bool:
        """Checks if a message contains a banned link"""
        bad_links: list[str] = await find_list(guild, self.database, self.database.bad_links)
        if not bad_links or len(bad_links) <= 0:
            return False
        bad_link_pattern: LiteralString = '|'.join([r'\b' + r'[\s]*'.join(list(bad_link)) + r'\b' for bad_link in bad_links])
        bad_link_regex: re.Pattern[str] = re.compile(bad_link_pattern, re.IGNORECASE)
        return bool(bad_link_regex.search(content))
    
    async def check_invite(self, content: str, guild: discord.Guild) -> bool:
        """Checks if a message contains an invite from a non-whitelisted guild"""
        invite_whitelist: list[int] = await find_list(guild, self.database, self.database.invite_whitelist)
        if invite_whitelist and len(invite_whitelist) > 0:
            if re.findall(r"(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite)\/[a-zA-Z0-9]+",content):
                invite_links: List[Any] = re.findall(r"discord(?:app)?\.com\/invite\/([a-zA-Z0-9]+)", content) + \
                            re.findall(r"discord\.(gg|io|me|li)\/([a-zA-Z0-9]+)", content)
                invite_codes: List[Any] = [invite[-1] for invite in invite_links]
                for invite_code in invite_codes:
                    try:
                        invite: discord.Invite = await self.bot.fetch_invite(invite_code)
                        if invite.guild.id not in invite_whitelist:
                            return True
                    except Exception:
                        pass
        return False
    
    async def check_mentions(self, guild: discord.Guild, member: discord.Member) -> bool:
        """Checks if the member exceeds the number of text mentions in a given time"""
        mentions = 0
        mentionspam_time, _= await find_time(guild, self.database, self.database.mentionspam_time)
        mentionspam_amount: int = await find_int(guild, self.database, self.database.mentionspam_amount)
        if not mentionspam_amount or not mentionspam_time:
            return False
        messages: List[discord.Message] = []
        for channel in guild.text_channels:
            try:
                async for msg in channel.history(limit=mentionspam_amount, after=discord.utils.utcnow() - mentionspam_time):
                    if msg.author.id == member.id:
                        text_mentions: List = await self.has_mention(msg)
                        if text_mentions:
                            messages.append(msg)
                            mentions += len(text_mentions)
                        if mentions >= mentionspam_amount:
                            for message in messages:
                                await message.delete()
                            return True
            except discord.Forbidden:
                continue
        if mentions >= mentionspam_amount:
            for message in messages:
                await message.delete()
            return True
        return False

    async def check_word(self, content: str, guild: discord.Guild) -> bool:
        """Checks if a message contains a bad word"""
        bad_words: list[str] = await find_list(guild, self.database, self.database.bad_words)
        if not bad_words or len(bad_words) <= 0:
            return False
        bad_word_pattern: LiteralString = '|'.join([r'\b' + r'[\s]*'.join(list(word)) + r'\b' for word in bad_words])
        bad_word_regex: re.Pattern[str] = re.compile(bad_word_pattern, re.IGNORECASE)
        return bool(bad_word_regex.search(content))
    
    async def check_time(self, guild: discord.Guild, member: discord.Member) -> bool:
        """Grabs the time limit for a server and if the user violated that time limit"""
        time_limit, _ = await find_time(guild, self.database, self.database.time_limit)
        return False if not time_limit else bool(discord.utils.utcnow() - member.joined_at < time_limit)
    
    async def has_mention(self, message: discord.Message) -> List:
        """Checks if a given message has a user or role mention within the message"""
        user_mention_pattern: re.Pattern[str] = re.compile(r"<@!?\d+>")
        role_mention_pattern: re.Pattern[str] = re.compile(r"<@&\d+>")
        return user_mention_pattern.findall(message.content) + role_mention_pattern.findall(message.content)

    async def send_drama_alert(self, guild: discord.Guild, type: str, message: discord.Message) -> None:
        """Sends a message in the drama channel"""
        current_time: datetime = discord.utils.utcnow()
        automod: AsyncIOMotorCollection = await self.database.get_guild_collection(guild.id, self.database.automod)
        drama_channel: discord.abc.GuildChannel | discord.Thread = await find_channel(guild, self.database, self.database.drama_channel)
        if not drama_channel:
            return
        embed = discord.Embed(title=f"{type}",description=f"Potential trouble found in {message.channel.mention}",timestamp=current_time)
        async for msg in message.channel.history(limit=5,after=datetime(current_time.year, current_time.month, current_time.day, tzinfo=timezone.utc),oldest_first=True):
            embed.add_field(name=msg.author.name, value=msg.content, inline=False)
        embed.add_field(name=message.author.name,value=message.content,inline=False)
        drama_message: discord.Message = await drama_channel.send(embed=embed)
        automod.insert_one({DRAMA_CHANNEL: drama_channel.id,DRAMA_MESSAGE: drama_message.id,CHANNEL_ID: message.channel.id,MESSAGE_ID: message.id, USER: message.author.id})
        for emote in AUTOMOD_EMOTES:
            await drama_message.add_reaction(emote)
    
    @commands.Cog.listener()
    async def on_automod_action(self, execution: discord.AutoModAction) -> None:
        if execution.rule_trigger_type == discord.AutoModRuleTriggerType.spam:
            return
        if await self.check_time(execution.guild, execution.member):
            await execution.guild.ban(execution.member, reason="Automatic action carried out for violating automod within join time limit.")
            
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Checks if a user's name contains a banned link or has an account that is below the minimum age"""
        if await self.account_age(member.guild, member):
            await member.ban(reason="Automatic action carried out for insufficient account age.")
        if await self.check_link(member.display_name, member.guild) or await self.check_link(member.global_name, member.guild) or await self.check_link(member.name, member.guild):
            await member.ban(reason="Automatic action carried out for having link in name.")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Checks if a message contains a banned link/word, has too many mentions, or has a non-whitelisted invite. If any of these are infracted before the time limit is up, they will be autobanned."""
        moderation: Moderation = self.bot.get_cog("Moderation")
        if message.author.bot or message.author.guild_permissions.administrator or message.author.guild_permissions.manage_guild:
            return
        if await self.check_link(message.content, message.guild):
            await message.delete()
            await moderation.punishment_steps(message.guild, "ban", [message.author], "Automatic action carried out for posting links.", self.bot.user, None, None, None)
            return
        bad_words: bool = await self.check_word(message.content, message.guild)
        if bad_words:
            await message.delete()
            await message.channel.send("Please refrain from using innapropriate language.")
            await moderation.punishment_steps(message.guild, "warn", [message.author], "Automatic action carried out for using a blacklisted word", self.bot.user, None, None, None)
            await self.send_drama_alert(message.guild, "blacklistedwords", message)
        bad_invite: bool = await self.check_invite(message.content, message.guild)
        if bad_invite:
            await message.delete()
            await message.channel.send("Please refrain from posting other Discord invites.")
            await moderation.punishment_steps(message.guild, "warn", [message.author], "Automatic action carried out for posting invites", self.bot.user, None, None, None)
            await self.send_drama_alert(message.guild, "discordinvites", message)
        mentions: List = await self.has_mention(message)
        if mentions:
            mentionspam: bool = await self.check_mentions(message.guild, message.author)
            if mentionspam:
                await message.channel.send("Please refrain from using so many mentions!")
                await moderation.punishment_steps(message.guild, "warn", [message.author], "Automatic action carried out for spamming mentions", self.bot.user, None, None, None)
                await self.send_drama_alert(message.guild, "mentionspam", message)
        else:
            mentionspam = False
        if bad_words or bad_invite or mentionspam:
            if await self.check_time(message.guild, message.author):
                await message.guild.ban(message.author, reason="Automatic action carried out for violating automod within join time limit.")   
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """Deals with the reactions in a drama channel post"""
        if payload.user_id == self.bot.user.id:
            return
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        payload_user: discord.Member = guild.get_member(payload.user_id)
        if payload_user.bot:
            return
        perms: discord.Permissions = payload_user.guild_permissions
        channel: discord.abc.GuildChannel | discord.Thread = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
        automod: AsyncIOMotorCollection = await self.database.get_guild_collection(payload.guild_id,self.database.automod)
        drama_channel: discord.abc.GuildChannel | discord.Thread = await find_channel(guild, self.database, self.database.drama_channel)
        if not drama_channel or drama_channel.id != payload.channel_id:
            return
        entry: Any = await automod.find_one({DRAMA_MESSAGE: payload.message_id})
        if not entry:
            return
        mute_role: discord.Role = await find_role(guild, self.database, self.database.mute_role)
        user: discord.Member = guild.get_member(entry[USER])
        moderation: Moderation = self.bot.get_cog("Moderation")
        if payload.emoji.name == "⏲️" and perms.moderate_members:
            await moderation.punishment_steps(guild, "timeout", [user], "Drama watcher timeout.", payload_user, "27d", None, timedelta(days=27))
            await asyncio.sleep(2419200)
            await moderation.punishment_steps(guild, "untimeout", [user], f"Automatic untimeout from timeout made 27d ago by {payload_user.name} (ID: {payload_user.id})", payload_user, None, None, None)
        elif payload.emoji.name == "🔨" and perms.ban_members:
            await moderation.punishment_steps(guild, "ban", [user], "Drama watcher ban.", payload_user, None, None, None)
        elif payload.emoji.name == "🔇" and mute_role and perms.manage_roles:
            await self.automod_mute(moderation, guild, [user], mute_role, payload_user, "Drama watcher permanent mute", None, None)
        elif payload.emoji.name == "🔊" and mute_role and perms.manage_roles:
            await moderation.punishment_steps(guild, "unmute", [user], "Drama watcher unmute.", payload_user, None, mute_role, None)
        elif payload.emoji.name == "👢" and perms.kick_members:
            await moderation.punishment_steps(guild, "kick", [user], "Drama watcher kick.", payload_user, None, None, None)
        elif payload.emoji.name == "🗑️" and perms.manage_messages:
            await moderation.punishment_steps(guild, "delete", [user], "Drama watcher delete", payload_user, None, None, None, None)
        elif payload.emoji.name == "1️⃣" and mute_role and perms.manage_roles:
            await self.automod_mute(moderation, guild, [user], mute_role, payload_user, "Drama-watcher 12-hour mute", timedelta(hours=12), "12h")
        elif payload.emoji.name == "2️⃣" and mute_role and perms.manage_roles:
            await self.automod_mute(moderation, guild, [user], mute_role, payload_user, "Drama watcher 24-hour mute", timedelta(hours=24), "24h")
        elif payload.emoji.name == "3️⃣" and mute_role and perms.manage_roles:
            await self.automod_mute(moderation, guild, [user], mute_role, payload_user, "Drama watcher 48-hour mute", timedelta(hours=48), "48h")
        elif payload.emoji.name == "❌" and perms.manage_messages:
            payload_message: discord.Message = await channel.fetch_message(payload.message_id)
            await payload_message.delete()
            await automod.delete_one({MESSAGE_ID: payload.message_id})

async def setup(bot: commands.Bot) -> None: 
    """Sets up the Automod Cog"""
    await bot.add_cog(Automod(bot))
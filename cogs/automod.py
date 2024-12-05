import asyncio
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands
from moderation import Moderation
import re
from typing import List, Union 
from utility.finder import find_channel, find_int, find_role, find_time
from utility.guild import Database

automod_emotes = ["⏲️", "🔨", "🔇", "🔊", "👢", "1️⃣", "2️⃣", "3️⃣", "❌"]

class Automod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Automod module"""
        self.bot = bot
        self.database = Database(self.bot)
    
    async def account_age(self, guild: discord.Guild, user: discord.Member) -> bool:
        """Checks the minimum account age for a server and if an account matches that criteria"""
        account_age = await find_time(guild, self.database, "min_account_age")
        if not account_age:
            return False
        account_age_threshold = discord.utils.utcnow() - account_age
        return bool(user.created_at >= account_age_threshold)
    
    async def automod_mute(self, moderation: Moderation, guild: discord.Guild, users: List[Union[discord.Member, discord.User]], mute_role: discord.Role, user_p: discord.Member, reason: str, time: timedelta = None, time_str: str = None):
        """Performs the mute based on the reaction given in the automod"""
        mutes, failed_mutes = await moderation.perform_mute(guild, [users[0]], mute_role, user_p, reason, time_str)
        if len(mutes) > 0:
            await moderation.log_punishment("mute", guild, users[0], reason, user_p, time_str)
        if time:
            await asyncio.sleep(time.total_seconds())
            successful_unmutes, failed_unmutes = await moderation.perform_unmute(guild, [users[0]], mute_role, f"Automatic unmute from mute made {time_str} ago by {user_p.name} (ID: {user_p.id})")
            if len(successful_unmutes) > 0:
                await moderation.log_punishment("unmute", guild, users[0], f"Automatic unmute from mute made {time_str} ago by {user_p.name} (ID: {user_p.id})", user_p)
    
    async def check_link(self, content: str, guild: discord.Guild) -> bool:
        """Checks if a message contains a banned link"""
        bad_links = await self.database.get_config(guild.id, "bad_links")
        if not bad_links or len(bad_links) <= 0:
            return False
        bad_link_pattern = '|'.join([r'\b' + r'[\s]*'.join(list(link)) + r'\b' for link in bad_links])
        bad_link_regex = re.compile(bad_link_pattern, re.IGNORECASE)
        return bool(bad_link_regex.search(content))
    
    async def check_invite(self, content: str, guild: discord.Guild) -> bool:
        """Checks if a message contains an invite from a non-whitelisted guild"""
        invite_whitelist = await self.database.get_config(guild.id, "invite_whitelist")
        if len(invite_whitelist) == 0:
            return False
        invite_pattern = r"(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite)\/[a-zA-Z0-9]+"
        invites = re.findall(invite_pattern,content)
        if invites:
            invite_links = re.findall(r"discord(?:app)?\.com\/invite\/([a-zA-Z0-9]+)", content) + \
                           re.findall(r"discord\.(gg|io|me|li)\/([a-zA-Z0-9]+)", content)
            invite_codes = [invite[-1] for invite in invite_links]
            for invite_code in invite_codes:
                try:
                    invite = await self.bot.fetch_invite(invite_code)
                    if invite.guild.id not in invite_whitelist:
                        return True
                except Exception:
                    pass
        return False
    
    async def check_mentions(self, guild: discord.Guild, user: discord.Member) -> bool:
        """Checks if the user exceeds the number of text mentions in a given time"""
        user_id = user.id
        current_time = discord.utils.utcnow()
        recent_mentions = 0
        mentionspam_time = await find_time(guild, self.database, "mentionspam_time")
        mentionspam_amount = await find_int(guild, self.database, "mentionspam_amount")
        if not mentionspam_amount or not mentionspam_time:
            return False
        current_datetime = datetime.fromtimestamp(current_time, timezone.utc)
        after_time = current_datetime - mentionspam_time
        messages: List[discord.Message] = []
        for channel in guild.text_channels:
            try:
                async for msg in channel.history(limit=mentionspam_amount, after=after_time):
                    if msg.author.id == user_id:
                        text_mentions = await self.has_mention(msg)
                        if text_mentions:
                            messages.append(msg)
                            recent_mentions += len(text_mentions)
                        if recent_mentions >= mentionspam_amount:
                            for message in messages:
                                await message.delete()
                            return True
            except discord.Forbidden:
                continue
        if recent_mentions >= mentionspam_amount:
            for message in messages:
                await message.delete()
            return True
        return False

    async def check_word(self, content: str, guild: discord.Guild) -> bool:
        """Checks if a message contains a bad word"""
        bad_words = await self.database.get_config(guild.id, "bad_words")
        if not bad_words or len(bad_words) <= 0:
            return False
        bad_word_pattern = '|'.join([r'\b' + r'[\s]*'.join(list(word)) + r'\b' for word in bad_words])
        bad_word_regex = re.compile(bad_word_pattern, re.IGNORECASE)
        return bool(bad_word_regex.search(content))
    
    async def check_time(self, guild: discord.Guild, user: discord.Member) -> bool:
        """Grabs the time limit for a server and if the user violated that time limit"""
        current_time = discord.utils.utcnow()
        time_limit = await find_time(guild, self.database, "time_limit")
        if not time_limit:
            return False
        join_time = user.joined_at
        time_since_join = current_time - join_time
        return bool(time_since_join < time_limit)

    async def send_drama_alert(self, guild: discord.Guild, type: str, message: discord.Message):
        """Sends a message in the drama channel"""
        time = discord.utils.utcnow()
        automod = await self.database.get_guild_collection(guild.id, "automod")
        drama_channel = await find_channel(guild, self.database, "drama_channel")
        if not drama_channel:
            return
        embed = discord.Embed(title=f"{type}",description=f"Potential trouble found in {message.channel.mention}",timestamp=time)
        async for msg in message.channel.history(limit=5,oldest_first=True):
            embed.add_field(name=msg.author.name, value=msg.content, inline=False)
        embed.add_field(name=message.author.name,value=message.content,inline=False)
        drama_message = await drama_channel.send(embed=embed)
        drama_entry = {"drama_channel": drama_channel.id,"drama_message": drama_message.id,"message_channel_id": message.channel.id,"message_id": message.id,"user": message.author.id}
        automod.insert_one(drama_entry)
        for emote in automod_emotes:
            await drama_message.add_reaction(emote)
    
    async def has_mention(self, message: discord.Message):
        user_mention_pattern = re.compile(r"<@!?\d+>")
        role_mention_pattern = re.compile(r"<@&\d+>")
        return user_mention_pattern.findall(message.content) + role_mention_pattern.findall(message.content)
            
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Checks if a user's name contains a banned link or has an account that is below the minimum age"""
        guild = member.guild
        if await self.account_age(guild, member):
            await member.ban(reason="Automatic action carried out for insufficient account age.")
        if await self.check_link(member.display_name, guild) or await self.check_link(member.global_name, guild) or await self.check_link(member.name, guild):
            await member.ban(reason="Automatic action carried out for having link in name.")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Checks if a message contains a banned link/word, has too many mentions, or has a non-whitelisted invite. If any of these are infracted before the time limit is up, they will be autobanned."""
        moderation: Moderation = self.bot.get_cog("Moderation")
        if message.author.bot:
            return
        if message.author.guild_permissions.administrator or message.author.guild_permissions.manage_guild:
            return
        if await self.check_link(message.content, message.guild):
            await message.delete()
            await message.author.ban(reason="Automatic action carried out for posting links.")
            return
        bad_words = await self.check_word(message.content, message.guild)
        if bad_words:
            await message.delete()
            await message.channel.send("Please refrain from using innapropriate language.")
            await moderation.perform_warn(message.guild, [message.author], self.bot.user, "Automatic action carried out for using a blacklisted word")
            await self.send_drama_alert(message.guild, "blacklistedwords", message)
        bad_invite = await self.check_invite(message.content, message.guild)
        if bad_invite:
            await message.delete()
            await message.channel.send("Please refrain from posting other Discord invites.")
            await moderation.perform_warn(message.guild, [message.author], self.bot.user, "Automatic action carried out for posting invites")
            await self.send_drama_alert(message.guild, "discordinvites", message)
        mentionspam = await self.has_mention(message)
        deleted = await self.check_mentions(message.guild, message.author)
        if deleted:
            await message.channel.send("Please refrain from using so many mentions!")
            await moderation.perform_warn(message.guild, [message.author], self.bot.user, "Automatic action carried out for spamming mentions")
            await self.send_drama_alert(message.guild, "mentionspam", message)
        if bad_words or bad_invite or mentionspam:
            if await self.check_time(message.guild, message.author):
                await message.guild.ban(message.author, reason="Automatic action carried out for violating automod within join time limit.")   
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Deals with the reactions in a drama channel post"""
        if payload.user_id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        user_p = guild.get_member(payload.user_id)
        if user_p.bot:
            return
        perms = user_p.guild_permissions
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
        automod = await self.database.get_guild_collection(payload.guild_id,"automod")
        drama_channel = await find_channel(guild, self.database, "drama_channel")
        if not drama_channel or drama_channel.id != payload.channel_id:
            return
        message_entry = await automod.find_one({"drama_message": payload.message_id})
        if not message_entry:
            return
        mute_role = await find_role(guild, self.database, "mute_role")
        user_id = message_entry["user"]
        user = guild.get_member(user_id)
        moderation: Moderation = self.bot.get_cog("Moderation")
        if payload.emoji.name == "⏲️" and perms.moderate_members:
            timeouts, failed_timeouts = await moderation.perform_timeout(guild, [user], timedelta(days=27), user_p, "Drama watcher timeout.", "27d")
            if len(timeouts) > 0:
                await moderation.log_punishment("timeout", guild, user, "Drama watcher timeout", user_p)
            await asyncio.sleep(2419200)
            untimeouts, failed_untimeouts = await moderation.perform_untimeout(guild, [user], user_p, f"Automatic untimeout from timeout made 27d ago by {user_p.name} (ID: {user_p.id})")
            if len(untimeouts) > 0:
                await moderation.log_punishment("untimeout", guild, user, f"Automatic untimeout from timeout made 27d ago by {user_p.name} (ID: {user_p.id})", user_p)
        elif payload.emoji.name == "🔨" and perms.ban_members:
            await moderation.perform_ban(guild, [user], user_p, "Drama watcher ban.")
        elif payload.emoji.name == "🔇" and mute_role and perms.manage_roles:
            await self.automod_mute(moderation, guild, [user], mute_role, user_p, "Drama watcher permanent mute", None, None)
        elif payload.emoji.name == "🔊" and mute_role and perms.manage_roles:
            unmutes, failed_unmutes = await moderation.perform_unmute(guild, [user], mute_role, user_p, "Drama watcher unmute.")
            if len(unmutes) > 0:
                await moderation.log_punishment("unmute", guild, user, "Drama watcher unmute.", user_p)
        elif payload.emoji.name == "👢" and perms.kick_members:
            await moderation.perform_kick(guild, [user], user_p, "Drama watcher kick.")
        elif payload.emoji.name == "1️⃣" and mute_role and perms.manage_roles:
            await self.automod_mute(moderation, guild, [user], mute_role, user_p, "Drama-watcher 12-hour mute", timedelta(hours=12), "12h")
        elif payload.emoji.name == "2️⃣" and mute_role and perms.manage_roles:
            await self.automod_mute(moderation, guild, [user], mute_role, user_p, "Drama watcher 24-hour mute", timedelta(hours=24), "24h")
        elif payload.emoji.name == "3️⃣" and mute_role and perms.manage_roles:
            await self.automod_mute(moderation, guild, [user], mute_role, user_p, "Drama watcher 48-hour mute", timedelta(hours=48), "48h")
        elif payload.emoji.name == "❌" and perms.manage_messages:
            payload_message = await channel.fetch_message(payload.message_id)
            await payload_message.delete()
            await automod.delete_one({"message_id": payload.message_id})

async def setup(bot: commands.Bot): 
    """Sets up the Automod Cog"""
    await bot.add_cog(Automod(bot))
from datetime import datetime, timedelta
from discord.ext import commands
from typing import List, Sequence, Tuple, Union
from utility.finder import find_channel, has_valid_id
from utility.guild import Database, ordinal
from utility.permissions import channel_role_overrides, role_permissions
import discord

class Logs(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the Logs module"""
        self.bot: commands.Bot = bot
        self.database = Database(self.bot)
            
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: List[discord.Message]):
        """When messages get purged from a server, the message log will log all the messages and who sent them"""
        message_log: discord.abc.GuildChannel | discord.Thread = await find_channel(messages[0].guild, self.database, self.database.message_log)
        if not message_log:
            return
        embed = discord.Embed(color=discord.Color.brand_red(),title=f"{len(messages)} purged in {messages[0].channel.name}", timestamp = discord.utils.utcnow())
        embed.set_footer(text=f"{len(messages)} latest shown")
        for message in messages:
            if await has_valid_id(message.author, message.channel, message.guild, self.database, self.database.log_ignores):
                continue
            embed.add_field(name="",value=f"{message.author.name}: {message.content}",inline=False)
        await message_log.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """When a channel is created in a server, the server log will log the type of channel, the channel name, the category (if applicable), and the role/member overrides"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(channel.guild, self.database, self.database.server_log)
        if not server_log:
            return
        channel_type: str = channel.type.name[0].upper() + channel.type.name[1:]
        embed = discord.Embed(color=discord.Color.green(), title=f"{channel_type} channel created", timestamp=discord.utils.utcnow())
        embed.add_field(name="**Name:**", value=channel.name, inline=False)
        if not isinstance(channel, discord.CategoryChannel):
            embed.add_field(name="**Category:**", value=channel.category, inline=False)
        for role, overwrite in channel.overwrites.items():
            allowed_perms, denied_perms = await channel_role_overrides(overwrite)
            if len(allowed_perms) > 0 or len(denied_perms) > 0:
                overwrite_s: str = ""
                for perm in allowed_perms:
                    overwrite_s += f"{perm}: ✅\n"
                for perm in denied_perms:
                    overwrite_s += f"{perm}: ❌\n"
            if isinstance(role, discord.Role):
                embed.add_field(name="",value=f"**Role override for {role.mention}**\n{overwrite_s}",inline=False)
            elif isinstance(role, discord.Member):
                embed.add_field(name="",value=f"**Member override for {role.mention}**\n{overwrite_s}",inline=False)
            else:
                embed.add_field(name="",value=f"**Override for {role.id}**\n{overwrite_s}",inline=False)
        embed.set_footer(text=f"Channel ID: {channel.id}")
        await server_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """When a channel gets deleted, the server log will log the channel type, name, and category (if applicable)"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(channel.guild, self.database, self.database.server_log)
        if not server_log:
            return
        channel_type: str = channel.type.name[0].upper() + channel.type.name[1:]
        embed = discord.Embed(color=discord.Color.red(), title=f"{channel_type} channel deleted", timestamp=discord.utils.utcnow())
        embed.add_field(name="", value=f"**Name:** {channel.name}",inline=False)
        if not isinstance(channel, discord.CategoryChannel):
            embed.add_field(name="", value=f"**Category:** {channel.category}",inline=False)
        embed.set_footer(text=f"Channel ID: {channel.id}")
        await server_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """When a channel gets updated, the server log will log the channel type, new name, new category (if applicable), and new role/member overrides"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(after.guild, self.database, self.database.server_log)
        if not server_log:
            return
        embed = discord.Embed(color=discord.Color.green(), title="Channel updated")
        before_changes: list[str] = []
        after_changes: list[str] = []
        if before.name != after.name:
            before_changes.append(f"**Name:** {before.name}")
            after_changes.append(f"**Name:** {after.name}")
        if before.category != after.category and not isinstance(after, discord.CategoryChannel):
            before_changes.append(f"**Category:** {before.category}")
            after_changes.append(f"**Category:** {after.category}")
        if before_changes or after_changes:
            embed.add_field(name="Before", value="\n".join(before_changes) or "No Changes")
            embed.add_field(name="After", value="\n".join(after_changes) or "No Changes")
        sentence: str = ""
        for item, after_overwrite in after.overwrites.items():
            after_allowed, after_denied = await channel_role_overrides(after_overwrite)
            before_overwrite: discord.PermissionOverwrite = before.overwrites.get(item)
            if not before_overwrite:
                for perm in after_allowed:
                    sentence += f"{perm}: ⬜ ➜ ✅\n"
                for perm in after_denied:
                    sentence += f"{perm}: ⬜ ➜ ❌\n"
                if isinstance(item, discord.Role) or isinstance(item, discord.Member):
                    item_mention: str = item.mention 
                else:
                    item_mention: int = item.id 
                embed.add_field(name="", value=f"**Overwrites for {item.mention} in {after.mention} created**\n {sentence}", inline=False)
            elif before_overwrite != after_overwrite:
                before_allowed, before_denied = await channel_role_overrides(before_overwrite)
                covered_perms = set()
                for perm in before_allowed:
                    if perm in after_denied:
                        sentence += f"{perm}: ✅ ➜ ❌\n"
                        covered_perms.add(perm)
                    elif perm not in after_allowed and perm not in after_denied:
                        sentence += f"{perm}: ✅ ➜ ⬜\n"
                        covered_perms.add(perm)
                for perm in before_denied:
                    if perm in after_allowed:
                        sentence += f"{perm}: ❌ ➜ ✅\n"
                        covered_perms.add(perm)
                    elif perm not in after_allowed and perm not in after_denied:
                        sentence += f"{perm}: ❌ ➜ ⬜\n"
                        covered_perms.add(perm)
                for perm in after_allowed:
                    if perm not in before_allowed and perm not in covered_perms:
                        sentence += f"{perm}: ⬜ ➜ ✅\n"
                        covered_perms.add(perm)
                for perm in after_denied:
                    if perm not in before_denied and perm not in covered_perms:
                        sentence += f"{perm}: ⬜ ➜ ❌\n"
                        covered_perms.add(perm)
                if sentence:
                    if isinstance(item, discord.Role) or isinstance(item, discord.Member):
                        item_mention = str(item.mention)
                    else:
                        item_mention = item.id
                    embed.add_field(name="", value=f"**Overwrites for {item_mention} in {after.mention} updated**\n{sentence}", inline=False)
        if before_changes or after_changes or sentence != "":
            await server_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: Sequence[discord.Emoji], after: Sequence[discord.Emoji]) -> None:
        """When an emote is created, deleted, or renamed, the server log will log the following:
        Emote creations - Emote image, emote name
        Emote deletions - Emote name
        Emote updates - Old emote name, new emote name"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(guild, self.database, self.database.server_log)
        if not server_log:
            return
        before_set = set(before)
        after_set = set(after)
        added_emojis: set[discord.Emoji] = after_set - before_set
        for added_emoji in added_emojis:
            embed = discord.Embed(color=discord.Color.brand_green(),title="Emoji created",timestamp=discord.utils.utcnow())
            embed.add_field(name="",value=f"{added_emoji} {added_emoji.name}")
            embed.set_footer(text=f"Emoji ID: {added_emoji.id}")
            await server_log.send(embed=embed)
        removed_emojis: set[discord.Emoji] = before_set - after_set
        for removed_emoji in removed_emojis:
            embed = discord.Embed(color=discord.Color.brand_red(),title="Emoji deleted",timestamp=discord.utils.utcnow())
            embed.add_field(name="",value=f"{removed_emoji.name}")
            embed.set_footer(text=f"Emoji ID: {removed_emoji.id}")
            await server_log.send(embed=embed)
        updated_emojis: List[Tuple[(discord.Emoji, discord.Emoji)]] = []
        for old_emoji in before:
            for new_emoji in after:
                if old_emoji.id == new_emoji.id and old_emoji.name != new_emoji.name:
                    updated_emojis.append((old_emoji, new_emoji))
        for old_emoji, new_emoji in updated_emojis:
            embed = discord.Embed(color=discord.Color.blue(),title="Emoji renamed",timestamp=discord.utils.utcnow())
            embed.add_field(name="",value=f"{new_emoji} {old_emoji.name} ➜ {new_emoji.name}")
            embed.set_footer(text=f"Emoji ID: {new_emoji.id}")
            await server_log.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """When the bot joins a new server, it will automatically set the default configuration settings"""
        await self.database.setup_default_config(guild.id)
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        """When a role is created in the server, the server log will log the role's name, color, permissions, and whether it is mentionable and/or displayed seperately"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(role.guild, self.database, self.database.server_log)
        if not server_log:
            return
        embed = discord.Embed(color=discord.Color.brand_green(),title="New role created",timestamp=discord.utils.utcnow())
        embed.add_field(name="",value=f"**Name:** {role.name}",inline=False)
        embed.add_field(name="",value=f"**Color:** {str(role.color)}",inline=False)
        embed.add_field(name="",value=f"**Mentionable:** {role.mentionable}",inline=False)
        embed.add_field(name="",value=f"**Displayed separately:** {role.hoist}",inline=False)
        role_perms: list[str] = await role_permissions(role)
        if len(role_perms) > 0:
            embed.add_field(name="",value=f"**Permissions:** {', '.join(role_perm for role_perm in role_perms)}")
        embed.set_footer(text=f"Role ID: {role.id}")
        await server_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """When a role is deleted in the server, the server log will log the role's name, color, position, creation time, and whether it is mentionable and/or displayed seperately"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(role.guild, self.database, self.database.server_log)
        if not server_log:
            return
        current_time: datetime = discord.utils.utcnow()
        embed = discord.Embed(color=discord.Color.brand_red(),title=f"Role {role.name} removed",timestamp=current_time)
        embed.add_field(name="",value=f"**Name:** {role.name}",inline=False)
        embed.add_field(name="",value=f"**Color:** {str(role.color)}",inline=False)
        embed.add_field(name="",value=f"**Mentionable:** {role.mentionable}",inline=False)
        embed.add_field(name="",value=f"**Displayed separately:** {role.hoist}",inline=False)
        embed.add_field(name="",value=f"**Position:** {role.position}",inline=False)
        embed.add_field(name="",value=f"Created {discord.utils.format_dt(current_time, 'R')}",inline=False)
        embed.set_footer(text=f"Role ID: {role.id}")
        await server_log.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        """When a role is updated in the server, the server log will log the new name, color, added permissions, removed permissions, and if it can or can no longer be mentioned"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(after.guild, self.database, self.database.server_log)
        if not server_log:
            return
        before_changes: List[str] = [f"**Name:** {before.name}"] if before.name != after.name else []
        after_changes: List[str] = [f"**Name:** {after.name}"] if after.name != before.name else []
        before_changes = before_changes + [f"**Mentionable:** {before.mentionable}"] if before.mentionable != after.mentionable else before_changes
        after_changes = after_changes + [f"**Mentionable:** {after.mentionable}"] if after.mentionable != before.mentionable else after_changes
        before_changes = before_changes + [f"**Color:** {str(before.color)}"] if before.color != after.color else before_changes
        after_changes = after_changes + [f"**Color:** {str(after.color)}"] if after.color != before.color else after_changes
        before_perms: List[str] = await role_permissions(before)
        after_perms: List[str] = await role_permissions(after)
        added_perms: list[str] = []
        removed_perms: list[str] = []
        for perm_b in before_perms:
            for perm_a in after_perms:
                if perm_a not in before_perms:
                    added_perms.append(perm_a)
                if perm_b not in after_perms:
                    removed_perms.append(perm_b)
        sentence_a: str = "**Added:** " + ", ".join(perm for perm in added_perms)
        sentence_r: str = "**Removed: **" + ", ".join(perm for perm in removed_perms)
        if len(added_perms) > 0 and len(removed_perms) > 0:
            sentence: str = sentence_a + "\n" + sentence_r
        elif len(added_perms) == 0 and len(removed_perms) > 0:
            sentence = sentence_r
        elif len(added_perms) > 0 and len(removed_perms) == 0:
            sentence = sentence_a
        else:
            sentence = ""
        embed = discord.Embed(color=discord.Color.blue(), title=f"Role '{after.name}' Updated",timestamp=discord.utils.utcnow())
        if before_changes:
            embed.add_field(name="Before", value="\n".join(before_changes) or "No changes", inline=True)
        if after_changes:
            embed.add_field(name="After", value="\n".join(after_changes) or "No changes", inline=True)
        if sentence != "":
            embed.add_field(name="New permissions",value=sentence,inline=False)
        if len(embed.fields) > 0:
            embed.set_footer(text=f"Role ID: {after.id}")
            await server_log.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild: discord.Guild, before: Sequence[discord.GuildSticker], after: Sequence[discord.GuildSticker]):
        """When a sticker is created, deleted, or renamed, the server log will log the following:
        Sticker creations - Sticker image, sticker name, sticker emoji, sticker description
        Emote deletions - Sticker name
        Emote updates - Old sticker name, new sticker name, old sticker emoji, new sticker emoji, old sticker description, new sticker description"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(guild, self.database, self.database.server_log)
        if not server_log:
            return
        before_set = set(before)
        after_set = set(after)
        added_stickers: set[discord.GuildSticker] = after_set - before_set
        for added_sticker in added_stickers:
            embed = discord.Embed(color=discord.Color.brand_green(),title="Sticker created",timestamp=discord.utils.utcnow())
            embed.add_field(name="Name:",value=f"{added_sticker.name}",inline=False)
            embed.add_field(name="Description:",value=added_sticker.description,inline=False)
            try:
                emote: discord.Emoji = await guild.fetch_emoji(int(added_sticker.emoji))
                emote_os = str(emote)
            except Exception:
                emote_os = "Unknown Emote"
            embed.add_field(name="Related Emoji:",value=emote_os,inline=False)
            embed.set_image(url=added_sticker.url)
            embed.set_footer(text=f"Sticker ID: {added_sticker.id}")
            await server_log.send(embed=embed)
        removed_stickers: set[discord.GuildSticker] = before_set - after_set
        for removed_sticker in removed_stickers:
            embed = discord.Embed(color=discord.Color.brand_red(),title="Sticker deleted",timestamp=discord.utils.utcnow())
            embed.add_field(name="",value=f"{removed_sticker.name}")
            embed.set_footer(text=f"Sticker ID: {removed_sticker.id}")
            await server_log.send(embed=embed)
        updated_stickers: List[Tuple[(discord.GuildSticker, discord.GuildSticker)]] = []
        for old_sticker in before:
            for new_sticker in after:
                if old_sticker.id == new_sticker.id:
                    if old_sticker.name != new_sticker.name or old_sticker.emoji != new_sticker.emoji or old_sticker.description != new_sticker.description:
                        updated_stickers.append((old_sticker, new_sticker))
        for old_sticker, new_sticker in updated_stickers:
            embed = discord.Embed(color=discord.Color.blue(),title="Sticker updated",timestamp=discord.utils.utcnow())
            if old_sticker.name != new_sticker.name:
                embed.add_field(name="",value=f"{old_sticker.name} ➜ {new_sticker.name}",inline=False)
            if old_sticker.emoji != new_sticker.emoji and old_sticker.emoji.isnumeric():
                if old_sticker.emoji.isnumeric():
                    try:
                        emote = await guild.fetch_emoji(int(old_sticker.emoji))
                        emote_os = str(emote)
                    except Exception:
                        emote_os = "Unknown Emote"
                else:
                    emote_os: str = old_sticker.emoji
                if new_sticker.emoji.isnumeric():
                    try:
                        emote_n: discord.Emoji = await guild.fetch_emoji(int(new_sticker.emoji))
                        emote_ns = str(emote_n)
                    except Exception:
                        emote_ns = "Unknown Emote"
                else:
                    emote_ns: str = new_sticker.emoji
                embed.add_field(name="Related Emoji:",value=f"{emote_os} ➜ {emote_ns}",inline=False)
            if old_sticker.description != new_sticker.description:
                embed.add_field(name="Description:",value=f"{old_sticker.description} ➜ {new_sticker.description}",inline=False)
            embed.set_footer(text=f"Sticker ID: {new_sticker.id}")
            await server_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        """When the server is updated, the server log will log the new name, the new AFK timeout amount, the new verification level, and the new icon"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(after, self.database, self.database.server_log)
        if not server_log:
            return
        embed = discord.Embed(color=discord.Color.blue(),title="Server Updated",timestamp=discord.utils.utcnow())
        before_changes: List[str] = [f"**Name:** {before.name}"] if before.name != after.name else []
        after_changes: List[str] = [f"**Name:** {after.name}"] if after.name != before.name else []
        values: dict[int, str] = {60: "1 minute",300: "5 minutes",900: "15 minutes",1800: "30 minutes",3600: "1 hour",}
        before_changes = before_changes + [f"**AFK timeout:** {values[before.afk_timeout]}"] if before.afk_timeout != after.afk_timeout else before_changes
        after_changes = after_changes + [f"**AFK timeout:** {values[after.afk_timeout]}"] if after.afk_timeout != before.afk_timeout else after_changes
        name_b: str = before.afk_channel.name if before.afk_channel and before.afk_channel != after.afk_channel else "None"
        name_a: str = after.afk_channel.name if after.afk_channel and after.afk_channel != before.afk_channel else "None"
        before_changes = before_changes + [f"**AFK Channel:** {name_b}"] if name_b != "None" else before_changes
        after_changes = after_changes + [f"**AFK Channel:** {name_a}"] if name_a != "None" else after_changes
        before_changes = before_changes + [f"**Verification Level:** {before.verification_level.name}"] if before.verification_level != after.verification_level else before_changes
        after_changes = after_changes + [f"**Verification Level:** {after.verification_level.name}"] if after.verification_level != before.verification_level else after_changes
        if len(before_changes) > 0:
            changes_b: str = "\n".join(change for change in before_changes)
            embed.add_field(name="Before",value=changes_b)
        if len(after_changes) > 0:
            changes_a: str = "\n".join(change for change in after_changes)
            embed.add_field(name="After",value=changes_a)
        if before.icon != after.icon:
            embed.add_field(name="New icon",value="",inline=False)
            embed.set_image(url=after.icon.url)
        await server_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite) -> None:
        """When an invite is created in the server, the server log will log the invite code and who created the invite"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(invite.guild, self.database, self.database.server_log)
        if not server_log:
            return
        embed = discord.Embed(color=discord.Color.brand_green(), title="Invite created")
        embed.add_field(name="",value=f"**Code:** {invite.code}",inline=False)
        embed.add_field(name="",value=f"**Created By:** {invite.inviter}",inline=False)
        embed.set_footer(text=f"ID: {invite.id}")
        await server_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite) -> None:
        """When an invite is deleted in the server, the server log will log the invite code and who created the invite (If possible)"""
        server_log: discord.abc.GuildChannel | discord.Thread = await find_channel(invite.guild, self.database, self.database.server_log)
        if not server_log:
            return
        embed = discord.Embed(color=discord.Color.brand_red(), title="Invite deleted")
        embed.add_field(name="",value=f"**Code:** {invite.code}",inline=False)
        embed.add_field(name="",value=f"**Uses:** {invite.uses}",inline=False)
        embed.set_footer(text=f"ID: {invite.id}")
        await server_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.Member, discord.User]) -> None:
        """When a member gets banned from the server, the member log will log the user's name, avatar, and ID"""
        member_log: discord.abc.GuildChannel | discord.Thread = await find_channel(guild, self.database, self.database.member_log)
        if not member_log:
            return
        embed = discord.Embed(color=discord.Color.brand_red(),title="Member banned",timestamp=discord.utils.utcnow())
        embed.set_author(name=user.name, icon_url=user.avatar.url)
        embed.add_field(name="",value=user.mention)
        embed.set_footer(text=f"ID: {user.id}")
        await member_log.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """When a member joins the server, the join-leave-log will log the user's name, avatar, their join # (They're the nth to join), creation date, and ID"""
        join_leave_log: discord.abc.GuildChannel | discord.Thread = await find_channel(member.guild, self.database, self.database.join_leave_log)
        if not join_leave_log:
            return
        embed = discord.Embed(color=discord.Color.brand_green(),title="Member joined",timestamp=discord.utils.utcnow())
        embed.set_author(name=member.name, icon_url=member.avatar.url)
        ordinal_num: str = await ordinal(member.guild.member_count)
        embed.add_field(name="",value=f"{member.mention} {ordinal_num} to join\ncreated {discord.utils.format_dt(member.created_at, 'R')}")
        embed.set_footer(text=f"ID: {member.id}")
        await join_leave_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """When a member leaves the server, the join-leave-log will log the user's name, avatar, mention, join time, roles prior to leaving, and ID"""
        join_leave_log: discord.abc.GuildChannel | discord.Thread = await find_channel(member.guild, self.database, self.database.join_leave_log)
        if not join_leave_log:
            return
        embed = discord.Embed(color=discord.Color.brand_green(),title="Member left",timestamp=discord.utils.utcnow())
        embed.set_author(name=member.name, icon_url=member.avatar.url)
        embed.add_field(name="",value=f"{member.mention} joined {discord.utils.format_dt(member.joined_at, 'R')}",inline=False)
        tr: List[str] = [role.name for role in member.roles if role != member.guild.default_role]
        if len(tr) > 0:
            embed.add_field(name="",value=f"**Roles:** {', '.join(t for t in tr)}",inline=False)
        embed.set_footer(text=f"ID: {member.id}")
        await join_leave_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        """When a user gets unbanned from the server, the member log will log the user's name, avatar, mention, and ID"""
        member_log: discord.abc.GuildChannel | discord.Thread = await find_channel(guild, self.database, self.database.member_log)
        if not member_log:
            return
        embed = discord.Embed(color=discord.Color.blue(),title="Member unbanned",timestamp=discord.utils.utcnow())
        embed.set_author(name=user.name, icon_url=user.avatar.url)
        embed.add_field(name="",value=user.mention)
        embed.set_footer(text=f"ID: {user.id}")
        await member_log.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """When a member updates their roles or gets timed out/removed from timeout, the member log will log the following:
        Role updates - Added roles, removed roles, user's name, avatar, ID
        Role additions - Added roles, user's name, avatar, ID
        Role removals - Removed roles, user's name, avatar, ID
        User timeouts - User's name, avatar, ID
        User untimeouts - User's name, avatar, ID"""
        member_log: discord.abc.GuildChannel | discord.Thread = await find_channel(after.guild, self.database, self.database.member_log)
        if not member_log:
            return
        removed_roles: list[str] = []
        added_roles: list[str] = []
        for role in before.roles:
            if role not in after.roles:
                removed_roles.append(role.mention)
        for role in after.roles:
            if role not in before.roles:
                added_roles.append(role.mention)
        if len(added_roles) > 0 and len(removed_roles) > 0:
            embed = discord.Embed(color = discord.Color.blurple(),title="Roles updated",timestamp=discord.utils.utcnow())
            embed.set_author(name=after.name, icon_url=after.avatar.url)
            added_role_list: str = ", ".join(role for role in added_roles)
            removed_role_list: str = ", ".join(role for role in removed_roles)
            embed.add_field(name="",value=f"**Added:** {added_role_list}")
            embed.add_field(name="",value=f"**Removed:** {removed_role_list}")
            embed.set_footer(text=f"ID: {after.id}")
            await member_log.send(embed=embed)
        elif len(added_roles) > 0 and len(removed_roles) <= 0:
            item: str = "Role" if len(added_roles) <= 1 else "Roles"
            embed = discord.Embed(color=discord.Color.blurple(),title=f"{item} added", timestamp=discord.utils.utcnow())
            embed.set_author(name=after.name, icon_url=after.avatar.url)
            embed.add_field(name="",value=", ".join(role for role in added_roles))
            embed.set_footer(text=f"ID: {after.id}")
            await member_log.send(embed=embed)
        elif len(added_roles) <= 0 and len(removed_roles) > 0:
            item = "Role" if len(removed_roles) <= 1 else "Roles"
            embed = discord.Embed(color=discord.Color.blurple(),title=f"{item} removed", timestamp=discord.utils.utcnow())
            embed.set_author(name=after.name, icon_url=after.avatar.url)
            embed.add_field(name="",value=", ".join(role for role in removed_roles))
            embed.set_footer(text=f"ID: {after.id}")
            await member_log.send(embed=embed)
        if not before.is_timed_out() and after.is_timed_out():
            embed = discord.Embed(color=discord.Color.orange(),title="Member timeout",timestamp=discord.utils.utcnow())
            embed.set_author(name=after.name, icon_url=after.avatar.url)
            embed.add_field(name="",value=after.mention)
            embed.set_footer(text=f"ID: {after.id}")
            await member_log.send(embed=embed)
            await discord.utils.sleep_until(after.timed_out_until + timedelta(seconds=10))
            if not after.is_timed_out():
                embed = discord.Embed(color=discord.Color.yellow(),title="Member removed from timeout",timestamp=discord.utils.utcnow())
                embed.set_author(name=after.name, icon_url=after.avatar.url)
                embed.add_field(name="",value=after.mention)
                embed.set_footer(text=f"ID: {after.id}")
                await member_log.send(embed=embed)
        elif before.is_timed_out() and not after.is_timed_out():
            embed = discord.Embed(color=discord.Color.yellow(),title="Member removed from timeout",timestamp=discord.utils.utcnow())
            embed.set_author(name=after.name, icon_url=after.avatar.url)
            embed.add_field(name="",value=after.mention)
            embed.set_footer(text=f"ID: {after.id}")
            await member_log.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """When a message gets deleted from a server, the message log will log the author's name, avatar, and ID, the channel's name, the message's content, message ID, and all attachments if possible"""
        if message.author.bot or await has_valid_id(message.author, message.channel, message.guild, self.database, self.database.log_ignores):
            return
        message_log: discord.abc.GuildChannel | discord.Thread = await find_channel(message.guild, self.database, self.database.message_log)
        if not message_log:
            return
        embed = discord.Embed(color=discord.Color.brand_red(),title=f"Message deleted in {message.channel.name}",timestamp=discord.utils.utcnow())
        embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
        embed.add_field(name="",value=message.content + f"\n\nMessage ID: {message.id}")
        embed.set_footer(text=f"ID: {message.author.id}")
        if message.attachments:
            filenames: str = ", ".join(attachment.filename for attachment in message.attachments)
            embed.add_field(name="Attachments",value=f"{filenames}")
        await message_log.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """When a message gets edited in the server, the message log will log the channel's name, the user's name, avatar, and ID, and the message's old vs new content and URL"""
        if before.author.bot or before.content == after.content or await has_valid_id(after.author, after.channel, after.guild, self.database, self.database.log_ignores):
            return
        message_log: discord.abc.GuildChannel | discord.Thread = await find_channel(after.guild, self.database, self.database.message_log)
        if not message_log:
            return
        embed = discord.Embed(color=discord.Color.blue(),title=f"Message edited in {after.channel.name}",url=after.jump_url,timestamp=discord.utils.utcnow())
        embed.set_author(name=after.author.name, icon_url=after.author.avatar.url)
        before_content: str = before.content if len(before.content) <= 1024 else before.content[:1010] + "..."
        after_content: str = after.content if len(after.content) <= 1024 else after.content[:1021] + "..."
        embed.add_field(name="", value=f"**Before:**\n{before_content}", inline=False)
        embed.add_field(name="", value=f"**After:**\n{after_content}", inline=False)
        embed.set_footer(text=f"ID: {after.author.id}")
        await message_log.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """When a user joins, leaves, or moves voice channels, the voice log will log the following:
        VC joins - user's name, avatar, ID, voice channel's name
        VC leaves - user's name, avatar, ID, voice channel's name
        VC moves - user's name, avatar, ID, before channel's name, after channel's name"""
        voice_log: discord.abc.GuildChannel | discord.Thread = await find_channel(member.guild, self.database, self.database.voice_log)
        if not voice_log:
            return
        if not before.channel and after.channel:
            embed = discord.Embed(color=discord.Color.brand_green(),title="Member joined voice channel",timestamp=discord.utils.utcnow())
            embed.set_author(name=member.name, icon_url=member.avatar.url)
            embed.add_field(name="",value=f"**{member.name}** joined {after.channel.name}")
            embed.set_footer(text=f"ID: {member.id}")
            await voice_log.send(embed=embed)
        if before.channel and not after.channel:
            embed = discord.Embed(color=discord.Color.brand_red(),title="Member left voice channel",timestamp=discord.utils.utcnow())
            embed.set_author(name=member.name, icon_url=member.avatar.url)
            embed.add_field(name="",value=f"**{member.name}** left {before.channel.name}")
            embed.set_footer(text=f"ID: {member.id}")
            await voice_log.send(embed=embed)
        if before.channel and after.channel and before.channel != after.channel:
            embed = discord.Embed(color=discord.Color.brand_green(),title="Member changed voice channel",timestamp=discord.utils.utcnow())
            embed.set_author(name=member.name, icon_url=member.avatar.url)
            embed.add_field(name="",value=f"**Before:** {before.channel.name}",inline=False)
            embed.add_field(name="",value=f"**After:** {after.channel.name}",inline=False)
            embed.set_footer(text=f"ID: {member.id}")
            await voice_log.send(embed=embed)

async def setup(bot: commands.Bot) -> None: 
    """Sets up the Logs Cog"""
    await bot.add_cog(Logs(bot))
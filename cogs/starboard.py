from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Any, Tuple, Union
from utility.finder import find_channel, find_int, has_valid_id
from utility.guild import Database
import discord

GUILD_ID = "guild_id"
ORIGINAL_MESSAGE_ID = "original_message_id"
STARBOARD_MESSAGE_ID = "starboard_message_id"
STAR_EMOJI = "⭐"

class Starboard(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the Starboard module"""
        self.bot: commands.Bot = bot
        self.database = Database(self.bot)

    async def build_starboard_embed(self, message: discord.Message, star_count: int) -> Tuple[str, discord.Embed]:
        """Builds the embed for when a post should be starboarded"""
        default_emote: discord.Emoji | str = await self.get_default_emote(message.guild.id)
        if isinstance(default_emote, discord.Emoji):
            custom_emoji: discord.Emoji = message.guild.get_emoji(default_emote.id)
            default_emote = str(custom_emoji) if custom_emoji else STAR_EMOJI
        embed = discord.Embed(color=discord.Color.gold(), timestamp=message.created_at)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        embed.add_field(name="",value=message.content if len(message.content) <= 1024 else message.content[:1024],inline=False)
        embed.add_field(name="Source", value=f"[Jump!]({message.jump_url})", inline=False)
        embed.set_footer(text=message.id)
        first_image = True
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith("image/"):
                if first_image:
                    embed.set_image(url=attachment.url)
                    first_image = False
                else:
                    embed.add_field(name="Additional Image", value=f"[View Image]({attachment.url})", inline=False)
            else:
                embed.add_field(name="Attachment", value=f"[{attachment.filename}]({attachment.url})", inline=False)
        content: str = f"{default_emote} **{star_count}** {message.channel.mention}"
        return content, embed
    
    async def get_default_emote(self, guild_id: int) -> Union[discord.Emoji, str]:
        """Grabs the default starboard emote for a given server."""
        default_emote: int | str = await self.database.get_config(guild_id, self.database.default_emote)
        if not default_emote:
            return STAR_EMOJI
        if isinstance(default_emote, str):
            return default_emote
        emoji: discord.Emoji = self.bot.get_emoji(default_emote)
        return emoji if emoji else STAR_EMOJI
    
    async def get_star_count(self, message: discord.Message) -> int:
        """Gets the number of reactions/\"stars\" that a message has"""
        default_emote: discord.Emoji | str = await self.get_default_emote(message.guild.id)
        reactions: discord.Reaction = discord.utils.get(message.reactions, emoji=default_emote)
        return reactions.count if reactions else 0
    
    async def handle_star_reaction(self, reaction: discord.Reaction, guild: discord.Guild) -> None:
        """Determines if a post has the necessary number of reactions/\"stars\" to be posted to the starboard"""
        message: discord.Message = reaction.message
        star_count: int = await self.get_star_count(message)
        star_threshold: int = await find_int(guild, self.database, self.database.star_threshold)
        if star_threshold and star_count >= star_threshold:
            await self.post_to_starboard(message, star_count)

    async def post_to_starboard(self, message: discord.Message, star_count: int) -> None:
        """Posts the message to the starboard and inserts the relevant information into the database"""
        starboard_channel: discord.abc.GuildChannel | discord.Thread = await find_channel(message.guild, self.database, self.database.starboard_channel)
        if not starboard_channel:
            return
        starboard_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(message.guild.id, self.database.starboard)
        entry: Any = await starboard_collection.find_one({ORIGINAL_MESSAGE_ID: message.id})
        content, embed = await self.build_starboard_embed(message, star_count)
        starboard_message = await starboard_channel.fetch_message(entry[STARBOARD_MESSAGE_ID]) if entry else await starboard_channel.send(content=content, embed=embed)
        await starboard_message.edit(content=content, embed=embed) if entry else await starboard_collection.insert_one({ORIGINAL_MESSAGE_ID: message.id, STARBOARD_MESSAGE_ID: starboard_message.id, GUILD_ID: message.guild.id})
    
    async def remove_starboard_message(self, message_id: int, guild: discord.Guild) -> None:
        """Removes a post from the starboard"""
        starboard_channel: discord.abc.GuildChannel | discord.Thread = await find_channel(guild, self.database, self.database.starboard_channel)
        if not starboard_channel:
            return
        starboard_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(guild.id, self.database.starboard)
        entry: Any = await starboard_collection.find_one({ORIGINAL_MESSAGE_ID: message_id})
        if not entry:
            return
        try:
            starboard_message_id: int = entry[STARBOARD_MESSAGE_ID]
            starboard_message: discord.Message = await starboard_channel.fetch_message(starboard_message_id)
            await starboard_message.delete()
            await starboard_collection.delete_one({STARBOARD_MESSAGE_ID: starboard_message_id})
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """If a message that is starred gets deleted, the associated starboard post should also be deleted"""
        starboard_channel: discord.abc.GuildChannel | discord.Thread = await find_channel(message.guild, self.database, self.database.starboard_channel)
        if not starboard_channel:
            return
        starboard_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(message.guild.id, self.database.starboard)
        entry: Any = await starboard_collection.find_one({ORIGINAL_MESSAGE_ID: message.id})
        if entry:
            try:
                starboard_message = await starboard_channel.fetch_message(entry[STARBOARD_MESSAGE_ID])
                await starboard_message.delete()
                await starboard_collection.delete_one({STARBOARD_MESSAGE_ID: starboard_message.id})
            except Exception:
                pass
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """If a message that is starred gets edited, the associated starboard post should also be edited"""
        starboard_channel: discord.abc.GuildChannel | discord.Thread = await find_channel(after.guild, self.database, self.database.starboard_channel)
        if not starboard_channel:
            return
        starboard_collection: AsyncIOMotorCollection = await self.database.get_guild_collection(after.guild.id, self.database.starboard)
        entry: Any = await starboard_collection.find_one({ORIGINAL_MESSAGE_ID: before.id})
        if entry:
            starboard_message: discord.Message = await starboard_channel.fetch_message(entry[STARBOARD_MESSAGE_ID])
            default_emote: discord.Emoji | str = await self.get_default_emote(after.guild.id)
            star_count: int = sum(1 for r in after.reactions if r.emoji == default_emote)
            content, embed = await self.build_starboard_embed(after, star_count)
            await starboard_message.edit(content=content,embed=embed)
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]) -> None:
        """When a reaction is made on a post, it will check if the reaction was the default star emote, and then determines if the post should be posted to starboard"""
        if not await find_int(user.guild, self.database, self.database.star_threshold) or reaction.message.author == user or await has_valid_id(user, reaction.message.channel, reaction.message.guild, self.database, self.database.starboard_blacklist) or await has_valid_id(reaction.message.author, reaction.message.channel, reaction.message.guild, self.database, self.database.starboard_blacklist):
            return
        default_emote: discord.Emoji | str = await self.get_default_emote(user.guild.id)
        if type(default_emote) == type(reaction.emoji) and reaction.emoji == default_emote:
            await self.handle_star_reaction(reaction, user.guild)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]) -> None:
        """When a reaction is removed on a post, it should determine if that post should stay up due to the number of reactions, and if so, edits the post to reflect the number of stars. If not, it will delete the starboard post."""
        star_threshold: int = await self.database.get_config(user.guild.id, self.database.star_threshold)
        if not star_threshold or star_threshold <= 0 or reaction.message.author == user or await has_valid_id(user, reaction.message.channel, reaction.message.guild, self.database, self.database.starboard_blacklist) or await has_valid_id(reaction.message.author, reaction.message.channel, reaction.message.guild, self.database, self.database.starboard_blacklist):
            return
        default_emote: discord.Emoji | str = await self.get_default_emote(user.guild.id)
        if type(default_emote) == type(reaction.emoji) and reaction.emoji == default_emote:
            await self.remove_starboard_message(reaction.message.id, user.guild) if sum(1 for r in reaction.message.reactions if str(r.emoji) == str(reaction.emoji)) < star_threshold else await self.handle_star_reaction(reaction, user.guild)

async def setup(bot: commands.Bot) -> None:
    """Sets up the Starboard Cog"""
    await bot.add_cog(Starboard(bot))

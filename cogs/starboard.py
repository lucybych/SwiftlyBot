import discord
from discord.ext import commands
from typing import Union
from utility.finder import find_channel, find_int, has_valid_id
from utility.guild import Database

class Starboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Starboard module"""
        self.bot = bot
        self.database = Database(self.bot)

    async def build_starboard_embed(self, message: discord.Message, star_count: int):
        """Builds the embed for when a post should be starboarded"""
        default_emote = await self.get_default_emote(message.guild.id)
        if isinstance(default_emote, discord.Emoji):
            custom_emoji = message.guild.get_emoji(default_emote.id)
            if custom_emoji:
                default_emote = str(custom_emoji)
            else:
                default_emote = "⭐"
        embed = discord.Embed(color=discord.Color.gold(), description=message.content,timestamp=message.created_at)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
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
        content = f"{default_emote} **{star_count}** {message.channel.mention}"
        return content, embed
    
    async def get_default_emote(self, guild_id: int):
        """Grabs the default starboard emote for a given server."""
        default_emote = await self.database.get_config(guild_id, "default_emote")
        if not default_emote:
            return "⭐"
        if isinstance(default_emote, str):
            return default_emote
        emote = self.bot.get_emoji(default_emote)
        return emote if emote else "⭐"
    
    async def get_star_count(self, message: discord.Message):
        """Gets the number of reactions/\"stars\" that a message has"""
        default_emote = await self.get_default_emote(message.guild.id)
        star_reaction = discord.utils.get(message.reactions, emoji=default_emote)
        return star_reaction.count if star_reaction else 0
    
    async def handle_star_reaction(self, reaction: discord.Reaction, guild: discord.Guild):
        """Determines if a post has the necessary number of reactions/\"stars\" to be posted to the starboard"""
        message = reaction.message
        star_count = await self.get_star_count(reaction.message)
        star_threshold = await find_int(guild, self.database, "star_threshold")
        if star_threshold and star_count >= star_threshold:
            await self.post_to_starboard(message, star_count)

    async def post_to_starboard(self, message: discord.Message, star_count: int):
        """Posts the message to the starboard and inserts the relevant information into the database"""
        starboard_channel = await find_channel(message.guild, self.database, "starboard_channel")
        if not starboard_channel:
            return
        starboard = await self.database.get_guild_collection(message.guild.id, "starboard")
        existing_starboard_message = await starboard.find_one({"original_message_id": message.id})
        if existing_starboard_message:
            starboard_message = await starboard_channel.fetch_message(existing_starboard_message["starboard_message_id"])
            content, embed = await self.build_starboard_embed(message, star_count)
            await starboard_message.edit(content=content,embed=embed)
        else:
            content, embed = await self.build_starboard_embed(message, star_count)
            starboard_message = await starboard_channel.send(content=content,embed=embed)
            starboard.insert_one({"original_message_id": message.id, "starboard_message_id": starboard_message.id, "guild_id": message.guild.id})
    
    async def remove_starboard_message(self, message_id: int, guild: discord.Guild):
        """Removes a post from the starboard"""
        starboard_channel = await find_channel(guild, self.database, "starboard_channel")
        if not starboard_channel:
            return
        starboard_config = await self.database.get_guild_collection(guild.id, "starboard")
        starboard_entry = await starboard_config.find_one({"original_message_id": message_id})
        if not starboard_entry:
            return
        try:
            starboard_message_id = starboard_entry["starboard_message_id"]
            starboard_message = await starboard_channel.fetch_message(starboard_message_id)
            await starboard_message.delete()
            await starboard_config.delete_one({"starboard_message_id": starboard_message_id})
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """If a message that is starred gets deleted, the associated starboard post should also be deleted"""
        starboard_channel = await find_channel(message.guild, self.database, "starboard_channel")
        if not starboard_channel:
            return
        starboard = await self.database.get_guild_collection(message.guild.id, "starboard")
        existing_starboard_message = await starboard.find_one({"original_message_id": message.id})
        if existing_starboard_message:
            try:
                starboard_message = await starboard_channel.fetch_message(existing_starboard_message["starboard_message_id"])
                await starboard_message.delete()
                await starboard.delete_one({"starboard_message_id": starboard_message.id})
            except Exception:
                pass
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """If a message that is starred gets edited, the associated starboard post should also be edited"""
        starboard_channel = await find_channel(after.guild, self.database, "starboard_channel")
        if not starboard_channel:
            return
        starboard = await self.database.get_guild_collection(after.guild.id, "starboard")
        existing_starboard_message = await starboard.find_one({"original_message_id": before.id})
        if existing_starboard_message:
            starboard_message = await starboard_channel.fetch_message(existing_starboard_message["starboard_message_id"])
            default_emote = await self.get_default_emote(after.guild.id)
            star_count = sum(1 for r in after.reactions if r.emoji == default_emote)
            content, embed = await self.build_starboard_embed(after, star_count)
            await starboard_message.edit(content=content,embed=embed)
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
        """When a reaction is made on a post, it will check if the reaction was the default star emote, and then determines if the post should be posted to starboard"""
        if not await find_int(user.guild, self.database, "star_threshold"):
            return
        if reaction.message.author == user:
            return
        if not await has_valid_id(user, reaction.message.channel, reaction.message.guild, self.database, "starboard_blacklist") or not await has_valid_id(reaction.message.author, reaction.message.channel, reaction.message.guild, self.database, "starboard_blacklist"):
            return
        default_emote = await self.get_default_emote(user.guild.id)
        if type(default_emote) == type(reaction.emoji) and reaction.emoji == default_emote:
            await self.handle_star_reaction(reaction, user.guild)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
        """When a reaction is removed on a post, it should determine if that post should stay up due to the number of reactions, and if so, edits the post to reflect the number of stars. If not, it will delete the starboard post."""
        threshold = await self.database.get_config(user.guild.id, "star_threshold")
        if not threshold or threshold <= 0:
            return
        if reaction.message.author == user:
            return
        if not await has_valid_id(user, reaction.message.channel, reaction.message.guild, self.database, "starboard_blacklist") or not await has_valid_id(reaction.message.author, reaction.message.channel, reaction.message.guild, self.database, "starboard_blacklist"):
            return
        default_emote = await self.get_default_emote(user.guild.id)
        if type(default_emote) == type(reaction.emoji) and reaction.emoji == default_emote:
            if sum(1 for r in reaction.message.reactions if str(r.emoji) == str(reaction.emoji)) < threshold:
                await self.remove_starboard_message(reaction.message.id, user.guild)
            else:
                await self.handle_star_reaction(reaction, user.guild)

async def setup(bot: commands.Bot):
    """Sets up the Starboard Cog"""
    await bot.add_cog(Starboard(bot))

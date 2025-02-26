from datetime import timedelta
from discord import File
from discord.ext import commands
from io import BytesIO
from PIL import Image
from PIL.ImageFile import ImageFile
from typing import Annotated, List, Union
import aiohttp
import asyncio
import discord
import io

CATEGORY = "category"
DEFAULT_NAME = "new-channel"
DEFAULT_ROLE = "new role"
FORMAT = "PNG"
FORUM = "forum"
STAGE = "stage"
TEXT = "text"
VOICE = "voice"

class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the Utility module"""
        self.bot: commands.Bot = bot
    
    @commands.command()
    @commands.has_permissions(manage_expressions=True)
    async def addemoji(self, ctx: commands.Context, emoji_name: str, link) -> None:
        """Adds emoji from given link with the given name."""
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                if response.status == 200:
                    image_data: bytes = await response.read()
                    try:
                        emoji: discord.Emoji = await ctx.guild.create_custom_emoji(name=emoji_name, image=image_data)
                        await ctx.send(f"Emoji '{str(emoji)}' added with the name \"{emoji_name}!\"")
                    except Exception:
                        await ctx.send(f"Failed to add emoji.")
                else:
                    await ctx.send("Failed to retrieve image from the link. Please make sure the URL is valid.")
    @addemoji.error
    async def on_addemoji_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid name and link.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to add emotes to this server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_expressions=True)
    async def addsticker(self, ctx: commands.Context, sticker_name: str, link, emoji: Union[str,discord.Emoji], description: str = "") -> None:
        """Adds a sticker with the given name, link, and description"""
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                if response.status == 200:
                    image_data: bytes = await response.read()
                    image: ImageFile = Image.open(BytesIO(image_data))
                    if image.format != FORMAT:
                        with BytesIO() as png_image:
                            image.save(png_image, format=FORMAT)
                            png_image.seek(0)
                            file = File(png_image, filename="sticker.png")
                    else:
                        file = File(BytesIO(image_data), filename="sticker.png")
                    try:
                        await ctx.guild.create_sticker(name=sticker_name, description=description, emoji=emoji, file=file)
                        await ctx.send(f"Sticker '{sticker_name}' added successfully!")
                    except Exception as e:
                        await ctx.send(f"Failed to add sticker: {e}")
                else:
                    await ctx.send("Failed to retrieve image from the link. Make sure the URL is valid.")
    @addsticker.error
    async def on_addsticker_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid name, link, and description, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to add stickers to this server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def avatar(self, ctx: commands.Context, members: commands.Greedy[discord.Member]) -> None:
        """Displays the given user(s) global profile and server profile, or the command user's profile(s)"""
        members = [ctx.author] if len(members) == 0 else members
        for member in members:
            if member.display_avatar:
                await ctx.send(f"User global profile: {member.display_avatar.url}")
            if member.guild_avatar:
                await ctx.send(f"User server profile: {member.guild_avatar.url}")
    @avatar.error
    async def on_avatar_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is valid user(s) found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.group(invoke_without_command=True)
    async def channel(self, ctx: commands.Context) -> None:
        await ctx.send("Available subcommands: `clone`, `create`, `delete`")

    @channel.command(name="clone")
    @commands.has_permissions(manage_channels=True)
    async def channelclone(self, ctx: commands.Context, channel: discord.abc.GuildChannel,*, channel_name: str = DEFAULT_NAME) -> None:
        """Clones a channel into a new channel with the given name"""
        await channel.clone(name=channel_name)
        await ctx.send(f"Channel **{channel.name}** cloned into **{channel_name}**")
    @channelclone.error
    async def on_channelclone_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel and name, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have the necessary permissions to clone channels.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @channel.command(name="create")
    @commands.has_permissions(manage_channels=True)
    async def channelcreate(self, ctx: commands.Context, channel_name = DEFAULT_NAME, type: Annotated[str, lambda s: s.lower()] = TEXT) -> discord.Message | None:
        """Creates a new channel of the given type with the given name"""
        if type == TEXT:
            await ctx.guild.create_text_channel(name=channel_name)
        elif type == VOICE:
            await ctx.guild.create_voice_channel(name=channel_name)
        elif type == FORUM:
            await ctx.guild.create_forum(name=channel_name)
        elif type == STAGE:
            await ctx.guild.create_stage_channel(name=channel_name)
        elif type == CATEGORY:
            await ctx.guild.create_category(name=channel_name)
        else:
            return await ctx.send("Invalid channel type. Ensure that the channel type is specified as text, voice, forum, stage, or category")
        await ctx.send(f"Successfully created new {type} channel with name **{channel_name}**.")
    @channelcreate.error
    async def on_channelcreate_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel name and type (text, voice, forum, stage, or category).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to create channels.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel type (text, voice, forum, stage, category).") 
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @channel.command(name="delete")
    @commands.has_permissions(manage_channels=True)
    async def channeldelete(self, ctx: commands.Context, channels: commands.Greedy[discord.abc.GuildChannel]) -> None:
        """Deletes given channel(s)."""
        for channel in channels:
            channel_name: str = channel.name
            await channel.delete()
            await ctx.send(f"Successfully removed channel **{channel_name}**")
    @channeldelete.error
    async def on_channeldelete_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to delete channels.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @channel.command(name="name")
    @commands.has_permissions(manage_channels=True)
    async def channelname(self, ctx: commands.Context, channel: discord.abc.GuildChannel, *, channel_name: str = DEFAULT_NAME) -> discord.Message | None: 
        """Renames a given channel to the given new name."""
        if not isinstance(channel, (discord.abc.GuildChannel)):
            return await ctx.send("Sorry, I can't edit the name of this type of channel.")
        old_name: str = channel.name
        await channel.edit(name=channel_name) 
        await ctx.send(f"**{old_name}** successfully changed to **{channel_name}**")
    @channelname.error
    async def on_channelname_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel and name, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to rename channels.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def check(self, ctx: commands.Context) -> None:
        """Gives some general information about a server, such as number of members, roles, and channels."""
        await ctx.send(f"Some Server Info:\n- Members: {ctx.guild.member_count}\n- Roles: {len(ctx.guild.roles) - 1}\n- Channels: {len(ctx.guild.channels) - len(ctx.guild.categories)}")
    @check.error
    async def on_check_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?check")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def echo(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str) -> None:
        """\"Echoes\" a message from one channel to another."""
        await channel.send(message)
        await ctx.message.add_reaction("✅")
    @echo.error
    async def on_echo_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid text channel and message.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use the echo command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel found in the server and message.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def inrole(self, ctx: commands.Context, role: discord.Role) -> discord.Message | None:
        """Determine how many users are in the given role, and dumps a text file with their username(s) and user ID(s)."""
        if len(role.members) == 0:
            return await ctx.send("Role has no members to dump.")
        user_list: str = "\n".join([f"{index + 1}. {member.name} ({member.id})" for index, member in enumerate(role.members)])
        await ctx.send(file=discord.File(io.BytesIO(user_list.encode('utf-8')), f"{role.name}_members.txt"))
    @inrole.error
    async def on_inrole_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid role.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use the inrole command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(mention_everyone=True)
    async def multiping(self, ctx: commands.Context, role1: discord.Role, role2: discord.Role) -> None:
        """Creates a new temporary role, adds all users who have the given role1 or role2 to that new role, and mentions the role, before deleting it."""
        role_name: str = role1.name + role2.name
        role_name = role_name if len(role_name) <= 32 else role_name[:32]
        multiping_role: discord.Role = await ctx.guild.create_role(name=role_name)
        members: list[discord.Member] = [member for member in role1.members] + [member for member in role2.members if role1 not in member.roles]
        for member in members:
            await member.add_roles(multiping_role)
        await ctx.send(multiping_role.mention)
        await asyncio.sleep(10)
        await multiping_role.delete()
    @multiping.error
    async def on_multiping_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include two valid roles.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ping users with at least one of multiple roles.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that both roles are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    @commands.has_permissions(change_nickname=True)
    async def nick(self, ctx: commands.Context, name: str) -> None:
        await ctx.author.edit(nick=name)
        await ctx.send(f"{ctx.author.mention}'s nickname has been changed to {name}!")
    
    @commands.command()
    async def poll(self, ctx: commands.Context, duration: int, multiple: bool, question: str, *answers: str) -> discord.Message | None:
        """Creates a poll with the given question, duration (hours), and answers"""
        if not 1 <= duration:
            return await ctx.send("Poll duration must be at least 1 hour")
        duration = 96 if duration > 96 else duration
        if len(answers) < 1 or len(answers) > 10:
            return await ctx.send("You must provide between 1 and 10 answers for the poll.")
        poll = discord.Poll(question=question, duration=timedelta(hours=duration), multiple=multiple, layout_type=discord.PollLayoutType.default)
        for answer in answers:
            poll.add_answer(text=answer)
        await ctx.send(poll=poll)
        await ctx.send(f"Poll created by {ctx.author.mention}! It will end in {duration} hours.")

    @commands.command()
    async def qpoll(self, ctx: commands.Context, *, question: str) -> None:
        """Creates a quick poll with simple yes or no answers"""
        message: discord.Message = await ctx.send(f"**{ctx.author.name}** asks: {question}")
        await message.add_reaction("👍")
        await message.add_reaction("👎")

    @commands.group(invoke_without_command=True)
    async def role(self, ctx: commands.Context) -> None:
        await ctx.send("Available subcommands: `clone`, `color`, `delete`")
    
    @role.command(name="add", aliases=['sr', 'setrole'])
    @commands.has_permissions(manage_roles=True)
    async def roleadd(self, ctx: commands.Context, role: discord.Role, members: commands.Greedy[discord.Member]) -> None:
        """Adds the given role to the given user(s)"""
        s_adds: List[discord.Member] = []
        f_adds: List[discord.Member] = []
        for member in members:
            try:
                await member.add_roles(role)
                s_adds.append(member)
            except Exception:
                f_adds.append(member)
        if len(s_adds) > 0:
            await ctx.send(f"Added **{role.name}** to {', '.join(user.name for user in s_adds)}.")
        if len(f_adds) > 0:
            await ctx.send(f"Failed to add **{role.name}** to {', '.join(user.name for user in f_adds)}.")
    @roleadd.error
    async def on_roleadd_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid role and user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to add roles to users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role and user(s) found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    @role.command(name="clone")
    @commands.has_permissions(manage_roles=True)
    async def roleclone(self, ctx: commands.Context, role: discord.Role,*, role_name: str = DEFAULT_ROLE) -> None:
        """Clones a role into a new role with the given name (or default if no name is provided)."""
        if len(role_name) > 32:
            role_name = role_name[:32]
        new_role: discord.Role = await ctx.guild.create_role(name=role_name,permissions=role.permissions,colour=role.colour,hoist=role.hoist,mentionable=role.mentionable,reason=f"Role cloned by {ctx.author} from {role.name}")
        await new_role.edit(position=role.position)
        await ctx.send(f"✅ Successfully cloned role **'{role.name}'** to **'{role_name}'**")
    @roleclone.error
    async def on_roleclone_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid role and name, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to clone roles.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role and name.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to perform this action.")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Failed to clone role.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    @role.command(name="color")
    @commands.has_permissions(manage_roles=True)
    async def rolecolor(self, ctx: commands.Context, roles: commands.Greedy[discord.Role], role_color: discord.Color = discord.Color.default()) -> None:
        """Changes the color of given role(s) to the given new color, or default if no color is provided."""
        for role in roles:
            color: discord.Colour = role.color
            await role.edit(color=role_color)
            embed = discord.Embed(color=role_color, title="Role color changed")
            embed.add_field(name="",value=f"{role.mention} had its color changed from {color} to {role_color}")
            await ctx.send(embed=embed)
    @rolecolor.error
    async def on_rolecolor_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid role and color, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to change role colors.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role and color.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    @role.command(name="create")
    @commands.has_permissions(manage_roles=True)
    async def rolecreate(self, ctx: commands.Context, role_name: str = DEFAULT_ROLE, role_color: discord.Color = discord.Color.default()) -> None:
        """Creates a new role with the given name and color, or default if no name/color is provided"""
        role_name = role_name if len(role_name) <= 32 else role_name[:32]
        role: discord.Role = await ctx.guild.create_role(name=role_name,color=role_color)
        embed = discord.Embed(color=role_color,title="Success!")
        embed.add_field(name="",value=f"The role **{role.name}** has been created.\n**Color:** {role.color}\n**Mentionable:** {role.mentionable}\n**Shown Separately:** {role.hoist}",inline=False)
        embed.set_footer(text=role.id)
        await ctx.send(embed=embed)
    @rolecreate.error
    async def on_createrole_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid name, if necessary, and color, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to create roles.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid name and color.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @role.command(name="delete")
    @commands.has_permissions(manage_roles=True)
    async def deleterole(self, ctx: commands.Context, roles: commands.Greedy[discord.Role]) -> None:
        """Deletes given role(s), if it exists/they exist."""
        for role in roles:
            role_color: discord.Colour = role.color
            role_name: str = role.name
            await role.delete()
            embed = discord.Embed(color=role_color,title="Success!")
            embed.add_field(name="",value=f"The role {role_name} has been Removed.",inline=False)
            await ctx.send(embed=embed)
    @deleterole.error
    async def on_deleterole_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid role.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to delete roles.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @role.command(name="in")
    @commands.has_permissions(manage_roles=True)
    async def rolein(self, ctx: commands.Context, role1: discord.Role, role2: discord.Role) -> discord.Message | None:
        """Adds role2 to all members in role1, if they do not already have role2."""
        num_s_adds = 0
        num_f_adds = 0
        for member in role1.members:
            if role2 not in member.roles:
                try:
                    await member.add_roles(role2)
                    num_s_adds += 1
                except Exception:
                    num_f_adds += 1
                    continue
        if num_s_adds == 0 and num_f_adds == 0:
            return await ctx.send(f"There are no members with the role {role1.name}")
        embed = discord.Embed(color=discord.Color.brand_green(),title="Success")
        if num_s_adds > 0:
            embed.add_field(name="",value=f"Added {role2.mention} to {num_s_adds} {'members' if num_s_adds != 1 else 'member'}.")
        if num_f_adds > 0:
            embed.add_field(name="",value=f"Failed to add {role2.mention} to {num_f_adds} {'members' if num_f_adds != 1 else 'member'}.")
        await ctx.send(embed=embed)
    @rolein.error
    async def on_rolein_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include two valid roles.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use rolein (Must have Manage Roles).")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it both roles are valid and found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @role.command(name="info")
    async def roleinfo(self, ctx: commands.Context, role: discord.Role) -> None:
        embed = discord.Embed(title="Role info", color=role.color)
        embed.add_field(name="",value=f"Name: {role.name}")
        embed.add_field(name="",value=f"Members: {len(role.members)}")
        embed.add_field(name="",value=f"Color: {str(role.color)}")
        return
     
    @role.command(name="name")
    @commands.has_permissions(manage_roles=True)
    async def rolename(self, ctx: commands.Context, role: discord.Role, *, role_name: str = DEFAULT_ROLE) -> None:
        """Changes the name of the given role to the given new name."""
        role_name = role_name if len(role_name) <= 32 else role_name[:32]
        old_role_name: str = role.name
        await role.edit(name=role_name)
        embed = discord.Embed(color=role.color, title="Role name changed")
        embed.add_field(name="",value=f"{role.mention} had its name changed from **{old_role_name}** to **{role_name}**")
        await ctx.send(embed=embed)
    @rolename.error
    async def on_rolename_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a role and name, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to change a role's name.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role found in the server and name.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
    
    @role.command(name="rall")
    @commands.has_permissions(manage_roles=True)
    async def rolerall(self, ctx: commands.Context, roles: commands.Greedy[discord.Role]) -> None:
        """Removes all members from the given role(s)"""
        for role in roles:
            num_members = 0
            for member in role.members:
                try:
                    await member.remove_roles(role)
                    num_members += 1
                except Exception:
                    pass
            await ctx.send(f"Removed **{role.name}** from {num_members} members.")
    @rolerall.error
    async def on_rolerall_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid role(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to remove all members from specific roles.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that all roles are valid and found in the server.")
        else:
           await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
             
    @role.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def roleremove(self, ctx: commands.Context, role: discord.Role, members: commands.Greedy[discord.Member]) -> None:
        """Removes the given role from the given user(s)"""
        s_removals: List[discord.Member] = []
        f_removals: List[discord.Member] = []
        for member in members:
            try:
                if role in member.roles:
                    await member.remove_roles(role)
                    s_removals.append(member)
                else:
                    f_removals.append(role)
            except Exception:
                f_removals.append(member)
        if len(s_removals) > 0:
            await ctx.send(f"Removed **{role.name}** from {'**, **'.join(member.name for member in s_removals)}.")
        if len(f_removals) > 0:
            await ctx.send(f"Failed to remove **{role.name}** from {'**, **'.join(member.name for member in f_removals)}.")
    @roleremove.error
    async def on_roleremove_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid role and user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to remove roles from users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that the role/user(s) are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @role.command(name="removeall")
    @commands.has_permissions(manage_roles=True)
    async def roleremoveall(self, ctx: commands.Context, members: commands.Greedy[discord.Member]) -> None:
        """Removes all roles from the given user(s)."""
        for member in members:
            for role in member.roles:
                if role != member.guild.default_role:
                    try:
                        await member.remove_roles(role)
                    except Exception:
                        pass
        embed = discord.Embed(color=discord.Color.brand_green(),title="Success")
        embed.add_field(name="",value=f"Removed all roles from {'**, **'.join(member.name for member in members)}.")
        await ctx.send(embed=embed)
    @roleremoveall.error
    async def on_roleremoveall_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to remove all roles from users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @role.command(name="rin")
    @commands.has_permissions(manage_roles=True)
    async def rolerin(self, ctx: commands.Context, role1: discord.Role, role2: discord.Role) -> None:
        """Removes role2 from all members in role1, if they have both roles."""
        num_s_removes = 0
        num_f_removes = 0
        for member in role1.members:
            if role2 in member.roles:
                try:
                    await member.remove_roles(role2)
                    num_s_removes += 1
                except Exception:
                    num_f_removes += 1
                    pass
        embed = discord.Embed(color=discord.Color.brand_green(),title="Success")
        if num_s_removes == 0 and num_f_removes == 0:
            await ctx.send(f"There are no members with the role {role1.name}")
        if num_s_removes > 0:
            embed.add_field(name="",value=f"Removed {role2.mention} from {num_s_removes} {'members' if num_s_removes != 1 else 'member'}.")
        if num_f_removes > 0:
            embed.add_field(name="",value=f"Failed to remove {role2.mention} from {'members' if num_f_removes != 1 else 'member'}.")
        await ctx.send(embed=embed)
    @rolerin.error
    async def on_rolerin_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include two valid roles.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use rolerin (Must have Manage Roles).")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that both roles are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def seeemote(self, ctx: commands.Context, emoji: discord.Emoji) -> None:
        await ctx.send(f"Name: {emoji.name}, Emoji: {str(emoji)}, Link: {emoji.url}")
    
    @commands.command()
    async def serverinfo(self, ctx: commands.Context) -> None:
        """Displays information about the server (features, boost level, number of channels, etc.)"""
        guild: discord.Guild | None = ctx.guild  
        voice_channels_num: int = len(guild.voice_channels)
        num_members: int = len([member for member in guild.members if not member.bot])
        num_bots: int = ctx.guild.member_count - num_members
        verification_levels: dict[discord.VerificationLevel, str] = {discord.VerificationLevel.none: "None", discord.VerificationLevel.low: "Low", discord.VerificationLevel.medium: "Medium", discord.VerificationLevel.high: "High (╯°□°）╯︵  ┻━┻", discord.VerificationLevel.highest: "Extreme ┻━┻ミ＼(≧ﾛ≦＼)"}
        embed = discord.Embed(title=f"Info for {guild.name}", color=discord.Color.blue(),timestamp=guild.created_at)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Owner", value=guild.owner.name, inline=True)
        embed.add_field(name="Features", value="\n".join([f"✅ {feature.replace('_', ' ').title()}" for feature in guild.features]) if len(guild.features) > 0 else "None", inline=True)
        embed.add_field(name="Boosts", value=f"Level {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)
        embed.add_field(name="Channels", value=f"💬 {len(guild.text_channels)} ({len([channel for channel in guild.text_channels if not channel.permissions_for(guild.default_role).read_messages])} locked)\n"
                                               f"🔊 {voice_channels_num} ({len([channel for channel in guild.voice_channels if not channel.permissions_for(guild.default_role).connect])} locked)", inline=True)
        embed.add_field(name="Info", value=f"Verification level: {verification_levels[guild.verification_level]}\n[Icon Link]({guild.icon.url if guild.icon else 'No Link'})", inline=True)
        embed.add_field(name="Members", value=f"Total: {guild.member_count}\nHumans: {num_members}\nBots: {num_bots}", inline=True)
        embed.add_field(name="Roles", value=f"{len(guild.roles)} roles", inline=True)
        embed.set_footer(text=f"ID: {guild.id}, Created")
        await ctx.send(embed=embed)
    @serverinfo.error
    async def on_serverinfo_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?serverinfo")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['changetemp', 'temperature', 'changetemperature', 'ct'])
    async def temp(self, ctx: commands.Context, temp: Annotated[str, lambda s: s.upper()]) -> None:
        """Converts the given temperature to Celsius (C) if Farenheit (F) is given, and vice versa."""
        if temp[-1] == 'C':
            temp_c = float(temp[:-1])
            temp_f: float = (temp_c * 9/5) + 32
            await ctx.send(f"{temp_c}°C is {temp_f:.2f}°F")
        elif temp[-1] == 'F':
            temp_f = float(temp[:-1])
            temp_c: float = (temp_f - 32) * 5/9
            await ctx.send(f"{temp_f}°F is {temp_c:.2f}°C")
        else:
            raise commands.UserInputError
    @temp.error
    async def on_temp_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid temperature.")
        elif isinstance(error, commands.UserInputError):
            await ctx.send("Invalid temperature input. Make sure that the temperature ends in 'C' or 'F' (Case insensitive)")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    async def userid(self, ctx: commands.Context, user: discord.User) -> None:
        await ctx.send(user.id)
    @userid.error
    async def on_userid_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.UserNotFound):
            await ctx.send("User cannot be found (They must be available in the server)")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    async def userinfo(self, ctx: commands.Context, members: commands.Greedy[discord.Member]) -> None:
        """Displays information about given user(s) (username, ID, number of roles, account creation/join date, etc.), or command user if none is provided"""
        members = [ctx.author] if len(members) == 0 else members
        for member in members:
            try:
                await ctx.send(f"**__User info for {member.mention}:__**\n- **Name:** {member.name}\n- **# of Roles:** {len(member.roles)}\n- **User ID:** {member.id}\n- **Created:** {discord.utils.format_dt(member.created_at, 'R')}\n- **Joined:** {discord.utils.format_dt(member.joined_at, 'R')}\n- **Name Color:** {member.color}\n- **Avatar Link:** {member.avatar.url}")
            except Exception:
                await ctx.send(f"Could not find information for user {member.name}")
                pass
    @userinfo.error
    async def on_userinfo_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
async def setup(bot: commands.Bot): 
    """Sets up the Utility Cog"""
    await bot.add_cog(Utility(bot))
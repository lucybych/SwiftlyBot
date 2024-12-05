import aiohttp
import asyncio
import discord
from discord import File
from discord.ext import commands
import io
from io import BytesIO
from PIL import Image
from typing import List, Literal, Optional

class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the Utility module"""
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(manage_expressions=True)
    async def addemoji(self, ctx: commands.Context, name: str, link):
        """ Adds emoji from given link with the given name. """
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                if response.status == 200:
                    image_data = await response.read()
                    try:
                        await ctx.guild.create_custom_emoji(name=name, image=image_data)
                        await ctx.send(f"Emoji '{name}' added successfully!")
                    except Exception as e:
                        await ctx.send(f"Failed to add emoji: {e}")
                else:
                    await ctx.send("Failed to retrieve image from the link. Please make sure the URL is valid.")
    @addemoji.error
    async def on_addemoji_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid name and link.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to add emotes to this server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_expressions=True)
    async def addsticker(self, ctx: commands.Context, name: str, link, emoji: discord.Emoji, description: Optional[str]):
        """Adds a sticker with the given name, link, and description"""
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image = Image.open(BytesIO(image_data))
                    if image.format != "PNG":
                        with BytesIO() as png_image:
                            image.save(png_image, format="PNG")
                            png_image.seek(0)
                            file = File(png_image, filename="sticker.png")
                    else:
                        file = File(BytesIO(image_data), filename="sticker.png")
                    try:
                        await ctx.guild.create_sticker(name=name, description=description, emoji=emoji, file=file)
                        await ctx.send(f"Sticker '{name}' added successfully!")
                    except Exception as e:
                        await ctx.send(f"Failed to add sticker: {e}")
                else:
                    await ctx.send("Failed to retrieve image from the link. Make sure the URL is valid.")
    @addsticker.error
    async def on_addsticker_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid name, link, and description, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to add stickers to this server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def avatar(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        """ Displays the given user(s) global profile and server profile, if applicable """
        users = [ctx.author] if len(users) == 0 else users
        for user in users:
            if user.display_avatar:
                await ctx.send(f"User global profile: {user.display_avatar.url}")
            if user.guild_avatar:
                await ctx.send(f"User server profile: {user.guild_avatar.url}")
    @avatar.error
    async def on_avatar_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is valid user(s) found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def channelclone(self, ctx: commands.Context, channel: discord.abc.GuildChannel,*, newchannel: str = "new-channel"):
        """ Clones a channel into a new channel with the given name """
        await channel.clone(name=newchannel)
        await ctx.send(f"Channel **{channel.name}** cloned into **{newchannel}**")
    @channelclone.error
    async def on_channelclone_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel and name, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have the necessary permissions to clone channels.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def channelcreate(self, ctx: commands.Context, channelname: str, type: str):
        """ Creates a new channel of the given type with the given name """
        if type.lower() == 'text':
            await ctx.guild.create_text_channel(name=channelname)
        elif type.lower() == 'voice':
            await ctx.guild.create_voice_channel(name=channelname)
        elif type.lower() == 'forum':
            await ctx.guild.create_forum(name=channelname)
        elif type.lower() == 'stage':
            await ctx.guild.create_stage_channel(name=channelname)
        elif type.lower() == 'category':
            await ctx.guild.create_category(name=channelname)
        else:
            await ctx.send("Invalid channel type. Ensure that the channel type is specified as text, voice, forum, stage, or category")
            return
        await ctx.send(f"Successfully created new {type} channel with name **{channelname}**.")
    @channelcreate.error
    async def on_channelcreate_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel name and type (text, voice, forum, stage, or category).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to create channels.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel type (text, voice, forum, stage, category).") 
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def channeldelete(self, ctx: commands.Context, channel: discord.abc.GuildChannel):
        """ Deletes a given channel. """
        name = channel.name
        await channel.delete()
        await ctx.send(f"Successfully removed channel **{name}**")
    @channeldelete.error
    async def on_channeldelete_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to delete channels.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def channelname(self, ctx: commands.Context, channel: discord.abc.GuildChannel, *, newname: str = "new-channel"): 
        """ Renames a given channel to the given new name. """
        if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel, discord.StageChannel, discord.ForumChannel)):
            old_name = channel.name
            await channel.edit(name=newname) 
            await ctx.send(f"**{old_name}** successfully changed to **{newname}**")
        else:
            await ctx.send("Sorry, I can't edit the name of this type of channel.")
    @channelname.error
    async def on_channelname_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel and name, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to rename channels.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def check(self, ctx: commands.Context):
        """ Gives some general information about a server, such as number of members, roles, and channels. """
        await ctx.send(f"Some Server Info:\n- Members: {ctx.guild.member_count}\n- Roles: {len(ctx.guild.roles)}\n- Channels: {len(ctx.guild.channels)}")
    @check.error
    async def on_check_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?check")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def createrole(self, ctx: commands.Context, name: str = "new role", color: discord.Color = discord.Color.default()):
        """ Creates a new role with the given name and color, or default if no color is provided"""
        new_role = await ctx.guild.create_role(name=name,color=color)
        embed = discord.Embed(color=color,title="Success!")
        embed.add_field(name="",value=f"The role **{new_role.name}** has been created.\n**Color:** {new_role.color}\n**Mentionable:** {new_role.mentionable}\n**Shown Separately:** {new_role.hoist}",inline=False)
        embed.set_footer(text=new_role.id)
        await ctx.send(embed=embed)
    @createrole.error
    async def on_createrole_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid name, if necessary, and color, if necessary.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to create roles.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid name and color.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def deleterole(self, ctx: commands.Context, role: discord.Role):
        """ Deletes a given role, if it exists. """
        color = role.color
        name = role.name
        await role.delete()
        embed = discord.Embed(color=color,title="Success!")
        embed.add_field(name="",value=f"The role {name} has been Removed.",inline=False)
        await ctx.send(embed=embed)
    @deleterole.error
    async def on_deleterole_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid role.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to delete roles.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def echo(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        """ \"Echoes\" a message from one channel to another. """
        await channel.send(message)
        await ctx.message.add_reaction("✅")
    @echo.error
    async def on_echo_error(self, ctx: commands.Context, error):
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
    async def inrole(self, ctx: commands.Context, role: discord.Role):
        """ Determine how many users are in the given role, and dumps a text file with their username(s) and user ID(s). """
        members: List[discord.Member] = [member for member in ctx.guild.members if role in member.roles]
        if len(members) == 0:
            await ctx.send("Role has no members to dump.")
            return
        user_list = "\n".join([f"{index + 1}. {member.name} ({member.id})"
                               for index, member in enumerate(members)])
        file = io.BytesIO(user_list.encode('utf-8'))
        file_name = f"{role.name}_members.txt"
        await ctx.send(file=discord.File(file, file_name))
    @inrole.error
    async def on_inrole_error(self, ctx: commands.Context, error):
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
    async def multiping(self, ctx: commands.Context, role1: discord.Role, role2: discord.Role):
        """Creates a new temporary role, adds all users who have the given role1 or role2 to that new role, and mentions the role, before deleting it. """
        new_name = role1.name + role2.name
        if len(new_name) > 32:
            new_name = new_name[:32]
        multiping_role = await ctx.guild.create_role(name=new_name)
        for member in ctx.guild.members:
            if role1 in member.roles or role2 in member.roles:
                await member.add_roles(multiping_role)
        await ctx.send(multiping_role.mention)
        await asyncio.sleep(10)
        await multiping_role.delete()
    @multiping.error
    async def on_multiping_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include two valid roles.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ping users with at least one of multiple roles.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that both roles are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['sr','setrole'])
    @commands.has_permissions(manage_roles=True)
    async def roleadd(self, ctx: commands.Context, role: discord.Role, users: commands.Greedy[discord.Member]):
        """ Adds the given role to the given user(s) """
        role_added_to: List[discord.Member] = []
        failed_addition: List[discord.Member] = []
        for user in users:
            try:
                await user.add_roles(role)
                role_added_to.append(user)
            except Exception:
                failed_addition.append(user)
        if len(role_added_to) > 0:
            success_message = "**, **".join(x.name for x in role_added_to)
            await ctx.send(f"Added **{role.name}** to {success_message}.")
        if len(failed_addition) > 0:
            failed_message = "**, **".join(x.name for x in failed_addition)
            await ctx.send(f"Failed to add **{role.name}** to {failed_message}.")
    @roleadd.error
    async def on_roleadd_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid role and user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to add roles to users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role and user(s) found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def roleclone(self, ctx: commands.Context, role: discord.Role,*, newrole: str = "new role"):
        """ Clones a role into a new role with the given name. """
        new_role = await ctx.guild.create_role(name=newrole,permissions=role.permissions,colour=role.colour,hoist=role.hoist,mentionable=role.mentionable,reason=f"Role cloned by {ctx.author} from {role.name}")
        await new_role.edit(position=role.position)
        await ctx.send(f"✅ Successfully cloned role **'{role.name}'** to **'{newrole}'**")
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
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rolecolor(self, ctx: commands.Context, role: discord.Role, color: discord.Color = discord.Color.default()):
        """ Changes the color of given role to the given new color. """
        old_color = role.color
        await role.edit(color=color)
        embed = discord.Embed(color=color, title="Role color changed")
        embed.add_field(name="",value=f"{role.mention} had its color changed from {old_color} to {color}")
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
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rolein(self, ctx: commands.Context, role1: discord.Role, role2: discord.Role):
        """ Adds role2 to all members in role1, if they do not already have role2. """
        num_members = 0
        num_failed_members = 0 
        for member in ctx.guild.members:
            if role1 in member.roles and role2 not in member.roles:
                try:
                    await member.add_roles(role2)
                    num_members += 1
                except Exception:
                    num_failed_members += 1
                    continue
        embed = discord.Embed(color=discord.Color.brand_green(),title="Success")
        message_s = "members" if num_members != 1 else "member"
        message_f = "members" if num_failed_members != 1 else "member"
        if num_members > 0:
            embed.add_field(name="",value=f"Added {role2.mention} to {num_members} {message_s}.")
        if num_failed_members > 0:
            embed.add_field(name="",value=f"Failed to add {role2.mention} to {num_failed_members} {message_f}.")
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
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rolename(self, ctx: commands.Context, role: discord.Role, *, name: str = "new role"):
        """ Changes the name of the given role to the given new name. """
        old_name = role.name
        await role.edit(name=name)
        embed = discord.Embed(color=role.color, title="Role name changed")
        embed.add_field(name="",value=f"{role.mention} had its name changed from **{old_name}** to **{name}**")
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
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rolerall(self, ctx: commands.Context, roles: commands.Greedy[discord.Role]):
        """ Removes all members from the given role(s) """
        for role in roles:
            num_members = 0
            for member in ctx.guild.members:
                if role in member.roles:
                    try:
                        await member.remove_roles(role)
                        num_members += 1
                    except Exception:
                        pass
            await ctx.send(f"Removed **{role.name}** from {num_members} members.")
    @rolerall.error
    async def on_rolerall_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid role(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to remove all members from specific roles.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that all roles are valid and found in the server.")
        else:
           await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
             
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def roleremove(self, ctx: commands.Context, role: discord.Role, users: commands.Greedy[discord.Member]):
        """ Removes the given role from the given user(s) """
        role_removed_from: List[discord.Member] = []
        failed_removal: List[discord.Member] = []
        for user in users:
            try:
                await user.remove_roles(role)
                role_removed_from.append(user)
            except Exception:
                failed_removal.append(user)
        if len(role_removed_from) > 0:
            success_message = "**, **".join(x.name for x in role_removed_from)
            await ctx.send(f"Removed **{role.name}** from {success_message}.")
        if len(failed_removal) > 0:
            failed_message = "**, **".join(x.name for x in failed_removal)
            await ctx.send(f"Failed to remove **{role.name}** from {failed_message}.")
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
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def roleremoveall(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        """ Removes all roles from the given user(s). """
        for user in users:
            for role in user.roles:
                if role.name != "@everyone":
                    try:
                        await user.remove_roles(role)
                    except Exception:
                        pass
        message = "**, **".join(x.name for x in users)
        embed = discord.Embed(color=discord.Color.brand_green(),title="Success")
        embed.add_field(name="",value=f"Removed all roles from {message}.")
        await ctx.send(embed=embed)
    @roleremoveall.error
    async def on_roleremoveall_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to remove all roles from users.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rolerin(self, ctx: commands.Context, role1: discord.Role, role2: discord.Role):
        """ Removes role2 from all members in role1, if they have role2. """
        num_members = 0
        num_failed_members = 0
        for member in ctx.guild.members:
            if role1 in member.roles and role2 not in member.roles:
                try:
                    await member.remove_roles(role2)
                    num_members += 1
                except Exception:
                    num_failed_members += 1
                    pass
        embed = discord.Embed(color=discord.Color.brand_green(),title="Success")
        message_s = "members" if num_members != 1 else "member"
        message_f = "members" if num_failed_members != 1 else "member"
        if num_members > 0:
            embed.add_field(name="",value=f"Removed {role2.mention} from {num_members} {message_s}.")
        if num_failed_members > 0:
            embed.add_field(name="",value=f"Failed to remove {role2.mention} from {num_failed_members} {message_f}.")
        await ctx.send(embed=embed)
    @rolerin.error
    async def on_rolerin_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include two valid roles.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use rolerin (Must have Manage Roles).")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that both roles are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def serverinfo(self, ctx: commands.Context):
        """ Displays information about the server (features, boost level, number of channels, etc.) """
        guild = ctx.guild  
        voice_channels = len(guild.voice_channels)
        humans = len([member for member in guild.members if not member.bot])
        bots = ctx.guild.member_count - humans
        verification_levels = {discord.VerificationLevel.none: "None", discord.VerificationLevel.low: "Low", discord.VerificationLevel.medium: "Medium", discord.VerificationLevel.high: "High (╯°□°）╯︵  ┻━┻", discord.VerificationLevel.highest: "Extreme ┻━┻ミ＼(≧ﾛ≦＼)"}
        embed = discord.Embed(title=f"Info for {guild.name}", color=discord.Color.blue(),timestamp=guild.created_at)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Owner", value=guild.owner.name, inline=True)
        embed.add_field(name="Features", value="\n".join([f"✅ {feature.replace('_', ' ').title()}" for feature in guild.features]) if len(guild.features) > 0 else "None", inline=True)
        embed.add_field(name="Boosts", value=f"Level {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)
        embed.add_field(name="Channels", value=f"💬 {len(guild.text_channels)} ({len([channel for channel in guild.text_channels if not channel.permissions_for(guild.default_role).read_messages])} locked)\n"
                                               f"🔊 {voice_channels} ({len([channel for channel in guild.voice_channels if not channel.permissions_for(guild.default_role).connect])} locked)", inline=True)
        embed.add_field(name="Info", value=f"Verification level: {verification_levels[guild.verification_level]}\n[Icon Link]({guild.icon.url})", inline=True)
        embed.add_field(name="Members", value=f"Total: {guild.member_count}\nHumans: {humans}\nBots: {bots}", inline=True)
        embed.add_field(name="Roles", value=f"{len(guild.roles)} roles", inline=True)
        embed.set_footer(text=f"ID: {guild.id}, Created")
        await ctx.send(embed=embed)
    @serverinfo.error
    async def on_serverinfo_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?serverinfo")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['changetemp', 'temperature', 'changetemperature', 'ct'])
    async def temp(self, ctx: commands.Context, temp: str):
        """ Converts the given temperature to Celsius (C) if Farenheit (F) is given, and vice versa. """
        if temp[-1].upper() == 'C':
            temp_c = float(temp[:-1])
            temp_f = (temp_c * 9/5) + 32
            await ctx.send(f"{temp_c}°C is {temp_f:.2f}°F")
        elif temp[-1].upper() == 'F':
            temp_f = float(temp[:-1])
            temp_c = (temp_f - 32) * 5/9
            await ctx.send(f"{temp_f}°F is {temp_c:.2f}°C")
        else:
            raise commands.UserInputError
    @temp.error
    async def on_temp_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid temperature.")
        elif isinstance(error, commands.UserInputError):
            await ctx.send("Invalid temperature input. Make sure that the temperature ends in 'C' or 'F' (Case insensitive)")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def userinfo(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        """ Displays information about given user(s) (username, ID, number of roles, account creation/join date, etc.) """
        users = [ctx.author] if len(users) == 0 else users
        for user in users:
            try:
                await ctx.send(f"**__User info for {user.mention}:__**\n- **Name:** {user.name}\n- **# of Roles:** {len(user.roles)}\n- **User ID:** {user.id}\n- **Created:** {discord.utils.format_dt(user.created_at, 'R')}\n- **Joined:** {discord.utils.format_dt(user.joined_at, 'R')}\n- **Name Color:** {user.color}\n- **Avatar Link:** {user.avatar.url}")
            except Exception:
                await ctx.send(f"Could not find information for user {user.name}")
                pass
    @userinfo.error
    async def on_userinfo_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include valid user(s).")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that all users are valid and in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
async def setup(bot: commands.Bot): 
    """Sets up the Utility Cog"""
    await bot.add_cog(Utility(bot))
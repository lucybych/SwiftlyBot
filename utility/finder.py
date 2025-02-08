from typing import List, Union
from utility.guild import Database, parse_time_string
import discord

async def find_bool(guild: discord.Guild, database: Database, type: str):
    """Finds a boolean value in a database and returns True or False depending on the configuration and type."""
    bool_val = await database.get_config(guild.id, type)
    return bool_val

async def find_channel(guild: discord.Guild, database: Database, type: str):
    """Finds a Discord channel and returns the channel or nothing depending on the configuration and type."""
    channel_id = await database.get_config(guild.id, type)
    if not channel_id or channel_id == 0:
        return None
    try:
        channel = await guild.fetch_channel(channel_id)
        return channel
    except Exception:
         return None
    
async def find_int(guild: discord.Guild, database: Database, type: str):
    """Finds a number and returns said number or nothing depending on the configuration and type."""
    num = await database.get_config(guild.id, type)
    if not num or num <= 0:
        return None
    return num
    
async def find_role(guild: discord.Guild, database: Database, type: str):
    """Finds a role and returns said role or nothing depending on the configuration and type."""
    roleid = await database.get_config(guild.id, type)
    if not roleid or roleid == 0:
        return None
    try:
        roles = await guild.fetch_roles()
        for roler in roles:
            if roler.id == roleid:
                return roler
        return None
    except Exception:
        return None

async def find_str(guild: discord.Guild, database: Database, type: str):
    """Finds a string/text and returns said string/text or nothing depending on the configuration and type."""
    string = await database.get_config(guild.id, type)
    if not string or string == "":
        return None
    return string

async def find_time(guild: discord.Guild, database: Database, type: str):
    """Finds a time string/text and returns said time or nothing depending on the configuration and type."""
    time = await database.get_config(guild.id, type)
    if not time or time == "0s":
        return None
    time_amount = await parse_time_string(time)
    return time_amount

async def has_roles(user: discord.Member, roles: List[int]):
    """Checks role IDs and determines if a given user has one or more of such roles."""
    for role in user.roles:
        if role.id in roles:
            return True
    return False

async def has_valid_id(user: discord.Member, channel: discord.abc.GuildChannel, guild: discord.Guild, database: Database, type: str):
    """Checks if either a user or a channel is within an ID list configuration (Usually used for white or blacklists)"""
    id_list = await database.get_config(guild.id, type)
    if not id_list or len(id_list) == 0:
        return False
    has_roless = await has_roles(user, id_list)
    if user.id in id_list or has_roless:
        return True
    elif channel and channel.id in id_list:
        return True
    return False

async def view_ids(guild: discord.Guild, database: Database, type: str):
    """Grabs and returns a presentable list of channels, members, and roles based on a configuration and type."""
    id_list = await database.get_config(guild.id, type)
    items: List[Union[discord.abc.GuildChannel, discord.Member, discord.Role]] = []
    if id_list:
        for item in id_list:
            potential_user = discord.utils.get(guild.members, id=item)
            if potential_user:
                items.append(potential_user)
                pass
            potential_role = discord.utils.get(guild.roles, id=item)
            if potential_role:
                items.append(potential_role)
                pass
            potential_channel = discord.utils.get(guild.channels, id=item)
            if potential_channel:
                items.append(potential_channel)
                pass
        sentence = ", ".join(item.mention for item in items)
    else:
        sentence = "None"
    return sentence

from datetime import timedelta
from typing import Any, List, Union
from utility.guild import Database, expand_time_string, parse_time_string
import discord

async def find_bool(guild: discord.Guild, database: Database, type: str) -> bool:
    """Finds a boolean value in a database and returns True or False depending on the configuration and type."""
    bool_val: bool = await database.get_config(guild.id, type)
    return bool_val

async def find_channel(guild: discord.Guild, database: Database, type: str) -> discord.abc.GuildChannel | discord.Thread:
    """Finds a Discord channel and returns the channel or nothing depending on the configuration and type."""
    channel_id: int = await database.get_config(guild.id, type)
    if not channel_id or channel_id == 0:
        return None
    try:
        channel: discord.abc.GuildChannel | discord.Thread = await guild.fetch_channel(channel_id)
        return channel
    except Exception:
         return None
    
async def find_int(guild: discord.Guild, database: Database, type: str) -> int:
    """Finds a number and returns said number or nothing depending on the configuration and type."""
    num: int = await database.get_config(guild.id, type)
    if not num or num <= 0:
        return 0
    return num

async def find_list(guild: discord.Guild, database: Database, type: str) -> list[Any]:
    listy: List[Any] = await database.get_config(guild.id, type)
    if not listy or len(listy) == 0:
        return []
    return listy
    
async def find_role(guild: discord.Guild, database: Database, type: str) -> discord.Role:
    """Finds a role and returns said role or nothing depending on the configuration and type."""
    roleid: int = await database.get_config(guild.id, type)
    if not roleid or roleid == 0:
        return None
    try:
        roles: List[discord.Role] = await guild.fetch_roles()
        for roler in roles:
            if roler.id == roleid:
                return roler
        return None
    except Exception:
        return None

async def find_str(guild: discord.Guild, database: Database, type: str) -> str:
    """Finds a string/text and returns said string/text or nothing depending on the configuration and type."""
    string: str = await database.get_config(guild.id, type)
    if not string or string == "":
        return None
    return string

async def find_time(guild: discord.Guild, database: Database, type: str) -> tuple[timedelta, str]:
    """Finds a time string/text and returns said time or nothing depending on the configuration and type."""
    time: str = await database.get_config(guild.id, type)
    if not time or time == "0s":
        return None, "0 seconds/infinite"
    time_amount: timedelta = await parse_time_string(time)
    expanded: str = await expand_time_string(time)
    return time_amount, expanded

async def has_roles(user: discord.Member, roles: List[int]) -> bool:
    """Checks role IDs and determines if a given user has one or more of such roles."""
    for role in user.roles:
        if role.id in roles:
            return True
    return False

async def has_valid_id(user: discord.Member, channel: discord.abc.GuildChannel, guild: discord.Guild, database: Database, type: str) -> bool:
    """Checks if either a user or a channel is within an ID list configuration (Usually used for white or blacklists)"""
    id_list: list[int] = await database.get_config(guild.id, type)
    if not id_list or len(id_list) == 0:
        return False
    has_roless: bool = await has_roles(user, id_list)
    if user.id in id_list or has_roless:
        return True
    elif channel and channel.id in id_list:
        return True
    return False

async def view_ids(guild: discord.Guild, database: Database, type: str) -> str:
    """Grabs and returns a presentable list of channels, members, and roles based on a configuration and type."""
    id_list: list[int] = await database.get_config(guild.id, type)
    items: List[Union[discord.abc.GuildChannel, discord.Member, discord.Role]] = []
    if id_list:
        for item in id_list:
            potential_user: discord.Member = discord.utils.get(guild.members, id=item)
            if potential_user:
                items.append(potential_user)
                pass
            potential_role: discord.Role = discord.utils.get(guild.roles, id=item)
            if potential_role:
                items.append(potential_role)
                pass
            potential_channel: discord.abc.GuildChannel | discord.Thread = discord.utils.get(guild.channels, id=item)
            if potential_channel:
                items.append(potential_channel)
                pass
        sentence: str = ", ".join(item.mention for item in items)
    else:
        sentence = "None"
    return sentence

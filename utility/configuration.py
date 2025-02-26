from datetime import timedelta
import discord
from discord.ext import commands
from typing import Any, List, Union
from pymongo.results import UpdateResult
from utility.guild import Database, expand_time_string, parse_time_string

async def update_bool(ctx: commands.Context, database: Database, type: str, sentence: str):
    """Updates a boolean value in the database by toggling it on/off"""
    configuration: Any = await database.get_config(ctx.guild.id, type)
    if configuration:
        update: UpdateResult = await database.update_config(ctx.guild.id, {"$set": {type: False}})
        await ctx.send(f"Successfully disabled {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to disable {sentence}.")
    else:
        update = await database.update_config(ctx.guild.id, {"$set": {type: True}})
        await ctx.send(f"Successfully enabled {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to enable {sentence}.")   

async def update_id(ctx: commands.Context, database: Database, type: str, item: Union[discord.abc.GuildChannel, discord.Member, discord.User, discord.Role], sentence: str):
    """Updates a channel/member/user/role ID in the database by either disabling it (Setting it to 0) or setting it to the item's ID"""
    if not item:
        update: UpdateResult = await database.update_config(ctx.guild.id, {"$set": {type: 0}})
        await ctx.send(f"Successfully disabled the {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to disable the {sentence} (Is it already disabled?).")
    else:
        update = await database.update_config(ctx.guild.id, {"$set": {type: item.id}})
        await ctx.send(f"Successfully set the {sentence} to {item.name}.") if update.modified_count > 0 else await ctx.send(f"Failed to set the {sentence} to {item.name} (Is it already set to this?).")

async def update_id_list(ctx: commands.Context, database: Database, type: str, item: Union[discord.Guild, discord.abc.GuildChannel, discord.Member, discord.User, discord.Role], sentence: str):
    """Adds a guild/channel/member/user/role ID to a list in the database, or resets the list if no items are provided"""
    configuration: List[Union[discord.Guild, discord.abc.GuildChannel, discord.Member, discord.User, discord.Role]] = await database.get_config(ctx.guild.id, type)
    if not item:
        update: UpdateResult = await database.update_config(ctx.guild.id, {"$set": {type: []}})
        await ctx.send(f"Successfully reset the {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to reset the {sentence} (Is it already empty?).")
    else:
        if configuration and item.id in configuration:
            configuration.remove(item.id)
            update = await database.update_config(ctx.guild.id, {"$set": {type: configuration}})
            await ctx.send(f"Successfully removed {item.name} from {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to remove {item.name} from {sentence}.")
        else:
            if not configuration:
                configuration = [item.id]
            else:
                configuration.append(item.id)
            update = await database.update_config(ctx.guild.id, {"$set": {type: configuration}})
            await ctx.send(f"Successfully added {item.name} to {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to add {item.name} to {sentence}")
    
async def update_int(ctx: commands.Context, database: Database, type: str, id: int, sentence: str):
    """Updates a number in the database by setting it to 0 or to the given id/number"""
    if not id:
        update: UpdateResult = await database.update_config(ctx.guild.id, {"$set": {type: 0}})
        await ctx.send(f"Successfully disabled the {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to disable the {sentence} (Is it already disabled?).")
    else:
        if id < 0:
            return await ctx.send("Invalid number, please ensure that the number is positive.")
        update = await database.update_config(ctx.guild.id, {"$set": {type: id}})
        await ctx.send(f"Succesfully set the {sentence} to {id}.") if update.modified_count > 0 else await ctx.send(f"Failed to set the {sentence} to {id} (Is it already set to this number?).")

async def update_list(ctx: commands.Context, database: Database, type: str, item: str, sentence: str):
    """Adds an item to a list in the database, or resets the list if no items are provided"""
    configuration: List[str] = await database.get_config(ctx.guild.id, type)
    if not item:
        update: UpdateResult = await database.update_config(ctx.guild.id, {"$set": {type: []}})
        await ctx.send(f"Successfully reset the {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to reset the {sentence} (Is it already empty?).")
    else:
        if configuration and item in configuration:
            configuration.remove(item)
            update = await database.update_config(ctx.guild.id, {"$set": {type: configuration}})
            await ctx.send(f"Successfully removed {item} from {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to remove {item} from {sentence}.")
        else:
            configuration = [item] if not configuration else configuration.append(item)
            update = await database.update_config(ctx.guild.id, {"$set": {type: configuration}})
            await ctx.send(f"Successfully added {item} to {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to add {item} to {sentence}")

async def update_spam(ctx: commands.Context, database: Database, type: str, item1: str, item2: int, sentence1: str, sentence2: str):
    """Updates a spam configuration by either setting the time and amount or to disable the time and amount."""
    if not item1 and not item2:
        update: UpdateResult = await database.update_config(ctx.guild.id, {"$set": {f"{type}spam_amount": 0}})
        update2: UpdateResult = await database.update_config(ctx.guild.id, {"$set": {f"{type}spam_time": "0s"}})
        await ctx.send(f"Disabled this spam type.") if (update.modified_count > 0 and update2.modified_count > 0) else await ctx.send(f"Failed to disable the spam type (Is it already disabled?)")
    else:
        time_string: timedelta = await parse_time_string(item1)
        if not time_string:
            return await ctx.send("Invalid time value. Please make sure it is of the format <num><type> (Ex. \"2d\" or \"4w\") (To disable, do 0s).")
        str_1: str = await expand_time_string(item1)
        update = await database.update_config(ctx.guild.id, {"$set": {f"{type}spam_amount": item2}})
        update2 = await database.update_config(ctx.guild.id, {"$set": {f"{type}spam_time": item1}})
        if update.modified_count > 0 and update2.modified_count == 0:
            await ctx.send(f"Updated {sentence2} to **{item2}**.")
        elif update.modified_count == 0 and update2.modified_count > 0:
            await ctx.send(f"Updated {sentence1} to {str_1}.")
        elif update.modified_count > 0 and update2.modified_count > 0:
            await ctx.send(f"Updated {sentence1} to {str_1} and {sentence2} to {item2}.")
        else:
            await ctx.send(f"Failed to update {sentence1} and {sentence2} (Are they already set to these values?)")
    
async def update_str(ctx: commands.Context, database: Database, type: str, item: str, sentence: str) -> None:
    """Updates a string in the database by either setting it to an empty string or to the provided item"""
    if not item:
        update: UpdateResult = await database.update_config(ctx.guild.id, {"$set": {type: ""}})
        await ctx.send(f"Successfully disabled the {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to disable the {sentence} (Is it already disabled?)")
    else:
        update = await database.update_config(ctx.guild.id, {"$set": {type: item}})
        await ctx.send(f"Successfully set the {sentence} to {item}.") if update.modified_count > 0 else await ctx.send(f"Failed to set the {sentence} to {item}. (Is it already set to this message?)")

async def update_time(ctx: commands.Context, database: Database, type: str, time: str, sentence: str) -> None:
    """Updates a time string in the database by either setting it to Infinite, 0s, or to the provided time"""
    if not time:
        update: UpdateResult = await database.update_config(ctx.guild.id, {"$set": {type: "0s"}})
        await ctx.send(f"Successfully disabled the {sentence}.") if update.modified_count > 0 else await ctx.send(f"Failed to disable the {sentence} (Is it already disabled?).")
    else:
        time_string: timedelta = await parse_time_string(time)
        if not time_string:
            return await ctx.send("Inputted time is not valid (Make sure it is of the format <num><type>, Ex. 2d or 4w5m)")
        expanded_time: str = await expand_time_string(time)
        update = await database.update_config(ctx.guild.id, {"$set": {type: time}})
        await ctx.send(f"Successfully set the {sentence} to {expanded_time}.") if update.modified_count > 0 else await ctx.send(f"Failed to set the {sentence} to {expanded_time} (Is it already set to this time?).")
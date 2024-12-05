from datetime import timedelta
import discord
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os

load_dotenv("variables.env")

class Database:    
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Creates a new Database, if the database has not already previously been initialized (Stays persistent on restarts)"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self, bot):
        """Initializes the Database by setting the bot, connecting to the MongoDB database, and initializing the default collection names and configuration values"""
        if not self.__initialized:
            self.__initialized = True
            self.bot = bot
            mongo_url = os.getenv("MONGODB_URI")
            self.mongo_client = AsyncIOMotorClient(mongo_url)
            self.default_config = {
                "bad_links": [],
                "bad_words": [],
                "time_limit": "0s",
                "min_account_age": "0s",
                "invite_whitelist": [],
                "drama_channel": 0,
                "warn_threshold": 0,
                "mentionspam_time": "0s",
                "mentionspam_amount": 0,
                "giveaway_blacklist": [],
                "giveaway_hosts": [],
                "levels_enabled": False,
                "level_blacklist": [],
                "level_messages": {},
                "default_level_message": "",
                "level_roles": {},
                "server_log": 0,
                "join_leave_log": 0,
                "member_log": 0,
                "message_log": 0,
                "voice_log": 0,
                "log_ignores": [],
                "ban_limit": 0,
                "mod_log": 0,
                "mute_role": 0,
                "quarantine_role": 0,
                "stickyroles": [],
                "sticky_blacklist": [],
                "starboard_channel": 0,
                "star_threshold": 0,
                "default_emote": 0,
                "starboard_blacklist": [],
                "welcome_channel": 0,
                "join_message": "",
                "leave_message": "",
                "ban_message": "",
            }
            self.collections_other = ["id", "voicelink", "config", "starboard", "roles", "reminders", "moderation", "quarantine", "level", "giveaway", "automod"]

    async def get_guild_database(self, guild_id): 
        """Grabs the database associated with the given guild ID"""
        return self.mongo_client[str(guild_id)] 
    
    async def get_guild_collection(self, guild_id: int, collection_name: str):
        """Grabs the collection for the given guild ID and name"""
        guild_db = await self.get_guild_database(guild_id)
        return guild_db[collection_name]
    
    async def get_config(self, guild_id, type):
        """Grabs the configuration type for a given server"""
        config = await self.get_guild_collection(guild_id, "config")
        item = await config.find_one({})
        if item:
            return item.get(f"{type}", None)
        return None
    
    async def update_config(self, guild_id, update):
        """Updates the configuration type for a given server"""
        config = await self.get_guild_collection(guild_id, "config")
        return await config.update_one({}, update)

    async def get_next_id(self, guild_id):
        """Grabs the next ID for moderation cases"""
        id_collection = await self.get_guild_collection(guild_id, "id")
        id_doc = await id_collection.find_one({})
        current_value = id_doc.get('value', 0) if id_doc else 0
        await id_collection.update_one({}, {"$set": {"value": current_value + 1}}, upsert=True)
        return current_value
    
    async def setup_default_config(self, guild_id):
        """Sets up default configuration for a new or existing guild."""
        guild_db = await self.get_guild_database(guild_id)
        existing_collections = await guild_db.list_collection_names()
        for item in self.collections_other:
            if item not in existing_collections:
                await guild_db.create_collection(item)
                if item == "id":
                    doc = {"value": 0}
                    id_collection = await self.get_guild_collection(guild_id, "id")
                    await id_collection.insert_one(doc)
        config_collection = await self.get_guild_collection(guild_id, "config")
        for key, value in self.default_config.items():
            await config_collection.update_one(
                {}, 
                {"$setOnInsert": {key: value}},
                upsert=True
            )

async def parse_time_string(time_str: str) -> timedelta:
        """Parses a time string to return a valid timedelta"""
        time_str = time_str.lower()
        time_parts = {"y": 31536000, "mo": 2592000, "w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}
        time_str = time_str.lower()
        total_seconds = 0
        for part in time_str.split():
            num = int(part[:-1])
            if num < 0:
                return None
            unit = part[-1]
            if unit not in time_parts:
                return None
            total_seconds += num * time_parts[unit]
        return timedelta(seconds=total_seconds)

async def expand_time_string(time_str: str) -> str:
    """Expands a time string into a proper sentence"""
    time_str = time_str.lower()
    time_parts = {"y": "years", "mo": "months", "w": "weeks", "d": "days", "h": "hours", "m": "minutes", "s": "seconds"}
    words = ""
    for part in time_str.split():
        num = part[:-1]
        unit = part[-1]
        if unit not in time_parts:
            return None
        words += str(num) + " " + time_parts[unit]
        words += ","
    return words[:-1]

async def ordinal(n):
    """Converts a number into an ordinal that can be used in sentences"""
    if 10 <= n % 100 <= 13:
        return f"{n}th"
    if n % 10 == 1:
        return f"{n}st"
    elif n % 10 == 2:
        return f"{n}nd"
    elif n % 10 == 3:
        return f"{n}rd"
    else:
        return f"{n}th"
    
async def get_channel(channel: str, guild: discord.Guild):
    """Gets a Discord channel based on a string"""
    if channel.startswith("<@"):
        return None
    if channel.startswith("<#"):
        c_id = int(channel[2:-1])
    else:
        c_id = int(channel)
    channel = discord.utils.get(guild.channels, id=c_id)
    return channel

async def get_user(user: str, guild: discord.Guild):
    """Gets a Discord user based on a string"""
    if user.startswith("<#"):
        return None
    if user.startswith("<@"):
        u_id = int(user[2:-1])
    else:
        u_id = int(user)
    user = discord.utils.get(guild.members, id=u_id)
    return user


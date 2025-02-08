from datetime import timedelta
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import discord
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
            self.automod = "automod"
            self.config = "config"
            self.giveaway = "giveaway"
            self.level = "level"
            self.moderation = "moderation"
            self.quarantine = "quarantine"
            self.starboard = "starboard"
            self.voicelink = "voicelink"
            self.id = "id"
            self.roles = "roles"
            self.reminders = "reminders"
            self.bad_links = "bad_links"
            self.bad_words = "bad_words"
            self.time_limit = "time_limit"
            self.min_account_age = "min_account_age"
            self.invite_whitelist = "invite_whitelist"
            self.drama_channel = "drama_channel"
            self.warn_threshold = "warn_threshold"
            self.mentionspam_time = "mentionspam_time"
            self.mentionspam_amount = "mentionspam_amount"
            self.giveaway_blacklist = "giveaway_blacklist"
            self.giveaway_hosts = "giveaway_hosts"
            self.levels_enabled = "levels_enabled"
            self.level_blacklist = "level_blacklist"
            self.level_messages = "level_messages"
            self.default_level_message = "default_level_message"
            self.level_roles = "level_roles"
            self.blocked_messages = "blocked_messages"
            self.server_log = "server_log"
            self.join_leave_log = "join_leave_log"
            self.member_log = "member_log"
            self.message_log = "message_log"
            self.voice_log = "voice_log"
            self.log_ignores = "log_ignores"
            self.ban_limit = "ban_limit"
            self.mod_log = "mod_log"
            self.mute_role = "mute_role"
            self.quarantine_role = "quarantine_role"
            self.stickyroles = "stickyroles"
            self.sticky_blacklist = "sticky_blacklist"
            self.starboard_channel = "starboard_channel"
            self.star_threshold = "star_threshold"
            self.default_emote = "default_emote"
            self.starboard_blacklist = "starboard_blacklist"
            self.welcome_channel = "welcome_channel"
            self.join_message = "join_message"
            self.leave_message = "leave_message"
            self.ban_message = "ban_message"
            self.default_config = {
                self.bad_links: [],
                self.bad_words: [],
                self.time_limit: "0s",
                self.min_account_age: "0s",
                self.invite_whitelist: [],
                self.drama_channel: 0,
                self.warn_threshold: 0,
                self.mentionspam_time: "0s",
                self.mentionspam_amount: 0,
                self.giveaway_blacklist: [],
                self.giveaway_hosts: [],
                self.levels_enabled: False,
                self.level_blacklist: [],
                self.level_messages: {},
                self.default_level_message: "",
                self.level_roles: {},
                self.server_log: 0,
                self.join_leave_log: 0,
                self.member_log: 0,
                self.message_log: 0,
                self.voice_log: 0,
                self.log_ignores: [],
                self.ban_limit: 0,
                self.mod_log: 0,
                self.mute_role: 0,
                self.quarantine_role: 0,
                self.stickyroles: [],
                self.sticky_blacklist: [],
                self.starboard_channel: 0,
                self.star_threshold: 0,
                self.default_emote: 0,
                self.starboard_blacklist: [],
                self.welcome_channel: 0,
                self.join_message: "",
                self.leave_message: "",
                self.ban_message: "",
            }
            self.collections_other = [self.id, self.voicelink, self.config, self.starboard, self.roles, self.reminders, self.moderation, self.quarantine, self.level, self.giveaway, self.automod]

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
        try:
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
        except Exception:
            return None

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
    words = words[:-1]
    if num == 1:
        return words[:-1]
    return words

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


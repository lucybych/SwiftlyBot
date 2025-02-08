from discord.ext import commands
from typing import Optional, Union
from utility.guild import Database, expand_time_string
import discord
import utility.configuration as config
import utility.finder as finder

config_commands_dict = {
    "automod": "Usage: m?automod\nPurpose: Displays the settings for the Automod module (Banned links/words, account time limit, minimum account age, invite whitelist, drama channel, warn threshold, mentionspam amount/time).",
    "badlinks": "Usage: m?badlinks (link)\nPurpose: Updates the list of banned links (Providing no input resets the list)",
    "badwords": "Usage: m?badwords (word)\nPurpose: Updates the list of banned words (Providing no input resets the list)",
    "dramachannel": "Usage: m?dramachannel (channel)\nPurpose: Sets or disables the drama channel",
    "invitewhitelist": "Usage: m?invitewhitelist (server ID)\nPurpose: Updates the list of allowed servers to have invites be posted (Providing no input resets the list)",
    "mentionspam": "Usage: m?mentionspam (time) (amount)\nPurpose: Sets or disables the amount of allowed mentions in a specified time",
    "minage": "Usage: m?minage (time)\nPurpose: Sets or disables the minimum account age upon joining the server",
    "timelimit": "Usage: m?timelimit (time)\nPurpose: Sets or disables the time limit a user has before being autobanned upon any infraction",
    "warnthreshold": "Usage: m?warnthreshold (num of warns/num)\nPurpose: Sets or disables the amount of warnings a user can have before being autobanned",
    "gblacklist": "Usage: m?gblacklist (user/role)\nPurpose: Updates the list of users/roles that are blacklisted from entering or winning giveaways (Providing no input resets the list)",
    "giveawayhost": "Usage: m?giveawayhost (user/role)\nPurpose: Updates the list of users/roles that can host giveaways (Proviing no input resets the list)",
    "giveaway": "Usage: m?giveaway\nPurpose: Displays the settings for the Giveaway module (Giveaway blacklist, giveaway hosts).",
    "dlevelmsg": "Usage: m?dlevelmsg (message)\nPurpose: Sets or disables the default level message (If no default level message, no level up messages or only special level up messages will be posted)",
    "levelconfig": "Usage: m?levelconfig\nPurpose: Displays the settings for the Level module (Level roles, default level message, level messages, level blacklist)",
    "levelmsg": "Usage: m?levelmsg <level/num> (message)\nPurpose: Sets the message given by a specific level upon leveling up, or removes the entry for that level if no input is provided",
    "levelrole": "Usage: m?levelrole <level/num> (role)\nPurpose: Sets the role given by a specific level, or removes the entry for that level if no input is provided",
    "leveltoggle": "Usage: m?leveltoggle\nPurpose: Toggles levels in the server, by either enabling or disabling it.",
    "lvlblacklist": "Usage: m?lvlblacklist (channel/role/user)\nPurpose: Updates the list of channels/users/roles blacklisted from gaining XP (Providing no input resets the list)",
    "ignored": "Usage: \nPurpose: Updates the list of channels/roles/members that won't be affected by logs (Providing no input resets the list)",
    "joinleavelog": "Usage: \nPurpose: Sets or disables the logging channel for when members join and leave the server",
    "logs": "Usage: \nPurpose: Displays the settings for the Logs module (server/join-leave/member/message/voice logs, log ignores).",
    "memberlog": "Usage: \nPurpose: Sets or disables the logging channel which tracks member changes",
    "messagelog": "Usage: \nPurpose: Sets or disables the logging channel which tracks message changes",
    "serverlog": "Usage: \nPurpose: Sets or disables the logging channel which tracks server changes",
    "voicelog": "Usage: \nPurpose: Sets or disables the logging channel which tracks voice channel changes",
    "moderation": "Usage: \nPurpose: Displays the settings for the Moderation module (ban limit, mod log, mute/quarantine roles).",
    "modlogset": "Usage: \nPurpose: Sets or disables the moderation logging channel for the server (If disabled, no moderation actions will be logged)",
    "muterole": "Usage: \nPurpose: Sets or disables the mute role in the server (If disabled, no mutes can occur)",
    "quarantinerole": "Usage: \nPurpose: Sets or disables the quarantine role for the server (If disabled, no quarantines can occur)",
    "rolesconfig": "Usage: \nPurpose: Displays the settings for the Roles module (Sticky roles, sticky roles blacklist).",
    "stickyblacklist": "Usage: \nPurpose: Updates the list of roles not affected by stickyroles (Providing no input resets the list)",
    "stickyrole": "Usage: \nPurpose: Toggles the stickyrole setting, by either enabling or disabling it",
    "defaultemote": "Usage: \nPurpose: Sets the emote for use in the starboard (Uses the default star reaction if no emote is provided)",
    "starboard": "Usage: \nPurpose: Displays the settings for the Starboard module (Starboard channel, blacklist, threshold, default emote).",
    "starboardblacklist": "Usage: \nPurpose: Updates the list of banned users, roles, and channels from starboarding posts and from getting posts on starboard (Providing no input resets the list)",
    "starboardchannel": "Usage: \nPurpose: Sets or disables the channel where starred posts are made to",
    "starthreshold": "Usage: \nPurpose: Sets or disables the amount of stars needed to get a post to starboard (0 means starboard is disabled)",
    "banmessage": "Usage: \nPurpose: Resets/disables the ban message in the server, if no message is provided. If message is provided, it will set the default ban message to the given message.",
    "joinmessage": "Usage: \nPurpose: Resets/disables the join message in the server, if no message is provided. If message is provided, it will set the default join message to the given message.",
    "leavemessage": "Usage: \nPurpose: Resets/disables the leave message in the server, if no message is provided. If message is provided, it will set the default leave message to the given message.",
    "welcome": "Usage: \nPurpose: Displays the settings for the Welcome module (Welcome channel, join/leave/ban messages)",
    "welcomechannel": "Usage: \nPurpose: Resets/disables the welcome channel in the server, if no channel is provided. If channel is provided, it will set the welcome channel to the given channel.",
}
emd_commands_dict = {
    "anchor": "Usage: m?anchor\nPurpose: For EMD staff to get pinged in staff chat",
    "anchovy": "Usage: m?anchovy\nPurpose: For EMD staff to get pinged in staff chat, but fishier 🐟",
    "betterdiscord": "Usage: m?betterdiscord\nPurpose: For EMD staff to use in regards to BetterDiscord or other modified Discord clients",
    "deadchat": "Usage: m?deadchat\nPurpose: For EMD staff to use when someone mentions if/when a chat is inactive",
    "dead": "Usage: m?dead\nPurpose: For EMD staff to use when someone mentions if/when a chat is inactive",
    "eee": "Usage: m?eee\nPurpose: Posts an invite to the spinoff server Eevee's Emote Encyclopedia",
    "emd": "Usage: m?emd\nPurpose: Posts EMD's permanent server invite",
    "emotes": "Usage: m?emotes\nPurpose: For EMD staff to use when someone asks about emotes",
    "ert": "Usage: m?ert\nPurpose: Posts an invite to the spinoff server Eevee's Rescue Team",
    "rescue": "Usage: m?rescue\nPurpose: Posts an invite to the spinoff server Eevee's Rescue Team",
    "introcl": "Usage: m?introcl\nPurpose: Goes through EMD's self-introductions channel and removes all intros from those who posted multiple or who have left the server",
    "lvlinfo": "Usage: m?lvlinfo\nPurpose: For EMD staff to use when someone asks about levels and the leveling system",
    "link": "Usage: m?link\nPurpose: For EMD staff to use when someone asks about posting/embedding links or attaching/posting files",
    "links": "Usage: m?links\nPurpose: For EMD staff to use when someone asks about posting/embedding links or attaching/posting files",
    "nick": "Usage: m?nick\nPurpose: For EMD staff to use when someone asks about changing their nickname",
    "nsfw": "Usage: m?nsfw\nPurpose: For EMD staff to use when someone asks about NSFW and the associated channels",
    "offserver": "Usage: m?offserver\nPurpose: For EMD staff to use when determining if a person off-server should be banned",
    "openoriginal": "Usage: m?openoriginal\nPurpose: For EMD staff to use when someone asks about large/elongated images",
    "rando": "Usage: m?rando\nPurpose: For EMD staff to use when someone asks about a random user getting banned",
    "reply": "Usage: m?reply\nPurpose: For EMD staff to use when someone asks about replying to other users",
    "roleinfo": "Usage: m?roleinfo\nPurpose: For EMD staff to use when someone asks about roles and/or how to obtain them",
    "scam": "Usage: m?scam\nPurpose: For EMD staff to use when someone asks about scams and hacks on Discord",
    "selfies": "Usage: m?selfies\nPurpose: For EMD staff to use when someone asks about selfies and/or the selfies channel",
    "sl": "Usage: m?sl <user>\nPurpose: For EMD staff to use to temporarily mute users, for fun!",
    "silenceliberal": "Usage: m?silenceliberal <user>\nPurpose: For EMD staff to use to temporarily mute users, for fun!",
    "trade": "Usage: m?trade\nPurpose: For EMD staff to use when someone asks about Pokemon trades",
    "trades": "Usage: m?trades\nPurpose: For EMD staff to use when someone asks about Pokemon trades",
    "troll": "Usage: m?troll\nPurpose: For EMD staff to use when someone asks about why a troll got banned",
    "trolls": "Usage: m?trolls\nPurpose: For EMD staff to use when someone asks about why a troll got banned",
    "vc": "Usage: m?vc\nPurpose: For EMD staff to use when someone asks about voice channels",
    "vcs": "Usage: m?vcs\nPurpose: For EMD staff to use when someone asks about voice channels",
}
giveaway_commands_dict = {
    "gstart": "Usage: m?gstart <time> <winners/num> <prize> \nPurpose: Starts a giveaway that will end in the given time, have the given number of winners, and is for the given prize",
    "greroll": "Usage: m?greroll <giveaway/message ID>\nPurpose: Rerolls a giveaway, if said giveaway exists and has ended",
}
level_commands_dict = {
    "givexp": "Usage: m?givexp <xp> (user)\nPurpose: Gives the number of experience to the given user, or the command user if no user is specified.",
    "level": "Usage: m?level (user)\nPurpose: Checks the level for the given user, or the command user",
    "lvl": "Usage: m?lvl (user)\nPurpose: Checks the level for the given user, or the command user",
    "leaderboard": "Usage: m?leaderboard (page)\nPurpose: Displays the users with the most XP, each page contains 20 entries (Page 1 is 1-20, 2 is 21-40, etc)",
    "lb": "Usage: m?lb (page)\nPurpose: Displays the users with the most XP, each page contains 20 entries (Page 1 is 1-20, 2 is 21-40, etc)",
    "removexp": "Usage: m?removexp <xp> (user)\nPurpose: Takes away the given number of XP away from the given user or the command user.",
    "resetxp": "Usage: m?resetxp (user)\nPurpose: Resets the experience of the given user or command user to 0 (Deletes their level entry)"
}
moderation_commands_dict = {
    "ab": "Usage: \nPurpose: ",
    "ban": "Usage: \nPurpose: ",
    "banlist": "Usage: \nPurpose: ",
    "bansync": "Usage: \nPurpose: ",
    "clearpunishment": "Usage: \nPurpose: ",
    "clearwarn": "Usage: \nPurpose: ",
    "kick": "Usage: \nPurpose: ",
    "modlog": "Usage: \nPurpose: ",
    "mute": "Usage: \nPurpose: ",
    "muted": "Usage: \nPurpose: ",
    "muterolecr": "Usage: \nPurpose: ",
    "muteroleup": "Usage: \nPurpose: ",
    "purge": "Usage: \nPurpose: ",
    "quarantine": "Usage: \nPurpose: ",
    "q": "Usage: \nPurpose: ",
    "quarantinecreate": "Usage: \nPurpose: ",
    "quarantineup": "Usage: \nPurpose: ",
    "rban": "Usage: \nPurpose: ",
    "reason": "Usage: \nPurpose: ",
    "removepunishment": "Usage: \nPurpose: ",
    "resetnick": "Usage: \nPurpose: ",
    "rn": "Usage: \nPurpose: ",
    "rkick": "Usage: \nPurpose: ",
    "rmute": "Usage: \nPurpose: ",
    "rquarantine": "Usage: \nPurpose: ",
    "rq": "Usage: \nPurpose: ",
    "rtimeout": "Usage: \nPurpose: ",
    "runban": "Usage: \nPurpose: ",
    "runmute": "Usage: \nPurpose: ",
    "runquarantine": "Usage: \nPurpose: ",
    "ruq": "Usage: \nPurpose: ",
    "runtimeout": "Usage: \nPurpose: ",
    "sb": "Usage: \nPurpose: ",
    "setnick": "Usage: \nPurpose: ",
    "sn": "Usage: \nPurpose: ",
    "tb": "Usage: \nPurpose: ",
    "timeout": "Usage: \nPurpose: ",
    "uau": "Usage: \nPurpose: ",
    "unban": "Usage: \nPurpose: ",
    "unmute": "Usage: \nPurpose: ",
    "unquarantine": "Usage: \nPurpose: ",
    "uq": "Usage: \nPurpose: ",
    "untimeout": "Usage: \nPurpose: ",
    "warn": "Usage: \nPurpose: ",
}
reminder_commands_dict = {
    "remind": "Usage: m?remind <time (Ex. 4w or 2mo2d) or timestamp> <dm/channel> <message> (Repeating time)\nPurpose: Creates a reminder for the command user, with the arguments of the time to remind the user, dm/channel specification, reminder message, and interval time for repeating reminders",
    "reminddelete": "Usage: m?reminddelete <reminder message ID> \nPurpose: Deletes a reminder for the user with the given reminder ID",
    "remindedit": "Usage: m?remindedit <reminder message ID> <message> \nPurpose: Edits a reminder for the user with the given ID, if they created the reminder",
    "remindlist": "Usage: m?remindlist\nPurpose: List all active reminders for the command user"
}
tmc_commands_dict = {}
tnb_commands_dict = {
    "betterdiscord": "Usage: m?betterdiscord\nPurpose: Better Discord copypasta, for when users ask about BetterDiscord, Vencord, or any other modified clients.",
    "deadchat": "Usage: m?deadchat\nPurpose: Dead chat copypasta, for staff use in TNB when users ask about dead chat or bring up how dead the chat is.",
    "dead": "Usage: m?dead\nPurpose: Dead chat copypasta, for staff use in TNB when users ask about dead chat or bring up how dead the chat is.",
    "nick": "Usage: m?nick\nPurpose: Nickname copypasta, for staff use in TNB when users ask about nicknames or changing their nickname.",
    "nsfw": "Usage: m?nsfw\nPurpose: NSFW copypasta, for staff use in TNB when users ask about NSFW or NSFW channels.",
    "roles": "Usage: m?roles\nPurpose: Roles copypasta, for staff use in TNB when users ask about roles.",
    "scam": "Usage: m?scam\nPurpose: Scam copypasta, for staff use in TNB when users ask or talk about scams.",
    "selfies": "Usage: m?selfies\nPurpose: Selfies copypasta, for staff use in TNB when users ask about selfies or a selfies channel.",
    "tnb": "Usage: m?tnb\nPurpose: Easy access to the permanent server invite for TNB.",
    "trade": "Usage: m?trade\nPurpose: Trades copypasta, for staff use in TNB when users ask about Pokemon trades or anything similar.",
    "trades": "Usage: m?trades\nPurpose: Trades copypasta, for staff use in TNB when users ask about Pokemon trades or anything similar.",
    "troll": "Usage: m?troll\nPurpose: Troll copypasta, for staff use in TNB when users ask about trolls.",
    "trolls": "Usage: m?trolls\nPurpose: Troll copypasta, for staff use in TNB when users ask about trolls.",
    "vcs": "Usage: m?vcs\nPurpose: Voice chat copypasta, for staff use in TNB when users ask about voice channels/VCs. ",
}
utility_commands_dict = {
    "addemoji": "Usage: m?addemoji <name> <link>\nPurpose: Adds emoji from given link with the given name.",
    "addsticker": "Usage: m?addsticker <name> <link> <emoji> <description>\nPurpose: Adds a sticker with the given name, link, and description.",
    "avatar": "Usage: m?avatar (user(s))\nPurpose: Displays the given user(s) global profile and server profile, or the command user's profile(s)",
    "channelcreate": "Usage: m?channelcreate <name> <type (Must be text, voice, forum, stage, or category)>\nPurpose: Creates a new channel of the given type with the given name",
    "channelclone": "Usage: m?channelclone <channel> <name>\nPurpose: Clones a channel into a new channel with the given name",
    "channeldelete": "Usage: m?channeldelete <channel>\nPurpose: Deletes a given channel.",
    "channelname": "Usage: m?channelname <channel> <name>\nPurpose: Renames a given channel to the given new name.",
    "check": "Usage: m?check\nPurpose: Gives some general information about a server, such as number of members, roles, and channels.",
    "createrole": "Usage: m?createrole (name) (color)\nPurpose: Creates a new role with the given name and color, or default if no name/color is provided",
    "deleterole": "Usage: m?deleterole <role>\nPurpose: Deletes a given role, if it exists.",
    "echo": "Usage: m?echo <channel> <message>\nPurpose: \"Echoes\" a message from one channel to another.",
    "inrole": "Usage: m?inrole <role>\nPurpose: Determine how many users are in the given role, and dumps a text file with their username(s) and user ID(s).",
    "multiping": "Usage: m?multiping <role1> <role2>\nPurpose: Creates a new temporary role, adds all users who have the given role1 or role2 to that new role, and mentions the role, before deleting it.",
    "roleadd": "Usage: m?roleadd <role> <user(s)>\nPurpose: Adds the given role to the given user(s)",
    "sr": "Usage: m?sr <role> <user(s)>\nPurpose: Adds the given role to the given user(s)",
    "setrole": "Usage: m?setrole <role> <user(s)>\nPurpose: Adds the given role to the given user(s)",
    "roleclone": "Usage: m?roleclone <role> (name)\nPurpose: Clones a role into a new role with the given name (or default if no name is provided).",
    "rolecolor": "Usage: m?rolecolor <role> (color)\nPurpose: Changes the color of given role to the given new color, or default if no color is provided.",
    "rolein": "Usage: m?rolein <role1> <role2>\nPurpose: Adds role2 to all members in role1, if they do not already have role2.",
    "rolename": "Usage: m?rolename <role> (name)\nPurpose: Changes the name of the given role to the given new name, or \"Request New Nickname\" if none is provided.",
    "rolerall": "Usage: m?rolerall <role(s)>\nPurpose: Removes all members from the given role(s)",
    "roleremove": "Usage: m?roleremove <role> <user(s)>\nPurpose: Removes the given role from the given user(s)",
    "roleremoveall": "Usage: m?roleremoveall <user(s)>\nPurpose: Removes all roles from the given user(s).",
    "rolerin": "Usage: m?rolerin <role1> <role2>\nPurpose: Removes role2 from all members in role1, if they have role2.",
    "serverinfo": "Usage: m?serverinfo\nPurpose: Displays information about the server (features, boost level, number of channels, etc.)",
    "temp": "Usage: m?temp <value><f/c>\nPurpose: Converts the given temperature to Celsius (C) if Farenheit (F) is given, and vice versa.",
    "changetemp": "Usage: m?changetemp <value><f/c>\nPurpose: Converts the given temperature to Celsius (C) if Farenheit (F) is given, and vice versa.",
    "temperature": "Usage: m?temperature <value><f/c>\nPurpose: Converts the given temperature to Celsius (C) if Farenheit (F) is given, and vice versa.",
    "changetemperature": "Usage: m?changetemperature <value><f/c>\nPurpose: Converts the given temperature to Celsius (C) if Farenheit (F) is given, and vice versa.",
    "ct": "Usage: m?ct <value><f/c>\nPurpose: Converts the given temperature to Celsius (C) if Farenheit (F) is given, and vice versa.",
    "userinfo": "Usage: m?userinfo (user(s))\nPurpose: Displays information about given user(s) (username, ID, number of roles, account creation/join date, etc.), or command user if none are provided",
}
voicelink_commands_dict = {
    "addvoicelink": "Usage: m?addvoicelink <Voice channel> <role>\nPurpose: Connects a role to a voice channel, that will be controlled based on when the user joins/leaves/moves from a voice channel.",
    "removevoicelink": "Usage: m?removevoicelink <Voice channel> <role>\nPurpose: Disconnects a role from a voice channel, meaning it will no longer be used when a user interacts with a voice channel."
}

EMD_SERVER_ID = 385956732888678402
RATE_LIMIT = 2000
TMC_SERVER_ID = 1142604515791618108
TNB_SERVER_ID = 932843700751597608

class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the configuration module"""
        self.bot = bot
        self.database = Database(self.bot)
#---------------------------------------------------------------------------------------------------------------------------------------
#Automod configurations 
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def automod(self, ctx: commands.Context):
        """Displays the settings for the Automod module (Banned links/words, account time limit, minimum account age, invite whitelist, drama channel, warn threshold, mentionspam amount/time)."""
        guild_id = ctx.guild.id
        bad_links = await self.database.get_config(guild_id, self.database.bad_links)
        bad_links_list = [] if not bad_links else bad_links
        bad_words = await self.database.get_config(guild_id, self.database.bad_words)
        bad_words_list = [] if not bad_words else bad_words
        time_limit = await self.database.get_config(guild_id, self.database.time_limit)
        time_limit_s = await expand_time_string(time_limit) if time_limit else "Disabled"
        min_account_age = await self.database.get_config(guild_id, self.database.min_account_age)
        min_account_age_s = await expand_time_string(min_account_age) if min_account_age else "Disabled"
        invite_whitelist = await self.database.get_config(guild_id, self.database.invite_whitelist)
        invite_whitelist_list = [] if not invite_whitelist else invite_whitelist
        drama_channel = await finder.find_channel(ctx.guild, self.database, self.database.drama_channel)
        warn_threshold = await self.database.get_config(guild_id, self.database.warn_threshold)
        mentionspam_time = await self.database.get_config(guild_id, self.database.mentionspam_time)
        mentionspam_time_s = await expand_time_string(mentionspam_time) if mentionspam_time else "Infinite time"
        mentionspam_amount = await self.database.get_config(guild_id, self.database.mentionspam_amount)
        embed = discord.Embed(color=discord.Color.dark_gray(),title="Automod Configuration")
        embed.add_field(name="Banned Links:",value=", ".join(link for link in bad_links_list),inline=False)
        embed.add_field(name="Banned Words:",value=", ".join(word for word in bad_words_list),inline=False)
        embed.add_field(name="Account Time Limit:",value=time_limit_s,inline=False)
        embed.add_field(name="Minimum Account Age:",value=min_account_age_s,inline=False)
        embed.add_field(name="Invite Whitelist (Guild IDs):",value=", ".join(str(guild) for guild in invite_whitelist_list),inline=False)
        embed.add_field(name="Drama Channel:",value=drama_channel.name if drama_channel else "Unknown Channel",inline=False)
        embed.add_field(name="Warn Threshold",value=warn_threshold,inline=False)
        embed.add_field(name="Mention Spam Amount and Time:",value=f"{mentionspam_amount} mentions in {mentionspam_time_s}",inline=False)
        await ctx.send(embed=embed)
    @automod.error
    async def on_automod_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?automod")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view the automod configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def badlinks(self, ctx: commands.Context, link: Optional[str]):
        """Updates the list of banned links (Providing no input resets the list)"""
        await config.update_list(ctx, self.database, self.database.bad_links, link, "link blacklist")
    @badlinks.error
    async def on_badlinks_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid link, or omit it to disable the bad links automod.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the bad links automod configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['censor'])
    @commands.has_permissions(manage_guild=True)
    async def badwords(self, ctx: commands.Context, word: Optional[str]):
        """Updates the list of banned words (Providing no input resets the list)"""
        await config.update_list(ctx, self.database, self.database.bad_words, word, "word blacklist")
    @badwords.error
    async def on_badwords_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a word, or omit it to disable the bad words automod.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the bad words automod configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def dramachannel(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Sets or disables the drama channel"""
        await config.update_id(ctx, self.database, self.database.drama_channel, channel, "drama channel")
    @dramachannel.error
    async def on_dramachannel_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel, or omit it to disable the drama channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the drama channel configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a channel found in server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def invitewhitelist(self, ctx: commands.Context, guild_id: Optional[int]):
        """Updates the list of allowed servers to have invites be posted (Providing no input resets the list)"""
        await config.update_list(ctx, self.database, self.database.invite_whitelist, guild_id, "invite whitelist")
    @invitewhitelist.error
    async def on_invitewhitelist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid guild ID, or omit it to completely enable invite automod.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the invite whitelist configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a number.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def mentionspam(self, ctx: commands.Context, amount: Optional[int], time: Optional[str]):
        """Sets or disables the amount of mentions in a specified time"""
        await config.update_spam(ctx, self.database, "mention", time, amount, "mention spam amount", "mention spam timeframe")
    @mentionspam.error
    async def on_mentionspam_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid time and number amount, or omit it to disable the mention spam automod.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the mention spam configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid time string and number.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def minage(self, ctx: commands.Context, time: Optional[str]):
        """Sets or disables the minimum account age upon joining the server"""
        await config.update_time(ctx, self.database, self.database.min_account_age, time, "minimum account age")
    @minage.error
    async def on_minage_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid time, or omit it to disable the minimum account join age automod.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the minimum account age configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def timelimit(self, ctx: commands.Context, time: Optional[str]):
        """Sets or disables the time limit a user has before being autobanned upon any infraction"""
        await config.update_time(ctx, self.database, self.database.time_limit, time, "autoban time limit")
    @timelimit.error
    async def on_timelimit_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid time, or omit it to disable the time limit automod.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the account time limit configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def warnthreshold(self, ctx: commands.Context, num: Optional[int]):
        """Sets or disables the amount of warnings a user can have before being autobanned"""
        await config.update_int(ctx, self.database, self.database.warn_threshold, num, "warning threshold")
    @warnthreshold.error
    async def on_warnthreshold_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid number, or omit it to disable the warning threshold amount.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a number.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the warning threshold configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
#---------------------------------------------------------------------------------------------------------------------------------------
#Giveaway configurations
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def gblacklist(self, ctx: commands.Context, item: Optional[Union[discord.User, discord.Member, discord.Role]]):
        """Updates the list of users/roles that are blacklisted from entering or winning giveaways (Providing no input resets the list)"""
        await config.update_id_list(ctx, self.database, self.database.giveaway_blacklist, item, "giveaway blacklist")
    @gblacklist.error
    async def on_gblacklist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid user or role, or omit it to disable the giveaway blacklist.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the giveaway blacklist configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a channel/role found in the server or user.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def giveawayhost(self, ctx: commands.Context, item: Optional[Union[discord.User, discord.Member, discord.Role]]):
        """Updates the list of users/roles that can host giveaways (Proviing no input resets the list)"""
        await config.update_id_list(ctx, self.database, self.database.giveaway_hosts, item, "giveaway host list")
    @giveawayhost.error
    async def on_giveawayhost_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid user or role, or omit it to disable giveaway hosts (Only staff can start or reroll giveaways).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the giveaway host list configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a channel/role found in the server or user.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def giveaway(self, ctx: commands.Context):
        """Displays the settings for the Giveaway module (Giveaway blacklist, giveaway hosts)."""
        giveaway_blacklist = await finder.view_ids(ctx.guild, self.database, self.database.giveaway_blacklist)
        giveaway_hosts = await finder.view_ids(ctx.guild, self.database, self.database.giveaway_hosts)
        embed = discord.Embed(color=discord.Color.dark_gray(),title="Giveaway Configuration")
        embed.add_field(name="Giveaway blacklist:",value=giveaway_blacklist,inline=False)
        embed.add_field(name="Giveaway hosts:",value=giveaway_hosts,inline=False)
        await ctx.send(embed=embed)
    @giveaway.error
    async def on_giveaway_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?giveaway")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view the giveaway configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
#---------------------------------------------------------------------------------------------------------------------------------------
#Level configurations
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def dlevelmsg(self, ctx: commands.Context, *, message: Optional[str]):
        """Sets or disables the default level message (If no default level message, no level up messages or only special level up messages will be posted)"""
        await config.update_str(ctx, self.database, self.database.default_level_message, message, "default level message")
    @dlevelmsg.error
    async def on_dlevelmsg_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a message, or omit it to disable the default level messages (Only special level messages or no level messages will trigger).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the default level message configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def levelconfig(self, ctx: commands.Context):
        """Displays the settings for the Level module (Level roles, default level message, level messages, level blacklist)"""
        guild_id = ctx.guild.id
        levels_enabled = await self.database.get_config(guild_id, self.database.levels_enabled)
        default_level_message = await self.database.get_config(guild_id, self.database.default_level_message)
        level_blacklist = await finder.view_ids(ctx.guild, self.database, self.database.level_blacklist)
        embed = discord.Embed(color=discord.Color.dark_gray(), title="Level configuration")
        embed.add_field(name="Levels Enabled:",value=levels_enabled, inline=False)
        embed.add_field(name="Default Level Message:", value=default_level_message or "Not set", inline=False)
        embed.add_field(name="Level Blacklist:",value=level_blacklist,inline=False)
        await ctx.send(embed=embed)
    @levelconfig.error
    async def on_level_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?levelconfig")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view the level configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.") 
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def levelmsg(self, ctx: commands.Context, level: int, *, message: Optional[str]):
        """Sets the message given by a specific level upon leveling up, or removes the entry for that level if no input is provided"""
        level_messages = await self.database.get_config(ctx.guild.id, self.database.level_messages)
        if not level_messages:
            level_messages = {}
        if not message:
            if str(level) in level_messages:
                del level_messages[str(level)]
                await self.database.update_config(ctx.guild.id, {"$set": {self.database.level_messages: level_messages}})
                await ctx.send(f"Successfully removed unique level message for level {level}.")
            else:
                await ctx.send(f"No unique level message found for level {level}.")
        else:
            level_messages = {str(level): message,}
            update = await self.database.update_config(ctx.guild.id, {"$set": {self.database.level_messages: level_messages}})
            if update.modified_count > 0:
                await ctx.send(f"Successfully added unique level message for level {level}.")
            else:
                await ctx.send(f"Failed to add unique level message for level {level}.")
    @levelmsg.error
    async def on_levelmsg_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid level and message.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the unique level messages configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that the level is a valid number.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def levelrole(self, ctx: commands.Context, level: int, role: Optional[discord.Role]):
        """Sets the role given by a specific level, or removes the entry for that level if no input is provided"""
        level_roles = await self.database.get_config(ctx.guild.id, self.database.level_roles)
        level_roles = level_roles if level_roles else {}
        if not role:
            if str(level) in level_roles:
                del level_roles[str(level)]
                await self.database.update_config(ctx.guild.id, {"$set": {self.database.level_roles: level_roles}})
                await ctx.send(f"Successfully removed unique level role for level {level}.")
            else:
                await ctx.send(f"No unique level role found for level {level}.")
        else:
            level_roles = {str(level): role.id}
            update = await self.database.update_config(ctx.guild.id, {"$set": {self.database.level_roles: level_roles}})
            if update.modified_count > 0:
                await ctx.send(f"Successfully added unique level role for level {level}.")
            else:
                await ctx.send(f"Failed to add unique level role for level {level}.")
    @levelrole.error
    async def on_levelrole_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid level and role.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the level roles configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that there is a valid level number and role in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")  
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def leveltoggle(self, ctx: commands.Context):
        """Toggles levels in the server, by either enabling or disabling it."""
        await config.update_bool(ctx, self.database, self.database.levels_enabled, "levels in the server")
    @leveltoggle.error
    async def on_leveltoggle_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("No arguments required, just do m?leveltoggle")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to enable/disable levels in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def lvlblacklist(self, ctx: commands.Context, item: Optional[Union[discord.abc.GuildChannel, discord.User, discord.Member, discord.Role]]):
        """Updates the list of channels/users/roles blacklisted from gaining XP (Providing no input resets the list)"""
        await config.update_id_list(ctx, self.database, self.database.level_blacklist, item, "level blacklist")
    @lvlblacklist.error
    async def on_lvlblacklist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel, user, or role.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the level blacklist configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel/role found in server or user.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
#---------------------------------------------------------------------------------------------------------------------------------------
#Logs configuration
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def ignored(self, ctx: commands.Context, item: Optional[Union[discord.abc.GuildChannel, discord.Role, discord.User, discord.Member]]):
        """Updates the list of channels/roles/members that won't be affected by logs (Providing no input resets the list)"""
        await config.update_id_list(ctx, self.database, self.database.log_ignores, item, "ignored logs list")
    @ignored.error
    async def on_ignored_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel, role, or user.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the log ignores list configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a channel found in server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def joinleavelog(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Sets or disables the logging channel for when members join and leave the server"""
        await config.update_id(ctx, self.database, self.database.join_leave_log, channel, "join/leave logging channel")
    @joinleavelog.error
    async def on_joinleavelog_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the join-leave log channel configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a channel found in server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def logs(self, ctx: commands.Context):
        """Displays the settings for the Logs module (server/join-leave/member/message/voice logs, log ignores)."""
        server_log = await finder.find_channel(ctx.guild, self.database, self.database.server_log)
        join_leave_log = await finder.find_channel(ctx.guild, self.database, self.database.join_leave_log)
        member_log = await finder.find_channel(ctx.guild, self.database, self.database.member_log)
        message_log = await finder.find_channel(ctx.guild, self.database, self.database.message_log)
        voice_log = await finder.find_channel(ctx.guild, self.database, self.database.voice_log)
        log_ignores = await finder.view_ids(ctx.guild, self.database, self.database.log_ignores)
        embed = discord.Embed(color=discord.Color.dark_gray(),title="Logs Configuration")
        embed.add_field(name="Server Log",value=server_log.mention if server_log else "Unknown Channel",inline=False)
        embed.add_field(name="Join/Leave Log",value=join_leave_log.mention if join_leave_log else "Unknown Channel",inline=False)
        embed.add_field(name="Member Log",value=member_log.mention if member_log else "Unknown Channel",inline=False)
        embed.add_field(name="Message Log",value=message_log.mention if message_log else "Unknown Channel",inline=False)
        embed.add_field(name="Voice Log",value=voice_log.mention if voice_log else "Unknown Channel",inline=False)
        embed.add_field(name="Log Ignores",value=log_ignores,inline=False)
        await ctx.send(embed=embed)
    @logs.error
    async def on_logs_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?logs")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view the logs configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def memberlog(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Sets or disables the logging channel which tracks member changes"""
        await config.update_id(ctx, self.database, self.database.member_log, channel, "member logging channel")
    @memberlog.error
    async def on_memberlog_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the member log channel configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a channel found in server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def messagelog(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Sets or disables the logging channel which tracks message changes"""
        await config.update_id(ctx, self.database, self.database.message_log, channel, "message logging channel")
    @messagelog.error
    async def on_messagelog_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the message log channel configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a channel found in server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def serverlog(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Sets or disables the logging channel which tracks server changes"""
        await config.update_id(ctx, self.database, self.database.server_log, channel, "server logging channel")
    @serverlog.error
    async def on_serverlog_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the server log channel configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a channel found in server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def voicelog(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Sets or disables the logging channel which tracks voice channel changes"""
        await config.update_id(ctx, self.database, self.database.voice_log, channel, "voice logging channel")
    @voicelog.error
    async def on_voicelog_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the voice log configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a channel found in server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
#---------------------------------------------------------------------------------------------------------------------------------------
#Moderation configuration
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def moderation(self, ctx: commands.Context):
        """Displays the settings for the Moderation module (ban limit, mod log, mute/quarantine roles)."""
        guild_id = ctx.guild.id
        ban_limit = await self.database.get_config(guild_id, self.database.ban_limit)
        mod_log = await finder.find_channel(ctx.guild, self.database, self.database.mod_log)
        mute_role = await finder.find_role(ctx.guild, self.database, self.database.mute_role)
        quarantine_role = await finder.find_role(ctx.guild, self.database, self.database.quarantine_role)
        embed = discord.Embed(color=discord.Color.dark_gray(),title="Moderation Configuration")
        embed.add_field(name="Ban Limit:",value=f"{ban_limit}/{RATE_LIMIT} bans for the day",inline=False)
        embed.add_field(name="Mod Log:",value=mod_log.mention if mod_log else "Unknown Channel",inline=False)
        embed.add_field(name="Mute Role:",value=mute_role.mention if mute_role else "Unknown Role",inline=False)
        embed.add_field(name="Quarantine Role:",value=quarantine_role.mention if quarantine_role else "Unknown Role",inline=False)
        await ctx.send(embed=embed)
    @moderation.error
    async def on_moderation_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?moderation")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view the moderation configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def modlogset(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Sets or disables the moderation logging channel for the server (If disabled, no moderation actions will be logged)"""
        await config.update_id(ctx, self.database, self.database.mod_log, channel, "moderation logging channel")
    @modlogset.error
    async def on_modlogset_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid text channel, or omit it if you want to disable the modlog.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel found in the server.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the mod log channel configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def muterole(self, ctx: commands.Context, role: Optional[discord.Role]):
        """Sets or disables the mute role in the server (If disabled, no mutes can occur)"""
        await config.update_id(ctx, self.database, self.database.mute_role, role, "mute role")
    @muterole.error
    async def on_muterole_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. please only provide a valid role, or omit it if you want to disable the mute role.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the mute role configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def quarantinerole(self, ctx: commands.Context, role: Optional[discord.Role]):
        """Sets or disables the quarantine role for the server (If disabled, no quarantines can occur)"""
        await config.update_id(ctx, self.database, self.database.quarantine_role, role, "quarantine role")
    @quarantinerole.error
    async def on_quarantinerole_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid role, or omit it if you want to disable the quarantine role.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the quarantine role configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
#---------------------------------------------------------------------------------------------------------------------------------------
#Roles configuration
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def rolesconfig(self, ctx: commands.Context):
        """Displays the settings for the Roles module (Sticky roles, sticky roles blacklist)."""
        guild_id = ctx.guild.id
        stickyroles = await self.database.get_config(guild_id, self.database.stickyroles)
        stickyroles_s = "Enabled" if stickyroles else "Disabled"
        sticky_blacklist = await finder.view_ids(ctx.guild, self.database, self.database.sticky_blacklist)
        embed = discord.Embed(color=discord.Color.dark_gray(),title="Roles Configuration")
        embed.add_field(name="Stickyroles",value=stickyroles_s,inline=False)
        embed.add_field(name="Sticky Blacklist:",value=sticky_blacklist,inline=False)
        await ctx.send(embed=embed)
    @rolesconfig.error
    async def on_rolesconfig_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?rolesconfig")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view the roles configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def stickyblacklist(self, ctx: commands.Context, role: Optional[discord.Role]):
        """Updates the list of roles not affected by stickyroles (Providing no input resets the list)"""
        await config.update_id_list(ctx, self.database, self.database.sticky_blacklist, role, "sticky role blacklist")
    @stickyblacklist.error
    async def on_stickyblacklist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid role, or omit it to disable the stickyroles blacklist.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the sticky blacklist configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid role in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def stickyrole(self, ctx: commands.Context):
        """Toggles the stickyrole setting, by either enabling or disabling it"""
        await config.update_bool(ctx, self.database, self.database.stickyroles, "sticky roles")
    @stickyrole.error
    async def on_stickyrole_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?stickyrole")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the stickyroles configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
#---------------------------------------------------------------------------------------------------------------------------------------
#Starboard configuration
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def defaultemote(self, ctx: commands.Context, emoji: Union[discord.Emoji, str] = "⭐"):
        """Sets the emote for use in the starboard (Uses the default star reaction if no emote is provided)"""
        if emoji and isinstance(emoji, discord.Emoji):
            if emoji.guild.id != ctx.guild.id:
                await ctx.send("Emote not available in the server.")
                return
            emote_id = emoji.id
        elif emoji and isinstance(emoji, str):
            emote_id = emoji
        else:
            emote_id = None
        if not emoji:
            update = await self.database.update_config(ctx.guild.id, {"$set": {self.database.default_emote: "⭐"}})
            if update.modified_count > 0:
                await ctx.send(f"Successfully reverted to the default starboard emote.")
            else:
                await ctx.send(f"Failed to revert to the default starboard emote. (Is it already set to the default?)")
        else:
            update = await self.database.update_config(ctx.guild.id, {"$set": {self.database.default_emote: emote_id}})
            if update.modified_count > 0:
                if isinstance(emoji, discord.Emoji):
                    await ctx.send(f"Successfully set {str(emoji)} as the default starboard emote.")
                else:
                    await ctx.send(f"Successfully set {emoji} as the default starboard emote.")
            else:
                await ctx.send(f"Failed to set this emoji as the default starboard emote (Is it already set to this emote?).")
    @defaultemote.error
    async def on_defaultemote_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid emote, or omit it to disable custom default starboard emote (Will use ⭐).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the default emote configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid emote.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def starboard(self, ctx: commands.Context):
        """Displays the settings for the Starboard module (Starboard channel, blacklist, threshold, default emote)."""
        guild_id = ctx.guild.id
        starboard_channel = await finder.find_channel(ctx.guild, self.database, self.database.starboard_channel)
        starboard_blacklist = await finder.view_ids(ctx.guild, self.database, self.database.starboard_blacklist)
        star_threshold = await self.database.get_config(guild_id, self.database.star_threshold)
        default_emote = await self.database.get_config(guild_id, self.database.default_emote)
        if isinstance(default_emote, int):
            emote = discord.utils.get(ctx.guild.emojis, id=default_emote)
            emote_s = str(emote) if emote else "Unknown emote"
        else:
            emote_s = default_emote
        embed = discord.Embed(color=discord.Color.dark_gray(),title="Starboard Configuration")
        embed.add_field(name="Starboard channel:",value=starboard_channel.mention if starboard_channel else "None",inline=True)
        embed.add_field(name="Starboard blacklist:",value=starboard_blacklist,inline=False)
        embed.add_field(name="Star threshold:",value=star_threshold,inline=False)
        embed.add_field(name="Default Emote:",value=emote_s,inline=False)
        await ctx.send(embed=embed)
    @starboard.error
    async def on_starboard_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?starboard")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view the starboard configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def starboardblacklist(self, ctx: commands.Context, item: Optional[Union[discord.abc.GuildChannel, discord.User, discord.Role]]):
        """Updates the list of banned users, roles, and channels from starboarding posts and from getting posts on starboard (Providing no input resets the list)"""
        await config.update_id_list(ctx, self.database, self.database.starboard_blacklist, item, "starboard blacklist")
    @starboardblacklist.error
    async def on_starboardblacklist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid channel, user, or role, or omit it to disable the starboard blacklist.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the starboard blacklist configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel/role found in the server or user.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def starboardchannel(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Sets or disables the channel where starred posts are made to"""
        await config.update_id(ctx, self.database, self.database.starboard_channel, channel, "starboard channel")
    @starboardchannel.error
    async def on_starboard_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid text channel, or omit it to disable the starbord channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the starboard channel configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid channel found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def starthreshold(self, ctx: commands.Context, num: Optional[int]):
        """Sets or disables the amount of stars needed to get a post to starboard (0 means starboard is disabled)"""
        await config.update_int(ctx, self.database, self.database.star_threshold, num, "starboard star threshold")
    @starthreshold.error
    async def on_starthreshold_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only include a valid number, or omit it to disable the star threshold (This will disable the starboard).")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the star threshold configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid number.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
#---------------------------------------------------------------------------------------------------------------------------------------
#Welcome configuration
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def banmessage(self, ctx: commands.Context, *, message: Optional[str]):
        """Resets/disables the ban message in the server, if no message is provided. If message is provided, it will set the default ban message to the given message."""
        await config.update_str(ctx, self.database, self.database.ban_message, message, "ban message")
    @banmessage.error
    async def on_banmessage_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. please only provide a message.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the ban message configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def joinmessage(self, ctx: commands.Context, *, message: Optional[str]):
        """Resets/disables the join message in the server, if no message is provided. If message is provided, it will set the default join message to the given message."""
        await config.update_str(ctx, self.database, self.database.join_message, message, "join message")
    @joinmessage.error
    async def on_leavemessage_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. please only provide a message.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the join message configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def leavemessage(self, ctx: commands.Context, *, message: Optional[str]):
        """Resets/disables the leave message in the server, if no message is provided. If message is provided, it will set the default leave message to the given message."""
        await config.update_str(ctx, self.database, self.database.leave_message, message, "leave message")
    @leavemessage.error
    async def on_leavemessage_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. please only provide a message.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the leave message configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def welcome(self, ctx: commands.Context):
        """Displays the settings for the Welcome module (Welcome channel, join/leave/ban messages)"""
        guild_id = ctx.guild.id
        welcome_channel = await finder.find_channel(ctx.guild, self.database, self.database.welcome_channel)
        join_message = await self.database.get_config(guild_id, self.database.join_message)
        leave_message = await self.database.get_config(guild_id, self.database.leave_message)
        ban_message = await self.database.get_config(guild_id, self.database.ban_message)
        embed = discord.Embed(color=discord.Color.dark_gray(), title="Welcome Configuration")
        embed.add_field(name="Welcome Channel", value=welcome_channel.mention if welcome_channel else "Unknown Channel", inline=False)
        embed.add_field(name="Join Message", value=join_message or "Not set", inline=False)
        embed.add_field(name="Leave Message", value=leave_message or "Not set", inline=False)
        embed.add_field(name="Ban Message", value=ban_message or "Not set", inline=False)
        await ctx.send(embed=embed)
    @welcome.error
    async def on_welcome_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?welcome")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to view the welcome configuration.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def welcomechannel(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Resets/disables the welcome channel in the server, if no channel is provided. If channel is provided, it will set the welcome channel to the given channel."""
        await config.update_id(ctx, self.database, self.database.welcome_channel, channel, "welcome channel")
    @welcomechannel.error
    async def on_welcomechannel_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. please only provide a valid channel.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to edit the welcome channel configuration.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a valid text channel found in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def chelp(self, ctx: commands.Context, command: str):
        if command in config_commands_dict:
            await ctx.send(config_commands_dict[command])
        elif command in emd_commands_dict and ctx.guild.id == EMD_SERVER_ID:
            await ctx.send(emd_commands_dict[command])
        elif command in giveaway_commands_dict:
            await ctx.send(giveaway_commands_dict[command])
        elif command in level_commands_dict:
            await ctx.send(level_commands_dict[command])
        elif command in moderation_commands_dict:
            await ctx.send(moderation_commands_dict[command])
        elif command in reminder_commands_dict:
            await ctx.send(reminder_commands_dict[command])
        elif command in tmc_commands_dict and ctx.guild.id == TMC_SERVER_ID:
            await ctx.send(tmc_commands_dict[command])
        elif command in tnb_commands_dict and ctx.guild.id == TNB_SERVER_ID:
            await ctx.send(tnb_commands_dict[command])
        elif command in utility_commands_dict:
            await ctx.send(utility_commands_dict[command])
        elif command in voicelink_commands_dict:
            await ctx.send(voicelink_commands_dict[command])
        else:
            await ctx.send("Command not found.")

async def setup(bot: commands.Bot): 
    """Sets up the Config cog"""
    await bot.add_cog(Config(bot))
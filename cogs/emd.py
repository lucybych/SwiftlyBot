from discord.ext import commands
from typing import List
from utility.finder import has_roles
import asyncio
import discord
import random
import re

blacklist_roles = [385963065469829120,845424391810580480,385965306696433668,385965575773618190,385985214796791808,385985247613026305,584478303818219536,619264009903800359,591349014889234531,619273032053162015,607328447689261098]
blacklist_roles_2 = [385963065469829120,845424391810580480,385965306696433668,385965575773618190]
blacklist_roles_3 = [385975834701463552,385975936585039883,385975983632809986,403294886155255823,559533095368523797,559533163215585290,559533193661906956,385974149018812416,743588174357332048,385974090839752704]
emd_server_id = 385956732888678402
level_roles = [385976059406843904, 385975834701463552, 385975936585039883, 385975983632809986, 403294886155255823, 559533095368523797, 559533163215585290, 559533193661906956]
mod_chat_id = 385966411165728800
mod_log_id = 385973126623789076
mute_role_id = 385978553935593472
self_intros_id = 385974149018812416
self_intros_id = 1336837177484771339
shame_images = ["https://i.imgur.com/Yca8mcX.png","https://i.imgur.com/SWPLesj.png"]
sl_images = ["https://i.imgur.com/vPOPWTo.png", "https://i.imgur.com/XYxjdWR.png", "https://i.imgur.com/k7wz69v.png", "https://i.imgur.com/OhWEiQF.png", "https://i.imgur.com/pOV7mRh.png", "https://i.imgur.com/dZKhFsE.png", "https://i.imgur.com/gl7Rbh6.png", "https://i.imgur.com/dHSGuBl.png", "https://i.imgur.com/lGnVMuv.png", "https://i.imgur.com/FuYokju.png", "https://i.imgur.com/6rbamK5.png", "https://i.imgur.com/N4b0SVB.png", "https://i.imgur.com/45R2ISm.png", "https://i.imgur.com/iZhOBJq.png", "https://i.imgur.com/KgHu3bm.png", "https://i.imgur.com/vSmFbYz.png", "https://i.imgur.com/Ukhb3xZ.png", "https://i.imgur.com/TyQozmx.png", "https://i.imgur.com/1vqPe7Y.png", "https://i.imgur.com/cUVxxW9.png", "https://i.imgur.com/8q3Ifd5.png"]
staff_roles = [385965575773618190,385965306696433668,385979606194454538]

class EMD(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the EMD module"""
        self.bot = bot
    
    async def has_link(self, content: str) -> bool:
        """Checks if a user's message in EMD contains a link, which would trigger the link prevention automod"""
        url_pattern = re.compile(r'https?://(?:www\.)?\S+|www\.\S+')
        return bool(url_pattern.search(content))

    async def is_valid_nickname(self, nickname: str) -> bool:
        """Checks if a user's name/nickname in EMD has 3 valid alphanumeric characters"""
        if not nickname:
            return False
        return bool(re.search(r'[a-zA-Z0-9]{3}', nickname))

    async def staff_check(self, ctx: commands.Context) -> bool:
        """Check if the user has staff roles."""
        if ctx.guild.id != emd_server_id:
            return False
        is_staff = await has_roles(ctx.author, staff_roles)
        if not is_staff:
            await ctx.send("You need to be staff to use this command, to help avoid spam.")
        return is_staff
    
    @commands.command()
    async def anchor(self, ctx: commands.Context):
        """For EMD staff to get pinged in staff chat"""
        if ctx.guild.id == emd_server_id:
            if not await has_roles(ctx.author, staff_roles):
                raise commands.MissingPermissions(["No staff roles"])
            channel = ctx.guild.get_channel(mod_chat_id)
            if channel:
                await channel.send(f"Here is your ping anchor, {ctx.author.mention}! ⚓")
            else:
                raise discord.InvalidData
        else:
            await ctx.send("Command not found.")
    @anchor.error
    async def on_anchor_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments, just do m?anchor.")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("You need to be staff to use this command.")
        elif isinstance(error, discord.InvalidData) or isinstance(error, discord.HTTPException):
            await ctx.send("Failed to retrieve mod_chat channel and/or send to the channel.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I cannot perform this action, due to missing permissions (Make sure I can view and send messages to the mod_chat channel).")
        elif isinstance(error, discord.NotFound):
            await ctx.send("mod_chat channel cannot be found. Contact swiftlynerd so that she can ensure the channel ID is accurate.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    async def anchovy(self, ctx: commands.Context):
        """For EMD staff to get pinged in staff chat, but fishier 🐟"""
        if ctx.guild.id == emd_server_id:
            if not await has_roles(ctx.author, staff_roles):
                raise commands.MissingPermissions(["No staff roles"])
            channel = ctx.guild.get_channel(mod_chat_id)
            if channel:
                await channel.send(f"Here is your ping anchovy, {ctx.author.mention}! 🐟")
            else:
                raise discord.InvalidData
    @anchovy.error
    async def on_anchovy_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments, just do m?anchovy.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You need to be staff to use this command.")
        elif isinstance(error, discord.InvalidData) or isinstance(error, discord.HTTPException):
            await ctx.send("Failed to retrieve mod_chat channel and/or send to the channel.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I cannot perform this action, due to missing permissions (Make sure I can view and send messages to the mod_chat channel).")
        elif isinstance(error, discord.NotFound):
            await ctx.send("mod_chat channel cannot be found. Contact swiftlynerd so that she can ensure the channel ID is accurate.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    async def betterdiscord(self, ctx: commands.Context):
        """For EMD staff to use in regards to BetterDiscord or other modified Discord clients"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.blue(),title="\"Is using BetterDiscord or other modified clients banned?\"")
            embed.add_field(name="",value="**__No, using BetterDiscord is not ban-worthy.__**"
                            +"\n\nSome relevant bits from the [Discord TOS](https://discord.com/terms#:~:text=Third%20Party%20Software%20and%20Services.):"
                            +"\n\n> *Our services may allow you to access apps, bots, or other products, features or services developed by third parties. It’s your choice whether to use these products [...]  While these third party services do need to follow all policies that apply to them [...] Discord is not responsible for products developed by third parties.*"
                            +"\n\nIn summary, modified clients like BetterDiscord are okay; Discord is simply saying that they are not responsible if a modified client harms you.",inline=False)
            embed.add_field(name="",value="\n\nIn general, Discord simply does not care about BetterDiscord; you will not be banned from here or Discord in general for using it properly. Moreover, Discord staff often use it, sometimes help support it or develop for it, and use it to see what features the userbase wants. Discord even approved them to get [a boosted member cap](https://support.discord.com/hc/en-us/articles/360052841734-Server-Member-Cap-Increases-), which obviously means Discord is okay with BetterDiscord as well."
                            +"\n\n**__In short: using BetterDiscord as provided and in a proper way is 100% safe for you and your account.__**",inline=False)
            embed.add_field(name="",value="\n\nFor those interested, you can also use the following links:"
                            +"\n\n- [BetterDiscord's website](https://betterdiscord.app/)"
                            +"\n- [BetterDiscord's Github](https://github.com/BetterDiscord/BetterDiscord)"
                            +"\n- [BetterDiscord's support server](https://discord.gg/0Tmfo5ZbORCRqbAd)"
                            +"\n- [Vencord](https://vencord.dev/download/) *(similar to BD, but less laggy - better, in the staff's opinion)*"
                            +"\n- [Have a free meme](https://i.imgur.com/QalN0Zj.png)",inline=False)
            await ctx.send(embed=embed)
    @betterdiscord.error
    async def on_betterdiscord_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments, just do m?betterdiscord.")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['dead'])
    async def deadchat(self, ctx: commands.Context):
        """For EMD staff to use when someone mentions if/when a chat is inactive"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.red(),title="On the matter of saying \"dead chat\" and such...")
            embed.add_field(name="",value="While it has become somewhat of a meme on Discord, we would like to ask you refrain from using the \"dead chat lol\" meme here. This is because..."
                            +"\n\n- ...it doesn't suddenly make the chat more active."
                            +"\n- ...it often actually makes chat even more dead."
                            +"\n- ...just because the chat is slower than you like, doesn't mean that it's really dead."
                            +"\n- ...frankly, it just gets on people's nerves and contributes nothing of value conversationally."
                            +"\n\nSo, please refrain from memeing about the chat's activity level here. At times the chat will be blazing fast, and at others slow and chill. And nothing is wrong with that, even if it doesn't quite suit you.",inline=False)
            await ctx.send(embed=embed)
    @deadchat.error
    async def on_deadchat_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments, just do m?deadchat.")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def eee(self, ctx: commands.Context):
        """Posts an invite to the spinoff server Eevee's Emote Encyclopedia"""
        if ctx.guild.id == emd_server_id:
            await ctx.send("Want more emotes? Check out our emote-focused spinoff server, Eevee's Emote Encyclopedia, which features over 200 emote servers, including:"
                        +"\n\n- servers for portraits from PMD titles"
                        +"\n- emotes of various Pokemon series assets"
                        +"\n- servers for games, streamers, and more, popular with EMD members for emotes"
                        +"\n- EMD's overflow emote servers, which can be found in #extra_emd_emotes!"
                        +"\n\nhttps://discord.gg/CzRP6pH")
    @eee.error
    async def on_eee_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments, just do m?eee.")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def emd(self, ctx: commands.Context):
        """Posts EMD's permanent server invite"""
        if ctx.guild.id == emd_server_id:
            await ctx.send("Want to invite your friends to Eevee's Mystery Dungeon? Here's a permanent link to the server!\n\nhttps://discord.gg/emd")
    @emd.error
    async def on_emd_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments, just do m?emd.")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def emotes(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about emotes"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(), title="\"Why can't I use external emotes? I have Nitro!\"")
            embed.add_field(name="",value="EMD prevents the posting of external emotes until you hit **__Level 1__** in the server."
                            +"\n\nThe reason is because we don't want people posting inappropriate emotes and such to troll the server the second they join."
                            +"\n\n*(Other level-based perks are described [here](https://discord.com/channels/385956732888678402/385972526590722048/725839644016640022).)*",inline=False)
            await ctx.send(embed=embed)
    @emotes.error
    async def on_emotes_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?emotes")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['rescue'])
    async def ert(self, ctx: commands.Context):
        """Posts an invite to the spinoff server Eevee's Rescue Team"""
        if ctx.guild.id == emd_server_id:
            await ctx.send("Need a rescue in a PMD game? Be sure to check out our spinoff server, Eevee's Rescue Team, to get some help!"
                       +"\n\nhttps://discord.gg/E57gMQq")
    @ert.error
    async def on_ert_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?ert")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def introcl(self, ctx: commands.Context):
        """Goes through EMD's self-introductions channel and removes all intros from those who posted multiple or who have left the server"""
        if ctx.guild.id != emd_server_id:
            return
        if not await has_roles(ctx.author, staff_roles):
            raise commands.MissingPermissions(["No staff roles"])
        intro_channel = ctx.guild.get_channel(self_intros_id)
        if intro_channel:
            latest_messages = {}
            messages: List[discord.Message] = []
            async for message in intro_channel.history(limit=None):
                if message.author not in ctx.guild.members:
                    messages.append(message)
                else:
                    if message.author in latest_messages:
                        messages.append(message)
                    else:
                        latest_messages[message.author] = message
            num_deleted = 0
            if messages:
                for message in messages[1:]:
                    try:
                        await message.delete()
                        num_deleted += 1
                    except Exception:
                        pass
                if num_deleted > 0:
                    await ctx.send(f"🧹 Cleaned up {num_deleted} messages!", delete_after=5)
                else:
                    await ctx.send(f"No messages to delete!",delete_after=5)
                    await ctx.message.delete()
            else:
                await ctx.send("Nothing to clean up!", delete_after=5)
            if ctx.channel.id == self_intros_id:
                await ctx.message.delete()
        else:
            raise discord.InvalidData
    @introcl.error
    async def on_introcl_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?introcl")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to clean up intros, you must have the Staff, Managers, or Admin roles.")
        elif isinstance(error, discord.InvalidData) or isinstance(error, discord.HTTPException):
            await ctx.send("Failed to retrieve self_introductions channel, its history, and/or send to the channel.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I cannot perform this action, due to missing permissions (Make sure I can view the self_introductions channel, its history, and send messages in this channel).")
        elif isinstance(error, discord.NotFound):
            await ctx.send("mod_chat channel cannot be found. Contact swiftlynerd so that she can ensure the channel ID is accurate.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def lvlinfo(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about levels and the leveling system"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="Level-Up System Information")
            embed.add_field(name="",value="Some math on our EXP./level-up system may be found [here](https://i.imgur.com/lZ5Wq9b.png). *(This was originally designed for Mee6, but Carl-bot's mechanics are set to be identical.)*"
                            +"\n\nLevel-based perks can be found [here](https://discord.com/channels/385956732888678402/385972526590722048/1096633121958547588).",inline=False)
            await ctx.send(embed=embed)
    @lvlinfo.error
    async def on_lvlinfo_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?lvlinfo")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['links'])
    async def link(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about posting/embedding links or attaching/posting files"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(), title="\"Why can't I post files or links here?\"")
            embed.add_field(name="",value="You cannot post files, links, images, videos, or embeds in this server until you reach **__Level 1.__** If you try to post a link anyways, your post will be auto-deleted by a bot; if you do this twice, you will be muted automatically. We apologize for this minor inconvenience, but it's a good measure to help prevent trolls; Level 1 does not take much time to reach."
                            +"\n\nMoreover, while you will be able to post links at Level 1, you won't be able to post files or have links embed in <#385974351905685505> or <#596235298728312832> until you reach **__Level 70.__** This is done in order to prevent spam; <#385974292778713106> can be used in the meantime. *(Even then, for those above Level 70, we want media posted in the gens to be relevant, not random stuff.)*"
                            +"\n\n*(Other level-based perks are described [here](https://discord.com/channels/385956732888678402/385972526590722048/725839644016640022).)*",inline=False)
            await ctx.send(embed=embed)
    @link.error
    async def on_link_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?link")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")

    @commands.command()
    async def nick(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about changing their nickname"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="\"How do I change my nickname?\"")
            embed.add_field(name="",value="In order to help people get used to our rules on usernames/nicknames, you can't change your own nickname until you reach Level 10. If you want to change your name before then, you can ask a member of the staff to do it for you; just tell them what name you want in <#743588174357332048>!"
                            +"\n\nOur rules on nicknames can be found [here](https://discord.com/channels/385956732888678402/385972494429061131/782737583154397224)."
                            +"\n\n*(Other level-based perks are described [here](https://discord.com/channels/385956732888678402/385972526590722048/725839644016640022).)*",inline=False)
            await ctx.send(embed=embed)
    @nick.error
    async def on_nick_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?nick")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")      

    @commands.command()
    async def nsfw(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about NSFW and the associated channels"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(), title="\"Do you have NSFW channels?\" / \"Where are the NSFW channels?\"")
            embed.add_field(name="",value="This server does have NSFW channels; however, they're not available until you hit Level 20. You'll have to contact a mod to confirm your age; we will let you in, if we think you should be in those channels. (We don't let in people who are known to be here just for the NSFW stuff, or people who have a tendency to make people feel creeped out or uncomfortable. That stuff falls very out of line with our server culture.)"
                            +"\n\nOnce you've gotten the 18+ role from a mod, you'll be able to get the NSFW role from #age_restricted-channels."
                            +"\n\n*(Other level-based perks are described [here](https://discord.com/channels/385956732888678402/385972526590722048/725839644016640022).)*",inline=False)
            await ctx.send(embed=embed)
    @nsfw.error
    async def on_nsfw_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?nsfw")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def offserver(self, ctx: commands.Context):
        """For EMD staff to use when determining if a person off-server should be banned"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="Roxy's criteria for off-server bans:")
            embed.add_field(name="",value="*Evaluate the actual risk to the server and its members by the following criteria:*"
                            +"\n\n(1) **Severity of the user's deeds** -- Is it something so extreme that we don't want even a chance of happening here?"
                            +"\n\n(2) **Credibility of the source and the evidence presented** -- Do we know and trust the source of the information well enough to know they aren't lying, and is the evidence they have actually enough to back up the severity of their claims?"
                            +"\n\n(3) **Potential of the user to actually cause issues here** -- Are they actually likely to end up here, and if so, are they likely to repeat their previous actions?",inline=False)
            await ctx.send(embed=embed)
    @offserver.error
    async def on_offserver_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?offserver")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def openoriginal(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about large/elongated images"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(), title="\"I can't read this long picture, it's too blurry.\"")
            embed.add_field(name="",value="*(Often the situation looks like [this](https://i.imgur.com/BzmBvsY.png).)*"
                            +"\n\nYou need to open the original file in your browser."
                            +"\n\nOn desktop, click on the image, and then on the \"Open in Browser\" button below the image. ([Picture](https://i.imgur.com/QIaYzfX.png).)"
                            +"\n\nOn mobile, tap the image, then the three dots in the top-right, and then on the \"Open in Browser\" option. ([Picture](https://i.imgur.com/76DBuEa.png).)",inline=False)
            await ctx.send(embed=embed)
    @openoriginal.error
    async def on_openoriginal_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?openoriginal")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def rando(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about a random user getting banned"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="\"Why was this random person banned?\"")
            embed.add_field(name="",value="Likely, it was due to flagrant disregard of the rules as a fresh or inactive member of the server."
                            +"\n\nIn general, questions like these - from people who have no relation to the banned person - are irksome to deal with, because they come off as one of the following:"
                            +"\n\n- Being nosy or a busybody. Curiosity is nice and all, but there's a time and place for everything."
                            +"\n\n- Fueling a need to witness and understand drama (or what the internet loosely considers it); this one is self-explanatory."
                            +"\n\n- Openly distrusting staff (of this server or in general) on principle, and seeing yourself as an auditor of sorts. *(Truthfully, if you're distrustful of the staff here, why are you even here?)*",inline=False)
            embed.add_field(name="",value="\n\nThe issue we have with this is:"
                            +"\n\n- Staff document the majority of bans thoroughly on this server in a private channel, as a \"cover your ass\" measure and for communication purposes with ourselves or other servers/people. *(This channel will not be made public, since it contains personal info and NSFL content/links.)*",inline=False)
            embed.add_field(name="",value="\n\n- In a server of 20,000+ people, having to field this question multiple times for the same ban as we have in the past - all from people who really don't care and are \"just curious\" - is really not worth the effort. \"5634th troll that spammed slurs\" is really not something that needs elaboration."
                            +"\n\nTransparency is valued amongst the staff, and we have no issues clarifying the specific details of a ban to those who ultimately ***have a genuine need to know.*** Constantly having to answer to people's apparent need for drama, to have their curiosity sated, or to feel like you're looking over our shoulder at every turn, however, not so much.",inline=False)
            await ctx.send(embed=embed)
    @rando.error
    async def on_rando_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?rando")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def reply(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about replying to other users"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="Pings When Replying")
            embed.add_field(name="",value="**Replying is able to ping people.** When you opt to reply to someone, by default it pings them. You can turn this off by clicking/tapping the option in yellow [here](https://i.imgur.com/8OaumBw.png). You can tell when a reply has pinged someone based on whether there is an \"@\" in the quoted text ([example](https://i.imgur.com/QAtxS07.png))."
                            +"\n\nBy default, Discord sadly has the reply ping left \"ON\", i.e. by default your replies ping people unless turned off. If you have [BetterDiscord](https://betterdiscord.app/), a plugin to make the default be \"OFF\" is [here](https://cdn.discordapp.com/attachments/478310940975038482/1085072352636841995/NRM.plugin.js). Holding Shift as you click the button to start a reply also defaults it to being \"OFF\"."
                            +"\n\nPlease respect people's wishes to not be pinged. *(And those who do not want to be pinged, please include it in your username/nickname so we know.)*",inline=False)
            await ctx.send(embed=embed)
    @reply.error
    async def on_reply_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?reply")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def roleinfo(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about roles and/or how to obtain them"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="Where can I get roles?")
            embed.add_field(name="",value="Most of our roles are found in either Channels and Roles or our \"Role Management\" category, near the top of the channel list! ([Here's a picture.](https://i.imgur.com/iPs6o9o.png))"
                            +"\n\nEach channel has a particular purpose in mind:"
                            +"\n\n<id:customize> - Change your color, notifications for server events, announcements, and free games!"
                            +"\n<#643958100109295626> - For age restricted channels (Such as NSFW or selfies) (Note you must both be Level 20 or above and have the 18+ role)"
                            +"\n<#986717375707635772> - For level-locked channels (Such as politics or giveaways) (Note that you must be at least Level 20 or above to view this channel and the channels locked behind levels)",inline=False)
            embed.add_field(name="",value="\n\nOther roles you cannot get yourself include:"
                            +"\n\n- Roles given to mods, staff, & bots"
                            +"\n- Roles given as a punishment *(mutes, channel bans, etc.)*"
                            +"\n- Roles for custom colors *(given as a level perk or to staff/patrons)*"
                            +"\n- Roles for levels & their perks *(level system explained [here](https://discord.com/channels/385956732888678402/385972526590722048/725839644016640022))*"
                            +"\n- Roles to reward server boosters & patrons"
                            +"\n\nThat should describe basically every role here.",inline=False)
            await ctx.send(embed=embed)
    @roleinfo.error
    async def on_roleinfo_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?roleinfo")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def scam(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about scams and hacks on Discord"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.purple(),title="Recent Discord Scams & Hacking:")
            embed.add_field(name="",value="A friend of the server put together a Google Doc describing some common Discord scams that have gone around or are currently going around, and some tips on how to protect yourself from them."
                            +"\n\nYou can read her write-up at this link: <https://bit.ly/3fu5wIl>",inline=False)
            await ctx.send(embed=embed)
    @scam.error
    async def on_scam_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?scam")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def selfies(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about selfies and/or the selfies channel"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="Is there a selfies channel?")
            embed.add_field(name="",value="This server does have a selfie channel; however, it is not available until you hit Level 20. Even then, you'll have to contact a mod to confirm your age and then you'll be able to get the Selfies role from #level-locked_channels."
                            +"\n\n(The age and level limits are to keep minors safe and help prevent creeps. The selfies channel is still SFW despite the age limit. For many of the same reasons, please refrain from posting selfies outside of the selfies channel.)"
                            +"\n\n*(Other level-based perks are described [here](https://discord.com/channels/385956732888678402/385972526590722048/725839644016640022).)*",inline=False)
            await ctx.send(embed=embed)
    @selfies.error
    async def on_selfies_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?selfies")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['silenceliberal'])
    async def sl(self, ctx: commands.Context, member: discord.Member):
        """For EMD staff to use to temporarily mute users, for fun!"""
        if ctx.guild.id == emd_server_id:
            if not await has_roles(ctx.author, staff_roles):
                raise commands.MissingPermissions(["No staff roles"])
            mute_role = ctx.guild.get_role(mute_role_id)
            if mute_role:
                await member.add_roles(mute_role)
                await ctx.send("*(Muted for 36 seconds.)*\n" + random.choice(sl_images))
                await asyncio.sleep(36)
                await member.remove_roles(mute_role)
            else:
                raise commands.RoleNotFound
    @sl.error
    async def on_sl_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Too many arguments provided. Please only provide a single valid user.")
        elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.CommandInvokeError):
            await ctx.send("You need to be staff to use this command to prevent abuse. https://i.imgur.com/BqyTn8y.png")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("Mute role not found. Contact swiftlynerd to ensure the mute role ID is properly configured.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to add/remove this role to/from users.")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error occurred when adding/removing the mute role. Make sure that the mute role is in the server.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid input. Ensure that it is a user in the server.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['trades'])
    async def trade(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about Pokemon trades"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="Looking for Pokemon trades?")
            embed.add_field(name="",value="We're not a trading server, and [as the rules note](https://discord.com/channels/385956732888678402/385972494429061131/782737693079109693) we generally don't appreciate people who aren't active in the server using us to get trades done. Plenty of dedicated Discord servers exist (try looking on [Discord's site](https://discord.com/servers?query=pokemon+trades), [Discord.me](https://discord.me/servers?search=pokemon+trades&language=1), or [Disboard](https://disboard.org/search?keyword=pokemon+trades)), as do forums like [GameFAQs](https://gamefaqs.gamespot.com/), [Serebii](https://forums.serebii.net/), [Smogon](https://www.smogon.com/forums/forums/wi-fi.53/), and [any number of subreddits](https://www.reddit.com/search/?q=pokemon+trades&type=sr), so please use those instead.",inline=False)
            await ctx.send(embed=embed)
    @trade.error
    async def on_trade_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?trade")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['trolls'])
    async def troll(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about why a troll got banned"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="\"Why were they banned?\" / \"What happened?\"")
            embed.add_field(name="",value="Asking why someone got banned and a mod posted this in response? Presumably that person had just joined or barely used the server? It's because the person was a troll, and we don't put up with their crap here. You don't really need to know the details of why *(unless you're a friend of theirs or something - we don't appreciate people being nosy for its own sake)*, but usually that can encompass anything of *(but is __not__ limited to)*:"
                            +"\n\n- Posting blatantly homophobic, transphobic, etc. things"
                            +"\n- Posting blatantly racist things"
                            +"\n- Posting Nazi sympathism or other such things"
                            +"\n- Joining with a Nazi or overtly anti-LGBT pfp and/or username"
                            +"\n- Posting overtly NSFW stuff"
                            +"\n- Advertising on join (e.g. posting server invites)"
                            +"\n\n... or any number of other things.",inline=False)
            embed.add_field(name="",value="\n\nWe've made this command because we get this question frequently enough to be an annoyance, with the same common-sense response given every time. This is made increasingly worse by the fact that all trolls want is a reaction and your attention, and talking about them after the fact furthers that."
                            +"\n\n**tl;dr version --** If someone who just joined got banned, and you have no relation to them whatsoever, all you need to know is they were acting in bad faith on join, or were some kind of other bad actor. It's best to simply ignore their existence and move on.",inline=False)
            await ctx.send(embed=embed)
    @troll.error
    async def on_troll_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?troll")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['vcs'])
    async def vc(self, ctx: commands.Context):
        """For EMD staff to use when someone asks about voice channels"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="\"Do you have VCs?\" / \"Where are the VCs?\"")
            embed.add_field(name="",value="This server does have several voice channels; however, they're not available until you reach Level 10. This is to help prevent trolls from entering the server and immediately bugging the VCs, on top of how hard they are to be moderated in general."
                            +"\n\n*(Other level-based perks are described [here](https://discord.com/channels/385956732888678402/385972526590722048/725839644016640022).)*",inline=False)
            await ctx.send(embed=embed)
    @vc.error
    async def on_vc_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?vc")
        elif isinstance(error, discord.HTTPException):
            await ctx.send("Error sending the embedded message.")
        elif isinstance(error, discord.Forbidden):
            await ctx.send("I do not have permission to send messages in this channel.")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
                  
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Checks for if a user has a valid nickname in EMD (at least 3 alphanumeric characters) and changes it to \"Request New Nickname\" if it violates these rules"""
        if member.guild.id != emd_server_id:
            return
        if not await self.is_valid_nickname(member.global_name) or not await self.is_valid_nickname(member.display_name) or await self.is_valid_nickname(member.name):
            await member.edit(nick="Request New Nickname")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Checks for if a user in EMD either posted @everyone or @here, posted a deez-nuts-esque joke, posted a weed-cat joke, or posted a link. If the 
        user does not have any of the \"safe\" roles, they will be unofficially warned"""
        if message.author.bot:
            return
        if message.guild.id != emd_server_id:
            return 
        if "@everyone" in message.content or "@here" in message.content and not await has_roles(message.author, blacklist_roles_3):
            embed = discord.Embed(color=discord.Color.dark_gray())
            embed.set_image(url=random.choice(shame_images))
            await message.channel.send(content=f"{message.author.mention} -- That didn't ping anybody, genius.", embed=embed)
            await message.delete()
        if any(word in message.content.lower() for word in ["bophades", "dees nuts", "deez", "deez nuts", "ligma", "sugondese"]) and not await has_roles(message.author, blacklist_roles):
            embed = discord.Embed(color=discord.Color.red())
            embed.add_field(name="",value=f"{message.author.mention}, please don't post/mention inappropriate jokes like this in the server [as mentioned explicitly in the rules](https://discord.com/channels/385956732888678402/385972494429061131/782737871504277545).",inline=False)
            await message.delete()
            await message.channel.send(embed=embed, delete_after=5)
        if "weed cat" in message.content.lower() and not await has_roles(message.author, blacklist_roles_2):
            embed = discord.Embed(color=discord.Color.red())
            embed.add_field(name="",value=f"{message.author.mention}, please don't post drug jokes in the server ([link to the rule](https://discord.com/channels/385956732888678402/385972494429061131/782737534559453254)).",inline=False)
            await message.delete()
            await message.channel.send(embed=embed, delete_after=5)
        has_link = await self.has_link(message.content)
        if has_link and not await has_roles(message.author, level_roles):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, we do not allow links until Level 1, as an anti-troll measure.",delete_after=5)
            channel = message.guild.get_channel(mod_log_id)
            if channel:
                embed = discord.Embed(color=discord.Color.red(),title="",description="",timestamp=discord.utils.utcnow())
                embed.add_field(name="",value=f"**Message sent by {message.author.mention} deleted in {message.channel.mention}**\n{message.content}", inline=False)
                embed.add_field(name="Reason",value="Contains link",inline=False)
                embed.set_footer(text=f"ID: {message.author.id}")
                await channel.send(embed=embed)
        if not message.content.startswith("m?"):
            await self.bot.process_commands(message)

async def setup(bot: commands.Bot): 
    """Sets up the EMD cog"""
    await bot.add_cog(EMD(bot))
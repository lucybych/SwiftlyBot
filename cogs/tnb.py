from discord.ext import commands
from utility.finder import has_roles
import discord

tnb_server_id = 932843700751597608
staff_roles = [933217733603123240,933217763957284956]

class TNB(commands.Cog):
    def __init__(self, bot):
        """Initializes the TNB module"""
        self.bot = bot
    
    async def staff_check(self, ctx: commands.Context) -> bool:
        """Check if the user has staff roles."""
        if ctx.guild.id != tnb_server_id:
            return False
        is_staff = await has_roles(ctx.author, staff_roles)
        if not is_staff:
            await ctx.send("You need to be staff to use this command, to help avoid spam.")
        return is_staff
        
    @commands.command()
    async def betterdiscord(self, ctx: commands.Context):
        """Better Discord copypasta, for when users ask about BetterDiscord, Vencord, or any other modified clients."""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.blue(),title="\"Is using BetterDiscord or other modified clients banned?\"")
            embed.add_field(name="",value="**__No, using BetterDiscord is not ban-worthy.__**"
                            +"\n\nSome relevant bits from the [Discord TOS](https://discord.com/terms#:~:text=Third%20Party%20Software%20and%20Services.):"
                            +"\n\n> *Our services may allow you to access apps, bots, or other products, features or services developed by third parties. It’s your choice whether to use these products [...]  While these third party services do need to follow all policies that apply to them [...] Discord is not responsible for products developed by third parties.*"
                            +"\n\nIn summary, modified clients like BetterDiscord are okay; Discord is simply saying that they are not responsible if a modified client harms you.",inline=False)
            embed.add_field(name="",value="\n\nIn general, Discord simply does not care about BetterDiscord; you will not be banned from here or Discord in general for using it properly. Moreover, Discord staff often use it, sometimes help support it or develop for it, and use it to see what features the userbase wants. Discord even approved them to get [a boosted member cap](https://support.discord.com/hc/en-us/articles/360052841734-Server-Member-Cap-Increases-), which obviously means Discord is okay with BetterDiscord as well.",inline=False)
            embed.add_field(name="",value="\n\n**__In short: using BetterDiscord as provided and in a proper way is 100% safe for you and your account.__**"
                            +"\n\nFor those interested, you can also use the following links:"
                            +"\n\n- [BetterDiscord's website](https://betterdiscord.app/)""\n- [BetterDiscord's Github](https://github.com/BetterDiscord/BetterDiscord)"
                            +"\n- [BetterDiscord's support server](https://discord.gg/0Tmfo5ZbORCRqbAd)"
                            +"\n- [Vencord](https://vencord.dev/download/) *(similar to BD, but less laggy - better, in the staff's opinion)*"
                            +"\n- [Have a free meme](https://i.imgur.com/QalN0Zj.png)")
            await ctx.send(embed=embed)
    @betterdiscord.error
    async def on_betterdiscord_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?betterdiscord")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['dead'])
    async def deadchat(self, ctx: commands.Context):
        """Dead chat copypasta, for staff use in TNB when users ask about dead chat or bring up how dead the chat is."""
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
            await ctx.send("Command requires no extra arguments. Please only do m?deadchat or m?dead")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def nick(self, ctx: commands.Context):
        """Nickname copypasta, for staff use in TNB when users ask about nicknames or changing their nickname."""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="How do I change my nickname?")
            embed.add_field(name="",value="In order to help people get used to our rules on usernames/nicknames, you can't change your own nickname until you reach Level 10. If you want to change your name before then, you can ask a member of the staff to do it for you; just tell them what name you want in <#932853269636730880>, or feel free to DM them instead!"
                            +"\n\nOur rules on nicknames can be found in the rules channel: https://discord.com/channels/932843700751597608/932849190109851669/958755071020109855",inline=False)
            await ctx.send(embed=embed)
    @nick.error
    async def on_nick_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?nick")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def nsfw(self, ctx: commands.Context):
        """NSFW copypasta, for staff use in TNB when users ask about NSFW or NSFW channels."""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="\"Do you have NSFW channels?\" / \"Where are the NSFW channels?\"")
            embed.add_field(name="",value="This server does *not* have any NSFW channels. We are not an NSFW server, nor will we be adding any NSFW channels in the future. This is meant to be a more mature environment, but NSFW things do not fall in line with the culture we wish to have in the server. If you're here just for NSFW, please find another server for that kind of stuff.")
            await ctx.send(embed=embed)
    @nsfw.error
    async def on_nsfw_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?nsfw")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def roles(self, ctx: commands.Context):
        """Roles copypasta, for staff use in TNB when users ask about roles."""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.blue(),title="Where can I get roles?")
            embed.add_field(name="",value="Most of our assignable roles can be found in Channels and Roles, which contains:"
                            +"\n\n- Notification roles, such as for server announcements, channel announcements, and welcoming users into the server"
                            +"\n- Color roles, which can customize what color you are in the server. There are also custom colors, but these require becoming a Contributor in some form (Staff, Server Supporters, Patreons, etc)"
                            +"\n\nThe remainder of our roles are through other means, such as:"
                            +"\n\n- Admin/Staff roles- Punishment roles, only given when a user breaks the rules and requires more strict punishments than warns"
                            +"\n- Perk roles, given when a user has subscribed to the server, have boosted the server, subscribed to the channel Patreon, or contributed to the server/channel in some form (Example, creating emotes)"
                            +"\n- Level roles, which are given depending on what level you are within the server (can check with ?lvl)"
                            +"\n- The VC role which is only obtained when joining a VC"
                            +"\n- Bot roles, which are for (you guessed it), bots.",inline=False)
            await ctx.send(embed=embed)
    @roles.error
    async def on_roles_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?roles")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def scam(self, ctx: commands.Context):
        """Scam copypasta, for staff use in TNB when users ask or talk about scams."""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_gray(),title="Common Discord Scams and Hacking:")
            embed.add_field(name="",value="We are aware of several common ways to scam/hack users on Discord. A friend of the server made a Google Doc for their own server, for tips on how to protect yourself from them. The Doc can be found here: <https://bit.ly/3fu5wIl>",inline=False)
            await ctx.send(embed=embed)
    @scam.error
    async def on_scam_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?scam")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def selfies(self, ctx: commands.Context):
        """Selfies copypasta, for staff use in TNB when users ask about selfies or a selfies channel."""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="Is there a selfies channel?")
            embed.add_field(name="",value="This server does *not* have a selfie channel, and we do not allow selfies in the server. This is to keep minors safe and to prevent creeps.")
            await ctx.send(embed=embed)
    @selfies.error
    async def on_selfies_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?selfies")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def tnb(self, ctx: commands.Context):
        """Easy access to the permanent server invite for TNB."""
        if ctx.guild.id == tnb_server_id:
            await ctx.send("Wanna invite your friends to The Nerd Brigade? Here's our perma-invite!: https://discord.gg/XBqnnvA6tz")
    @tnb.error
    async def on_tnb_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?tnb")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['trades'])
    async def trade(self, ctx: commands.Context):
        """Trades copypasta, for staff use in TNB when users ask about Pokemon trades or anything similar."""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(),title="Looking for Pokemon trades?")
            embed.add_field(name="",value="We're not a trading server, and [as the rules note](https://discord.com/channels/385956732888678402/385972494429061131/782737693079109693) we generally don't appreciate people who aren't active in the server using us to get trades done. Plenty of dedicated Discord servers exist (try looking on [Discord's site](https://discord.com/servers?query=pokemon+trades), [Discord.me](https://discord.me/servers?search=pokemon+trades&language=1), or [Disboard](https://disboard.org/search?keyword=pokemon+trades)), as do forums like [GameFAQs](https://gamefaqs.gamespot.com/), [Serebii](https://forums.serebii.net/), [Smogon](https://www.smogon.com/forums/forums/wi-fi.53/), and [any number of subreddits](https://www.reddit.com/search/?q=pokemon+trades&type=sr), so please use those instead.",inline=False)
            await ctx.send(embed=embed)
    @trade.error
    async def on_trade_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?trade or m?trades")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command(aliases=['trolls'])
    async def troll(self, ctx: commands.Context):
        """Troll copypasta, for staff use in TNB when users ask about trolls."""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(), title="\"Why were they banned?\" / \"What happened?\"")
            embed.add_field(name="",
                value=(
                    "Asking why someone got banned and a mod posted this in response? "
                    "Presumably that person had just joined or barely used the server? "
                    "It's because the person was a troll, and we don't put up with their crap here. "
                    "You don't really need to know the details of why *(unless you're a friend of theirs or something - "
                    "we don't appreciate people being nosy for its own sake)*, but usually that can encompass anything of "
                    "*(but is __not__ limited to)*:"
                    + "\n\n- Posting blatantly homophobic, transphobic, etc. things"
                    + "\n- Posting blatantly racist things"
                    + "\n- Posting Nazi sympathism or other such things"
                    + "\n- Joining with a Nazi or overtly anti-LGBT pfp and/or username"
                    + "\n- Posting overtly NSFW stuff"
                    + "\n- Advertising on join (e.g. posting server invites)"
                    + "\n\n... or any number of other things."
                ),
                inline=False
            )
            embed.add_field(name="",value="\n\nWe've made this command because we get this question frequently enough to be an annoyance, "
                    "with the same common-sense response given every time. This is made increasingly worse by the fact "
                    "that all trolls want is a reaction and your attention, and talking about them after the fact "
                    "furthers that."
                    + "\n\n**tl;dr version --** If someone who just joined got banned, and you have no relation to them "
                    "whatsoever, all you need to know is they were acting in bad faith on join, or were some kind of "
                    "other bad actor. It's best to simply ignore their existence and move on.",inline=False)
            await ctx.send(embed=embed)
    @troll.error
    async def on_troll_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?troll or m?trolls")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
            
    @commands.command()
    async def vcs(self, ctx: commands.Context):
        """Voice chat copypasta, for staff use in TNB when users ask about voice channels/VCs."""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_gray(),title="\"Do you have VCs?\" / \"Where are the VCs?\"")
            embed.add_field(name="",value="This server does have several voice channels; however, they're not available until you reach Level 10. This is to help prevent trolls from entering the server and immediately bugging the VCs, on top of how hard they are to be moderated in general.")
            await ctx.send(embed=embed)
    @vcs.error
    async def on_vcs_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("Command requires no extra arguments. Please only do m?vcs")
        else:
            await ctx.send(f"An unexpected error occurred with the command. Input message: {ctx.message.content}. Error: {error}. Please contact swiftlynerd for potential fixes/explanations.")
              
async def setup(bot: commands.Bot): 
    """Sets up the TNB Cog"""
    await bot.add_cog(TNB(bot))
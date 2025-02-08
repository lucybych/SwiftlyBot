from discord.ext import commands
from utility.finder import has_roles
import discord
import random
import re

mod_chat_id = 1142605344594477067
no_level_id = 1146135827219492984
shame_images = ["https://i.imgur.com/Yca8mcX.png","https://i.imgur.com/SWPLesj.png"]
staff_roles = [1142608956024438885, 1142609047598661674, 1146872239715786752]
tmc_server_id = 1142604515791618108

DEFAULT_NICK = "Request New Nickname"

class TMC(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Initializes the TMC module"""
        self.bot = bot
    
    async def is_valid_nickname(self, nickname: str) -> bool:
        """Checks if a user's name/nickname in EMD has 3 valid alphanumeric characters"""
        if not nickname:
            return False
        return bool(re.search(r'[a-zA-Z0-9]{3}', nickname))
    
    async def staff_check(self, ctx: commands.Context) -> bool:
        """Check if the user has staff roles."""
        if ctx.guild.id != tmc_server_id:
            return False
        is_staff = await has_roles(ctx.author, staff_roles)
        if not is_staff:
            await ctx.send("You need to be staff to use this command.")
        return is_staff
    
    @commands.command()
    async def anchor(self, ctx: commands.Context):
         """For TMC staff to get pinged in staff chat"""
         if ctx.guild.id == tmc_server_id:
            is_staff = await self.staff_check(ctx)
            if not is_staff:
                await ctx.send("You need to be staff to use this command.")
                return
            channel = self.bot.get_channel(mod_chat_id)
            await channel.send(f"Here is your ping anchor, {ctx.author.mention}! ⚓")
    
    @commands.command()
    async def anchovy(self, ctx: commands.Context):
        """For TMC staff to get pinged in staff chat, but fishier 🐟"""
        if ctx.guild.id == tmc_server_id:
            is_staff = await self.staff_check(ctx)
            if not is_staff:
                await ctx.send("You need to be staff to use this command.")
                return
            channel = self.bot.get_channel(mod_chat_id)
            await channel.send(f"Here is your ping anchovy, {ctx.author.mention}! 🐟")
    
    @commands.command()
    async def betterdiscord(self, ctx: commands.Context):
        """For TMC staff to use in regards to BetterDiscord or other modified Discord clients"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.blurple(), title="\"Is using BetterDiscord or other modified clients banned?\"")
            embed.add_field(name="",value="**__No, using BetterDiscord is not ban-worthy.__**"
                            +"\n\nSome relevant bits from the [Discord TOS:](https://discord.com/terms#:~:text=Third%20Party%20Software%20and%20Services.)"
                            +"\n\n> Our services may allow you to access apps, bots, or other products, features or services developed by third parties. It’s your choice whether to use these products [...] While these third party services do need to follow all policies that apply to them [...] Discord is not responsible for products developed by third parties."
                            +"\n\nIn summary, modified clients like BetterDiscord are okay; Discord is simply saying that they are not responsible if a modified client harms you.",inline=False)
            embed.add_field(name="",value="\n\nIn general, Discord simply does not care about BetterDiscord; you will not be banned from here or Discord in general for using it properly. Moreover, Discord staff often use it, sometimes help support it or develop for it, and use it to see what features the userbase wants. Discord even approved them to get a [boosted member cap](https://support.discord.com/hc/en-us/articles/360052841734-Server-Member-Cap-Increases-), which obviously means Discord is okay with BetterDiscord as well."
                            +"\n\n**__In short: using BetterDiscord as provided and in a proper way is 100% safe for you and your account.__**",inline=False)
            embed.add_field(name="",value="\n\nFor those interested, you can also use the following links:"
                            +"\n\n* [BetterDiscord's website](https://betterdiscord.app/)"
                            +"\n* [BetterDiscord's Github](https://github.com/BetterDiscord/BetterDiscord)"
                            +"\n* [BetterDiscord's support server](https://discord.gg/0Tmfo5ZbORCRqbAd)"
                            +"\n* [Vencord](https://vencord.dev/download/) (similar to BD, but less laggy - better, in Eev's opinion)"
                            +"\n* [Have a free meme](https://i.imgur.com/QalN0Zj.png)",inline=False)
            await ctx.send(embed=embed)
    
    @commands.command()
    async def cheese(self, ctx: commands.Context):
        """Sends a picture of cheese, because get cheesed"""
        await ctx.send("https://i.imgur.com/8EUsHqQ.png")

    @commands.command(aliases=['links'])
    async def link(self, ctx: commands.Context):
        """For TMC staff to use when someone asks about posting/embedding links or attaching/posting files"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(), title="\"Why can't I post files or links here?\"")
            embed.add_field(name="",value="You cannot post files, links, images, videos, or embeds in this server until you reach **__Level 1__**. If you try to post a link anyways, your post will be auto-deleted by a bot; if you do this twice, you will be muted automatically. We apologize for this minor inconvenience, but it's a good measure to help prevent trolls; Level 1 does not take much time to reach."
                            +"\n\nMoreover, while you will be able to post links at Level 1, you won't be able to post files or have links embed in <#1142604517603561535> or <#1142606088148094988> until you reach **__Level 20__**. This is done in order to prevent spam; <#1142606134218334368> can be used in the meantime. *(Even then, for those above Level 20, we want media posted in the gens to be relevant, not random stuff.)*"
                            +"\n\n*(Other level-based perks are described [here](https://discord.com/channels/1142604515791618108/1142604517603561535/1260050727351488573).)*",inline=False)
            await ctx.send(embed=embed)
    
    @commands.command()
    async def nolvl(self, ctx: commands.Context, members: commands.Greedy[discord.Member]):
        """For TMC staff to add the No Level role to users more conveniently/quickly"""
        if await self.staff_check(ctx):
            no_lvl = ctx.guild.get_role(no_level_id)
            for member in members:
                await member.add_roles(no_lvl)
                await ctx.send(f"Added the **{no_lvl.name}** role to {member.mention}.")
    
    @commands.command()
    async def nsfw(self, ctx: commands.Context):
        """For TMC staff to use when someone asks about NSFW and the associated channels"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.dark_blue(), title="\"Do you have NSFW channels?\" / \"Where are the NSFW channels?\"")
            embed.add_field(name="",value="This server does have NSFW channels; however, they're not available until you hit Level 20. You'll have to contact a mod to give a form of ID; we will let you in, if we think you should be in those channels. (We don't let in people who are known to be here just for the NSFW stuff, or people who have a tendency to make people feel creeped out or uncomfortable. That stuff falls very out of line with our server culture.)"
                            +"\n\n*(Other level-based perks are described [here](https://discord.com/channels/1142604515791618108/1142604766610980945/1146869599061672127).)*",inline=False)
            await ctx.send(embed=embed)
    
    @commands.command()
    async def openoriginal(self, ctx: commands.Context):
        """For TMC staff to use when someone asks about large/elongated images"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.blue(), title="\"I can't read this long picture, it's too blurry.\"")
            embed.add_field(name="",value="*(Often the situation looks like [this](https://i.imgur.com/BzmBvsY.png).)*"
                            +"\n\nYou need to open the original file in your browser."
                            +"\n\nOn desktop, click on the image, and then on the \"Open in Browser\" button below the image. [(Picture.)](https://i.imgur.com/QIaYzfX.png)"
                            +"\n\nOn mobile, tap the image, then the three dots in the top-right, and then on the \"Open in Browser\" option. [(Picture.)](https://i.imgur.com/76DBuEa.png)",inline=False)
            await ctx.send(embed=embed)
    
    @commands.command()
    async def scam(self, ctx: commands.Context):
        """For TMC staff to use when someone asks about scams and hacks on Discord"""
        if await self.staff_check(ctx):
            embed = discord.Embed(color=discord.Color.purple(), title="Recent Discord Scams & Hacking:")
            embed.add_field(name="",value="Eev put together a Google Doc describing some common Discord scams going around as of late that have compromised a number of accounts, and some tips on how to protect yourself from them."
                            +"\n\nYou can read her write-up at this link: https://bit.ly/3fu5wIl",inline=False)
            await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Checks for if a user has a valid nickname in TMC (at least 3 alphanumeric characters) and changes it to \"Request New Nickname\" if it violates these rules"""
        if member.guild.id != tmc_server_id:
            return
        if not await self.is_valid_nickname(member.global_name) or not await self.is_valid_nickname(member.display_name) or await self.is_valid_nickname(member.name):
            await member.edit(nick=DEFAULT_NICK)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Checks for if a user in TMC posted @everyone or @here, If the user does not have any of the \"safe\" roles, they will be unofficially warned"""
        if message.author.bot:
            return
        if message.guild.id != tmc_server_id:
            return
        if "@everyone" in message.content or "@here" in message.content:
            embed = discord.Embed(color=discord.Color.purple())
            embed.set_image(url=random.choice(shame_images))
            await message.channel.send(f"{message.author.mention} -- That didn't ping anybody, genius.",embed=embed)
            await message.delete()
    
async def setup(bot): 
    await bot.add_cog(TMC(bot))
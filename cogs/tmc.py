import discord
from discord.ext import commands
from typing import Union
import random

tmc_server_id = 1142604515791618108
mod_chat_id = 1142605344594477067
staff_roles = [1142608956024438885, 1142609047598661674, 1146872239715786752]
shame_images = ["https://i.imgur.com/Yca8mcX.png","https://i.imgur.com/SWPLesj.png"]

class TMC(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def is_staff(self, user: Union[discord.Member, discord.User]):
        user_roles = user.roles
        for role in user_roles:
            if role.id in staff_roles:
                return True
        return False
    
    @commands.command()
    async def anchor(self, ctx: commands.Context):
         if ctx.guild.id == tmc_server_id:
            is_staff = await self.is_staff(ctx.user)
            if not is_staff:
                await ctx.send("You need to be staff to use this command.")
                return
            channel = self.bot.get_channel(mod_chat_id)
            await channel.send(f"Here is your ping anchor, {ctx.author.mention}! ⚓")
    
    @commands.command()
    async def anchovy(self, ctx: commands.Context):
        if ctx.guild.id == tmc_server_id:
            is_staff = await self.is_staff(ctx.author)
            if not is_staff:
                await ctx.send("You need to be staff to use this command.")
                return
            channel = self.bot.get_channel(mod_chat_id)
            await channel.send(f"Here is your ping anchovy, {ctx.author.mention}! 🐟")
    
    @commands.command()
    async def betterdiscord(self, ctx: commands.Context):
        if ctx.guild.id == tmc_server_id:
            is_staff = await self.is_staff(ctx.author)
            if not is_staff:
                await ctx.send("You need to be staff to use this command, to help avoid spam.")
                return
            embed = discord.Embed(color=discord.Color.blurple(), title="\"Is using BetterDiscord or other modified clients banned?\"")
            embed.add_field(name="",value="**__No, using BetterDiscord is not ban-worthy."
                            +"\n\nSome relevant bits from the [Discord TOS:](https://discord.com/terms#:~:text=Third%20Party%20Software%20and%20Services.)"
                            +"\n\n> Our services may allow you to access apps, bots, or other products, features or services developed by third parties. It’s your choice whether to use these products [...] While these third party services do need to follow all policies that apply to them [...] Discord is not responsible for products developed by third parties."
                            +"\n\nIn summary, modified clients like BetterDiscord are okay; Discord is simply saying that they are not responsible if a modified client harms you."
                            +"\n\nIn general, Discord simply does not care about BetterDiscord; you will not be banned from here or Discord in general for using it properly. Moreover, Discord staff often use it, sometimes help support it or develop for it, and use it to see what features the userbase wants. Discord even approved them to get a [boosted member cap](https://support.discord.com/hc/en-us/articles/360052841734-Server-Member-Cap-Increases-), which obviously means Discord is okay with BetterDiscord as well."
                            +"\n\n**__In short: using BetterDiscord as provided and in a proper way is 100% safe for you and your account.__**"
                            +"\n\nFor those interested, you can also use the following links:"
                            +"\n\n* [BetterDiscord's website](https://betterdiscord.app/)"
                            +"\n\n* [BetterDiscord's Github](https://github.com/BetterDiscord/BetterDiscord)"
                            +"\n\n* [BetterDiscord's support server](https://discord.gg/0Tmfo5ZbORCRqbAd)"
                            +"\n\n* [Vencord](https://vencord.dev/download/) (similar to BD, but less laggy - better, in Eev's opinion)"
                            +"\n\n* [Have a free meme](https://i.imgur.com/QalN0Zj.png)",inline=False)
            await ctx.send(embed=embed)
    
    @commands.command(aliases=['c'])
    async def check(self, ctx: commands.Context):
        await ctx.send(f"**__Some Server Info:__**\n\n* Members: {ctx.guild.member_count}\n* Roles: {len(ctx.guild.roles)}\nChannels: {len(ctx.guild.channels)}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild.id != tmc_server_id:
            return
        if "@everyone" in message.content or "@here" in message.content:
            try:
                embed = discord.Embed(color=discord.Color.purple())
                embed.url(random.choice(shame_images))
                await message.channel.send(f"{message.author.mention} -- That didn't ping anybody, genius.",embed=embed)
                await message.delete()
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass
    
async def setup(bot): 
    await bot.add_cog(TMC(bot))
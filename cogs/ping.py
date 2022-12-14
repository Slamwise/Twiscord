from discord.ext import commands, tasks


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Pong!"""
        await ctx.send("Pong!")

    @commands.command()
    async def bing(self, ctx: commands.Context):
        """Bong!"""
        await ctx.send("Bong!")

    @commands.command()
    async def joe(self, ctx: commands.Context):
        """mama!"""
        await ctx.send("mama!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))

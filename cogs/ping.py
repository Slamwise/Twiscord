from discord.ext import commands, tasks


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        await ctx.send("Pong!")

    @commands.command()
    async def bing(self, ctx: commands.Context):
        await ctx.send("Bong!")


def setup(bot: commands.Bot):
    bot.add_cog(Ping(bot))

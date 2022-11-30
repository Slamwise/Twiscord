from discord.ext import commands


class Notify(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def start(self, ctx: commands.Context):
        tweets = self.bot.get_cog("Tweets")

        await tweets.setup_hook()


def setup(bot: commands.Bot):
    bot.add_cog(Notify(bot))

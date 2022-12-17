import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from collections import deque
import os
from pprint import pprint
import asyncio


def main():
    load_dotenv()

    # class BotOverride(commands.Bot):
    #     def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)

    #     def run(self, token, *args, **kwargs):
    #         async def runner():
    #             async with self:
    #                 await self.start(token)

    #         try:
    #             asyncio.run(runner())
    #         except KeyboardInterrupt:
    #             print("closing!")
    #             return

    # bot = BotOverride(command_prefix="?", intents=discord.Intents.all())
    bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user}")

    @bot.event
    async def on_shutdown():
        print("caught!")

    asyncio.run(bot.load_extension("cogs.ping"))
    asyncio.run(bot.load_extension("cogs.tweetcog"))
    asyncio.run(bot.load_extension("cogs.textcog"))

    # a = discord.Embed(title="Example embed", description="this is the contents of the embed", url="https://twitter.com")
    # await bot.get_channel(1044767055116763176).send(embed=a)

    token = os.environ.get("DISCORD_BOT_TOKEN")

    bot.run(token)


if __name__ == "__main__":
    main()

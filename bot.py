import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from collections import deque
import os
from pprint import pprint
import asyncio


def main():
    load_dotenv()
    bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())

    asyncio.run(bot.load_extension("cogs.ping"))
    asyncio.run(bot.load_extension("cogs.tweetcog"))
    asyncio.run(bot.load_extension("cogs.textcog"))

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user}")

        # a = discord.Embed(title="Example embed", description="this is the contents of the embed", url="https://twitter.com")
        # await bot.get_channel(1044767055116763176).send(embed=a)

    token = os.environ.get("DISCORD_BOT_TOKEN")
    bot.run(token)


if __name__ == "__main__":
    main()

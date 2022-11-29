
import discord
from discord.ext import tasks
from dotenv import load_dotenv
from tweets import fetch_tweets
from collections import deque
import os
import asyncio
from pprint import pprint


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tweets = deque([], maxlen=100)
        self.tweet_ids = deque([], maxlen=100)
        self.count = 0

    async def on_ready(self):
        await self.setup_hook()
        print(f"Logged in as {self.user}")

    async def setup_hook(self):
        if not self.tweet_fetcher.is_running():
            self.tweet_fetcher.start()

    async def on_message(self, message: discord.Message):
        print(f"Message from {message.author}: {message.content}")

    @tasks.loop(seconds=5)
    async def tweet_fetcher(self):
        channel = self.get_channel(1044767055116763176)
        new_tweets = fetch_tweets(1286099901840003000, "TT3Private")
        if len(self.tweets) != 0:
            i = 0
            tweets_to_add = []
            while i < len(new_tweets) and new_tweets[i][1] not in self.tweet_ids:
                tweets_to_add.append(new_tweets[i])
                i += 1
            tweet_ids_to_add = [tweet[1] for tweet in tweets_to_add]

            if tweets_to_add:
                tweets_to_add = list(reversed(tweets_to_add))
                for tweet in tweets_to_add:
                    await channel.send(f"New tweet:\n{tweet[2]}")
                self.tweets.extend(tweets_to_add)
                self.tweet_ids.extend(tweet_ids_to_add)
            pprint(self.tweets)
            pprint(self.tweet_ids)
        else:  # first fetch
            self.tweets.extend(list(reversed(new_tweets)))
            self.tweet_ids.extend([tweet[1] for tweet in new_tweets])
            await channel.send(f"Last tweet:\n{self.tweets[-1][2]}")
            pprint(self.tweets)

        self.count += 1
        print(self.count)

    @tweet_fetcher.before_loop
    async def pre_fetch(self):
        await self.wait_until_ready()


def main():
    load_dotenv()
    token = os.environ.get("DISCORD_BOT_TOKEN")
    client = MyClient(intents=discord.Intents.all())
    client.run(token)


if __name__ == "__main__":
    main()

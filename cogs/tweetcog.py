from discord.ext import tasks, commands
from discord import Embed, Colour
from pprint import pprint
from tweets import create_api, get_list_timeline
from collections import deque, defaultdict
from dequeset import OrderedDequeSet
import tweepy as tp
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
import os


shared_tweets = defaultdict(lambda: OrderedDequeSet(maxlen=100))


class Tweets(commands.Cog):
    def __init__(self, bot: commands.Bot, *args, **kwargs):
        load_dotenv()
        self._ROOTCHANNEL = int(os.environ.get("ROOTCHANNEL"))
        print(self._ROOTCHANNEL)
        self.bot = bot
        self.api: tp.API = create_api()
        self.list_id = 1597755224684388353
        self.owner_id = 1094812631205101600
        self.recency_queue: OrderedDequeSet = OrderedDequeSet(maxlen=200)
        self.tweets = defaultdict(lambda: OrderedDequeSet(maxlen=100))
        self.tweet_ids = defaultdict(lambda: OrderedDequeSet(maxlen=100))
        self.subsconfig = defaultdict(list)
        self.channels = defaultdict(list)
        self.global_list = []
        self.count = 0
        self.most_recent_update = datetime.now().timestamp()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.tweet_fetcher.is_running():
            members = self.api.get_list_members(list_id=self.list_id, owner_id=self.owner_id)
            self.global_list = [member.screen_name for member in members]
            await self.tweet_fetcher.start()

    def add_list_member(self, account):
        self.api.add_list_member(list_id=self.list_id, owner_id=self.owner_id, screen_name=account)

    @tasks.loop(seconds=1)
    async def tweet_fetcher(self):
        fetched = False
        while not fetched:
            try:
                fresh_tweets = get_list_timeline(self.list_id, self.owner_id, self.api)
                fetched = True
            except tp.TwitterServerError as ServerError:
                logging.warning(f"Error caught: {ServerError}")
                await asyncio.sleep(2)

        if len(self.recency_queue) > 0:
            recent_tweet_timestamp = self.recency_queue[-1][0]
            to_send = defaultdict(list)

            # Get only tweets newer than the recency queue
            recent_tweets = OrderedDequeSet(
                filter(
                    lambda x: x[0] > recent_tweet_timestamp and x[0] > self.most_recent_update,
                    fresh_tweets,
                )
            )

            # Iterate through the neweest tweets and add them to the to_send pile
            for tweet in recent_tweets:
                if tweet[1] in self.subsconfig:
                    to_send[tweet[1]].append(tweet)

            if len(to_send) > 0:
                for account, new_tweets in to_send.items():
                    if self.subsconfig.get(account) is None:
                        continue

                    channels = self.subsconfig.get(account)
                    for channel in channels:
                        [
                            asyncio.create_task(
                                self.bot.get_channel(channel).send(
                                    content=f"https://twitter.com/{tweet[1]}/status/{tweet[2]}",
                                    embed=Embed(
                                        colour=Colour.from_rgb(52, 61, 65),
                                        timestamp=datetime.fromtimestamp(tweet[0]),
                                        title=f"@{tweet[1]}",
                                        url=f"https://twitter.com/{tweet[1]}/status/{tweet[2]}",
                                        description=tweet[3],
                                        type="rich",
                                    ),
                                )
                            )
                            for tweet in new_tweets
                        ]

            self.recency_queue = self.recency_queue.union(recent_tweets)
            [shared_tweets[tweet[1]].add(tweet) for tweet in recent_tweets]
            self.count += 1
            print(self.count)

        else:  # first fetch tweet.created_at, tweet.author.screen_name.strip().lower(), tweet.id, tweet.full_text
            self.recency_queue = OrderedDequeSet(fresh_tweets, maxlen=200)
            [shared_tweets[tweet[1]].add(tweet) for tweet in self.recency_queue]
            self.count += 1
            print(self.count)

    @tweet_fetcher.before_loop
    async def _prefetch(self):
        """Helper to startup fetcher"""
        await self.bot.wait_until_ready()

    async def add_user_to_list(self, screen_name):
        """Adds new user to twitter list member"""
        self.api.add_list_member(list_id=self.list_id, screen_name=screen_name)

    def check_user_still_needed(self, screen_name):
        return self.subsconfig.get(screen_name) is not None

    def command_cleaner(self, command: str):
        return command.lower()

    def remove_list_user(self, screen_name: str):
        try:
            self.api.remove_list_member(list_id=self.list_id, owner_id=self.owner_id, screen_name=screen_name)
        except tp.BadRequest:
            print(f"ERROR: User {screen_name} not in the current list")

    @commands.command()
    async def showall(self, ctx: commands.Context):
        """Show all accounts the bot currently tracks"""
        if not self.global_list:
            await ctx.send("No one in the global list")
            return

        await ctx.send(", ".join(self.global_list))

    @commands.command(name="recent")
    async def recent_x(self, ctx: commands.Context, *args):
        """Display the most recent x twitter users in the fetch list"""
        if len(args) != 1:
            await ctx.send("Please only provide one number")
            return

        try:
            num = int(args[0])
            if len(self.global_list) < num:
                await ctx.send(", ".join(self.global_list))
            else:
                await ctx.send(", ".join(self.global_list[-1 : (-1 - num) : -1]))
        except ValueError:
            await ctx.send("Please only use numbers")

    @commands.command(name="followingnow")
    async def followingnow(self, ctx: commands.Context):
        """Display all the accounts the current channel is following"""
        follows = [account for account, channels in self.subsconfig.items() if ctx.channel.id in channels]
        lenfol = len(follows)
        if lenfol == 0:
            await ctx.send("This channel is currently following: No one")
        else:
            await ctx.send(f"This channel is currently following: {', '.join(follows)}")

    @commands.command()
    async def follow(self, ctx: commands.Context, *args):
        """Follow a new user in this channel"""
        if not args:
            await ctx.send("Please provide an account with the command e.g ?follow firstsquawk or ?follow !all")

        elif len(args) > 1:
            await ctx.send("?follow can only handle one account at a time.")

        elif args[0] == "!all":
            if not self.global_list:
                await ctx.send("No one in global list, please specify an account")
                self.most_recent_update = datetime.now().timestamp()
            else:
                for account in self.global_list:
                    self.subsconfig[account].append(ctx.channel.id)
                    self.most_recent_update = datetime.now().timestamp()
                ctx.send(f"Following all stored accounts")

        else:
            try:
                cleaned_name = args[0].strip().lower()
                _ = self.api.get_user(screen_name=cleaned_name)
                if ctx.channel.id not in self.subsconfig[cleaned_name]:
                    self.subsconfig[cleaned_name].append(ctx.channel.id)
                    if cleaned_name not in self.global_list:
                        self.global_list.append(cleaned_name)
                        self.add_list_member(cleaned_name)
                    await ctx.send(f"Now following {args[0]}")
                    self.most_recent_update = datetime.now().timestamp()
                else:
                    await ctx.send(f"Twitter user {args[0]} is already followed on this channel.")
            except tp.NotFound as e:
                await ctx.send(f"Twitter user {args[0]} is not valid account")
                logging.info(e)
            except Exception as e:
                print(e)
                await ctx.send(f"Another error occurred please try again later")

    @commands.command()
    async def unfollow(self, ctx: commands.Context, *args):
        """Unfollow one or more accounts from the channels following"""
        rem = []

        for name in args:
            try:
                name = name.lower().strip()
                self.subsconfig[name].remove(ctx.channel.id)
                rem.append(name)
            except (ValueError, KeyError):
                pass
        if not rem:
            asyncio.create_task(ctx.send(f"Removed no one from your channel's follows list"))
        else:
            if len(rem) == 1:
                asyncio.create_task(ctx.send(f"Removed {rem[0]} from your channel's follows list"))
            else:
                asyncio.create_task(ctx.send(f"Removed {', '.join(rem)} from your channel's follows list"))
            for name in rem:
                needed = self.check_user_still_needed(name)
                if not needed:
                    self.global_list.remove(name)
                    del self.subsconfig[name]
                    self.remove_list_user(name)

    @commands.command()
    async def start(self, ctx: commands.Context):
        """Start the fetcher if not currently running"""
        tweets = self.bot.get_cog("Tweets")
        if tweets.tweet_fetcher.is_running():
            await ctx.send(f"Underlying tweet fetcher already running, please provide an account name with the command")
            return

        await self.bot.wait_until_ready()
        await tweets.tweet_fetcher.start()

    @commands.command(hidden=True)
    async def rootstop(self, ctx: commands.Context):
        """Allows admin channel to be the only one to stop the bot"""
        if ctx.channel.id != self._ROOTCHANNEL:
            return
        tweets = self.bot.get_cog("Tweets")
        if tweets.tweet_fetcher.is_running():
            tweets.tweet_fetcher.stop()
            return

        await ctx.send("Tweet fetcher not running")

    @commands.command(hidden=True)
    async def rootremove(self, ctx: commands.Context, *args):
        """Allows admin channel to remove a user from the twitter list"""
        if ctx.channel.id != self._ROOTCHANNEL:
            return
        if len(args) > 1:
            asyncio.create_task(ctx.send(f"Cannot pass more than one user to remove"))
            return
        self.remove_list_user(args[0])
        if self.subsconfig.get(args[0]):
            del self.subsconfig[args[0]]

    @commands.command(hidden=True)
    async def rootremoveall(self, ctx: commands.Context):
        if ctx.channel.id != self._ROOTCHANNEL:
            return

        all_users = self.api.get_list_members(list_id=self.list_id, owner_id=self.owner_id)
        for user in all_users:
            screen_name = user.screen_name
            self.remove_list_user(screen_name=screen_name)
        asyncio.create_task(ctx.send("Removed all users from twitter list"))


async def setup(bot: commands.Bot):
    await bot.add_cog(Tweets(bot))

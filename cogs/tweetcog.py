from discord.ext import tasks, commands
from pprint import pprint
from tweets import fetch_tweets, create_api
from collections import deque, defaultdict
import tweepy as tp
import asyncio


class Tweets(commands.Cog):
    def __init__(self, bot: commands.Bot, *args, **kwargs):
        self.bot = bot
        self.api: tp.API = create_api()
        self.list_id = 1597755224684388353
        self.owner_id = 1094812631205101600
        self.tweets = defaultdict(lambda: deque([], maxlen=100))
        self.tweet_ids = defaultdict(lambda: deque([], maxlen=100))
        self.subsconfig = defaultdict(list)
        self.channels = defaultdict(list)
        self.global_list = []
        self.count = 0

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.tweet_fetcher.is_running():
            members = self.api.get_list_members(list_id=self.list_id, owner_id=self.owner_id)
            self.global_list = [member.screen_name for member in members] + ["firstsquawk", "test", "test2"]
            await self.tweet_fetcher.start()

    @tasks.loop(seconds=5)
    async def tweet_fetcher(self):
        name = "firstsquawk"
        new_tweets = fetch_tweets(name)
        if len(self.tweets) != 0:
            i = 0
            tweets_to_add = []
            while i < len(new_tweets) and new_tweets[i][1] not in self.tweet_ids[name]:
                tweets_to_add.append(new_tweets[i])
                i += 1

            tweet_ids_to_add = [tweet[1] for tweet in tweets_to_add]
            if tweets_to_add:
                tweets_to_add = list(reversed(tweets_to_add))
                if self.channels:
                    pass
                self.tweets[name].extend(tweets_to_add)
                self.tweet_ids[name].extend(tweet_ids_to_add)
            self.count += 1
            pprint(self.count)
        else:  # first fetch
            self.tweets[name].extend(list(reversed(new_tweets)))
            self.tweet_ids[name].extend([tweet[1] for tweet in new_tweets])
            self.count += 1
            print(self.count)

    @tweet_fetcher.before_loop
    async def _prefetch(self):
        """Helper to startup fetcher"""
        await self.bot.wait_until_ready()

    async def add_user_to_list(self, screen_name):
        """Adds new user to twitter list member"""
        self.api.add_list_member(list_id=self.list_id, screen_name=screen_name)

    async def check_user_still_needed(self, screen_name):
        for channel, sublist in self.channels.items():
            if screen_name in sublist:
                return True
        return False

    async def command_cleaner(self, command: str):
        return command.lower()

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
        follows = self.channels[ctx.channel.id]
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

        if args[0] == "!all":
            if not self.global_list:
                await ctx.send("No one in global list, please specify an account")
                return

            self.channels[ctx.channel.id] = self.global_list

        else:
            self.channels[ctx.channel.id].append(args[0])

    @commands.command()
    async def remove(self, ctx: commands.Context, *args):
        """Remove one or more accounts from the channels following"""
        rem = []

        for name in args:
            try:
                self.channels[ctx.channel.id].remove(name)
                rem.append(name)
            except ValueError:
                pass
        if not rem:
            await ctx.send(f"Removed no one from your channel's follows list")
        else:
            if len(rem) == 1:
                await ctx.send(f"Removed {rem[0]} from your channel's follows list")
                return
            await ctx.send(f"Removed {', '.join(rem)} from your channel's follows list")

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
        """Allows our channel to be the only one to stop the bot"""
        if ctx.channel.id != 1044767055116763176:
            return
        tweets = self.bot.get_cog("Tweets")
        if tweets.tweet_fetcher.is_running():
            tweets.tweet_fetcher.stop()
            return

        await ctx.send("Tweet fetcher not running")


def setup(bot: commands.Bot):
    bot.add_cog(Tweets(bot))

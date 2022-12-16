from discord.ext import tasks, commands
from texts import send_sms
from collections import defaultdict
from cogs.tweetcog import shared_tweets
from dequeset import OrderedDequeSet
from tweets import create_api
import tweepy as tp
import asyncio
import os
import logging
import pprint
import ast
import subprocess

class Texts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.subsconfig = defaultdict(set)
        self.api: tp.API = create_api()
        #Needs to be pickled on shutdown:
        self.msg_history = defaultdict(lambda: OrderedDequeSet(maxlen=100))

    @commands.Cog.listener()
    async def on_ready(self):
        server = subprocess.Popen(['python3','webhooks.py'])
        if not self.check_tweets.is_running():
            await self.check_tweets.start()

    @tasks.loop(seconds=0.5)
    async def check_tweets(self):
        pprint(shared_tweets)
        for handle in shared_tweets:
            if handle not in self.subsconfig:
                continue
            else:
                change_queue = open("changes.txt", "r")
                for line in change_queue.splitlines(keepends=False):
                    change = ast.literal_eval(line)
                    pprint(change)
                pprint('1')
                nums = tuple(self.subsconfig[handle])
                if handle not in self.msg_history or shared_tweets[handle][-1] != self.msg_history[handle][-1][0]:
                    pprint('2')
                    self.msg_history[handle].add((shared_tweets[handle][-1], nums))
                    for num in nums:
                        pprint('3')
                        await send_sms(num, shared_tweets[handle][-1][-1])

    @check_tweets.before_loop
    async def _precheck(self):
        """Helper to startup checker"""
        await self.bot.wait_until_ready()
                
    @commands.command()
    async def subscribe_texts(self, ctx=commands.Context, *args):
        """Subscribe a phone number to receive notifcations from a specified Twitter handle"""
        if not args or len(args[0]) != 10:
            asyncio.create_task(ctx.send("Please provide a valid US phone number in format: ?##########"))

        elif len(args) != 2:
            asyncio.create_task(ctx.send("Please use command with format: ?subscribe_texts <phone number> <twitter handle>"))

        else:
            try:
                cleaned_name = args[1].strip()
                _ = self.api.get_user(screen_name=cleaned_name)
                self.subsconfig[cleaned_name].add(args[0])
                asyncio.create_task(ctx.send(f"{args[0]} now following {args[1]}"))
            except tp.NotFound as e:
                asyncio.create_task(ctx.send(f"Twitter user {args[1]} is not valid account"))
                logging.info(e)
            except Exception as e:
                asyncio.create_task(ctx.send(f"Another error occurred please try again later"))
                logging.warn(e)

    @commands.command()
    async def unsubscribe_texts(self, ctx=commands.Context, *args):
        """Remove a phone number from the specified Twitter handle's notifications"""
        if not args or len(args[0]) != 10:
            asyncio.create_task(ctx.send("Please provide a valid US phone number in format: ?##########"))
        elif len(args) != 2:
            asyncio.create_task(ctx.send("Please use command with format: ?subscribe_texts <phone number> <twitter handle>"))
        else:
            try:
                cleaned_name = args[1].strip().lower()
                _ = self.api.get_user(screen_name=cleaned_name)
                self.subsconfig[cleaned_name].remove(args[0])
                asyncio.create_task(ctx.send(f"{args[0]} unsubscribed from {args[1]}"))
            except tp.NotFound as e:
                asyncio.create_task(ctx.send(f"Twitter user {args[1]} is not valid account"))
                logging.info(e)
            except Exception as e:
                asyncio.create_task(ctx.send(f"Another error occurred please try again later"))
                logging.warn(e)

async def setup(bot: commands.Bot):
    await bot.add_cog(Texts(bot))

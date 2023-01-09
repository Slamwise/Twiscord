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
from pprint import pprint
import ast
import subprocess
from copy import deepcopy
from webhooks import app
from threading import Thread
import requests
from encrypt import decrypt_msg
import json

class Texts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.subsconfig = defaultdict(set)
        self.api: tp.API = create_api()
        # Needs to be pickled on shutdown:
        self.msg_history = defaultdict(lambda: OrderedDequeSet(maxlen=100))

    @commands.Cog.listener()
    async def on_ready(self):
        #server = subprocess.Popen(["python3", "webhooks.py"])
        if requests.get("http://3.92.223.40/example").status_code != 200:
            server = Thread(target=app.run)
            server.start()
        if not self.check_tweets.is_running():
            await self.check_tweets.start()

    @tasks.loop(seconds=2)
    async def check_tweets(self):
        numbers = set(number for handle in self.subsconfig for number in handle)
        try:
            resp = requests.get(f"http://3.92.223.40/get_changes")
            json_object = json.loads(decrypt_msg(resp, "priv_key.pm"))
            changes = [tuple(x) for x in json_object]
            print("first")
            for num in numbers:
                sub_changes = (c for c in changes if c[0] == num)
                for s in [sub_changes]:
                    if s[-1] == "r":
                        self.subsconfig[s[1]].remove(s[0])
                        requests.post(f"http://3.92.223.40/clear_changes?number={num}&handle={s[1]}")
                    if s[-1] == "all":
                        for h in self.subsconfig.values():
                            h.remove(s[0])
                            requests.post(f"http://3.92.223.40/clear_all_changes?number={num}")
                    if s[-1] == "a":
                        self.subsconfig[s[1]].add(s[0])
                        requests.post(f"http://3.92.223.40/clear_changes?number={num}&handle={s[1]}")
            print("second")
        except Exception as e:
            logging.info(e)

        self.shared_tweets = deepcopy(shared_tweets)
        for handle in self.shared_tweets: # Check each handle {handle: ODS[tweet1, tweet2, ...]}
            if handle not in self.subsconfig:
                continue
            elif self.shared_tweets[handle][-1] not in [msg[0] for msg in self.msg_history[handle]]:
                nums = tuple(self.subsconfig[handle]) # (num1, num2, ...) subscribed to this twitter handle
                self.msg_history[handle].add((self.shared_tweets[handle][-1], nums))
                for num in nums:
                    print(self.msg_history[handle])
                    #await send_sms(num, self.shared_tweets[handle][-1][-1])

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
                cleaned_name = args[1].strip().lower()
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

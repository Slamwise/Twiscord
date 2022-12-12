from discord.ext import tasks, commands
from texts import send_sms
from dotenv import load_dotenv
from collections import defaultdict
from tweetcog import shared_data
from dequeset import OrderedDequeSet
import tweepy as tp
import asyncio
import os
import logging

class Texts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        load_dotenv()
        env = dict(os.environ)
        self.bot = bot
        self.subsconfig = defaultdict(list)
        self.api: tp.API = create_api()
        #Needs to be pickled on shutdown:
        self.msg_history = defaultdict(lambda: OrderedDequeSet(maxlen=100))

    @tasks.loop(seconds=0.5)
    async def check_tweets(self):
        for handle in shared_data:
            if handle not in self.subsconfig:
                continue
            else:
                nums = self.subsconfig[handle]
                
                if handle not in self.msg_history or handle[-1] != self.msg_history[handle][-1][0]:
                    self.msg_history[handle].append((handle[-1], nums))
                    for num in nums:
                        await send_sms(num, handle[-1][2])
                
    @commands.command()
    async def subscribe_texts(self, ctx=commands.Context, *args):
        """Subscribe a phone number to receive notifcations from a specified Twitter handle"""
        if not args or len(args[0]) != 10:
            await ctx.send("Please provide a valid US phone number in format: ?##########")

        elif len(args) != 2:
            await ctx.send("Please use command with format: ?subscribe_texts <phone number> <twitter handle>")

        else:
            try:
                cleaned_name = args[1].strip().lower()
                _ = self.api.get_user(screen_name=cleaned_name)
                self.subsconfig[cleaned_name].append(args[0])
                await ctx.send(f"Now following {args[0]}")
            except tp.NotFound as e:
                await ctx.send(f"Twitter user {args[0]} is not valid account")
                logging.info(e)
            except Exception as e:
                await ctx.send(f"Another error occurred please try again later")
                logging.warn(e)


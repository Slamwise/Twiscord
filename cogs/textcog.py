from discord.ext import commands
from texts import send_sms
from dotenv import load_dotenv
from collections import defaultdict
import os

class Texts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        load_dotenv()
        env = dict(os.environ)
        self.bot = bot
        self.subsconfig = defaultdict(list)
        self.last_tweet = ''
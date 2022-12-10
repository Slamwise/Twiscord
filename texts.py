from twilio.rest import Client
import os
from dotenv import load_dotenv
import aiohttp

load_dotenv()
env = dict(os.environ)

account_sid = env["ACCOUNT_SID"]
auth_token = env["AUTH_TOKEN"]

async def send_sms(number, msg):
    from_ = env["TWILIO_PHONE_NUM"]
    auth = aiohttp.BasicAuth(login=account_sid, password=auth_token)
    async with aiohttp.ClientSession(auth = aiohttp.BasicAuth(login=account_sid, password=auth_token)) as session:
        return await session.post(
            f'https://api.twilio.com/2010-0-01/Accounts/{account_sid}/Messages.json',
            data={'From': from_, 'To': number, 'Body': msg})
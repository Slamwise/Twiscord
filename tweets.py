import tweepy as tp
import os
from dotenv import load_dotenv

load_dotenv()
env = dict(os.environ)


def create_auth():
    access_token = env["ACCESS_TOKEN"]
    consumer_key = env["CONSUMER_KEY"]
    access_token_secret = env["ACCESS_SECRET"]
    consumer_secret = env["CONSUMER_SECRET"]
    return tp.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)


def create_api() -> tp.API:
    auth = create_auth()
    return tp.API(auth=auth, wait_on_rate_limit=True)


def fetch_tweets(screen_name: str, api: tp.API = None):
    if not api:
        api = create_api()
    tweets = api.user_timeline(screen_name=screen_name, tweet_mode="extended")
    cleaned_tweets = [[tweet.created_at, tweet.id, tweet.full_text] for tweet in tweets]
    return cleaned_tweets


if __name__ == "__main__":
    api = create_api()
    api.add_list_member()

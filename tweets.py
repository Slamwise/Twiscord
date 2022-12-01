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


def get_list_timeline(list_id: int, owner_id: int, api: tp.API = None):
    if not api:
        api = create_api()
    tweets = api.list_timeline(list_id=list_id, owner_id=owner_id, count=100, tweet_mode="extended")
    cleaned_tweets = [(tweet.created_at, tweet.id, tweet.user.screen_name.lower(), tweet.full_text) for tweet in tweets]
    return cleaned_tweets


if __name__ == "__main__":
    api = create_api()
    print(get_list_timeline(1597755224684388353, 1094812631205101600, api))

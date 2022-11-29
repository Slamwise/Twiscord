import tweepy as tp
import os
from dotenv import load_dotenv

load_dotenv()
env = dict(os.environ)


def fetch_tweets(user_id, screen_name: str):
    access_token = env["ACCESS_TOKEN"]
    consumer_key = env["CONSUMER_KEY"]
    access_token_secret = env["ACCESS_SECRET"]
    consumer_secret = env["CONSUMER_SECRET"]
    auth = tp.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
    api = tp.API(auth=auth, wait_on_rate_limit=True)
    tweets = api.user_timeline(user_id=user_id, screen_name=screen_name, tweet_mode="extended")
    cleaned_tweets = [[tweet.created_at, tweet.id, tweet.full_text] for tweet in tweets]
    return cleaned_tweets


if __name__ == "__main__":
    print(fetch_tweets(1286099901840003000, "TT3Private"))

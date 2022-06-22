import os
import requests
from scripts.utils.time import get_timestamp
import tweepy


def authenticate_twitter(github_action, proxy):
    """
    Authenticates Twitter
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :param proxy: <Boolean> Whether to use a proxy or not
    :return: api <tweepy.api> the tweepy api response
    """

    # Uses GitHub Secrets to store and load credentials
    if github_action:
        auth = tweepy.OAuthHandler(os.environ['consumer_key'], os.environ['consumer_secret'])
        auth.set_access_token(os.environ['access_token'], os.environ['access_token_secret'])

    # Else uses local twitter_credentials.py file
    else:
        import config.twitter_credentials as twitter_credentials
        auth = tweepy.OAuthHandler(twitter_credentials.consumer_key, twitter_credentials.consumer_secret)
        auth.set_access_token(twitter_credentials.access_token, twitter_credentials.access_token_secret)

    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
    })

    if proxy:
        import config.proxies as set_proxies
        proxies = set_proxies.set_ons_proxies(ssl=False, headers=headers)
        api = tweepy.API(auth, wait_on_rate_limit=True, proxy=proxies.get('https'))
        api.session.verify = False
    else:
        api = tweepy.API(auth, wait_on_rate_limit=True)

    return api


def post_status(response, proxy, github_action):
    """
    Posts response to Twitter
    :param response: <string> The string response to post
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as an automated GitHub Action
    :return: <string> The response of whether the service is online or not
    """

    api = authenticate_twitter(github_action, proxy)

    # Posts status to Twitter
    api.update_status(response)

    print("Posted update to Twitter")

def post_media(proxy, github_action, service):
    """
    Posts response to Twitter
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as an automated GitHub Action
    :param service: <string> Premium or Fast Track
    :return: <string> The response of whether the service is online or not
    """

    api = authenticate_twitter(github_action, proxy)

    # Posts status to Twitter
    media = api.media_upload(filename='out.png')

    timestamp = get_timestamp(github_action, timestamp_string_format='%d/%m/%Y %H:%M')
    api.update_status(status=f'The latest {service} slots as of {timestamp}', media_ids=[media.media_id])

    print("Posted update to Twitter")


def update_twitter_bio(github_action, proxy, one_week_status, premium_status):
    """
    Update Twitter Bio
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :param proxy: <Boolean> Whether using a proxy or not
    :param one_week_status: <string> The status of the one week service
    :param premium_status: <string> The status of the premium service
    """
    timestamp = get_timestamp(github_action, timestamp_string_format='%H:%M')

    api = authenticate_twitter(github_action, proxy)

    if premium_status == "Busy":
        premium_status_symbol = f"OP ️is busy,"
    elif premium_status == "True":
        premium_status_symbol = f"OP is online,"
    else:
        premium_status_symbol = f"OP is offline,"

    if one_week_status == "Busy":
        one_week_status_symbol = f"FT is busy"
    elif one_week_status == "True":
        one_week_status_symbol = f"FT is online"
    else:
        one_week_status_symbol = f"FT is offline"

    new_bio = f"Unofficial bot. Runs every minute. Please check http://gov.uk/get-a-passport-urgently before " \
              f"booking. {premium_status_symbol} {one_week_status_symbol} (updated {timestamp})."

    # Posts status to Twitter
    api.update_profile(description=new_bio)

    print("Updated bio on Twitter")


def online_status_on_last_check_twitter(service, github_action, proxy):
    """
    Returns string value depending if the Twitter bio says a service is online or offline
    :param service: <string> Either fast track or premium to check
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :param proxy: <Boolean> Whether using a proxy or not
    :return: <string> True or False string based on what is in the bio
    """
    # Uses GitHub Secrets to store and load credentials
    api = authenticate_twitter(github_action, proxy)

    id = "1521412356361920516"
    user = api.get_user(user_id=id)
    bio_desc = user.description

    if service == "fast track":
        if "FT is online" in bio_desc:
            return 'True'
        else:
            return 'False'
    elif service == "premium":
        if "OP is online" in bio_desc:
            return 'True'
        else:
            return 'False'
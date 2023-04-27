import os
import requests
from scripts.utils.time import get_timestamp
import tweepy


def authenticate_twitter(github_action, proxy, gt):
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
        if gt:
            import config.twitter_credentials_gt as twitter_credentials
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
    :return: <string> The tweet id
    """

    api = authenticate_twitter(github_action, proxy, gt = False)

    # Posts status to Twitter
    tweet = api.update_status(response)
    tweet_id = tweet.id_str

    print("Posted update to Twitter")

    return tweet_id

def post_quick_check(proxy, github_action, service):
    """
    Posts text response to Twitter
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as an automated GitHub Action
    :param service: <string> Premium or Fast Track
    :return: <string> The response of whether the service is online or not
    """

    if service == 'fast track':
        url = "https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/tweet_id_ft.md"
    elif service == 'premium':
        url = "https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/tweet_id_op.md"

    tweetid = requests.get(url).\
        text.replace("\n","")

    api = authenticate_twitter(github_action, proxy, gt = False)

    timestamp = get_timestamp(github_action, timestamp_string_format='%d/%m/%Y %H:%M')

    if service == "fast track":
        message = f"Fast Track appointments seem to have been added at {timestamp}. The bot will try and get the " \
                  f"number and location now."

    api.update_status(status=message,
                      in_reply_to_status_id=tweetid)

    print("Posted text update to Twitter")

def post_media(proxy, github_action, service):
    """
    Posts response to Twitter
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as an automated GitHub Action
    :param service: <string> Premium or Fast Track
    :return: <string> The response of whether the service is online or not
    """

    if service == 'fast track':
        url = "https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/tweet_id_ft.md"
    elif service == 'premium':
        url = "https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/tweet_id_op.md"

    tweetid = requests.get(url).\
        text.replace("\n","")

    api = authenticate_twitter(github_action, proxy, gt = False)

    # Posts status to Twitter
    media = api.media_upload(filename='out.png')

    timestamp = get_timestamp(github_action, timestamp_string_format='%d/%m/%Y %H:%M')

    if service == "fast track":
        message = f"The latest Fast Track appointment slots as of {timestamp}. More may be added whilst the service" \
                  f" is online. I'll keep checking if more are added."
    elif service == "premium":
        message = f"The latest Premium appointment slots as of {timestamp}. More may be added " \
                  f"whilst the service is online. I'll keep checking if more are added."

    api.update_status(status=message,
                      media_ids=[media.media_id],
                      in_reply_to_status_id=tweetid)

    print("Posted update to Twitter")


def post_media_update_gt(proxy, github_action, locs_added_checked):
    """
    Posts response to Twitter
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as an automated GitHub Action
    :param locs_added_checked: <list> Locations added
    :return: <string> The response of whether the service is online or not
    """

    api = authenticate_twitter(github_action, proxy, gt = True)

    # Posts status to Twitter
    media = api.media_upload(filename='out.png')

    timestamp = get_timestamp(github_action, timestamp_string_format='%d/%m/%Y %H:%M')

    locations = ' and '.join(locs_added_checked)

    message = f"🎫 (Golden Ticket) Want to change your Fast Track booking? New appointments have " \
              f"been added for {locations}." \
              f"\n" \
              f"\n" \
              f"🎫 explained here: https://twitter.com/ukpassportcheck/status/1646491695607840768" \
              f"\n" \
              f"(contribute a ☕ to help running costs at: https://www.buymeacoffee.com/ukpassportcheck)"

    api.update_status(status=message,
                      media_ids=[media.media_id])

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

    api = authenticate_twitter(github_action, proxy, gt = False)

    if premium_status == "Error":
        premium_status_symbol = f"OP ️is error,"
    elif premium_status == "True":
        premium_status_symbol = f"OP is online,"
    else:
        premium_status_symbol = f"OP is offline,"

    if one_week_status == "Error":
        one_week_status_symbol = f"FT is error"
    elif one_week_status == "True":
        one_week_status_symbol = f"FT is online"
    else:
        one_week_status_symbol = f"FT is offline"

    new_bio = f"Also see @passportwaiting & @ukpassportgold 🎫. Read http://gov.uk/get-a-passport-urgently" \
              f". {premium_status_symbol} {one_week_status_symbol} (at {timestamp}). Charity link below"

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
    api = authenticate_twitter(github_action, proxy, gt = False)

    id = "1521412356361920516"
    user = api.get_user(user_id=id)
    bio_desc = user.description

    if service == "fast track":
        if "FT is online" in bio_desc:
            return 'True'
        elif "FT is offline" in bio_desc:
            return 'False'
        elif "FT is error" in bio_desc:
            return 'Error'

    elif service == "premium":
        if "OP is online" in bio_desc:
            return 'True'
        else:
            return 'False'


def post_media_update(proxy, github_action, locs_added_checked, service):
    """
    Posts response to Twitter
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as an automated GitHub Action
    :param locs_added_checked: <list> Locations added
    :return: <string> The response of whether the service is online or not
    """

    if service == "fast track":
        tweetid = requests.get("https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/tweet_id_ft.md").\
            text.replace("\n","")
    else:
        tweetid = requests.get("https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/tweet_id_op.md").\
            text.replace("\n","")

    api = authenticate_twitter(github_action, proxy, gt = False)

    # Posts status to Twitter
    media = api.media_upload(filename='out.png')

    locations = ' and '.join(locs_added_checked)

    if service == "fast track":
        message = f"New Fast Track slots have been added for {locations}." \
                  f"\n" \
                  f"\n" \
                  f"(contribute a ☕ to help running costs at: https://www.buymeacoffee.com/ukpassportcheck)"
    else:
        message = f"New or unbooked Premium slots have been added for {locations}." \
                  f"\n" \
                  f"\n" \
                  f"(contribute a ☕ to help running costs at: https://www.buymeacoffee.com/ukpassportcheck)"

    api.update_status(status=message,
                      media_ids=[media.media_id],
                      in_reply_to_status_id=tweetid)

    print("Posted update to Twitter")
    return message

def post_status_update(proxy, github_action):
    """
    Posts response to Twitter
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as an automated GitHub Action
    :param locs_added_checked: <list> Locations added
    :return: <string> The response of whether the service is online or not
    """

    timestamp = get_timestamp(github_action, timestamp_string_format='%d/%m/%Y %H:%M')

    tweetid = requests.get("https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/tweet_id_ft.md").\
        text.replace("\n","")

    api = authenticate_twitter(github_action, proxy, gt = False)

    message = f"No appointments available at the moment. The bot will keep checking and post when " \
              f"appointments are added ({timestamp})."

    api.update_status(status=message, in_reply_to_status_id=tweetid)

    print("Posted update to Twitter")
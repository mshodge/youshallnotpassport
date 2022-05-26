from datetime import datetime, timedelta
from github import Github
import os
import pandas as pd
import requests
import tweepy
import urllib3

urllib3.disable_warnings()

is_proxy = False
is_github_action = True
to_save_csv = False
is_twitter = True


def authenticate_twitter(github_action, proxy):
    """
    Authenticates Twitter
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :param proxy: <Boolean> Whether to use a proxy or not
    :return: api <tweepy.api> the tweepy api response
    """

    # Uses GitHub Secrets to store and load credentials
    if github_action:
        auth = tweepy.OAuthHandler(os.environ['bio_consumer_key'], os.environ['bio_consumer_secret'])
        auth.set_access_token(os.environ['bio_access_token'], os.environ['bio_access_token_secret'])

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


def get_timestamp(github_action, timestamp_string_format='%H:%M'):
    """
    Gets timestamp
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :param timestamp_string_format: <string> The datetime format to return
    :return: timestamp <string> The formatted datetime
    """
    if github_action:
        timestamp = datetime.now() + timedelta(hours=1)
        timestamp = timestamp.strftime(timestamp_string_format)
    else:
        timestamp = datetime.now().strftime(timestamp_string_format)
    return timestamp


def update_twitter_bio(github_action, proxy, one_week_status, premium_status):
    """
    Update Twitter Bio
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :param proxy: <Boolean> Whether using a proxy or not
    :param one_week_status: <string> The status of the one week service
    :param premium_status: <string> The status of the premium service
    """
    timestamp = get_timestamp(github_action, timestamp_string_format='%H:%M')

    # Uses GitHub Secrets to store and load credentials
    if github_action:
        auth = tweepy.OAuthHandler(os.environ['bio_consumer_key'], os.environ['bio_consumer_secret'])
        auth.set_access_token(os.environ['bio_access_token'], os.environ['bio_access_token_secret'])

    # Else uses local twitter_credentials.py file
    else:
        import config.twitter_credentials as twitter_credentials
        auth = tweepy.OAuthHandler(twitter_credentials.bio_consumer_key, twitter_credentials.bio_consumer_secret)
        auth.set_access_token(twitter_credentials.bio_access_token, twitter_credentials.bio_access_token_secret)

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

    new_bio = f"Unofficial bot. Runs every ~30 mins. Please check http://gov.uk/get-a-passport-urgently before " \
              f"booking. {premium_status_symbol} {one_week_status_symbol} (updated {timestamp})."

    # Posts status to Twitter
    api.update_profile(description=new_bio)

    print("Updated bio on Twitter")


def read_online_status():
    """
    Loads online status file
    :return: df_online_status <DataFrame> The Dataframe with online status in
    """

    df_online_status = pd.read_csv("https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/online.csv")
    return df_online_status


def online_status_on_last_check(df_old_online_status, service):
    """
    Returns value from dataframe
    :param df_old_online_status: <DataFrame> The DataFrame of online status
    :param service: <string> The service type
    :return: <string> Whether the status is online ('True', 'Busy') or not ('False')
    """

    return str(df_old_online_status[df_old_online_status['service'] == service]['online'].values[0])


def update_online_status(df_status, github_action):
    """
    Updates csv file on GitHub and local
    :param df_status: <DataFrame> The DataFrame from the current check
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :return: <string> The response of whether the service is online or not
    """

    print("Updating online status csv file both locally and on GitHub")

    # Gets current csv file from open repo
    org = "mshodge"
    repo = "youshallnotpassport"
    branch = "main"
    file_path = "data/online.csv"

    df_string = df_to_csv_string(df_status)

    if github_action:
        token = os.environ['access_token_github']
    else:
        import config.github_credentials as github_credentials
        token = github_credentials.access_token

    # Authenticates GitHub and updates file with df_string
    g = Github(token)
    repo = g.get_repo(f"{org}/{repo}")
    contents = repo.get_contents(file_path, ref=branch)

    repo.update_file(path=file_path,
                     message="updating online status",
                     content=df_string,
                     branch=branch,
                     sha=contents.sha)

    # Also, saves to local disk
    df.to_csv(file_path)


def df_to_csv_string(df_to_convert):
    """
    Converts a pandas DataFrame into a csv string for upload to GitHub
    :param df_to_convert: <DataFrame> The DataFrame
    :return: df_string <string> The rDa
    """

    df_string = ""

    # For columns
    for idx, value in enumerate(df_to_convert.columns.to_list()):
        if idx < df_to_convert.columns.shape[0] - 1:
            df_string += value + ","
        else:
            df_string += value + "\n"

    # For all rows in DataFrame
    for index, row in df_to_convert.iterrows():
        for idx, value in enumerate(row.to_list()):
            if idx < df_to_convert.columns.shape[0] - 1:
                df_string += str(value) + ","
            else:
                df_string += str(value) + "\n"

    return df_string


def update_csv(df_response_from_check, github_action):
    """
    Updates csv file on GitHub and local
    :param df_response_from_check: <DataFrame> The DataFrame from the current check
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :return: <string> The response of whether the service is online or not
    """

    print("Updating csv file both locally and on GitHub")

    # Gets current csv file from open repo
    org = "mshodge"
    repo = "youshallnotpassport"
    branch = "main"
    file_path = "data/data.csv"
    csv_url = f'https://raw.githubusercontent.com/{org}/{repo}/{branch}/{file_path}'

    df_data = pd.read_csv(csv_url)
    df_data = pd.concat([df_data, df_response_from_check], ignore_index=True)
    df_string = df_to_csv_string(df_data)

    if github_action:
        token = os.environ['access_token_github']
    else:
        import config.github_credentials as github_credentials
        token = github_credentials.access_token

    # Authenticates GitHub and updates file with df_string
    g = Github(token)
    repo = g.get_repo(f"{org}/{repo}")
    contents = repo.get_contents(file_path, ref=branch)

    repo.update_file(path=file_path,
                     message="updating data",
                     content=df_string,
                     branch=branch,
                     sha=contents.sha)

    # Also, saves to local disk
    df.to_csv(file_path)


def post(response, proxy, github_action):
    """
    Posts response to Twitter
    :param response: <string> The string response to post
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as an automated GitHub Action
    :return: <string> The response of whether the service is online or not
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

    # Posts status to Twitter
    api.update_status(response)

    print("Posted update to Twitter")


def check(proxy, github_action):
    """
    Checks if the passport services are online or not
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as an automated GitHub Action
    :return: <string> The response of whether the service is online or not
    """
    url_one_week = "https://www.passportappointment.service.gov.uk/outreach/publicbooking.ofml"
    url_premium = "https://www.passport.service.gov.uk/urgent/" \
                  "?_ga=2.165977918.1052226504.1651564347-663154096.1628163070"

    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
    })

    # Uses requests library to get response from url pages. Proxy is there in case you are scraping from behind a
    # VPN. See README.md for more information
    if proxy:
        import config.proxies as set_proxies

        proxies = set_proxies.set_ons_proxies(ssl=False, headers=headers)
        page_one_week = requests.get(url_one_week, proxies=proxies,
                                     verify=False, headers=headers,
                                     timeout=600)
        page_premium = requests.get(url_premium, proxies=proxies, verify=False, headers=headers, timeout=600)
        page_one_text = page_one_week.text
        page_premium_text = page_premium.text
        page_one_week.close()
        page_premium.close()
    else:
        page_one_week = requests.get(url_one_week, timeout=600)
        page_premium = requests.get(url_premium, timeout=600)
        page_one_text = page_one_week.text
        page_premium_text = page_premium.text
        page_one_week.close()
        page_premium.close()

    # GitHub uses GMT and not BST so adjusting for that here
    # //TODO: Make this more dynamic and not hard coded, as when BST ends this will trip up
    timestamp = get_timestamp(github_action, timestamp_string_format='%d/%m/%Y %H:%M')

    # Reports if one week service is online or not
    if "service is unavailable" in page_one_text:
        response_one_week = f"One week fast track service is now offline ❌ ({timestamp})" \
                            f"\n" \
                            f"\n" \
                            f"Bot checks every minute, and will post again if status changes." \
                            f"\n" \
                            f"https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
        one_week_online = "False"
    elif "System busy" in page_one_text:
        response_one_week = f"One week fast track service is still online but busy ⚠️ ({timestamp})" \
                            f"\n" \
                            f"\n" \
                            f"Bot checks every minute, and will post again if status changes." \
                            f"\n" \
                            f"https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
        one_week_online = "True"
    else:
        response_one_week = f"One week fast track service is now online! ✅ ({timestamp})" \
                            f"\n" \
                            f"\n" \
                            f"Bot checks every minute, and will post again if status changes." \
                            f"\n" \
                            f"https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
        one_week_online = "True"

    # Reports if premium service is online or not
    if "service is unavailable" in page_premium_text:
        response_premium = f"Premium service is now offline ❌ ({timestamp})" \
                           f"\n" \
                           f"\n" \
                           f"Bot checks every minute, and will post again if status changes." \
                           f"\n" \
                           f"https://www.gov.uk/get-a-passport-urgently/online-premium-service"
        premium_online = "False"
    elif "Sorry, there are no available appointments" in page_premium_text:
        response_premium = f"Premium service now offline ❌ ({timestamp})" \
                           f"\n" \
                           f"\n" \
                           f"Bot checks every minute, and will post again if status changes" \
                           f"\n" \
                           f"https://www.gov.uk/get-a-passport-urgently/online-premium-service"
        premium_online = "False"
    elif "System busy" in page_premium_text:
        response_premium = f"Premium service is still online but busy ⚠️ ({timestamp})" \
                           f"\n" \
                           f"\n" \
                           f"Bot checks every minute, and will post again if status changes." \
                           f"\n" \
                           f"https://www.gov.uk/get-a-passport-urgently/online-premium-service"
        premium_online = "True"
    else:
        response_premium = f"Premium service is now online! ✅ ({timestamp})" \
                           f"\n" \
                           f"\n" \
                           f"Bot checks every minute, and will post again if status changes." \
                           f"\n" \
                           f"https://www.gov.uk/get-a-passport-urgently/online-premium-service"
        premium_online = "True"

    print(response_one_week)
    print(response_premium)

    # Creates a DataFrame from the response checks

    df_response_from_check = pd.DataFrame(
        [["one week fast track", one_week_online, timestamp],
         ["premium", premium_online, timestamp]],
        columns=['service', 'online', 'timestamp'])

    df_status = pd.DataFrame(
        [["fast_track", one_week_online],
         ["premium", premium_online]],
        columns=['service', 'online'])

    if to_save_csv:
        update_csv(df_response_from_check, github_action)

    return response_one_week, response_premium, premium_online, one_week_online, df_status


if __name__ == '__main__':

    response_one_week_check, response_premium_check, premium_online_check, one_week_online_check, df_status_is = \
        check(is_proxy, is_github_action)

    df = read_online_status()

    if is_twitter:
        # Now only posts if there has been a status change
        if one_week_online_check != online_status_on_last_check(df, 'fast_track'):
            print('\n\nOne week service status has changed, will post to Twitter!\n\n')
            post(response_one_week_check, is_proxy, is_github_action)
        if premium_online_check != online_status_on_last_check(df, 'premium'):
            print('\n\nPremium service status has changed, will post to Twitter!\n\n')
            post(response_premium_check, is_proxy, is_github_action)
        update_online_status(df_status_is, is_github_action)
        update_twitter_bio(is_github_action, is_proxy, one_week_online_check, premium_online_check)

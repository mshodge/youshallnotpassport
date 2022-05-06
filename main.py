import requests
import tweepy
from datetime import datetime, timedelta
import os
from github import Github
import pandas as pd
import urllib3

urllib3.disable_warnings()

proxy = False
github_action = True
save_csv = True
post_to_twitter = True

def df_to_csv_string(df):
    """
    Converts a pandas DataFrame into a csv string for upload to GitHub
    :param df: <DataFrame> The DataFrame
    :return: df_string <string> The rDa
    """

    df_string = ""

    # For columns
    for idx, value in enumerate(df.columns.to_list()):
        if idx < df.columns.shape[0] - 1:
            df_string += value + ","
        else:
            df_string += value + "\n"

    # For all rows in DataFrame
    for index, row in df.iterrows():
        for idx, value in enumerate(row.to_list()):
            if idx < df.columns.shape[0] - 1:
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

    df = pd.read_csv(csv_url)
    df = pd.concat([df, df_response_from_check], ignore_index=True)
    df_string = df_to_csv_string(df)

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
    :param github_action: <Boolean> Whether this will be deployed as a automated GitHub Action
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
    :param github_action: <Boolean> Whether this will be deployed as a automated GitHub Action
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
                                     verify="C:/GitProjects/youshallnotpassport/config/perm.cer", headers=headers,
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
    if github_action:
        timestamp = datetime.now() + timedelta(hours=1)
        timestamp = timestamp.strftime('%d/%m/%Y %H:%M')

    else:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')

    # Reports if one week service is online or not
    if "service is unavailable" in page_one_text:
        response = f"One week fast track service is unavailable ❌ ({timestamp}) " \
                   f"\n" \
                   f"https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
        one_week_online = "False"
    elif "System busy" in page_one_text:
        response = f"One week fast track service is online but busy ⚠️ ({timestamp}) " \
                   f"\n" \
                   f"https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
        one_week_online = "Busy"
    else:
        response = f"One week fast track service is available ✅ ({timestamp}) " \
                   f"\n" \
                   f"https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
        one_week_online = "True"

    # Reports if premiunm service is online or not
    if "service is unavailable" in page_premium_text:
        response += f"\n" \
                    f"\n" \
                    f"Premium service is unavailable ❌ ({timestamp}) " \
                    f"\n" \
                    f"https://www.gov.uk/get-a-passport-urgently/online-premium-service"
        premium_online = "False"
    elif "System busy" in page_premium_text:
        response += f"\n" \
                   f"\n" \
                   f"Premium service is online but busy ⚠️ ({timestamp}) " \
                   f"\n" \
                   f"https://www.gov.uk/get-a-passport-urgently/online-premium-service"
        premium_online = "Busy"
    else:
        response += f"\n" \
                    f"\n" \
                    f"Premium service is available ✅ ({timestamp}) " \
                    f"\n" \
                    f"https://www.gov.uk/get-a-passport-urgently/online-premium-service"
        premium_online = "True"

    print(response)

    # Creates a DataFrame from the response checks
    df_response_from_check = pd.DataFrame(
        [["one week fast track", one_week_online, timestamp],
         ["premium", premium_online, timestamp]],
        columns=['service', 'online', 'timestamp'])

    if save_csv:
        update_csv(df_response_from_check, github_action)

    return response, premium_online, one_week_online


if __name__ == '__main__':

    response, premium_online, one_week_online = check(proxy, github_action)

    if one_week_online != 'False' or premium_online != 'False':
        post(response, proxy, github_action)

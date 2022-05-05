import requests
import tweepy
from datetime import datetime, timedelta
import os
from github import Github
import pandas as pd


post_to_twitter = False
proxy = True
github_action = False

def df_to_csv_string(df):
    """
    Converts a pandas DataFrame into a csv string for upload to GitHub
    :param df: <DataFrame> The DataFrame
    :return: df_string <string> The rDa
    """

    df_string = ""

    for idx, value in enumerate(df.columns.to_list()):
        if idx < df.columns.shape[0] - 1:
            df_string += value + ","
        else:
            df_string += value + "\n"

    for index, row in df.iterrows():
        for idx, value in enumerate(row.to_list()):
            if idx < df.columns.shape[0] - 1:
                df_string += str(value) + ","
            else:
                df_string += str(value) + "\n"

    return df_string

def update_csv(service, online, timestamp, github_action):
    """
    Updates csv file on GitHub and local
    :param service: <string> The service as a string
    :param online: <Boolean> Whether the service is online or not
    :param timestamp: <string> A string timestamp in DD/MM/YYYY HH:MM format
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :return: <string> The response of whether the service is online or not
    """

    print("Updating csv file both locally, and on GitHub")

    org = "mshodge"
    repo = "youshallnotpassport"
    branch = "main"
    file_path = "data/data.csv"
    csv_url = f'https://raw.githubusercontent.com/{org}/{repo}/{branch}/{file_path}'
    df = pd.read_csv(csv_url)

    df_new = pd.DataFrame([[service, online, timestamp]], columns = ['service', 'online', 'timestamp'])

    df = df.append(df_new, ignore_index = True)

    if github_action:
        token = os.environ['github_token']
    else:
        import config.github_credentials as github_credentials
        token = github_credentials.access_token

    g = Github(token)
    repo = g.get_repo("mshodge/youshallnotpassport")
    contents = repo.get_contents(file_path, ref = "main")

    df_string = df_to_csv_string(df)

    repo.update_file(path = file_path, message = "updating data", content = df_string, branch = "main",
                     sha = contents.sha)

    df.to_csv(file_path)

def post(response, proxy, github_action):
    """
    Posts response to Twitter
    :param response: <string> The string response to post
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as a automated GitHub Action
    :return: <string> The response of whether the service is online or not
    """

    if github_action:
        auth = tweepy.OAuthHandler(os.environ['consumer_key'], os.environ['consumer_secret'])
        auth.set_access_token(os.environ['access_token'], os.environ['access_token_secret'])

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
        proxies = set_proxies.set_ons_proxies(ssl = False, headers = headers)
        api = tweepy.API(auth, wait_on_rate_limit = True, proxy = proxies.get('https'))
        api.session.verify = False
    else:
        api = tweepy.API(auth, wait_on_rate_limit = True)

    api.update_status(response)
    print("Posted to Twitter")


def check(proxy, github_action):
    """
    Checks if the passport services are online or not
    :param proxy: <Boolean> Whether to use a proxy or not, default is False
    :param github_action: <Boolean> Whether this will be deployed as a automated GitHub Action
    :return: <string> The response of whether the service is online or not
    """
    url_one_week = "https://www.passportappointment.service.gov.uk/outreach/publicbooking.ofml"
    url_premium = "https://www.passport.service.gov.uk/urgent/?_ga=2.165977918.1052226504.1651564347-663154096.1628163070"

    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
    })

    if proxy:
        import config.proxies as set_proxies

        proxies = set_proxies.set_ons_proxies(ssl = False, headers = headers)
        page_1_week = requests.get(url_one_week, proxies = proxies, verify = "C:/GitProjects/youshallnotpassport/config/perm.cer", headers = headers, timeout=600)
        page_premium = requests.get(url_premium, proxies = proxies, verify = False, headers = headers, timeout=600)
        page_1_week_text = page_1_week.text
        page_premium_text = page_premium.text
        page_1_week.close()
        page_premium.close()
    else:
        page_1_week = requests.get(url_one_week, verify = False, headers = headers, timeout=600)
        page_premium = requests.get(url_premium, verify = False, headers = headers, timeout=600)
        page_1_week_text = page_1_week.text
        page_premium_text = page_premium.text
        page_1_week.close()
        page_premium.close()

    if github_action:
        timestamp = datetime.now() + timedelta(hours=1)
        timestamp = timestamp.strftime('%d/%m/%Y %H:%M')

    else:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')


    if "service is unavailable" in page_1_week_text:
        response = f"One week fast track service is unavailable ❌ ({timestamp}) https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
        update_csv(service = "one week fast track", online = "False", timestamp = timestamp, github_action = github_action)
    elif "System busy" in page_1_week_text:
        response = f"One week fast track service is unavailable ❌ ({timestamp}) https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
        update_csv(service = "one week fast track", online = "False", timestamp = timestamp, github_action = github_action)
    else:
        response = f"One week fast track service is available ✅ ({timestamp}) https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
        update_csv(service = "one week fast track", online = "True", timestamp = timestamp, github_action = github_action)

    if "service is unavailable" in page_premium_text:
        response += f"\nPremium service is unavailable ❌ ({timestamp}) https://www.gov.uk/get-a-passport-urgently/online-premium-service"
        update_csv(service = "premium", online = "False", timestamp = timestamp, github_action = github_action)
    elif "System busy" in page_premium_text:
        response = f"Premium service is unavailable ❌ ({timestamp}) https://www.gov.uk/get-a-passport-urgently/online-premium-service"
        update_csv(service = "premium", online = "False", timestamp = timestamp, github_action = github_action)
    else:
        response += f"\nPremium service is available ✅ ({timestamp}) https://www.gov.uk/get-a-passport-urgently/online-premium-service"
        update_csv(service = "premium", online = "True", timestamp = timestamp, github_action = github_action)

    print(response)
    return response

if __name__ == '__main__':
    response = check(proxy, github_action)

    if post_to_twitter:
        post(response, proxy, github_action)
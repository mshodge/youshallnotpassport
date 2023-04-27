from github import Github
import os
import pandas as pd
import requests
import urllib3

from scripts.utils.twitter import post_status, update_twitter_bio, online_status_on_last_check_twitter
from scripts.utils.time import get_timestamp, check_if_half_hour_or_hour
from scripts.utils.github import read_online_status, update_online_status, update_tweet_id
from scripts.utils.sms import call_sms

urllib3.disable_warnings()

is_proxy = False
is_github_action = True
is_twitter = True


def df_to_csv_string(df_to_convert):
    """
    Converts a pandas DataFrame into a csv string for upload to GitHub
    :param df_to_convert: <DataFrame> The DataFrame
    :return: df_string <string> The rDa

    Args:
        df_to_convert: pd.DataFrame
            The DataFrame

    Returns:
        df_string: str
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


def update_csv(df, github_action, file_path, message):
    """
    Updates csv file on GitHub and local

    Args:
        df: pd.DataFrame
            The DataFrame from the current check

        github_action: Bool
            Whether a GitHub action or not, for auth

        file_path: str
            The path to upload the file to

        message: str
            The post message
    Returns:
        str
            The response of whether the service is online or not
    """

    print("Updating csv file both locally and on GitHub")

    # Gets current csv file from open repo
    org = "mshodge"
    repo = "youshallnotpassport"
    branch = "main"
    file_path = file_path
    csv_url = f'https://raw.githubusercontent.com/{org}/{repo}/{branch}/{file_path}'

    df_data = pd.read_csv(csv_url)
    df_data = pd.concat([df_data, df], ignore_index=True)
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
                     message=message,
                     content=df_string,
                     branch=branch,
                     sha=contents.sha)

    # Also, saves to local disk
    df_data.to_csv(f"{file_path}")


def run_appointments_code(id, github_action):
    """
    Returns value from dataframe

    Args:
        id: str
            The workflow id for github actions

        github_action: github_action: Bool
            If using github actions or not
    """

    if github_action:
        token = os.environ['access_token_github']
    else:
        import config.github_credentials as github_credentials
        token = github_credentials.access_token

    url = f"https://api.github.com/repos/mshodge/youshallnotpassport/actions/workflows/{id}/dispatches"
    headers = {"Authorization": "bearer " + token}
    json = {"ref": "main"}
    r = requests.post(url, headers=headers, json=json)
    print(r)


def online_status_on_last_check(df_old_online_status, service):
    """
    Returns value from dataframe

    Args:
        df_old_online_status: pd.DataFrame
            The DataFrame of online status

        service: str
            The service type

    Returns:
        str
            Whether the status is online ('True', 'Busy') or not ('False')
    """

    return str(df_old_online_status[df_old_online_status['service'] == service]['online'].values[0])


def check(proxy, github_action, to_save_csv):
    """
    Checks if the passport services are online or not

    Args:
        proxy: Bool
            Whether to use a proxy or not, default is False
        github_action: Bool
            Whether this will be deployed as an automated GitHub Action
        to_save_csv: Bool
            Whether to save to a csv

    """

    url_one_week = "https://www.passportappointment.service.gov.uk/outreach/publicbooking.ofml"
    url_premium = "https://www.passport.service.gov.uk/urgent/"

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
    timestamp_tweet = get_timestamp(github_action, timestamp_string_format='%d/%m %H:%M')

    # Reports if one week service is online or not
    if "there are no available appointments" in page_one_text or \
            "no Fast Track  appointments available" in page_one_text:
        response_one_week = f"❌ (FT) Fast Track service is now offline ({timestamp_tweet})" \
                            f"\n" \
                            f"\n" \
                            f"Say thanks with a ☕ at https://www.buymeacoffee.com/ukpassportcheck" \
                            f"\n" \
                            f"Charity donations 💙 at https://www.justgiving.com/fundraising/Donationsforzahary"
        one_week_online = "False"
    elif "is temporarily unavailable" in page_one_text:
        response_one_week = None
        one_week_online = None
    elif "503" in page_one_text:
        response_one_week = None
        one_week_online = None
    else:
        response_one_week = f"✅ (FT) Fast Track service is now online ({timestamp_tweet})" \
                            f"\n" \
                            f"\n" \
                            f"I'll try and post the appointments now..." \
                            f"\n" \
                            f"\n" \
                            f"(Still offline? Go back and click again)" \
                            f"\n" \
                            f"https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
        one_week_online = "True"

    # Reports if premium service is online or not
    if "there are no available appointments" in page_premium_text:
        response_premium = f"❌ (OP) Premium service is now offline ({timestamp_tweet})"\
                           f"\n" \
                           f"\n"\
                           f"Say thanks with a ☕ at https://www.buymeacoffee.com/ukpassportcheck" \
                           f"\n" \
                           f"Charity donations 💙 at https://www.justgiving.com/fundraising/Donationsforzahary"
        premium_online = "False"
    else:
        response_premium = f"✅ (OP) Premium service is now online ({timestamp_tweet})" \
                           f"\n" \
                           f"\n"\
                           f"I'll try and post the appointments now..." \
                           f"\n" \
                           f"(Sent to standard service? Go back and click again)" \
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
        update_csv(df_response_from_check, github_action, "data/data.csv", "updating data")

    return response_one_week, response_premium, premium_online, one_week_online, df_status


if __name__ == '__main__':

    check_if_save = check_if_half_hour_or_hour()

    response_one_week_check, response_premium_check, premium_online_check, one_week_online_check, df_status_is = \
        check(is_proxy, is_github_action, check_if_save)

    if response_one_week_check is not None and response_premium_check is not None:

        df = read_online_status()

        if is_twitter:
            # Now only posts if there has been a status change
            one_week_online_check_last = online_status_on_last_check_twitter("fast track", is_github_action, is_proxy)
            premium_online_check_last = online_status_on_last_check_twitter("premium", is_github_action,
                                                                            is_proxy)

            print(f'\n\nNew one week status is {one_week_online_check}, old was {one_week_online_check_last}\n')
            print(f'\n\nNew premium status is {premium_online_check}, old was {premium_online_check_last}\n')

            if one_week_online_check != one_week_online_check_last:
                print('\n\nOne week service status has changed, will post to Twitter!\n')
                tweet_id = post_status(response_one_week_check, is_proxy, is_github_action)
                update_tweet_id(is_github_action, tweet_id, 'fast track')
                call_sms('Fast Track', type="status", response=response_one_week_check)
                run_appointments_code("28775018", is_github_action)

            if premium_online_check != premium_online_check_last:
                print('\n\nPremium service status has changed, will post to Twitter!\n')
                tweet_id = post_status(response_premium_check, is_proxy, is_github_action)
                update_tweet_id(is_github_action, tweet_id, 'premium')
                call_sms('Premium', type="status", response=response_premium_check)
                run_appointments_code("28968845", is_github_action)

            update_online_status(df_status_is, is_github_action)
            update_twitter_bio(is_github_action, is_proxy, one_week_online_check, premium_online_check)

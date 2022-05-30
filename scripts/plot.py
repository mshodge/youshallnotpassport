from datetime import datetime, timedelta
import numpy as np
import os
import pandas as pd
import requests
import seaborn as sns
import tweepy

sns.set_theme()


is_github_action = False
is_proxy = False
is_twitter = False
today = datetime.now().strftime("%d/%m/%Y")
last_week = datetime.now() - timedelta(days=8)
last_week = last_week.strftime("%d/%m/%Y")

def print_current_files():
    current_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))
    # prints all files to check
    listOfFiles = list()
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(current_dir)):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames]

    for file_name in listOfFiles:
        print(file_name)

def post_to_twitter(github_action, proxy):
    """
        Posts response to Twitter
        :param github_action: <Boolean> Whether it is on GitHub action or not
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

    # Posts image to Twitter
    if github_action:
        filenames = ["/home/runner/work/youshallnotpassport/youshallnotpassport/data/latest_one week fast track_plot.png",
                     "/home/runner/work/youshallnotpassport/youshallnotpassport/data/latest_premium_plot.png"]
    else:
        filenames = ["../data/latest_one week fast track_plot.png", "../data/latest_premium_plot.png"]

    media_ids = []
    for filename in filenames:
        res = api.media_upload(filename)
        media_ids.append(res.media_id)

    api.update_status(status='Plots of when each service was online in the last week', media_ids=media_ids)


def read_data():
    df = pd.read_csv("https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/data.csv")
    df['count'] = np.where(df['online'] != 'False', 1, 0)
    df['date_col'] = pd.to_datetime(df['timestamp'], format='%d/%m/%Y %H:%M')
    df['date'] = df.timestamp.apply(lambda x: str(x).split(" ")[0])
    df['hour'] = df.timestamp.apply(lambda x: str(x).split(" ")[1].split(":")[0])
    df['day_of_week'] = pd.Series(df.date_col).dt.day_name()
    df['date_dow'] = df['date'] + " (" + df['day_of_week'] + ")"
    df = df[df['date'] < today]
    return df

def read_data_last_week():
    df = pd.read_csv("https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/data.csv")
    df['count'] = np.where(df['online'] != 'False', 1, 0)
    df['date_col'] = pd.to_datetime(df['timestamp'], format='%d/%m/%Y %H:%M')
    df['date'] = df.timestamp.apply(lambda x: str(x).split(" ")[0])
    df['hour'] = df.timestamp.apply(lambda x: str(x).split(" ")[1].split(":")[0])
    df['day_of_week'] = pd.Series(df.date_col).dt.day_name()
    df['date_dow'] = df['date'] + " (" + df['day_of_week'] + ")"
    df = df[df['date'] < today]
    df = df[df['date'] > last_week]
    return df

def reduce_and_pivot(df, service):
    df_service = df[df['service'] == service]
    df_service_pivot = pd.pivot_table(df_service, values='count',
                                      index='date_dow', columns='hour', aggfunc=np.sum, fill_value=0)
    return df_service_pivot


def plot(df, service, github_action, when):
    sns.set(rc={'figure.figsize': (18, 8)})
    ax = sns.heatmap(df, linewidths=.5, cbar=False, annot=True, cmap="Blues")
    ax.text(x=0.5, y=1.1, s=f'When was the {service} service online?',
            fontsize=18, weight='bold', ha='center', va='bottom', transform=ax.transAxes)
    ax.text(x=0.5, y=1.05, s=f'Count indicates how many times it was online {when} for every day and hour (max 2)',
            fontsize=12, alpha=0.75, ha='center', va='bottom', transform=ax.transAxes)
    ax.set_xlabel('Hour', fontsize=16)
    ax.set_ylabel('Date', fontsize=16)
    fig = ax.get_figure()
    print_current_files()

    if github_action:
        fig.savefig(f"/home/runner/work/youshallnotpassport/youshallnotpassport/data/latest_{service}_plot_{when.replace(' ', '_')}.png")
    else:
        fig.savefig(f"../data/latest_{service}_plot_{when.replace(' ', '_')}.png")
    fig.clf()
    return None


if __name__ == '__main__':

    df_of_raw_data = read_data()
    df_of_raw_data_last_week = read_data_last_week()

    for service_type in ["one week fast track", "premium"]:
        df_by_service = reduce_and_pivot(df_of_raw_data, service_type)
        df_by_service_last_week = reduce_and_pivot(df_of_raw_data_last_week, service_type)

        plot(df_by_service, service_type, is_github_action, when = "for the whole time-series")
        plot(df_by_service_last_week, service_type, is_github_action, when="last week")
    if is_twitter:
        post_to_twitter(is_github_action, is_proxy)

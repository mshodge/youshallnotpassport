import os
import pandas as pd
from github import Github

from scripts.utils.dataframes import df_to_csv_string


def read_online_status():
    """
    Loads online status file
    :return: df_online_status <DataFrame> The Dataframe with online status in
    """

    df_online_status = pd.read_csv(
        "https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/online.csv")
    return df_online_status


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
    df_status.to_csv(file_path)

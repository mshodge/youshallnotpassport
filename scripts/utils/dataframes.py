from github import Github
import os
import pandas as pd


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


def update_csv(df, github_action, file_path, message):
    """
    Updates csv file on GitHub and local
    :param df: <DataFrame> The DataFrame from the current check
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :param file_path: <string> The path to upload the file to
    :param message: <string> The post message
    :return: <string> The response of whether the service is online or not
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
    df_data.to_csv(f"../{file_path}")

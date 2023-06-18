from google.cloud import storage
import os

def online_status_on_last_google_storage(service, github_action, proxy):
    """
    Returns string value depending if the Twitter bio says a service is online or offline
    :param service: <string> Either fast track or premium to check
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :param proxy: <Boolean> Whether using a proxy or not
    :return: <string> True or False string based on what is in the bio
    """
    # Uses GitHub Secrets to store and load credentials
    if github_action:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    else:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r'config/gcp_credentials.json'

    storage_client = storage.Client()

    bucket = storage_client.bucket('ysnp-status')

    blob = bucket.blob('status.txt')

    with blob.open("r") as f:
        status = f.read()

    if service == "fast track":
        if "FT is online" in status:
            return 'True'
        elif "FT is offline" in status:
            return 'False'
        elif "FT is error" in status:
            return 'Error'

    elif service == "premium":
        if "OP is online" in status:
            return 'True'
        else:
            return 'False'


def update_status(github_action, proxy, one_week_status, premium_status):
    """
    Update Twitter Bio
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :param proxy: <Boolean> Whether using a proxy or not
    :param one_week_status: <string> The status of the one week service
    :param premium_status: <string> The status of the premium service
    """

    if github_action:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    else:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r'config/gcp_credentials.json'

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

    new_status = f"{premium_status_symbol} {one_week_status_symbol}"

    storage_client = storage.Client()

    bucket = storage_client.bucket('ysnp-status')

    blob = bucket.blob('status.txt')

    with blob.open("w") as f:
        f.write(new_status)

    print("Updated bio on GCP")
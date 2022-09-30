import json
import requests
import os
import google.oauth2.id_token
import google.auth.transport.requests
from google.oauth2.service_account import IDTokenCredentials
import time

from scripts.utils.time import get_timestamp


def get_token():

    sa_details = os.environ['gcp_token']

    sa_details = json.loads(sa_details)

    audience = 'https://europe-west2-youshallnotpassport.cloudfunctions.net/send_sms-http'

    credentials = IDTokenCredentials.from_service_account_info(
            sa_details,
            target_audience=audience)
    request = google.auth.transport.requests.Request()

    credentials.refresh(request)

    TOKEN = credentials.token
    return TOKEN

def call_sms(service, type, response):

    timestamp = get_timestamp(github_action=True, timestamp_string_format='%d/%m/%Y %H:%M')

    if service == "Fast Track":
        if type == "status":
            if "✅" in response:
                message = f"HMPO Fast Track service is now online {timestamp}. If more appointments are added, " \
                          f"you will receive another text. Booking link: " \
                          f"https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
            else:
                message = f"HMPO Fast Track service is now offline {timestamp}. You will get another text when it goes " \
                          f"online next."
        if type == "app":
            message = response
    elif service == "Premium":
        if type == "status":
            if "✅" in response:
                message = f"HMPO Premium service is now online {timestamp}. If more appointments are added, " \
                          f"you will receive another text. Booking link: " \
                          f"https://www.gov.uk/get-a-passport-urgently/online-premium-service"
            else:
                message = f"HMPO Premium service is now offline {timestamp}. You will get another text when it goes " \
                          f"online next."
        if type == "app":
            message = response

    token = get_token()

    param = {"service": service,
             "message": message}

    url = 'https://europe-west2-youshallnotpassport.cloudfunctions.net/send_sms-http'

    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(param)  # possible request parameters
    )
    r.status_code

if __name__ == "__main__":
    call_sms(service="Fast Track", type="status", response="✅")
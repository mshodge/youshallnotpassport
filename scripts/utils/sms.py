import json
import requests
import os
import google.oauth2.id_token
import google.auth.transport.requests
from google.oauth2.service_account import IDTokenCredentials


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

    if service == "Fast Track":
        if type == "status":
            if "✅" in response:
                message = f"Fast Track service is now online " \
                          f"https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service. You can cancel" \
                          f"your subscription here https://billing.stripe.com/p/login/6oE9Dv4Nw89G2QMaEE"
            else:
                message = f"Fast Track service is now offline. You can cancel " \
                          f"your subscription here https://billing.stripe.com/p/login/6oE9Dv4Nw89G2QMaEE"
        if type == "app":
            message = response
    elif service == "Premium":
        if type == "status":
            if "✅" in response:
                message = f"Premium service is now online " \
                          f"https://www.gov.uk/get-a-passport-urgently/online-premium-service. You can cancel" \
                          f"your subscription here https://billing.stripe.com/p/login/6oE9Dv4Nw89G2QMaEE"
            else:
                message = f"Premium service is now offline. You can cancel " \
                          f"your subscription here https://billing.stripe.com/p/login/6oE9Dv4Nw89G2QMaEE"
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
import json
import requests
import os

def get_token():
    token = os.environ['gcp_token']
    return token

def call_sms(service, type, response):

    if service == "Fast Track":
        if type == "status":
            if "✅" in response:
                message = f"Fast Track service is now online " \
                          f"https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service. You can cancel" \
                          f"your subscription here https://billing.stripe.com/p/login/6oE9Dv4Nw89G2QMaEE"
            else:
                message = f"Fast Track service is now offline. You can cancel" \
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
                message = f"Premium service is now offline. You can cancel" \
                          f"your subscription here https://billing.stripe.com/p/login/6oE9Dv4Nw89G2QMaEE"
        if type == "app":
            message = response

    token = get_token()

    param = {"service": service,
             "message": message}

    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(param)  # possible request parameters
    )
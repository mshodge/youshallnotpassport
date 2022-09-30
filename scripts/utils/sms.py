import json
import requests


def get_token():
    token = os.environ['gcp_token']
    return token

def call_sms(service, type, response):

    if service == "Fast Track"
        if type = "status":
            if ✅ in response:
                message = f"Fast Track service is now online https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service."
            else:
                message = f"Fast Track service is now offline."
    elif service == "Premium":
        if type = "status":
            if ✅ in response:
                message = f"Premium service is now online https://www.gov.uk/get-a-passport-urgently/online-premium-service."
            else:
                message = f"Premium service is now offline."

    token = get_token()

    param = {"service": service,
             "message": message}

    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(param)  # possible request parameters
    )
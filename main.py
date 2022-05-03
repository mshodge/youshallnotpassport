import requests
import tweepy
from datetime import datetime
import os


post_to_twitter = True
proxy = False
github_action = True

def post(response, proxy, github_action):
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


def check(proxy):
    url_one_week = "https://www.passportappointment.service.gov.uk/outreach/publicbooking.ofml"
    url_premium = "https://www.passport.service.gov.uk/urgent/?_ga=2.165977918.1052226504.1651564347-663154096.1628163070"

    if proxy:
        import config.proxies as set_proxies
        headers = requests.utils.default_headers()
        headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
        })

        proxies = set_proxies.set_ons_proxies(ssl = False, headers = headers)
        page_1_week = requests.get(url_one_week, proxies = proxies, verify = False, headers = headers)
        page_premium = requests.get(url_premium, proxies = proxies, verify = False, headers = headers)

    else:
        page_1_week = requests.get(url_one_week)
        page_premium = requests.get(url_premium)

    if "Sorry, this service is unavailable" in page_1_week.text:
        response = f"One week fast track service is unavailable ❎ ({datetime.now().strftime('%d/%m/%Y %H:%M')}) https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"
    else:
        response = f"One week fast track service is available ✅ ({datetime.now().strftime('%d/%m/%Y %H:%M')}) https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service"

    if "Sorry, this service is unavailable" in page_premium.text:
        response += f"\nPremium service is unavailable ❎ ({datetime.now().strftime('%d/%m/%Y %H:%M')}) https://www.gov.uk/get-a-passport-urgently/online-premium-service"
    else:
        response += f"\nPremium service is available ✅ ({datetime.now().strftime('%d/%m/%Y %H:%M')}) https://www.gov.uk/get-a-passport-urgently/online-premium-service"

    print(response)
    return response

if __name__ == '__main__':
    response = check(proxy)

    if post_to_twitter:
        post(response, proxy, github_action)

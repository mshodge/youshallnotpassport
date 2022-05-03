import requests
from datetime import datetime
import config.proxies as set_proxies


def check(proxy = False):
    url_one_week = "https://www.passportappointment.service.gov.uk/outreach/publicbooking.ofml"
    url_premium = "https://www.passport.service.gov.uk/urgent/?_ga=2.165977918.1052226504.1651564347-663154096.1628163070"

    if proxy:
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
        response_one_week = f"One week fast track service is unavailable ❎ ({datetime.now().strftime('%d/%m/%Y %H:%M')})"
    else:
        response_one_week = f"One week fast track service is available ✅ ({datetime.now().strftime('%d/%m/%Y %H:%M')})"

    if "Sorry, this service is unavailable" in page_premium.text:
        response_premium = f"Premium service is unavailable ❎ ({datetime.now().strftime('%d/%m/%Y %H:%M')})"
    else:
        response_premium = f"Premium service is available ✅ ({datetime.now().strftime('%d/%m/%Y %H:%M')})"

    print(response_one_week)
    print(response_premium)


if __name__ == '__main__':
    check(proxy = True)

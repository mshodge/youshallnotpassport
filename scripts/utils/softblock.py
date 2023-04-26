import chromedriver_autoinstaller
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import urllib.request
import requests
import time
import os


def get_azure_key(github_action) -> str:
    """
    Gets the Azure Key depending if it's running as a GitHub Action or not

    Params:
        github_action: Bool
            TRUE if it's running as a GitHub Action...

    Returns:
        token: str
            The token key for Azure
    """
    if github_action:
        token = os.environ['subscription_key']
    else:
        import config.azure_credentials as azure_credentials

        token = azure_credentials.subscription_key
    return token


def setup_selenium(url):
    """
    Sets up the Selenium webdriver

    Params:
        url: str
            The web url to create the driver for
        is_github_action: bool
            Whether running as a GitHub Action or not

    Returns:
        driver:
            The selenium web driver

    """

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument("--nogpu")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("--incognito")
    options.add_argument("--enable-javascript")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(options=options)

    ua = UserAgent()
    userAgent = ua.random

    driver.get(url)
    time.sleep(0.2)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": userAgent})

    return driver


def wait_in_queue(driver):
    """
    Waits in a queue if there is one

    Params:
        driver
            The selenium webdriver

    Returns:
        driver:
            The selenium web driver

    """

    keep_trying = True
    waited_time = 0

    while keep_trying:

        try:
            time_element = driver.find_element(by=By.XPATH,
                                                    value='/html/body/div[3]/div[3]/div[3]/div[2]/div[5]/div/p[3]/div[1]/span[2]')
            if len(time_element.text.split()) > 0:
                wait_time_is = time_element.text.split()[0]
                wait_time_is = wait_time_is
                print(f"Waiting time is {wait_time_is} minutes. Waited {waited_time} seconds")

            time.sleep(10)
            waited_time += 10
        except (StaleElementReferenceException, NoSuchElementException) as e:
            print(e)
            time.sleep(10)
            keep_trying = False
            return driver


def get_queue_status(driver) -> bool:
    """
    Checks for a recaptcha image and returns TRUE/FALSE

    Params:
        driver
            The selenium webdriver

    Returns:
        queue_found: Bool
            TRUE or FALSE depending if an image was found

    """
    try:
        driver.find_element(by=By.XPATH, value='/html/body/div[3]/div[3]/div[3]/div[2]/div[5]/div/p[3]/div[1]/span[2]')
        return True
    except NoSuchElementException:
        return False

def get_recapctha_image(driver) -> bool:
    """
    Checks for a recaptcha image and returns TRUE/FALSE

    Params:
        driver
            The selenium webdriver

    Returns:
        image_found: Bool
            TRUE or FALSE depending if an image was found

    """
    try:
        element = driver.find_element(by=By.XPATH,
                                           value='/html/body/div[2]/div[3]/div[3]/div[1]/div[2]/div/div/div/div[1]/div/fieldset/div[1]/img')
        img_url = element.get_attribute("src")
        urllib.request.urlretrieve(img_url, "local-filename.jpg")
        return True
    except NoSuchElementException:
        return False


def detect_text_url(is_github_action):
    """
    Checks for a recaptcha image and returns TRUE/FALSE

    Params:
        is_github_action: Bool
            TRUE if it's running as a GitHub Action...

    Returns:
        analysis
            JSON payload from Azure

    """
    subscription_key = get_azure_key(is_github_action)
    endpoint = "https://ysnp.cognitiveservices.azure.com/"

    text_recognition_url = endpoint + "/vision/v3.1/read/analyze"

    headers = {'Ocp-Apim-Subscription-Key': subscription_key, 'Content-Type': 'application/octet-stream'}
    with open('local-filename.jpg', 'rb') as f:
        data = f.read()
    response = requests.post(
        text_recognition_url, headers=headers, data=data)

    analysis = {}
    poll = True
    while poll:
        response_final = requests.get(
            response.headers["Operation-Location"], headers=headers)
        analysis = response_final.json()

        # print(json.dumps(analysis, indent=4))

        time.sleep(1)
        if "analyzeResult" in analysis:
            poll = False
        if "status" in analysis and analysis['status'] == 'failed':
            poll = False

    return analysis

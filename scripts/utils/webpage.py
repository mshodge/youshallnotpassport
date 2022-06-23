import time
from selenium.webdriver.common.by import By


def get_body(the_driver):
    """
    Get body text
    :param the_driver: <Selenium.webdriver> The selenium webdriver
    :return: body <>
    """

    body = the_driver.find_element(By.XPATH, '/html/body')
    return body


def click_page_element(the_driver, path_value, wait_time, by_what="xpath"):
    """
    Click the page element
    :param the_driver: <Selenium.webdriver> The selenium webdriver
    :param path_value: <string> the path value
    :param wait_time: <int> the wait time
    """

    time.sleep(wait_time)
    if by_what == "xpath":
        element = the_driver.find_element(by=By.XPATH, value=path_value)
    elif by_what == "class":
        element = the_driver.find_element(by=By.CLASS_NAME, value=path_value)
    element.click()


def enter_page_element(the_driver, path_value, value_to_enter, wait_time, by_what="xpath"):
    """
    Enter a value on the page
    :param the_driver: <Selenium.webdriver> The selenium webdriver
    :param path_value: <string> the path value
    :param value_to_enter: <string> the value to enter
    :param wait_time: <int> the wait time
    """

    time.sleep(wait_time)
    if by_what == "xpath":
        element = the_driver.find_element(by=By.XPATH, value=path_value)
    elif by_what == "class":
        element = the_driver.find_element(by=By.CLASS_NAME, value=path_value)
    element.send_keys(value_to_enter)

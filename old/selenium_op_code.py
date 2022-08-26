import chromedriver_autoinstaller
from datetime import datetime, timedelta, date
import numpy as np
import os
import pandas as pd
import requests
import seaborn as sns
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import sys
import time

from scripts.utils.twitter import post_media, post_media_update, post_status_update
from scripts.utils.dataframes import update_csv, get_csv
from scripts.utils.webpage import get_body, click_page_element, enter_page_element
from scripts.utils.github import update_no_app

chromedriver_autoinstaller.install()

def get_page(the_url, wait_time, sleep_time):
    """
    Get page
    :param the_url: <string> The url string
    :param wait_time: <int> Time to wait before checking page
    :param sleep_time: <int> Time to wait if failure
    :return: driver: <Selenium.webdriver> The selenium webdriver
    """

    keep_trying = True

    options = Options()
    if IS_GITHUB_ACTION:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    the_driver = webdriver.Chrome(options=options)

    while keep_trying:
        the_driver.get(the_url)
        body = get_body(the_driver)
        time.sleep(wait_time)
        if "Status last updated" in body.text:
            print(f"Waiting. Will check again in {sleep_time} seconds")
            time.sleep(sleep_time)
        elif "released soon" in body.text:
            print(f"Online Premium appointments will be released soon. Will check again in {sleep_time} seconds")
            time.sleep(sleep_time)
        elif "no available appointments" in body.text:
            print("Service is offline. Please try again when it's online.")
            return None
        elif "no Online Premium appointments available" in body.text:
            print("Service is offline. Please try again when it's online.")
            return None
        else:
            print("Success")
            keep_trying = False
    print(keep_trying)

    return the_driver

def input_information(the_driver):
    """
    Input information to the page
    :param the_driver: <Selenium.webdriver> The selenium webdriver
    :return driver: <Selenium.webdriver> The selenium webdriver
    """

    # Get started page
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/a', 0)

    # live in UK page
    click_page_element(the_driver, '//*[@id="is-uk-application-true-label"]', 0)
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/form/button', 0)

    # Applicant details page
    enter_page_element(the_driver, '//*[@id="date-of-birth-day"]', '01', 0)
    enter_page_element(the_driver, '//*[@id="date-of-birth-month"]', '01', 0)
    enter_page_element(the_driver, '//*[@id="date-of-birth-year"]', '1990', 0)
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/form/button', 0)

    # Passport before page
    click_page_element(the_driver, '//*[@id="previous-passport"]', 0)
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/form/button', 0)

    # Lost or stolen
    click_page_element(the_driver, '//*[@id="passport-lost-false"]', 0)
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/form/button', 0)

    # Name changed
    click_page_element(the_driver, '//*[@id="name-changed-false"]', 0)
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/form/button', 0)

    # Issued details page
    enter_page_element(the_driver, '//*[@id="passport-issue-day"]', '01', 0)
    enter_page_element(the_driver, '//*[@id="passport-issue-month"]', '01', 0)
    enter_page_element(the_driver, '//*[@id="passport-issue-year"]', '2010', 0)
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/form/button', 0)

    # Damaged
    click_page_element(the_driver, '//*[@id="damaged-false"]', 0)
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/form/button', 0)

    # Other passports
    click_page_element(the_driver, '//*[@id="other-passports-false"]', 0)
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/form/button', 0)

    # Go to appointments page
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/form/button', 0)

    # Go to appointments page
    click_page_element(the_driver, '//*[@id="main-content"]/div/div/div/form/button', 0)

    return the_driver

def clean_dataframe(df):
    """
    Clean the dataframe
    :param df: <pandas.dataframe> The pandas dataframe
    """

    for col in df.columns:
        df[col] = df[col].str.split().str[-1]

    df.index = ["London", "Peterborough", "Newport", "Liverpool", "Durham", "Glasgow", "Belfast"]

    df = df.replace(to_replace=['Available', 'Unavailable'], value=[1, 0])

    return df

def get_appointments(the_driver):
    """
    Get appointments
    :param the_driver: <Selenium.webdriver> The selenium webdriver
    :return df: <pandas.dataframe> The pandas dataframe
    """

    for i in range(0, 6):
        time.sleep(2)
        html = the_driver.page_source
        table = pd.read_html(html)
        df_tmp = table[0]
        df_tmp = clean_dataframe(df_tmp)
        print(df_tmp)

        if i != 0:
            cols_to_use = df_tmp.columns.difference(df.columns)
            df = pd.merge(df, df_tmp[cols_to_use], left_index=True, right_index=True, how="outer")
            df_col_order += list(df_tmp.columns)
        else:
            df = df_tmp
            df_col_order = list(df_tmp.columns)
        time.sleep(1)

        start_page = False

        if i == 0:
            try:
                the_driver.find_element(by=By.XPATH, value='//*[@id="main-content"]/form/div/div[2]/a')
            except NoSuchElementException:
                start_page = True

        if start_page:
            the_driver.find_element(by=By.XPATH, value='//*[@id="main-content"]/form/div/div/a')
            click_page_element(the_driver, '//*[@id="main-content"]/form/div/div/a', 2)
        else:
            if the_driver.find_element(by=By.XPATH, value='//*[@id="main-content"]/form/div/div[2]/a').size.get(
                    "height") != 0:
                the_driver.find_element(by=By.XPATH, value='//*[@id="main-content"]/form/div/div[2]/a')
                click_page_element(the_driver, '//*[@id="main-content"]/form/div/div[2]/a', 2)
            else:
                df_col_order = list(dict.fromkeys(df_col_order))
                df = df.reindex(df_col_order, axis=1)
                return df

def get_appointment_data(the_url):
    """
    The main function to get the appointment data from the table at the end of the process
    :input the_url: <string> The url to parse
    :return nice_appointments_df: <pandas.DataFrame> A pandas DataFrame of appointments, or None
    """

    driver = get_page(the_url, 1, 1)
    if driver is not None:
        try:
            driver_info = input_information(driver)
        except NoSuchElementException:
            run_github_action("28968845", IS_GITHUB_ACTION)
            print("Error. Will try again.")
            return None

        appointments_df = get_appointments(driver_info)

        if appointments_df is None:
            print("No appointments at the moment.")

            date_checked, result_checked = check_if_no_apps_before()

            if date_checked != TODAYS_DATE_IS:
                post_status_update(IS_PROXY, IS_GITHUB_ACTION)
                update_no_app(IS_GITHUB_ACTION, TODAYS_DATE_IS, "True", SERVICE)
            else:
                if result_checked == 'False':
                    post_status_update(IS_PROXY, IS_GITHUB_ACTION)
                    update_no_app(IS_GITHUB_ACTION, TODAYS_DATE_IS, "True", SERVICE)
            # say appointments have run out
            time.sleep(4 * 60)  # wait 4 mins before calling again
            run_github_action("32513748", IS_GITHUB_ACTION)
            return None

        else:
            nice_appointments_df = nice_dataframe(appointments_df)
            return nice_appointments_df

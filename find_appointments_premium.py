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

today = date.today()
TODAYS_DATE_IS = today.strftime("%d/%m/%Y")
MAIN_URL = 'https://www.passport.service.gov.uk/urgent/'
SERVICE = "premium"
IS_PROXY = False
IS_GITHUB_ACTION = True
IS_TWITTER = True


def check_diff_in_loc_counts(df):
    """
    Checks the difference in the counts of appointments at each office, if an office has 10 or more new appointments
    then the bot will flag this to be posted to Twitter
    :input df: <pandas.DataFrame> The pandas dataframe of latest results
    :return locs_added: <list> List of offices with new appointments added, is blank if None
    """

    df_old = get_csv("data/premium_appointments_locations.csv")
    df_diff = df_old.copy()
    df_diff['count'] = df['count'] - df_old['count']
    locs_added = []
    for index, row in df_diff.iterrows():
        if row['count'] > 1:
            locs_added.append(row['location'])

    return locs_added


def run_github_action(id):
    """
    Returns value from dataframe
    :param id: <string> the workflow id for github actions
    :param github_action: <Boolean> If using github actions or not
    """

    token = os.environ['access_token_github']
    url = f"https://api.github.com/repos/mshodge/youshallnotpassport/actions/workflows/{id}/dispatches"
    headers = {"Authorization": "bearer " + token}
    json = {"ref": "main"}
    r = requests.post(url, headers=headers, json=json)
    print(r)


def check_if_no_apps_before():
    """
    Checks if the bot has already seen a return of no appointments in the table already today
    :return no_app_check_date: <string> The date checked last
    :return no_app_check_result: <string> The result checked last
    """

    no_app_check = requests.get(
        "https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/premium_no_apps.md").text \
        .replace("\n", "").split(" ")
    no_app_check_date = no_app_check[0]
    no_app_check_result = no_app_check[1]
    return no_app_check_date, no_app_check_result


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


def long_dataframe(wide_df):
    """
    Make a long dataframe
    :param wide_df: <pandas.dataframe> The pandas dataframe
    """

    wide_df['location'] = wide_df.index
    long_df = pd.melt(wide_df, id_vars="location")
    long_df.columns = ["location", "appt_date", "count"]

    timestamp = datetime.now()
    timestamp = timestamp.strftime("%d/%m/%Y")

    long_df["scrape_date"] = timestamp

    return long_df


def nice_dataframe(not_nice_df):
    """
    Makes a nice dataframe
    :param not_nice_df: <pandas.dataframe> The pandas dataframe
    :return df: <pandas.dataframe> The pandas dataframe
    """

    base = datetime.today()
    date_list = [(base + timedelta(days=x)).strftime("%A %-d %B") for x in range(28)]
    better_date_list = [(base + timedelta(days=x)).strftime("%a %-d %b") for x in range(28)]

    nice_df = pd.DataFrame(columns=date_list,
                           index=["London", "Peterborough", "Newport", "Liverpool", "Durham", "Glasgow", "Belfast",
                                  "Birmingham"])

    not_nice_df.columns = not_nice_df.columns.str.replace("  ", " ")

    not_nice_df = not_nice_df.reset_index()
    for col in list(not_nice_df.columns):
        for idx in not_nice_df.index:
            location = not_nice_df.iloc[idx]["index"]

            number_of_appts = not_nice_df.iloc[idx][col]
            nice_df.at[location, col] = number_of_appts

    nice_df = nice_df.drop(columns=['index'])
    nice_df.columns = better_date_list

    nice_df = nice_df.fillna(0)
    nice_df = nice_df.astype(float)
    return nice_df


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


def make_figure(the_df):
    """
    Makes a seaborn heatmap figure from appointments dataframe
    :param the_df: <pandas.dataframe> The pandas dataframe
    """

    days_list = list(range(0, 10))
    days_list2 = list(range(10, 28))
    the_df[the_df.eq(0)] = np.nan
    appts = sns.heatmap(the_df, annot=True,
                        cbar=False, cmap="Blues", linewidths=1, linecolor="white",
                        vmin=0, vmax=30, annot_kws={"fontsize": 8})

    appts.set_title("Premium availability per location and date (1 = Available)\n\n")
    for i in range(len(days_list)):
        appts.text(i + 0.3, -0.1, str(days_list[i]), fontsize=8)
    for i in range(len(days_list2)):
        appts.text(i + 10.1, -0.1, str(days_list2[i]), fontsize=8)

    appts.figure.tight_layout()
    appts.text(10, -0.5, "(Days from Today)", fontsize=10)
    fig = appts.get_figure()
    fig.savefig("out.png")


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


def pipeline(first=True):
    """
    The main function to get the appointment data from the table at the end of the process
    :input first: <Boolean> The first run after the service has gone online?
    """

    print(f"Is first time running since going online: {first}")

    nice_appointments_df = get_appointment_data(MAIN_URL)  ## USMANS CODE TO REPLACE THIS FUNCTION

    if nice_appointments_df is None:
        print("Error. Will try again.")
        time.sleep(4 * 60)  # wait 4 mins before calling again
        run_github_action("32513748") if IS_GITHUB_ACTION else None
        return None

    print(nice_appointments_df)

    appointments_per_location = nice_appointments_df.sum(axis=1).to_frame().reset_index()
    appointments_per_location.columns = ['location', 'count']

    update_csv(appointments_per_location, IS_GITHUB_ACTION,
               "data/premium_appointments_locations.csv",
               "updating premium appointment location data", replace=True)

    if first is False:
        locs_added_checked = check_diff_in_loc_counts(appointments_per_location)
        if len(locs_added_checked) == 0:
            # time.sleep(5 * 60)  # wait 5 mins before calling again
            print("No new bulk Premium appointments have been added, will check again in 5 mins")
            time.sleep(4 * 60)  # wait 4 mins before calling again
            run_github_action("32513748") if IS_GITHUB_ACTION else None
            return None
    else:
        locs_added_checked = []

    make_figure(nice_appointments_df)
    if IS_TWITTER and first:
        post_media(IS_PROXY, IS_GITHUB_ACTION, SERVICE)
        update_no_app(IS_GITHUB_ACTION, TODAYS_DATE_IS, "False", SERVICE)

    # Posts a graph if new appointments have been added
    if IS_TWITTER and len(locs_added_checked) > 0:
        post_media_update(IS_PROXY, IS_GITHUB_ACTION, locs_added_checked, SERVICE)
        update_no_app(IS_GITHUB_ACTION, TODAYS_DATE_IS, "False", SERVICE)

    long_appointments_df = long_dataframe(nice_appointments_df)
    update_csv(long_appointments_df, IS_GITHUB_ACTION,
               "data/premium_appointments.csv",
               "updating premium appointment data", replace=False)
    time.sleep(4 * 60)  # wait 4 mins before calling again
    run_github_action("32513748") if IS_GITHUB_ACTION else None


if __name__ == "__main__":
    if sys.argv[1:][0] == 'True':
        is_first = True
    else:
        is_first = False

    pipeline(first=is_first)

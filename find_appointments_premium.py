import chromedriver_autoinstaller
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import seaborn as sns
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time

from scripts.utils.twitter import post_media
from scripts.utils.dataframes import update_csv
from scripts.utils.webpage import get_body, click_page_element, enter_page_element

chromedriver_autoinstaller.install()

is_proxy = False
is_github_action = True
is_twitter = True


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


def nice_dataframe(not_nice_df, numdays):
    """
    Makes a nice dataframe
    :param not_nice_df: <pandas.dataframe> The pandas dataframe
    :param numdays: <int> The number of days forward from today
    :return df: <pandas.dataframe> The pandas dataframe
    """

    base = datetime.today()
    date_list = [(base + timedelta(days=x)).strftime("%A %-d %B") for x in range(numdays)]
    better_date_list = [(base + timedelta(days=x)).strftime("%a %-d %b") for x in range(numdays)]


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
            if the_driver.find_element(by=By.XPATH, value='//*[@id="main-content"]/form/div/div[2]/a').size.get("height") != 0:
                the_driver.find_element(by=By.XPATH, value='//*[@id="main-content"]/form/div/div[2]/a')
                click_page_element(the_driver, '//*[@id="main-content"]/form/div/div[2]/a', 2)
            else:
                df_col_order = list(dict.fromkeys(df_col_order))
                df = df.reindex(df_col_order, axis=1)
                return df


def make_figure(the_df, numdays):
    """
    Makes a seaborn heatmap figure from appointments dataframe
    :param the_df: <pandas.dataframe> The pandas dataframe
    """
    days_list = list(range(0, 10))
    days_list2 = list(range(10, numdays))
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


if __name__ == "__main__":
    url = "https://www.passport.service.gov.uk/urgent/"
    driver = get_page(url, 1, 1)
    if driver is not None:
        driver_info = input_information(driver)
        appointments_df = get_appointments(driver_info)
        number_of_days_forward = 28
        nice_appointments_df = nice_dataframe(appointments_df, number_of_days_forward)
        print(appointments_df)
        make_figure(nice_appointments_df, number_of_days_forward)
        if is_twitter:
            post_media(is_proxy, is_github_action, "premium")
        long_appointments_df = long_dataframe(appointments_df)
        update_csv(long_appointments_df, is_github_action, "data/premium_appointments.csv",
                   "updating premium appointment data")

import chromedriver_autoinstaller
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import sys
import time

from scripts.utils.twitter import post_media, post_media_update, post_status_update
from scripts.utils.dataframes import update_csv, get_csv
from scripts.utils.webpage import get_body, click_page_element, enter_page_element
from scripts.utils.github import update_no_app

def get_appointments(the_driver):
    """
    Get appointments
    :param the_driver: <Selenium.webdriver> The selenium webdriver
    :return df: <pandas.dataframe> The pandas dataframe
    """

    for i in range(0, 6):
        time.sleep(2)
        html = the_driver.page_source
        if "There are no appointments available" in html:
            return None
        else:
            table = pd.read_html(html)
            df_tmp = table[0]
            df_tmp = clean_dataframe(df_tmp)
            print(df_tmp)

            if i != 0:
                cols_to_use = df_tmp.columns.difference(df.columns)
                df = pd.merge(df, df_tmp[cols_to_use], left_index=True, right_index=True, how='outer')
                df_col_order += list(df_tmp.columns)
            else:
                df = df_tmp
                df_col_order = list(df_tmp.columns)
            time.sleep(1)

            try:
                # the_driver.find_element(by=By.CLASS_NAME, value='datetablenext')
                the_driver.find_element(by=By.XPATH, value='//*[@id="Date_Table_Next_6__link"]')
                # click_page_element(the_driver, 'datetablenext', 4, by_what="class")
                click_page_element(the_driver, '//*[@id="Date_Table_Next_6__link"]', 1, by_what="xpath")
            except NoSuchElementException:
                df_col_order = list(dict.fromkeys(df_col_order))
                df = df.reindex(df_col_order, axis=1)
                return df

def get_page(the_url, wait_time=1):
    """
    Get page
    :param the_url: <string> The url string
    :param wait_time: <int> Time to wait before checking page
    :return: driver: <Selenium.webdriver> The selenium webdriver
    """

    keep_trying = True

    while keep_trying:
        options = Options()
        if IS_GITHUB_ACTION:
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        this_driver = webdriver.Chrome(options=options)

        this_driver.get(the_url)
        body = get_body(this_driver)
        time.sleep(wait_time)
        if "System busy" in body.text:
            print(f"System Busy, will try again in {wait_time} seconds")
            time.sleep(wait_time)
        elif "Error" in body.text:
            print(f"System Busy, will try again in {wait_time} seconds")
            time.sleep(wait_time)
        elif "no available appointments" in body.text:
            print("Service is offline. Please try again when it's online.")
            return None
        else:
            print("Success")
            return this_driver


def input_information(the_driver):
    """
    Input information to the page
    :param the_driver: <Selenium.webdriver> The selenium webdriver
    :return driver: <Selenium.webdriver> The selenium webdriver
    """

    # Get started page
    click_page_element(the_driver, '//*[@id="F_Passport_count-row"]/div[4]/div/fieldset/label[1]', 1)

    # Applicant details page
    enter_page_element(the_driver, '//*[@id="F_Applicant1_firstname"]', 'M', 1)
    enter_page_element(the_driver, '//*[@id="F_Applicant1_lastname"]', 'M', 1)
    enter_page_element(the_driver, '//*[@id="FD_Applicant1_dob"]', '01', 1)
    enter_page_element(the_driver, '//*[@id="FM_Applicant1_dob"]', '01', 1)
    enter_page_element(the_driver, '//*[@id="FY_Applicant1_dob"]', '1990', 1)
    click_page_element(the_driver, '//*[@id="BTB_BB_Next"]', 2)

    # Passport before page
    click_page_element(the_driver, '//*[@id="FLR_1_Applicant1_apptype_rb"]', 2)
    click_page_element(the_driver, '//*[@id="BTB_BA_Bnconfirmapptypes__pca"]', 1)

    # Go to appointments page
    click_page_element(the_driver, '//*[@id="BTB_BA_Bn_select_service__pca"]', 3)

    try:
        # Go to appointments page
        click_page_element(the_driver, '//*[@id="BTB_BA_Bn_select_service__pca"]', 3)
        return the_driver
    except NoSuchElementException:
        return the_driver


def clean_dataframe(unclean_df):
    """
    Clean the dataframe
    :param unclean_df: <pandas.dataframe> The pandas dataframe
    """

    clean_col_names = []

    for cols in unclean_df.columns:
        if sum(c.isdigit() for c in cols) == 2:
            clean_col_names.append(cols[-9:])
        else:
            clean_col_names.append(cols[-10:])

    unclean_df.columns = clean_col_names
    unclean_df = unclean_df.rename(columns=lambda x: x.replace("y", ""))
    unclean_df = unclean_df.replace({"appointments": ""}, regex=True)
    unclean_df = unclean_df.replace({"appointment": ""}, regex=True)
    unclean_df = unclean_df.replace(r"(\d+)", r" \1", regex=True)
    return unclean_df


def nice_dataframe(not_nice_df):
    """
    Makes a nice dataframe
    :param not_nice_df: <pandas.dataframe> The pandas dataframe
    :return df: <pandas.dataframe> The pandas dataframe
    """

    base = datetime.today()
    date_list = [(base + timedelta(days=x)).strftime("%a %-d %b") for x in range(28)]

    nice_df = pd.DataFrame(columns=date_list,
                           index=["London", "Peterborough", "Newport", "Liverpool", "Durham", "Glasgow", "Belfast",
                                  "Birmingham"])

    for col in not_nice_df.columns:
        for idx in not_nice_df.index:
            if type(not_nice_df.iloc[idx][col]) == str:
                location = not_nice_df.iloc[idx][col].split(" ")[0]
                number_of_appts = not_nice_df.iloc[idx][col].split(" ")[1]
                nice_df.at[location, col] = number_of_appts

    nice_df = nice_df.fillna(0)
    try:
        nice_df = nice_df.astype(float)
        return nice_df
    except ValueError:
        return None


def get_appointment_data(the_url):
    """
    The main function to get the appointment data from the table at the end of the process
    :input the_url: <string> The url to parse
    :return nice_appointments_df: <pandas.DataFrame> A pandas DataFrame of appointments, or None
    """

    driver = get_page(the_url, 1)
    if driver is not None:
        try:
            driver_info = input_information(driver)
        except NoSuchElementException:
            run_github_action("29224896") if IS_GITHUB_ACTION else None
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
            run_github_action("29224896") if IS_GITHUB_ACTION else None
            return None

        else:
            nice_appointments_df = nice_dataframe(appointments_df)
            return nice_appointments_df

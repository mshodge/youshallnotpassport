from datetime import datetime, date
import numpy as np
import os
import pandas as pd
import requests
import seaborn as sns
import sys
import time

from scripts.utils.twitter import post_media, post_media_update, post_quick_check
from scripts.utils.dataframes import update_csv, get_csv
from scripts.utils.github import update_no_app
from scripts.utils.sms import call_sms
from scripts.appointments_ft import get_appointment_data

today = date.today()
TODAYS_DATE_IS = today.strftime("%d/%m/%Y")
MAIN_URL = 'https://www.passportappointment.service.gov.uk/outreach/PublicBooking.ofml'
SERVICE = "fast track"
IS_PROXY = False
IS_GITHUB_ACTION = True
IS_TWITTER = True
wait_mins = 10
number_of_appointments_classed_as_bulk = 10

session = requests.Session()
session.headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
}


def run_github_action(id):
    """
    Runs the GitHub Action
    :param id: <string>

    Args:
        id: str
            The workflow id for GitHub actions

        default:
            The default datetime

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

    Returns:
        no_app_check_date: str
            The date checked last
        no_appointment_check_result: str
            The result checked last
    """

    no_appointment_check = requests.get(
        "https://raw.githubusercontent.com/mshodge/youshallnotpassport/main/data/no_apps.md").text \
        .replace("\n", "").split(" ")
    no_appointment_check_date = no_appointment_check[0]
    no_appointment_check_result = no_appointment_check[1]
    return no_appointment_check_date, no_appointment_check_result


def long_dataframe(wide_df):
    """
    Make a long dataframe

    Args:
        wide_df: pd.dataframe
            The pandas dataframe in wide format

    Returns:
        long_df: pd.dataframe
            The pandas dataframe in long format
    """

    wide_df["location"] = wide_df.index
    long_df = pd.melt(wide_df, id_vars="location")
    long_df.columns = ["location", "appt_date", "count"]

    timestamp = datetime.now()
    timestamp = timestamp.strftime("%d/%m/%Y %H:%M")

    long_df["scrape_date"] = timestamp

    return long_df


def make_figure(the_df):
    """
    Makes a seaborn heatmap figure from appointments dataframe

    Args:
        the_df: pd.dataframe
            The pandas dataframe
    """

    days_list = list(range(0, 10))
    days_list2 = list(range(10, 28))

    the_df[the_df.eq(0)] = np.nan
    appointments = sns.heatmap(the_df, annot=True,
                               cbar=False, cmap="Blues", linewidths=1, linecolor="white",
                               vmin=0, vmax=30, annot_kws={"fontsize": 8})
    appointments.set_title("The number of Fast Track appointments \n\n")

    for i in range(len(days_list)):
        appointments.text(i + 0.3, -0.1, str(days_list[i]), fontsize=8)

    for i in range(len(days_list2)):
        appointments.text(i + 10.1, -0.1, str(days_list2[i]), fontsize=8)

    appointments.text(10, -0.5, "(Days from Today)", fontsize=10)
    appointments.figure.tight_layout()
    fig = appointments.get_figure()
    fig.savefig("out.png")


def check_diff_in_loc_counts(df):
    """
    Checks the difference in the counts of appointments at each office, if an office has 10 or more new appointments
    then the bot will flag this to be posted to Twitter

    Args:
        df: pd.DataFrame>
            The pandas dataframe of the latest results

    Returns:
        locations_added: list
            List of offices with new appointments added, is blank if None
    """

    df_old = get_csv("data/fast_track_appointments_locations.csv")
    df_diff = df_old.copy()
    df_diff['count'] = df['count'] - df_old['count']
    locations_added = []
    for index, row in df_diff.iterrows():
        if row['count'] > number_of_appointments_classed_as_bulk:
            locations_added.append(row['location'])

    return locations_added


def pipeline(first):
    """
    The main function to get the appointment data from the table at the end of the process

    Args:
        first: Bool
            The first run after the service has gone online?
    """

    print(f"Is first time running since going online: {first}")

    if "check again later" in requests.get(MAIN_URL).text:
        raise Exception(f"It's offline!")

    try:
        nice_appointments_df = get_appointment_data(IS_GITHUB_ACTION, MAIN_URL)
    except ValueError:
        if first:
            run_github_action("28775018") if IS_GITHUB_ACTION else None
        else:
            run_github_action("29224896") if IS_GITHUB_ACTION else None
        raise Exception('Error. Failed to get the appointments table.')

    if nice_appointments_df is None:
        time.sleep(60)  # wait a minute before calling again
        run_github_action("29224896") if IS_GITHUB_ACTION else None
        raise Exception(f"Error. Appointments table returned was none. Will try again in one minute.")
    elif nice_appointments_df is False:
        time.sleep(60)  # wait a minute before calling again
        run_github_action("29224896") if IS_GITHUB_ACTION else None
        print(f"No Appointments were available. Will try again in one minute.")
        return None
    # elif nice_appointments_df == 'Block':
    #     print(f"Softblocked. Will try again in one minute.")
    #     time.sleep(10)  # wait a minute before calling again
    #     run_github_action("29224896") if IS_GITHUB_ACTION else None
    #     raise Exception(f"Error. Softblocked. Will try again in 10 seconds.")

    print(nice_appointments_df)

    appointments_per_location = nice_appointments_df.sum(axis=1).to_frame().reset_index()
    appointments_per_location.columns = ['location', 'count']

    failed = update_csv(appointments_per_location, IS_GITHUB_ACTION,
                        "data/fast_track_appointments_locations.csv",
                        "updating fast track appointment location data", replace=True)
    if failed:
        run_github_action("29224896")
        raise Exception(f"Error. Failed to return the GitHub file. Will try again.")

    if first is False:
        locations_added_checked = check_diff_in_loc_counts(appointments_per_location)
        if len(locations_added_checked) == 0:
            print(f"No new bulk appointments added. Will check again in {wait_mins} minutes.")
            time.sleep(wait_mins * 60)  # wait 3 mins before calling again
            run_github_action("29224896") if IS_GITHUB_ACTION else None
            return None
    else:
        locations_added_checked = []

    make_figure(nice_appointments_df)

    # Posts a first graph
    if IS_TWITTER and first:
        post_media(IS_PROXY, IS_GITHUB_ACTION, SERVICE)
        failed = update_no_app(IS_GITHUB_ACTION, TODAYS_DATE_IS, SERVICE, "False")
        if failed:
            run_github_action("29224896")
            raise Exception(f"Error. Failed to post to Twitter. Will try again.")

    # Posts a graph if new appointments have been added
    if IS_TWITTER and len(locations_added_checked) > 0:
        message = post_media_update(IS_PROXY, IS_GITHUB_ACTION, locations_added_checked, SERVICE)
        call_sms(SERVICE.title(), type="app", response=message)
        failed = update_no_app(IS_GITHUB_ACTION, TODAYS_DATE_IS, SERVICE, "False")
        if failed:
            run_github_action("29224896")
            raise Exception(f"Error. Failed to post the SMS. Will try again.")

    long_appointments_df = long_dataframe(nice_appointments_df)
    failed = update_csv(long_appointments_df, IS_GITHUB_ACTION,
                        "data/fast_track_appointments.csv",
                        "updating fast track appointment data", replace=False)

    time.sleep(wait_mins * 60)  # wait 3 mins before calling again
    print(f"Successfully found new appointments, will check again in {wait_mins} minutes")
    run_github_action("29224896") if IS_GITHUB_ACTION else None


if __name__ == "__main__":
    if sys.argv[1:][0] == 'True':
        is_first = True
    else:
        is_first = False

    pipeline(first=is_first)

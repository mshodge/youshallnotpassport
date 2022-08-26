"""
Module to obtain free slots for fast track passport appointments.

Inspired by https://github.com/mshodge/youshallnotpassport (@mshodge)

This script uses the requests library directly to make JS AJAX requests to the
server, without using a selenium webdriver.

Provides the functions:

*func*: `get_appointment_data` (main entry point)
*func*: `get_insthash`
*func*: `get_ajax`
*func*: `clean_df`
"""
import requests, re
from typing import Dict, Union
import dateutil.parser as dparser
from datetime import date as dt
from datetime import datetime, timedelta
import time

from bs4 import BeautifulSoup
import pandas as pd

__author__ = ['Dr. Usman Kayani']

MAIN_URL = 'https://www.passportappointment.service.gov.uk/outreach/PublicBooking.ofml'
MAIN_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
}

session = requests.Session()

def get_insthash() -> str:
    """
    Get the insthash.

    Returns:
        str
            Instance hash.
    """
    data = session.get(MAIN_URL)
    soup = BeautifulSoup(data.text, 'html.parser')
    insthash_data = soup.find('input', {'name': 'I_INSTHASH'})
    if insthash_data is None:
        return None
    return insthash_data['value']

def get_ajax(
    insthash: str,
    params: Dict = None,
    init: bool = False,
) -> str:
    """
    Get the ajax text to process JS request.

    Params:
        insthash: str
            Instance hash.
        params: Dict
            Parameters to pass to the request.
        init: bool
            Whether to get the initial data or not.

    Returns:
        str
            The ajax text for the post request.
    """
    open_tag = f"<ajaxrequest><insthash>{insthash}</insthash><post url='{MAIN_URL}'>"
    if init:
        return open_tag + "</post><saving>TRUE</saving></ajaxrequest>"

    params_list = [f'{key}={value}' for key, value in params.items()]
    return open_tag + '&amp;'.join(params_list) + '</post></ajaxrequest>'


def get_appointment_data() -> Union[str, pd.DataFrame]:
    """
    Get the appointment data.

    Returns:
        None
    """
    session.headers = MAIN_HEADERS

    r = session.get(MAIN_URL)
    no_appt_text = 'Sorry, there are no available appointments'
    if no_appt_text in r.text:
        return no_appt_text

    keep_trying = True
    while keep_trying:
        if "System busy" in r.text:
            print(f"System Busy, will try again in 1 second")
            time.sleep(1)
        elif "Error " in r.text:
            print(f"System Busy, will try again in 1 second")
            time.sleep(1)
        else:

            keep_trying = False
            insthash = get_insthash()
            section_hash = insthash.split('-')[-1]

            applicant_details = {
                'I_SUBMITCOUNT': '1',
                'I_INSTHASH': insthash,
                'I_PAGENUM': '1',
                'I_JAVASCRIPTON': '1',
                'I_UTFENCODED': 'TRUE',
                'I_ACCESS': '',
                'I_TABLELINK': '',
                'I_AJAXMODE': '',
                'I_SMALLSCREEN': '',
                'I_SECTIONHASH': f'{section_hash}_Section_start',
                'FHC_Passport_count': '',
                'F_Passport_count': '1',
                'F_Applicant1_firstname': 'm',
                'F_Applicant1_lastname': 'm',
                'FD_Applicant1_dob': '01',
                'FM_Applicant1_dob': '01',
                'FY_Applicant1_dob': '1990',
                'F_Applicant2_firstname': '',
                'F_Applicant2_lastname': '',
                'FD_Applicant2_dob': '',
                'FM_Applicant2_dob': '',
                'FY_Applicant2_dob': '',
                'F_Applicant3_firstname': '',
                'F_Applicant3_lastname': '',
                'FD_Applicant3_dob': '',
                'FM_Applicant3_dob': '',
                'FY_Applicant3_dob': '',
                'F_Applicant4_firstname': '',
                'F_Applicant4_lastname': '',
                'FD_Applicant4_dob': '',
                'FM_Applicant4_dob': '',
                'FY_Applicant4_dob': '',
                'F_Applicant5_firstname': '',
                'F_Applicant5_lastname': '',
                'FD_Applicant5_dob': '',
                'FM_Applicant5_dob': '',
                'FY_Applicant5_dob': '',
                'BB_Next': ''
            }

            application_type = {
                'I_SUBMITCOUNT': '1',
                'I_INSTHASH': insthash,
                'I_PAGENUM': '2',
                'I_JAVASCRIPTON': '1',
                'I_UTFENCODED': 'TRUE',
                'I_ACCESS': '',
                'I_TABLELINK': '',
                'I_AJAXMODE': '',
                'I_SMALLSCREEN': '',
                'I_SECTIONHASH': f'{section_hash}_Section_current_passports',
                'FHC_Applicant1_isadult': '',
                'F_Applicant1_isadult': 'on',
                'FHC_Applicant1_apptype_rb': '',
                'F_Applicant1_apptype_rb': 'REPLACE',
                'FHC_Applicant2_isadult': '',
                'FHC_Applicant2_apptype_rb': '',
                'FHC_Applicant3_isadult': '',
                'FHC_Applicant3_apptype_rb': '',
                'FHC_Applicant4_isadult': '',
                'FHC_Applicant4_apptype_rb': '',
                'FHC_Applicant5_isadult': '',
                'FHC_Applicant5_apptype_rb': '',
                'D_DEFBTN': 'BB_Reload'
            }

            service_type = {
                'I_SUBMITCOUNT': '1',
                'I_INSTHASH': insthash,
                'I_PAGENUM': '3',
                'I_JAVASCRIPTON': '1',
                'I_UTFENCODED': 'TRUE',
                'I_ACCESS': '',
                'I_TABLELINK': '',
                'I_AJAXMODE': '',
                'I_SMALLSCREEN': '',
                'I_SECTIONHASH': f'{section_hash}_Section_current_passports',
                'FHC_Applicant1_isadult': '',
                'F_Applicant1_isadult': 'on',
                'FHC_Applicant1_apptype_rb': '',
                'F_Applicant1_apptype_rb': 'REPLACE',
                'FHC_Applicant2_isadult': '',
                'FHC_Applicant2_apptype_rb': '',
                'FHC_Applicant3_isadult': '',
                'FHC_Applicant3_apptype_rb': '',
                'FHC_Applicant4_isadult': '',
                'FHC_Applicant4_apptype_rb': '',
                'FHC_Applicant5_isadult': '',
                'FHC_Applicant5_apptype_rb': '',
                'D_DEFBTN': 'BB_Reload',
                'BA_Bnconfirmapptypes__pca': ''
            }

            appointments1 = {
                'I_SUBMITCOUNT': '1',
                'I_INSTHASH': insthash,
                'I_PAGENUM': '4',
                'I_JAVASCRIPTON': '1',
                'I_UTFENCODED': 'TRUE',
                'I_ACCESS': '',
                'I_TABLELINK': '',
                'I_AJAXMODE': '',
                'I_SMALLSCREEN': '',
                'I_SECTIONHASH': f'{section_hash}_Section_selectservicetype',
                'FHC_Has_selected_servicetype__nosumm': '',
                'F_Selectedbuttonname_servicetype': '2',
                'BA_Bn_select_service__pca': ''
            }

            appointments2 = {
                'I_SUBMITCOUNT': '1',
                'I_INSTHASH': insthash,
                'I_PAGENUM': '5',
                'I_JAVASCRIPTON': '1',
                'I_UTFENCODED': 'TRUE',
                'I_ACCESS': '',
                'I_TABLELINK': '',
                'I_AJAXMODE': '',
                'I_SMALLSCREEN': '',
                'I_SECTIONHASH': f'{section_hash}_Section_availabledates',
                'FHC_Has_selected_date__nosumm': '',
                'FHC_Has_javascript_enabled__nosumm': '',
                'F_Has_javascript_enabled__nosumm': 'on',
                'F_Selectedbuttonname_date__nosumm': '',
                'F_Postcode__nosumm__sm': '',
                'Date_Table_Next_6': ''
            }

            # Ajax requests need to be in sequence for the data to be available.
            for stage in [applicant_details, application_type, service_type, appointments1]:
                r = session.post(
                    MAIN_URL,
                    headers={'Content-Type' : 'text/xml'},
                    data=get_ajax(insthash, stage)
                )

            no_appt_text = 'no available appointments'
            if no_appt_text in r.text:
                return None

            else:
                appt_page = 1
                data_list = []
                data_first = pd.read_html(r.text.replace('&lt;', '<').replace('&gt;', '>'))
                data_list.append(data_first[0])

                get_another_page = True

                while get_another_page:
                    if appt_page == 1:
                        data_previous = data_first
                    else:
                        data_previous = data_next

                    r = session.post(
                        MAIN_URL,
                        headers={'Content-Type': 'text/xml'},
                        data=get_ajax(insthash, appointments2),
                    )

                    data_next = pd.read_html(r.text.replace('&lt;', '<').replace('&gt;', '>'))

                    if data_next[0].equals(data_previous[0]) == True:
                        get_another_page = False
                        return clean_df(pd.concat(data_list, axis=1))
                    else:
                        data_list.append(data_next[0])
                        appt_page += 1

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataframe for the final output.

    Remove duplicates, redundant columns and reformatted data for each location.

    Params:
        df: pd.DataFrame
            The dataframe to clean.

    Returns:
        pd.DataFrame
            The cleaned dataframe
    """
    df = (
        df
        .loc[:, ~df.columns.duplicated()]
        .copy()
        .replace(' appointments', '', regex=True)
        .replace(' appointment', '', regex=True)
    )

    current_year = dt.today().year
    df.columns = [
        dparser
        .parse(date, fuzzy=True)
        .replace(year=current_year)
        for date in df.columns
    ]

    locations = [
        "London",
        "Peterborough",
        "Newport",
        "Liverpool",
        "Durham",
        "Glasgow",
        "Belfast",
        "Birmingham",
    ]

    dates = [(datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
              + timedelta(days=x)) for x in range(28)]

    ## MH EDIT ABOVE: datetime was bringing in current time too as replaced to 00:00:00 00:00

    df_clean = pd.DataFrame(columns=dates, index=locations)

    map = {}
    for date in df.columns:
        for val in df[date].dropna().to_list():
            location = re.search(r'([a-zA-Z ]*)', val).group()
            number = float(re.search(r'-?\d+\.?\d*', val).group())
            df_clean.loc[location, date] = number

    df_clean.columns = [x.strftime('%a %d %b') for x in df_clean.columns]
    return df_clean.fillna(0.0)


if __name__ == '__main__':
    data = get_appointment_data()
    if isinstance(data, pd.DataFrame):
        display(tabulate(data, headers='keys', tablefmt='psql'))
    else:
        print(data)

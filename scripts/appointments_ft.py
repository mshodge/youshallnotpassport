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
from dateutil import parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import time
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup
import pandas as pd

from scripts.utils.softblock import setup_selenium, wait_in_queue, get_recapctha_image, detect_text_url


MAIN_URL = 'https://www.passportappointment.service.gov.uk/outreach/PublicBooking.ofml'
MAIN_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
}

session = requests.Session()

def get_insthash(response):
    """
    Get the insthash.

    """

    soup = BeautifulSoup(response.text, 'html.parser')
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

    Args:
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


def quick_check() -> bool:
    """
    Get the appointment data.

    Returns:
        None
    """

    session.headers = MAIN_HEADERS

    r = session.get(MAIN_URL)
    no_appt_text = 'There are no Fast Track  appointments available'
    if no_appt_text in r.text:
        return False
    else:
        return True


def get_appointment_data(is_github_action) -> Union[str, pd.DataFrame]:
    """
    Get the appointment data.

    Args:
        is_github_action: Bool
            TRUE if it's running as a GitHub Action...

    Returns:
        None
    """
    session.headers = MAIN_HEADERS

    r = session.get(MAIN_URL)
    no_appt_text = 'There are no Fast Track  appointments available'
    if no_appt_text in r.text:
        return False

    soft_block_text = 'data-pageid="softblock"'
    queue_text = "You’re in a queue"

    check_for_image = True
    print(r.text)
    if soft_block_text in r.text:
        this_driver = setup_selenium(MAIN_URL, is_github_action)
        while check_for_image:
            image_found = get_recapctha_image(this_driver)
            if image_found:
                ocr_response = detect_text_url(is_github_action)
                recaptcha_text = ocr_response.get('analyzeResult').get('readResults')[0].get('lines')[0].get('text')
                element = this_driver.find_element(by=By.XPATH,
                                                   value='/html/body/div[2]/div[3]/div[3]/div[1]/div[2]/div/div/div/div[1]/div/fieldset/div[2]/div[2]/input')
                element.send_keys(recaptcha_text)
                time.sleep(2)
                element = this_driver.find_element(by=By.XPATH,
                                                   value='/html/body/div[2]/div[3]/div[3]/div[1]/div[2]/div/div/div/div[1]/button')
                element.click()
                time.sleep(2)
            else:
                check_for_image = False

    r = session.get(MAIN_URL)
    print(r)

    if queue_text in r.text:
        this_driver = wait_in_queue(this_driver)

        s = requests.Session()

        # Set correct user agent
        selenium_user_agent = this_driver.execute_script("return navigator.userAgent;")
        s.headers.update({"user-agent": selenium_user_agent})

        for cookie in this_driver.get_cookies():
            s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

        r = s.get(MAIN_URL)

    insthash = get_insthash(r)
    print(insthash)

    if insthash is None:
        return None

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
        r = s.post(
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
            try:
                data_next = pd.read_html(r.text.replace('&lt;', '<').replace('&gt;', '>'))
            except ValueError:
                return clean_df(pd.concat(data_list, axis=1))

            if data_next[0].equals(data_previous[0]) == True:
                get_another_page = False
                return clean_df(pd.concat(data_list, axis=1))
            else:
                data_list.append(data_next[0])
                appt_page += 1


def parse_future(timestr: str, default: datetime, **parse_kwargs):
    """
    Same as dateutil.parser.parse() but only returns future dates. So if you enter a new year it will recognise this

    Args:
        timestr: str
            The string of the time you want to parse

        default:
            The default datetime

    Returns:
        dt
            datetime
    """
    get_clean_string = ' '.join(re.sub( r"([A-Z])", r" \1", timestr).split()[-3:])

    now = default
    for _ in range(401):  # assume gregorian calendar repeats every 400 year
        try:
            dt = parser.parse(get_clean_string, default=default, **parse_kwargs)
        except ValueError:
            pass
        else:
            if dt > now: # found future date
                break
        default += relativedelta(years=+1)
    else: # future date not found
        raise ValueError('failed to find future date for %r' % (timestr,))
    return dt


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataframe for the final output.

    Remove duplicates, redundant columns and reformatted data for each location.

    Args:
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

    new_dates = []

    for date in df.columns:
        new_dates.append(parse_future(date, default=datetime(2022, 12, 1)))

    df.columns = new_dates

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

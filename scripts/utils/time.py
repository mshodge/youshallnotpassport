from datetime import datetime, timedelta


def get_timestamp(github_action, timestamp_string_format='%H:%M'):
    """
    Gets timestamp
    :param github_action: <Boolean> Whether a GitHub action or not, for auth
    :param timestamp_string_format: <string> The datetime format to return
    :return: timestamp <string> The formatted datetime
    """
    if github_action:
        timestamp = datetime.now() + timedelta(hours=1)
        timestamp = timestamp.strftime(timestamp_string_format)
    else:
        timestamp = datetime.now().strftime(timestamp_string_format)
    return timestamp


def check_if_half_hour_or_hour():
    """
    Checks if the time is 30 past or 0 past and returns a variable based on that
    :return: to_save_csv <boolean> Returns True if 30 or 0
    """
    # Get date time and convert to a string
    time_now = datetime.now().strftime("%M")
    mins = int(time_now)
    if mins in [29,30,31,59,0,1]:
        print("It's half past or at the hour, so I am saving data\n")
        to_save_csv = True
    else:
        to_save_csv = False
        print("It's not half past or at the hour, so I am not saving data\n")
    return to_save_csv
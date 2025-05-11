import calendar
import time
from datetime import datetime, timedelta
import parsedatetime as pdt


def is_day_formatted_as_date(day) -> bool:
    try:
        datetime.strptime(day, '%Y-%m-%d')
        return True
    except (TypeError, ValueError):
        return False


def get_next_weekday_as_date(weekday_number) -> str:
    start = datetime.strptime(datetime.now().strftime("%Y-%m-%d"), '%Y-%m-%d')
    day = timedelta((7 + weekday_number - start.weekday()) % 7)
    return (start + day).strftime("%Y-%m-%d")


def parse_date_to_weekday(date) -> str:
    return calendar.day_name[datetime.strptime(date, "%Y-%m-%d").weekday()]


def get_day_number(weekday_name) -> int:
    weekday = weekday_name.lower().capitalize()
    try:
        operator = '%a' if len(weekday) == 3 else '%A'
        day_num = time.strptime(weekday, operator).tm_wday
        return day_num if 0 <= day_num < 5 else None
    except ValueError:
        return None


def get_date(date) -> str:
    natural_date = pdt.Calendar().parseDT(date)[0]
    if datetime.today() >= natural_date:
        return None
    return natural_date.strftime('%Y-%m-%d')
# coding=utf-8
import calendar
import time
from datetime import datetime, timedelta

from lib.api.google_places import GooglePlaces


def get_user_name(user):
    return "<@" + user['user_id'] + "|" + user['user_name'] + ">"


def get_user_name_from_event(user):
    return "<@" + user['id'] + "|" + user['name'] + ">"


def is_day_formatted_as_date(day):
    try:
        datetime.strptime(day, '%Y-%m-%d')
        return True
    except TypeError:
        return False
    except ValueError:
        return False


def get_next_weekday_as_date(weekday_number):
    start = datetime.strptime(datetime.now().strftime("%Y-%m-%d"), '%Y-%m-%d')
    day = timedelta((7 + weekday_number - start.weekday()) % 7)

    return (start + day).strftime("%Y-%m-%d")


def parse_date_to_weekday(date):
    return calendar.day_name[datetime.strptime(date, "%Y-%m-%d").weekday()]


def get_day_number(weekday_name):
    weekday = weekday_name.lower().capitalize()

    try:
        # User should be able to write tuesday or tue, both should work
        if len(weekday) is 3:
            operator = '%a'
        else:
            operator = '%A'

        day_num = time.strptime(weekday, operator).tm_wday

        if 0 <= day_num < 5:
            return day_num
    except ValueError:
        return None

    return None


def get_date(date):
    if is_day_formatted_as_date(date):
        # Make sure date is in the future
        if datetime.today() >= datetime.strptime(date, "%Y-%m-%d"):
            return None

        weekday_name = parse_date_to_weekday(date)
        day_number = get_day_number(weekday_name)
        if day_number is not None:
            return date
    else:
        day_number = get_day_number(date)
        if day_number is not None:
            return get_next_weekday_as_date(day_number)

    return None


def print_afterwork_list(results):
    places = GooglePlaces()
    events = "Upcoming after work: \n"
    for item in results['Items']:
        weekday = datetime.strptime(item['Date'], "%Y-%m-%d").weekday()

        events += "*" + calendar.day_name[weekday] + "*"

        if 'Time' in item:
            events += " at *" + item['Time'] + "*"

        if 'Location' in item and item['Location'] != 'GPlaces':
            events += " by *" + item['Location'] + "*"

        if 'PlaceId' in item:
            place = places.get_place_information(item['PlaceId'])
            events += " by *" + place.name() + "*"
            events += " by *" + place.address() + "*"

        events += " started by *" + item['Author'] + "*"

        if 'Participants' in item and len(item['Participants']) > 0:
            events += "\n *Participants:* \n"
            for participant in item['Participants']:
                events += participant + "\n"
        else:
            events += "\nNo one is participating in this after work, *yet...*"

        events += "\n To join type */afterwork join %s*" % calendar.day_name[weekday].lower()
        events += "\n"

    return events


def print_afterwork_today(results):
    if 'Participants' in results['Item'] and len(results['Item']['Participants']) > 0:
        event = "*Reminder * Today there's an after work planned! \n"

        event += "*" + parse_date_to_weekday(results['Item']['Date']) + "*"

        if 'Time' in results['Item']:
            event += " at *" + results['Item']['Time'] + "*"

        if 'Location' in results['Item']:
            event += " by *" + results['Item']['Location'] + "*"

        event += " started by *" + results['Item']['Author'] + "*"
        event += "\n *Participants:* \n"
        for participant in results['Item']['Participants']:
            event += participant + "\n"

        event += "\n *Don't be late!*"
    else:
        event = "Hey guys, there was an after work planned for today, but no one wants to go :("

    return event


def get_valid_commands():
    return ['list', 'create', 'join', 'leave', 'delete', 'suggest']


def print_possible_commands():
    return """Possible commands are:
                \nlist \ncreate <day> <time> <place>\njoin <day>\nleave <day>\ndelete <day>"""


def print_afterwork_created(author, date, place):
    return """Hi! {author} created an after work! \n 
    *{weekday} ({date})* at *{place}* \n 
    To join type */afterwork join {date}* or */afterwork join {weekday}* 
    if is within this or next week.""".format(
        author=author, weekday=parse_date_to_weekday(date), date=date, place=place,
    )
# coding=utf-8
import calendar
import time
from datetime import datetime, timedelta
import parsedatetime as pdt

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
    natural_date = pdt.Calendar().parseDT(date)[0]
    print(natural_date)
    if datetime.today() >= natural_date:
        print('is before, wont allow it')
        return None

    return natural_date.strftime('%Y-%m-%d')


def print_afterwork_list(results):
    places = GooglePlaces()
    events = {
        'text': 'Upcoming after work events',
        'attachments': []
    }

    for item in results['Items']:
        place = places.get_place_information(item['PlaceId'])
        weekday = datetime.strptime(item['Date'], "%Y-%m-%d").weekday()
        attachment = {
            'title': '{place} on {weekday} at {time}'.format(
                place=place.name(),
                weekday=calendar.day_name[weekday],
                time=item['Time']
            ),
            'callback_id': 'handle_afterwork',
            'fields': [
                {
                    'title': 'Rating',
                    'value': place.rating(),
                    'short': 1
                },
                {
                    'title': 'Address',
                    'value': place.address(),
                    'short': 1
                }
            ],
            'color': place.format_open()['color'],
            'author_name': 'Created by: ' + item['Author'],
            'text': '',
            'actions': [
                {
                    'name': 'afterwork',
                    'text': 'Join afterwork',
                    'type': 'button',
                    'style': 'primary',
                    'value': 'join_afterwork|' + item['Date']
                },
                {
                    'name': 'afterwork',
                    'text': 'Leave afterwork',
                    'type': 'button',
                    'style': 'danger',
                    'value': 'leave_afterwork|' + item['Date']
                }
            ]
        }

        if 'Participants' in item and len(item['Participants']) > 0:
            attachment['text'] += "\n *Participants:* \n"
            for participant in item['Participants']:
                attachment['text'] += participant + "\n"
        else:
            attachment['text'] += "\nNo one is participating in this after work, *yet...*"
        events['attachments'].append(attachment)
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


def build_create_dialog():
    dialog = {
        'title': 'Create an afterwork',
        'submit_label': 'Create',
        'callback_id': "create_afterwork_dialog|",
        'elements': [
            {
                'label': 'Where?',
                'type': 'select',
                'data_source': 'external',
                'min_query_length': 3,
                'name': 'afterwork_place',
                'placeholder': 'Select a location and we will try to map it'
            },
            {
                'label': 'Which day?',
                'type': 'text',
                'name': 'afterwork_day',
                'placeholder': 'Select a day, just like you would say it'
            },
            {
                'label': 'What time?',
                'type': 'text',
                'name': 'afterwork_time',
                'placeholder': 'Pick a time, any time!'
            }
        ]
    }

    return dialog

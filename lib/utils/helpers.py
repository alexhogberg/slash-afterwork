# coding=utf-8
import calendar
import time
import os
from datetime import datetime, timedelta
import parsedatetime as pdt

from lib.api.google_places import GooglePlaces
from lib.models.event_place import EventPlace


def validate_token(token):
    return token == os.environ['SLACK_AUTH_KEY']


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
        if len(weekday) == 3:
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
    if datetime.today() >= natural_date:
        return None

    return natural_date.strftime('%Y-%m-%d')


def print_event_list(results, user):
    events = {
        'text': 'Upcoming events',
        'blocks': []
    }

    for item in results:
        place = item['Location']
        aw_date = item['Date'].split('|')[1]
        event_id = str(item['_id'])
        weekday = datetime.strptime(aw_date, "%Y-%m-%d").weekday()

        # Header block for the event
        events['blocks'].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{place['name']}* on *{calendar.day_name[weekday]}* at *{item['Time']}*\nCreated by: *<@{item['Author']}>*"
            },
        })

        # Fields block for additional details
        events['blocks'].append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Rating:*\n{place['rating']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Address:*\n{place['address']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Directions:*\n<{place['google_maps_url']}|Google Maps>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Place types:*\n{', '.join(place['types'])}"
                },
            ]
        })

        # Participants block
        if 'Participants' in item and len(item['Participants']) > 0:
            participants_text = "\n".join(
                [f"<@{participant}>" for participant in item['Participants']])
            events['blocks'].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Participants:*\n{participants_text}"
                }
            })
        else:
            events['blocks'].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "No one is participating in this event, *yet...*"
                }
            })

        # Actions block for buttons
        actions = []
        if 'Participants' in item and user not in item['Participants']:
            actions.append({
                "type": "button",
                "action_id": "join_event",
                "text": {
                    "type": "plain_text",
                    "text": "Join event",
                    "emoji": True
                },
                "style": "primary",
                "value": event_id
            })

        if 'Participants' in item and user in item['Participants']:
            actions.append({
                "type": "button",
                "action_id": "leave_event",
                "text": {
                    "type": "plain_text",
                    "text": "Leave event",
                    "emoji": True
                },
                "value": event_id
            })

        if user == item['Author']:
            actions.append({
                "type": "button",
                "action_id": "delete_event",
                "text": {
                    "type": "plain_text",
                    "text": "Delete event",
                    "emoji": True
                },
                "style": "danger",
                "value": event_id
            })

        events['blocks'].append({
            "type": "actions",
            "elements": actions
        })

        # Divider block between events
        events['blocks'].append({
            "type": "divider"
        })

    return events


def print_event_create():
    return {
        'text': 'There is no upcoming event planned',
        'blocks': [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "There is no upcoming event planned. Would you like to create one?"
                }
            },
            {
                "type": "actions",
                "block_id": "create_event_block",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Create event",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": "create_event|",
                        "action_id": "create_event_action"
                    }
                ]
            }
        ]
    }


def print_event_today(results):
    if 'Participants' in results['Item'] and len(results['Item']['Participants']) > 0:
        event = "*Reminder * Today there's an event planned! \n"

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
        event = "Hey guys, there was an event planned for today, but no one wants to go :("

    return event


def get_valid_commands():
    return ['list', 'create', 'join', 'leave', 'delete', 'suggest']


def print_possible_commands():
    return """Possible commands are:
                \nlist \ncreate <day> <time> <place>\njoin <day>\nleave <day>\ndelete <day>"""


def print_event_created(author, date, place: EventPlace, time, id):
    return {
        'text': 'A new event was created!',
        'blocks': [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*A new event was created!*\n\n*{place.name()}*\n{parse_date_to_weekday(date)} {date} at {time}\nStarted by: <@{author}>"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Address:*\n{place.address()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Rating:*\n{place.rating()}"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Join this event",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": id,
                        "action_id": "join_event"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Brought to you by *Eventer*"
                    },
                    {
                        "type": "image",
                        "image_url": "https://platform.slack-edge.com/img/default_application_icon.png",
                        "alt_text": "Eventer logo"
                    }
                ]
            }
        ]
    }


def build_create_dialog(value=None):
    place_picker = {
        "type": "input",
        "block_id": "suggest_place",
        "element": {
            "type": "external_select",
            "action_id": "suggest_place",
            "placeholder": {
                "type": "plain_text",
                "text": "Start typing to search for a place",
            },
            "min_query_length": 3
        },
        "label": {
            "type": "plain_text",
            "text": "Pick a place",
            "emoji": True
        }
    }

    dialog = {
        'type': 'modal',
        'title': {'type': 'plain_text', 'text': 'Create an event'},
        'submit': {'type': 'plain_text', 'text': 'Create'},
        'callback_id': "create_event_dialog|",
        "blocks": [
                {
                    "type": "input",
                    "block_id": "event_day",
                    "element": {
                        "type": "datepicker",
                        "action_id": "event_day",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a date",
                            "emoji": True
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Which day?",
                        "emoji": True
                    }
                },
            {
                    "type": "input",
                    "block_id": "event_time",
                    "element": {
                        "type": "timepicker",
                        "action_id": "event_time",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a time",
                            "emoji": True
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "What time?",
                        "emoji": True
                    }
                }
        ]
    }

    if value is not None:
        # Get value from places api
        places = GooglePlaces()
        place = places.get_place_information(value)
        text_block = {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": place.display_name.text
            },
            "block_id": f"suggest_place|{place.id}",
        }
        dialog['blocks'].insert(2, text_block)
    else:
        dialog['blocks'].insert(2, place_picker)

    return dialog


def extract_values(state):
    """
    Extracts the 'value' field from the given state object.

    Args:
        state (dict): The state object containing nested fields.

    Returns:
        dict: A dictionary with extracted values.
    """
    extracted_values = {}
    for block_id, block_data in state.get("values", {}).items():
        for action_id, action_data in block_data.items():
            if action_data["type"] == "plain_text_input":
                extracted_values[action_id] = action_data.get("value")
            elif action_data["type"] == "external_select":
                extracted_values[action_id] = action_data.get(
                    "selected_option", {}).get("value")
            elif action_data["type"] == "datepicker":
                extracted_values[action_id] = action_data.get("selected_date")
            elif action_data["type"] == "timepicker":
                extracted_values[action_id] = action_data.get("selected_time")
    return extracted_values

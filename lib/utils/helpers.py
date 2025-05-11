# coding=utf-8
import calendar
import time
import os
from datetime import datetime, timedelta
import parsedatetime as pdt

from lib.api.google_places import GooglePlaces
from lib.models.event import Event
from lib.models.event_place import EventPlace
from lib.models.slack_message import SlackMessage


def validate_token(token) -> bool:
    return token == os.environ['SLACK_AUTH_KEY']


def get_user_name(user) -> str:
    return "<@" + user['user_id'] + "|" + user['user_name'] + ">"


def get_user_name_from_event(user) -> str:
    return "<@" + user['id'] + "|" + user['name'] + ">"


def is_day_formatted_as_date(day) -> bool:
    try:
        datetime.strptime(day, '%Y-%m-%d')
        return True
    except TypeError:
        return False
    except ValueError:
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


def get_date(date) -> str:
    natural_date = pdt.Calendar().parseDT(date)[0]
    if datetime.today() >= natural_date:
        return None

    return natural_date.strftime('%Y-%m-%d')


def print_event_list(events: list[Event], user) -> SlackMessage:
    event_list = SlackMessage(
        text='Upcoming events',
        blocks=[]
    )

    for event in events:
        place = event.location
        event_id = str(event._id)
        weekday = datetime.strptime(event.date, "%Y-%m-%d").weekday()

        # Header block for the event
        event_list.blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{place.name()}* on *{calendar.day_name[weekday]}* at *{event.time}*\nCreated by: *<@{event.author}>*"
            },
        })

        # Fields block for additional details
        event_list.blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Rating:*\n{place.rating}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Address:*\n{place.address}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Directions:*\n<{place.gMapsPlace.google_maps_uri}|Google Maps>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Place types:*\n{', '.join(place.gMapsPlace.types)}"
                },
            ]
        })

        # Participants block
        if event.participants:
            participants_text = "\n".join(
                [f"<@{participant}>" for participant in event.participants])
            event_list.blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Participants:*\n{participants_text}"
                }
            })
        else:
            event_list.blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "No one is participating in this event, *yet...*"
                }
            })

        # Actions block for buttons
        actions = []
        if event.participants and user not in event.participants:
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

        if event.participants and user in event.participants:
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

        if user == event.author:
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

        event_list.blocks.append({
            "type": "actions",
            "elements": actions
        })

        # Divider block between events
        event_list.blocks.append({
            "type": "divider"
        })

    return event_list


def print_event_create() -> SlackMessage:
    return SlackMessage(
        text='There is no upcoming event planned',
        blocks=[
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
                        "value": "",
                        "action_id": "create_event_action"
                    }
                ]
            }
        ])


def print_event_today(event: Event) -> str:
    if event is None:
        return None    
    if len(event.participants) > 0:
        return_message = "*Reminder * Today there's an event planned! \n"

        return_message += "*" + parse_date_to_weekday(event.date) + "*"

        if event.time:
            return_message += " at *" + event.time + "*"

        if event.location:
            return_message += " by *" + event.location.name() + "*"

        return_message += " started by *@" + event.author + "*"
        return_message += "\n *Participants:* \n"
        for participant in event.participants:
            return_message += "@" + participant + "\n"

        return_message += "\n *Don't be late!*"
    else:
        return_message = "Hey guys, there was an event planned for today, but no one wants to go :("

    return return_message


def get_valid_commands() -> list:
    return ['list', 'create', 'suggest']


def print_possible_commands() -> str:
    return """Possible commands are:
                \nlist \ncreate\n suggest <place>"""


def print_event_created(event: Event) -> SlackMessage:
    return SlackMessage(
        text='A new event was created!',
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*A new event was created!*\n\n*{event.location.name()}*\n{parse_date_to_weekday(event.date)} {event.date} at {event.time}\nStarted by: <@{event.author}>"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": event.description if event.description else "No description provided"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Address:*\n{event.location.address()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Rating:*\n{event.location.rating()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Directions:*\n{event.location.directions_url()}"
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
    )


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


def extract_values(state) -> dict:
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

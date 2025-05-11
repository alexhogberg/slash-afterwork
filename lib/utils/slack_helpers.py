import calendar
from datetime import datetime
from lib.models.slack_message import SlackMessage
from lib.api.google_places import GooglePlaces
from lib.models.event import Event
from lib.utils.date_utils import parse_date_to_weekday


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
        event_list.add_block({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Event on {calendar.day_name[weekday]}",
                "emoji": True
            }
        })

        # Fields block for additional details
        event_list.add_section_block(
            text=f"*{event.location.name()}*",
            fields=[
                f"*Rating:*\n{place.rating}",
                f"*Address:*\n{place.address}",
                f"*Directions:*\n<{place.gMapsPlace.google_maps_uri}|Google Maps>",
                f"*Place types:*\n{', '.join(place.gMapsPlace.types)}"
            ]
        )

        # Participants block
        if event.participants:
            participants_text = "\n".join([f"<@{participant}>" for participant in event.participants])
            event_list.add_section_block(
                text=f"*Participants:*\n{participants_text}"
            )
        else:
            event_list.add_section_block(
                text="*Participants:*\nNo one is participating in this event, *yet...*"
            )

        # Actions block for buttons
        actions = []
        if event.participants and user not in event.participants:
            actions.append({
                "type": "button",
                "action_id": "join_event",
                "text": {"type": "plain_text", "text": "Join event", "emoji": True},
                "style": "primary",
                "value": event_id
            })

        if event.participants and user in event.participants:
            actions.append({
                "type": "button",
                "action_id": "leave_event",
                "text": {"type": "plain_text", "text": "Leave event", "emoji": True},
                "value": event_id
            })

        if user == event.author:
            actions.append({
                "type": "button",
                "action_id": "delete_event",
                "text": {"type": "plain_text", "text": "Delete event", "emoji": True},
                "style": "danger",
                "value": event_id
            })

        event_list.add_action_block(actions)
        event_list.add_divider_block()

    return event_list


def print_event_create() -> SlackMessage:
    slack_message = SlackMessage(
        text='There is no upcoming event planned',
        blocks=[]
    )

    # Add section block
    slack_message.add_section_block(
        text="There is no upcoming event planned. Would you like to create one?"
    )

    # Add action block with a button
    slack_message.add_action_block([
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "Create event", "emoji": True},
            "style": "primary",
            "value": "",
            "action_id": "create_event_action"
        }
    ])

    return slack_message


def print_event_today(event: Event) -> str:
    if event is None:
        return None
    if len(event.participants) > 0:
        return_message = f"*Reminder * Today there's an event planned! \n*{parse_date_to_weekday(event.date)}*"
        if event.time:
            return_message += f" at *{event.time}*"
        if event.location:
            return_message += f" by *{event.location.name()}*"
        return_message += f" started by *@{event.author}*\n *Participants:* \n"
        return_message += "\n".join([f"@{participant}" for participant in event.participants])
        return_message += "\n *Don't be late!*"
    else:
        return "Hey guys, there was an event planned for today, but no one wants to go :("
    return return_message


def print_event_created(event: Event) -> SlackMessage:
    slack_message = SlackMessage(
        text='A new event was created!',
        blocks=[]
    )

    # Add header section
    slack_message.add_section_block(
        text=f"*A new event was created!*\n\n*{event.location.name()}*\n{parse_date_to_weekday(event.date)} {event.date} at {event.time}\nStarted by: <@{event.author}>"
    )

    # Add description section
    slack_message.add_section_block(
        text=event.description if event.description else "No description provided"
    )

    # Add fields for address, rating, and directions
    slack_message.add_section_block(
        text="Event details",
        fields=[
            f"*Address:*\n{event.location.address()}",
            f"*Rating:*\n{event.location.rating()}",
            f"*Directions:*\n{event.location.directions_url()}"
        ]
    )

    # Add action button
    slack_message.add_action_block([
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "Join this event", "emoji": True},
            "style": "primary",
            "value": str(event._id),
            "action_id": "join_event"
        }
    ])

    # Add context with branding
    slack_message.add_context_block([
        {"type": "mrkdwn", "text": "Brought to you by *Eventer*"},
        {"type": "image", "image_url": "https://platform.slack-edge.com/img/default_application_icon.png", "alt_text": "Eventer logo"}
    ])

    return slack_message


def build_create_dialog(value=None):
    place_picker = {
        "type": "input",
        "block_id": "suggest_place",
        "element": {
            "type": "external_select",
            "action_id": "suggest_place",
            "placeholder": {"type": "plain_text", "text": "Start typing to search for a place"},
            "min_query_length": 3
        },
        "label": {"type": "plain_text", "text": "Pick a place", "emoji": True}
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
                    "placeholder": {"type": "plain_text", "text": "Select a date", "emoji": True}
                },
                "label": {"type": "plain_text", "text": "Which day?", "emoji": True}
            },
            {
                "type": "input",
                "block_id": "event_time",
                "element": {
                    "type": "timepicker",
                    "action_id": "event_time",
                    "placeholder": {"type": "plain_text", "text": "Select a time", "emoji": True}
                },
                "label": {"type": "plain_text", "text": "What time?", "emoji": True}
            },
            {
                "type": "input",
                "block_id": "event_description",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "event_description",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Describe the event"}
                },
                "label": {"type": "plain_text", "text": "Event Description", "emoji": True}
            }
        ]
    }

    if value is not None:
        places = GooglePlaces()
        place = places.get_place_information(value)
        text_block = {
            "type": "section",
            "text": {"type": "plain_text", "text": place.display_name.text},
            "block_id": f"suggest_place|{place.id}",
        }
        dialog['blocks'].insert(3, text_block)
    else:
        dialog['blocks'].insert(3, place_picker)

    return dialog


def print_possible_commands() -> str:
    return """Possible commands are:\nlist\ncreate\nsuggest <place>"""


def show_events_view(user_id, events):
    """
    Show the events view in the Slack app home tab.
    :param user_id: The ID of the user to show the events view to.
    :param events: A list of events to display.
    :return: A dictionary representing the Slack home tab view.
    """
    base_view = {
        "type": "home",
        "callback_id": "home_view",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Welcome to Event Bot!* :tada:\n\nEvent Bot helps you plan and manage events with your team. Use the button below to create a new event or browse the upcoming events."
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
                            "text": "Create Event",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": "create_event",
                        "action_id": "create_event_action"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Upcoming Events*"
                }
            },
            {
                "type": "divider"
            },
        ]
    }

    # Append the list of events
    event_blocks = print_event_list(events, user_id).blocks
    base_view['blocks'] += event_blocks

    return base_view
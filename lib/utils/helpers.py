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

def get_valid_commands() -> list:
    return ['list', 'create', 'suggest']

def get_user_name(user) -> str:
    return f"<@{user['user_id']}|{user['user_name']}>"


def get_user_name_from_event(user) -> str:
    return f"<@{user['id']}|{user['name']}>"


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

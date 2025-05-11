# coding=utf-8

from datetime import datetime

import pytest
from lib.models.event import Event
from lib.models.event_place import EventPlace
from google.maps.places_v1.types import Place
from lib.models.slack_message import SlackMessage
from lib.utils.date_utils import (
    is_day_formatted_as_date,
    get_next_weekday_as_date,
    parse_date_to_weekday,
    get_day_number,
    get_date,
)
from lib.utils.slack_helpers import (
    print_event_list,
    print_event_create,
    print_event_today,
    print_event_created,
    build_create_dialog,
    print_possible_commands
)
from lib.utils.helpers import (
    validate_token,
    get_user_name,
    get_user_name_from_event,
    get_valid_commands,
    extract_values,
)

@pytest.fixture
def get_mock_event():
    return Event(
        _id=1,
        date="2023-10-10",
        team_id="team_id",
        time="18:00",
        location=EventPlace(
            Place(
                name="Test Place",
                id="ChIJN1t_tDeuEmsRUsoyG83frY4",
                formatted_address="123 Test St",
                rating=4.5,
                types=["restaurant", "bar"])
        ),
        participants=["U12345"],
        author="U67890",
    )


def test_validate_token(monkeypatch):
    monkeypatch.setenv("SLACK_AUTH_KEY", "test_token")
    assert validate_token("test_token") is True
    assert validate_token("wrong_token") is False


def test_get_user_name():
    user = {"user_id": "U12345", "user_name": "testuser"}
    assert get_user_name(user) == "<@U12345|testuser>"


def test_get_user_name_from_event():
    user = {"id": "U12345", "name": "testuser"}
    assert get_user_name_from_event(user) == "<@U12345|testuser>"


def test_is_day_formatted_as_date():
    assert is_day_formatted_as_date("2023-10-10") is True
    assert is_day_formatted_as_date("10-10-2023") is False
    assert is_day_formatted_as_date(None) is False


def test_get_next_weekday_as_date():
    weekday_number = 2  # Wednesday
    result = get_next_weekday_as_date(weekday_number)
    assert datetime.strptime(
        result, "%Y-%m-%d").weekday() == weekday_number


def test_parse_date_to_weekday():
    assert parse_date_to_weekday("2023-10-10") == "Tuesday"


def test_get_day_number():
    assert get_day_number("Tuesday") == 1
    assert get_day_number("Tue") == 1
    assert get_day_number("InvalidDay") is None


def test_get_date():
    assert get_date("tomorrow") is not None
    assert get_date("next Thursday") is not None
    assert get_date("yesterday") is None


def test_print_event_list(get_mock_event):
    user = "U12345"
    slack_message = print_event_list([get_mock_event], user)
    assert isinstance(slack_message, SlackMessage)


def test_print_event_create():
    slack_message = print_event_create()
    assert isinstance(slack_message, SlackMessage)


def test_print_event_today():
    event = Event(
        _id=1,
        date="2023-10-10",
        team_id="team_id",
        time="18:00",
        location=EventPlace(
            Place(
                name="Test Place",
                id="ChIJN1t_tDeuEmsRUsoyG83frY4",
                formatted_address="123 Test St",
                rating=4.5,
                types=["restaurant", "bar"])
        ),
        participants=["U12345"],
        author="U67890",
    )
    result = print_event_today(event)
    assert "Reminder" in result
    assert "Tuesday" in result
    assert "started by *@U67890*" in result

def test_print_event_today_no_participants():
    event = Event(
        _id=1,
        date="2023-10-10",
        team_id="team_id",
        time="18:00",
        location=EventPlace(
            Place(
                name="Test Place",
                id="ChIJN1t_tDeuEmsRUsoyG83frY4",
                formatted_address="123 Test St",
                rating=4.5,
                types=["restaurant", "bar"])
        ),
        participants=[],
        author="U67890",
    )
    result = print_event_today(event)
    assert "Hey guys, there was an event planned for today, but no one wants to go :(" in result

def test_print_event_today_no_event():
    event = None
    result = print_event_today(event)
    assert result is None

def test_get_valid_commands():
    commands = get_valid_commands()
    assert isinstance(commands, list)
    assert "list" in commands


def test_print_possible_commands():
    result = print_possible_commands()
    assert "list" in result
    assert "create" in result


def test_print_event_created():
    event = Event(
        _id=1,
        date="2023-10-10",
        team_id="team_id",
        time="18:00",
        location=EventPlace(
            Place(
                name="Test Place",
                id="ChIJN1t_tDeuEmsRUsoyG83frY4",
                formatted_address="123 Test St",
                rating=4.5,
                types=["restaurant", "bar"])
        ),
        participants=[],
        author="U67890",
    )
    slack_message = print_event_created(event)
    assert isinstance(slack_message, SlackMessage)


def test_build_create_dialog():
    dialog = build_create_dialog()
    assert isinstance(dialog, dict)
    assert "blocks" in dialog


def test_extract_values():
    state = {
        "values": {
            "block1": {
                "action1": {"type": "plain_text_input", "value": "test_value"},
            },
            "block2": {
                "action2": {"type": "datepicker", "selected_date": "2023-10-10"},
            },
        }
    }
    extracted = extract_values(state)
    assert extracted["action1"] == "test_value"
    assert extracted["action2"] == "2023-10-10"

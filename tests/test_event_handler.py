import pytest
from unittest.mock import MagicMock, patch
from lib.event_handler import EventHandler
from lib.api.mongodb import EventMongoDAL
from lib.api.google_places import GooglePlaces
from lib.api.slack import Slack
from lib.models.event import Event
from lib.models.event_place import EventPlace
from google.maps.places_v1.types import Place

from lib.models.slack_message import SlackMessage
from lib.utils.slack_helpers import print_possible_commands

@pytest.fixture
@patch("lib.api.mongodb.EventMongoDAL", autospec=True)
def event_handler(mock_event_mongo_dal):
    # Mock the MongoDB connection and prevent actual database calls
    mock_event_mongo_dal.return_value = MagicMock()
    
    team_id = "test_team"
    bolt_client = MagicMock()
    say_func = MagicMock()
    respond_func = MagicMock()
    current_view = "test_view"
    
    # Pass the mocked EventMongoDAL instance to the EventHandler
    return EventHandler(
        team_id=team_id,
        bolt_client=bolt_client,
        say_func=say_func,
        respond_func=respond_func,
        current_view=current_view,
        event_dal=mock_event_mongo_dal.return_value
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

def test_parse_command_no_command(event_handler):
    event_handler.respond = MagicMock()
    event_handler.parse_command("", {})
    event_handler.respond.assert_called_once_with(f"No command given, {print_possible_commands()}")

def test_parse_command_invalid_command(event_handler):
    event_handler.respond = MagicMock()
    event_handler.parse_command("invalid_command", {})
    event_handler.respond.assert_called_once_with(f"Invalid command given, {print_possible_commands()}")

def test_list_event_with_results(event_handler, get_mock_event):
    event_handler.event_dal.list_events = MagicMock(return_value=[get_mock_event])
    event_handler.respond = MagicMock()
    event_handler.list_event("list", {"user_id": "test_user"})
    event_handler.respond.assert_called_once()

def test_list_event_no_results(event_handler):
    event_handler.event_dal.list_events = MagicMock(return_value=[])
    event_handler.respond = MagicMock()
    event_handler.list_event("list", {"user_id": "test_user"})
    called_args: SlackMessage = event_handler.respond.call_args[0][0]  # Extract the first argument passed to respond
    assert called_args["text"] == "There is no upcoming event planned"

def test_create_event(event_handler):
    event_handler.bolt_client.views_open = MagicMock()
    event_handler.respond = MagicMock()
    event_handler.create_event("list", {"trigger_id": "test_trigger"})
    event_handler.bolt_client.views_open.assert_called_once()
    event_handler.respond.assert_called_once_with('Please follow the instructions in the dialog!')

def test_join_event_success(event_handler):
    event_handler.event_dal.join_event = MagicMock(return_value=True)
    event_handler.send_epemeral_message = MagicMock()
    result = event_handler.join_event("test_author", "test_id", "test_channel")
    assert result is True
    event_handler.send_epemeral_message.assert_called_once_with(
        "*Great!* You've joined the event!", "test_author", "test_channel"
    )

def test_join_event_failure(event_handler):
    event_handler.event_dal.join_event = MagicMock(return_value=False)
    event_handler.send_epemeral_message = MagicMock()
    result = event_handler.join_event("test_author", "test_id", "test_channel")
    assert (None, "*Oops!* I couldn't join you to that event. Maybe you are already participating?")
    event_handler.send_epemeral_message.assert_called_once_with(
        "*Oops!* I couldn't join you to that event. Maybe you are already participating?",
        "test_author",
        "test_channel"
    )

def test_leave_event_success(event_handler):
    event_handler.event_dal.leave_event = MagicMock(return_value=True)
    event_handler.send_epemeral_message = MagicMock()
    result = event_handler.leave_event("test_id", "test_author", "test_channel")
    assert result is True
    event_handler.send_epemeral_message.assert_called_once_with(
        "*Done!* You are now removed from the event!", "test_author", "test_channel"
    )

def test_leave_event_failure(event_handler):
    event_handler.event_dal.leave_event = MagicMock(return_value=False)
    event_handler.send_epemeral_message = MagicMock()
    result = event_handler.leave_event("test_id", "test_author", "test_channel")
    assert (None, '*Oops!* Are you really joined to that event?')
    event_handler.send_epemeral_message.assert_called_once_with(
        "*Oops!* Are you really joined to that event?",
        "test_author",
        "test_channel"
    )

def test_suggest_event_no_area(event_handler):
    event_handler.bolt_client.chat_postEphemeral = MagicMock()
    event_handler.suggest_event(["suggest"], {})
    event_handler.bolt_client.chat_postEphemeral.assert_called_once_with("Please specify a location to search for")

def test_suggest_event_with_area(event_handler):
    event_handler.google_places.get_suggestions = MagicMock(return_value=[
        Place(
                name="Test Place",
                id="ChIJN1t_tDeuEmsRUsoyG83frY4",
                formatted_address="123 Test St",
                rating=4.5,
                types=["restaurant", "bar"]),
        Place(
                name="Another Place",
                id="ChIJN1t_tDeuEmsRUsoyG83frY5",
                formatted_address="456 Another St",
                rating=4.0,
                types=["cafe", "restaurant"]),
        Place(
                name="Third Place",
                id="ChIJN1t_tDeuEmsRUsoyG83frY6",
                formatted_address="789 Third St",
                rating=3.5,
                types=["bar", "night_club"])
    ])
    event_handler.respond = MagicMock()
    event_handler.suggest_event(["suggest", "New York"], {})
    event_handler.respond.assert_called_once()

def test_create_event_from_input(event_handler):
    event_handler.google_places.get_place_information = MagicMock()
    event_handler.google_places.format_place = MagicMock()
    event_handler.event_dal.insert_event = MagicMock(return_value="test_id")
    event_handler.say = MagicMock()
    event_handler.create_event_from_input(
        date="2023-10-01",
        place_id="test_place",
        time="18:00",
        author="test_author",
        channel_id="test_channel",
        description="Test Event"
    )
    event_handler.say.assert_called_once()
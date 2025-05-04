import pytest
from unittest.mock import MagicMock, patch
from bson.objectid import ObjectId
from lib.api.mongodb import EventMongoDAL


@pytest.fixture
def mock_mongo_client():
    with patch("lib.api.mongodb.MongoClient") as mock_client:
        yield mock_client


@pytest.fixture
def event_dal(mock_mongo_client):
    # Mock the database and collection
    mock_db = mock_mongo_client.return_value.events
    mock_db.events = MagicMock()
    dal = EventMongoDAL(team_id="test_team")
    dal.mongodb = mock_mongo_client.return_value
    dal.database = mock_db
    return dal


def test_insert_event(event_dal):
    mock_inserted_id = ObjectId()
    event_dal.database.events.insert_one = MagicMock(return_value=MagicMock(inserted_id=mock_inserted_id))

    result = event_dal.insert_event(
        date="2023-10-01",
        place="Test Place",
        place_id="123",
        event_time="18:00",
        author="test_user",
        channel_id="test_channel"
    )

    event_dal.database.events.insert_one.assert_called_once()
    assert result == str(mock_inserted_id)


def test_list_events(event_dal):
    mock_events = [
        {"_id": ObjectId(), "Date": "2023-10-01", "Location": "Test Place", "TeamId": "test_team", "Time": "18:00"},
        {"_id": ObjectId(), "Date": "2023-10-02", "Location": "Another Place", "TeamId": "test_team", "Time": "19:00"}
    ]

    # Mock the find method to return a mock cursor
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_events
    event_dal.database.events.find = MagicMock(return_value=mock_cursor)

    result = event_dal.list_events()

    # Assert that find was called with the correct filter
    event_dal.database.events.find.assert_called_once_with({'TeamId': "test_team"})
    # Assert that sort was called with the correct sorting criteria
    mock_cursor.sort.assert_called_once_with([('Date', 1), ('Time', 1)])
    # Assert the result matches the mocked events
    assert result == mock_events


def test_get_event(event_dal):
    mock_event = {"_id": ObjectId(), "Date": "test_team|2023-10-01", "Location": "Test Place"}
    event_dal.database.events.find_one = MagicMock(return_value=mock_event)

    result = event_dal.get_event(str(mock_event["_id"]))

    event_dal.database.events.find_one.assert_called_once_with({"_id": mock_event["_id"]})
    assert result == mock_event


def test_join_event(event_dal):
    mock_event_id = ObjectId()
    event_dal.database.events.update_one = MagicMock(return_value=MagicMock(modified_count=1))

    result = event_dal.join_event(str(mock_event_id), "test_user")

    event_dal.database.events.update_one.assert_called_once_with(
        {"_id": mock_event_id},
        {"$addToSet": {"Participants": "test_user"}}
    )
    assert result is not None


def test_leave_event(event_dal):
    mock_event_id = ObjectId()
    event_dal.database.events.update_one = MagicMock(return_value=MagicMock(modified_count=1))

    result = event_dal.leave_event(str(mock_event_id), "test_user")

    event_dal.database.events.update_one.assert_called_once_with(
        {"_id": mock_event_id},
        {"$pull": {"Participants": "test_user"}}
    )
    assert result is not None


def test_delete_event(event_dal):
    mock_event_id = ObjectId()
    event_dal.database.events.delete_one = MagicMock(return_value=MagicMock(deleted_count=1))

    result = event_dal.delete_event(str(mock_event_id), "test_user")

    event_dal.database.events.delete_one.assert_called_once_with(
        {"_id": mock_event_id, "Author": "test_user"}
    )
    assert result is not None
import pytest
from unittest.mock import MagicMock, patch
from bson.objectid import ObjectId
from lib.api.mongodb import EventMongoDAL
from lib.models.event import Event


@pytest.fixture
def mock_mongo_client():
    with patch("lib.api.mongodb.MongoClient") as mock_client:
        yield mock_client


@pytest.fixture
def get_mock_event():
    return {
        "_id": "0123456789ab0123456789ab",
        "team_id": "test_team",
        "date": "2023-10-01",
        "time": "18:00",
        "location": "Test Place",
        "description": "Test Description",
        "participants": ["user1", "user2"],
        "author": "test_user"
    }


@pytest.fixture
def event_dal(mock_mongo_client):
    # Mock the database and collection
    mock_db = mock_mongo_client.return_value.events
    mock_db.events = MagicMock()
    dal = EventMongoDAL(team_id="test_team")
    dal.mongodb = mock_mongo_client.return_value
    dal.database = mock_db
    return dal


def test_insert_event(event_dal, get_mock_event):
    mock_inserted_id = ObjectId()
    event_dal.database.events.insert_one = MagicMock(
        return_value=MagicMock(inserted_id=mock_inserted_id))

    # Create a mock event object
    event = Event(**get_mock_event)

    result = event_dal.insert_event(event)

    event_dal.database.events.insert_one.assert_called_once()
    assert result == str(mock_inserted_id)


def test_list_events(event_dal):
    mock_events = [
        {
            "_id": "123",
            "team_id": "test_team",
            "date": "2023-10-01",
            "time": "18:00",
            "location": "Test Place",
            "description": "Test Description",
            "participants": ["user1", "user2"],
            "author": "test_user"
        },
        {
            "_id": "234",
            "team_id": "test_team",
            "date": "2023-10-02",
            "time": "19:00",
            "location": "Another Place",
            "description": "Another Description",
            "participants": ["user3"],
            "author": "test_user"
        },
        {
            "_id": "456",
            "team_id": "test_team",
            "date": "2023-10-03",
            "time": "20:00",
            "location": "Third Place",
            "description": "Third Description",
            "participants": ["user4"],
            "author": "test_user"
        }
    ]
    # Mock the find method to return a mock cursor
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_events
    event_dal.database.events.find = MagicMock(return_value=mock_cursor)

    result = event_dal.list_events()

    # Assert that find was called with the correct filter
    event_dal.database.events.find.assert_called_once_with(
        {'team_id': "test_team"})
    # Assert that sort was called with the correct sorting criteria
    mock_cursor.sort.assert_called_once_with([('date', 1), ('time', 1)])
    # Assert the result matches the mocked events

    # Assert that the result is a list of Event objects
    assert isinstance(result, list)
    assert len(result) == len(mock_events)


def test_get_event(event_dal, get_mock_event):
    mock_event = Event(**get_mock_event)
    event_dal.database.events.find_one = MagicMock(return_value=get_mock_event)

    result = event_dal.get_event(str(mock_event._id))

    event_dal.database.events.find_one.assert_called_once_with(
        {"_id": ObjectId('0123456789ab0123456789ab')})
    assert result.team_id == mock_event.team_id


def test_join_event(event_dal, get_mock_event):
    mock_event = Event(**get_mock_event)
    mock_event_id = mock_event._id
    
    updated_event = {
        "_id": mock_event_id,
        "team_id": "test_team",
        "date": "2023-10-01",
        "time": "18:00",
        "location": "Test Place",
        "description": "Test Description",
        "participants": ["user1", "user2", "test_user"],
        "author": "test_user"
    }
    # Mock the find_one_and_update method to return a mock event
    event_dal.database.events.find_one_and_update = MagicMock(
        return_value=updated_event)

    result = event_dal.join_event(str(mock_event_id), "test_user")

    event_dal.database.events.find_one_and_update.assert_called_once_with(
        {'_id': ObjectId('0123456789ab0123456789ab')}, {
            '$addToSet': {'participants': 'test_user'}},
        return_document=True)
    assert result.participants == updated_event["participants"]


def test_leave_event(event_dal, get_mock_event):
    mock_event = Event(**get_mock_event)
    mock_event_id = mock_event._id
    
    updated_event = {
        "_id": mock_event_id,
        "team_id": "test_team",
        "date": "2023-10-01",
        "time": "18:00",
        "location": "Test Place",
        "description": "Test Description",
        "participants": ["user1"],
        "author": "test_user"
    }
    # Mock the find_one_and_update method to return a mock event
    event_dal.database.events.find_one_and_update = MagicMock(
        return_value=updated_event)

    result = event_dal.leave_event(str(mock_event_id), "user2")

    event_dal.database.events.find_one_and_update.assert_called_once_with(
        {'_id': ObjectId('0123456789ab0123456789ab')}, {
            '$pull': {'participants': 'user2'}},
        return_document=True)
    assert result.participants == updated_event["participants"]


def test_delete_event(event_dal):
    mock_event_id = ObjectId()
    event_dal.database.events.delete_one = MagicMock(
        return_value=MagicMock(deleted_count=1))
    
    event_dal.database.events.find_one = MagicMock(
        return_value={
            "_id": mock_event_id,
            "team_id": "test_team",
            "date": "2023-10-01",
            "time": "18:00",
            "location": "Test Place",
            "description": "Test Description",
            "participants": ["user1"],
            "author": "test_user"
        }
    )

    result = event_dal.delete_event(str(mock_event_id), "test_user")

    event_dal.database.events.delete_one.assert_called_once_with(
        {"_id": mock_event_id, "author": "test_user"}
    )
    assert result is not None

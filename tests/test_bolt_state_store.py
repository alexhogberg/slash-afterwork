import pytest, time
from unittest.mock import MagicMock, patch
from lib.bolt.MongoDBBoltOAuthStateStore import MongoDBOAuthStateStore


@pytest.fixture
def mock_mongo_client():
    with patch("lib.api.mongodb.MongoClient") as mock_client:
        yield mock_client


@pytest.fixture
def state_store(mock_mongo_client):
    mock_db = mock_mongo_client.return_value
    return MongoDBOAuthStateStore(expiration_seconds=600)


def test_issue_state(state_store):
    state_store.collection.insert_one = MagicMock()
    state = state_store.issue()
    assert state is not None
    state_store.collection.insert_one.assert_called_once()


def test_consume_valid_state(state_store):
    state_store.collection.find_one_and_delete = MagicMock(return_value={"state": "test_state", "created_at": time.time()})
    result = state_store.consume("test_state")
    assert result is True
    state_store.collection.find_one_and_delete.assert_called_once_with({"state": "test_state"})


def test_consume_invalid_state(state_store):
    state_store.collection.find_one_and_delete = MagicMock(return_value=None)
    result = state_store.consume("invalid_state")
    assert result is False
    state_store.collection.find_one_and_delete.assert_called_once_with({"state": "invalid_state"})
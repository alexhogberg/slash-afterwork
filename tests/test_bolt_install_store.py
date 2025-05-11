from unittest.mock import MagicMock, patch

import pytest
from slack_bolt.oauth.internals import Installation

from lib.bolt.MongoDBBoltOAuth import MongoInstallationStore


@pytest.fixture
def mock_mongo_client():
    with patch("lib.api.mongodb.MongoClient") as mock_client:
        yield mock_client


@pytest.fixture
def installation_store(mock_mongo_client):
    mock_db = mock_mongo_client.return_value
    return MongoInstallationStore()


def test_save_installation(installation_store):
    installation_store.db.slack_installations.update_one = MagicMock()
    installation_store.db.slack_bots.update_one = MagicMock()

    installation = Installation(
        enterprise_id="E123",
        team_id="T123",
        user_id="U123",
        bot_token="xoxb-123",
        bot_id="B123",
    )
    installation_store.save(installation)

    installation_store.db.slack_installations.update_one.assert_called_once()
    installation_store.db.slack_bots.update_one.assert_called_once()


def test_find_installation(installation_store):
    installation_store.db.slack_installations.find_one = MagicMock(
        return_value={
            "_id": "123",
            "enterprise_id": "E123",
            "team_id": "T123",
            "user_id": "U123",
            "bot_token": "xoxb-123",
            "bot_id": "B123",
        }
    )
    result = installation_store.find_installation(
        team_id="T123", user_id="U123", enterprise_id=None
    )
    assert result is not None
    assert result.team_id == "T123"
    assert result.user_id == "U123"
    installation_store.db.slack_installations.find_one.assert_called_once_with(
        {"team_id": "T123", "user_id": "U123"}
    )


def test_find_bot(installation_store):
    installation_store.db.slack_bots.find_one = MagicMock(
        return_value={
            "_id": "123",
            "enterprise_id": "E123",
            "team_id": "T123",
            "bot_token": "xoxb-123",
            "bot_id": "B123",
            "bot_user_id": "U123",
            "installed_at": "2025-05-04T12:00:00",
        }
    )
    result = installation_store.find_bot(team_id="T123", enterprise_id=None)
    assert result is not None
    assert result.team_id == "T123"
    assert result.bot_token == "xoxb-123"
    assert result.bot_user_id == "U123"
    assert result.installed_at == 1746360000
    installation_store.db.slack_bots.find_one.assert_called_once_with(
        {"team_id": "T123"}
    )


def test_delete_installation(installation_store):
    installation_store.db.slack_installations.delete_one = MagicMock()
    installation_store.delete_installation(
        team_id="T123", user_id="U123", enterprise_id=None
    )
    installation_store.db.slack_installations.delete_one.assert_called_once_with(
        {"enterprise_id": None, "team_id": "T123", "user_id": "U123"}
    )


def test_delete_bot(installation_store):
    installation_store.db.slack_bots.delete_one = MagicMock()
    installation_store.delete_bot(team_id="T123", enterprise_id=None)
    installation_store.db.slack_bots.delete_one.assert_called_once_with(
        {"enterprise_id": None, "team_id": "T123"}
    )

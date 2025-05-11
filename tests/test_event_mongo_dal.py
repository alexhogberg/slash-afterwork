# import pytest
# from lib.api.mongodb import EventMongoDAL
# from lib.models.event import Event
# from bson.objectid import ObjectId

# @pytest.fixture
# def event_dal():
#     # Use a test team_id to isolate test data
#     return EventMongoDAL(team_id="test_team")

# @pytest.fixture
# def test_event():
#     # Create a sample event for testing
#     return Event(
#         _id=None,
#         team_id="test_team",
#         date="2025-05-11",
#         time="12:00",
#         location={"name": "Test Location"},
#         description="Test Event Description",
#         participants=["test_user1"],
#         author="test_user1",
#     )

# def test_insert_event(event_dal, test_event):
#     # Insert the event
#     event_id = event_dal.insert_event(test_event)
#     assert event_id is not None

#     # Verify the event exists in the database
#     inserted_event = event_dal.get_event(event_id)
#     assert inserted_event is not None
#     assert inserted_event.date == test_event.date
#     assert inserted_event.time == test_event.time
#     assert inserted_event.location["name"] == test_event.location["name"]

# def test_list_events(event_dal, test_event):
#     # Insert the event
#     event_dal.insert_event(test_event)

#     # List events
#     events = event_dal.list_events()
#     assert len(events) > 0
#     assert any(event.date == test_event.date for event in events)

# def test_get_event(event_dal, test_event):
#     # Insert the event
#     event_id = event_dal.insert_event(test_event)

#     # Retrieve the event
#     retrieved_event = event_dal.get_event(event_id)
#     assert retrieved_event is not None
#     assert retrieved_event.date == test_event.date
#     assert retrieved_event.author == test_event.author

# def test_join_event(event_dal, test_event):
#     # Insert the event
#     event_id = event_dal.insert_event(test_event)

#     # Join the event
#     updated_event = event_dal.join_event(event_id, "test_user2")
#     assert "test_user2" in updated_event.participants

# def test_leave_event(event_dal, test_event):
#     # Insert the event
#     event_id = event_dal.insert_event(test_event)

#     # Leave the event
#     updated_event = event_dal.leave_event(event_id, "test_user1")
#     assert "test_user1" not in updated_event.participants

# def test_delete_event(event_dal, test_event):
#     # Insert the event
#     event_id = event_dal.insert_event(test_event)

#     # Delete the event
#     deleted_event = event_dal.delete_event(event_id, test_event.author)
#     assert deleted_event is not None

#     # Verify the event no longer exists
#     assert event_dal.get_event(event_id) is None

# @pytest.fixture(autouse=True)
# def cleanup(event_dal):
#     """
#     Cleanup test data after each test.
#     """
#     yield
#     event_dal.database.events.delete_many({"team_id": "test_team"})
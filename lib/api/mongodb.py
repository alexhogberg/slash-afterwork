import logging
import os

from bson.objectid import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument

from lib.models.event import Event

load_dotenv()
db_connection_string = os.getenv("MONGO_DB_CONNECTION_STRING")


class OauthMongoDAL:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.mongodb = MongoClient(db_connection_string)
        self.database = self.mongodb.events

    def get_workspace(self, team_id):
        try:
            return self.database.slack_installations.find_one({"team_id": team_id})
        except Exception as e:
            self.logger.error(f"Error fetching workspace: {e}")
            return None


class EventMongoDAL:
    def __init__(self, team_id):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.mongodb = MongoClient(db_connection_string)
        self.database = self.mongodb.events
        self.team_id = team_id
        
        # Safety check: Warn if using production team_id during tests
        if team_id == "test_team":
            self.logger.warning("Using test_team for integration tests.")
        elif "test" not in team_id:
            raise ValueError("Integration tests must use a test-specific team_id.")

    def get_formatted_date(self, date) -> str:
        return self.team_id + "|" + date

    def insert_event(self, event: Event):
        self.logger.info(
            "Trying to create event at {day} for user {author} in {team}".format(
                day=event.date, author=event.author, team=self.team_id
            )
        )
        try:
            id = self.database.events.insert_one(event.to_dict()).inserted_id
            return str(id)
        except Exception as e:
            self.logger.error(e)
            raise e

    def list_events(self) -> list[Event]:
        try:
            # Fetch all events for the team, sorted by date and time
            events = self.database.events.find({"team_id": self.team_id}).sort(
                [("date", 1), ("time", 1)]
            )
            # Convert the cursor to a list of Event objects
            events = [Event(**event) for event in events]
            return list(events)
        except Exception as e:
            self.logger.error(e)
            return []

    def get_event(self, id) -> Event:
        response = self.database.events.find_one({"_id": ObjectId(id)})
        print(response)
        # Check if the event exists
        if response is None:
            self.logger.info(f"Event {id} not found")
            return None
        # Convert the event to an Event object
        event = Event(**response)
        return event

    def join_event(self, id, author) -> Event:
        self.logger.info(
            f"Trying to join event {id} for user {author} in {self.team_id}"
        )
        try:
            response = self.database.events.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$addToSet": {"participants": author}},
                return_document=ReturnDocument.AFTER,
            )
            self.logger.debug(response)
            # Convert the event to an Event object
            event = Event(**response)
            return event
        except Exception as e:
            self.logger.error(e)
            return None

    def leave_event(self, id, author) -> Event:
        self.logger.info(f"Trying to leave event {id} for user {author}")
        try:
            response = self.database.events.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$pull": {"participants": author}},
                return_document=ReturnDocument.AFTER,
            )
            self.logger.debug(response)
            event = Event(**response)
            return event
        except Exception as e:
            self.logger.error(e)
            return None

    def delete_event(self, id, author) -> Event:
        self.logger.info(f"Trying to delete event {id} for user {author}")
        try:
            existing_event = self.database.events.find_one({"_id": ObjectId(id)})

            response = self.database.events.delete_one(
                {"_id": ObjectId(id), "author": author}
            )
            if response.deleted_count == 0:
                self.logger.warning(
                    f"User {author} is not the author of the event {id}"
                )
                return None
            self.logger.info(response)
            return Event(**existing_event)
        except Exception as e:
            self.logger.error(e)
            return None

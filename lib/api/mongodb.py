import logging
import os
from dotenv import load_dotenv
from pymongo import MongoClient

from bson.objectid import ObjectId


load_dotenv()
db_connection_string = os.getenv('MONGO_DB_CONNECTION_STRING')
if db_connection_string is None:
    raise ValueError(
        "MONGO_DB_CONNECTION_STRING is not set in the environment variables.")


class OauthMongoDAL:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.mongodb = MongoClient(db_connection_string)
        self.database = self.mongodb.events

    def get_workspace(self, team_id):
        try:
            return self.database.slack_installations.find_one({'team_id': team_id})
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

        # Remove the unique constraint on the 'Date' field
        # Drop the unique index if it exists
        self.database.events.drop_index("Date_1")
        # Recreate as a non-unique index
        self.database.events.create_index([('Date', 1)])
        self.database.events.create_index([('TeamId', 1)])

    def get_formatted_date(self, date):
        return self.team_id + '|' + date

    def insert_event(self, date, place, place_id, event_time, author, channel_id):
        self.logger.info('Trying to create event at {day} for user {author} in {team}'.format(
            day=date,
            author=author,
            team=self.team_id
        ))
        item = {
            'Date': self.get_formatted_date(date),
            'TeamId': self.team_id,
            'Location': place,
            'Time': event_time,
            'Author': author,
            'Channel': channel_id,
            'Participants': [author]
        }

        if place_id is not None:
            item['PlaceId'] = place_id

        try:
            id = self.database.events.insert_one(item).inserted_id
            return str(id)
        except Exception as e:
            self.logger.error(e)
            raise e

    def list_events(self):
        try:
            # Fetch all events for the team, sorted by date and time
            events = self.database.events.find({'TeamId': self.team_id}).sort([
                ('Date', 1), ('Time', 1)])
            return list(events)
        except Exception as e:
            self.logger.error(e)
            return []

    def get_event(self, id):
        response = self.database.events.find_one({"_id": ObjectId(id)})
        return response

    def join_event(self, id, author):
        self.logger.info(
            f'Trying to join event {id} for user {author} in {self.team_id}')
        try:
            event = self.database.events.update_one(
                {"_id": ObjectId(id)}, {"$addToSet": {"Participants": author}})
            self.logger.info(event)
            if event.modified_count == 0:
                self.logger.info(
                    f'User {author} already joined the event {id}')
                return None
            return event
        except Exception as e:
            self.logger.error(e)
            return None

    def leave_event(self, id, author):
        self.logger.info(f'Trying to leave event {id} for user {author}')
        try:
            event = self.database.events.update_one(
                {"_id": ObjectId(id)}, {"$pull": {"Participants": author}})
            print(event)
            self.logger.info(event)
            if event.modified_count == 0:
                self.logger.info(f'User {author} already left the event {id}')
                return None
            return event
        except Exception as e:
            self.logger.error(e)
            return None

    def delete_event(self, id, author):
        self.logger.info(f'Trying to delete event {id} for user {author}')
        try:
            event = self.database.events.delete_one(
                {"_id": ObjectId(id), "Author": author})
            if event.deleted_count == 0:
                self.logger.info(
                    f'User {author} is not the author of the event {id}')
                return None
            self.logger.info(event)
            return event
        except Exception as e:
            self.logger.error(e)
            return None

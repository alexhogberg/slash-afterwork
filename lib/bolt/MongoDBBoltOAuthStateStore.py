import time
from uuid import uuid4

from pymongo import ASCENDING
from slack_sdk.oauth.state_store import OAuthStateStore

from lib.api.mongodb import OauthMongoDAL


class MongoDBOAuthStateStore(OAuthStateStore):
    def __init__(self, expiration_seconds: int):
        self.db = OauthMongoDAL().database
        self.collection = self.db["oauth_states"]
        self.expiration_seconds = expiration_seconds

        # Ensure TTL index exists
        self.collection.create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=self.expiration_seconds,
        )

    def issue(self, *args, **kwargs) -> str:
        state = str(uuid4())
        try:
            self.collection.insert_one({"state": state, "created_at": time.time()})
            return state
        except Exception as e:
            raise e

    def consume(self, state: str) -> bool:
        try:
            result = self.collection.find_one_and_delete({"state": state})
            if result:
                created_at = result["created_at"]
                expiration = created_at + self.expiration_seconds
                still_valid = time.time() < expiration
                return still_valid
            else:
                return False
        except Exception as e:
            raise e

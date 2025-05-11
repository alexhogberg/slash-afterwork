from typing import Optional

from slack_bolt.oauth.internals import Installation
from slack_sdk.oauth.installation_store import InstallationStore
from slack_sdk.oauth.installation_store.models.bot import Bot

from lib.api.mongodb import OauthMongoDAL


class MongoInstallationStore(InstallationStore):
    def __init__(self):
        self.db = OauthMongoDAL().database

    def save(self, installation: Installation):
        self.db.slack_installations.update_one(
            {
                "enterprise_id": installation.enterprise_id,
                "team_id": installation.team_id,
            },
            {"$set": installation.to_dict()},
            upsert=True,
        )
        self.db.slack_bots.update_one(
            {
                "enterprise_id": installation.enterprise_id,
                "team_id": installation.team_id,
            },
            {"$set": installation.to_bot().to_dict()},
            upsert=True,
        )

    def find_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Installation]:
        if is_enterprise_install:
            result = self.db.slack_installations.find_one(
                {"enterprise_id": enterprise_id, "user_id": user_id}
            )
            if result:
                del result["_id"]
                return Installation(**result)
            result = self.db.slack_installations.find_one(
                {"enterprise_id": enterprise_id}
            )
            if result:
                del result["_id"]
                return Installation(**result)
            return None
        result = self.db.slack_installations.find_one(
            {"team_id": team_id, "user_id": user_id}
        )
        if result:
            del result["_id"]
            return Installation(**result)
        result = self.db.slack_installations.find_one({"team_id": team_id})
        if result:
            del result["_id"]
            return Installation(**result)
        return None

    def find_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Bot]:
        """Finds a bot scope installation per workspace / org"""
        if is_enterprise_install:
            result = self.db.slack_bots.find_one({"enterprise_id": enterprise_id})
            if result:
                del result["_id"]
                return Bot(**result)
            return None
        result = self.db.slack_bots.find_one({"team_id": team_id})
        if result:
            del result["_id"]
            return Bot(**result)
        return None

    def delete_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ) -> None:
        """Deletes a bot scope installation per workspace / org"""
        self.db.slack_bots.delete_one(
            {"enterprise_id": enterprise_id, "team_id": team_id}
        )

    def delete_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
    ) -> None:
        """Deletes an installation that matches the given IDs"""
        if user_id is not None:
            self.db.slack_installations.delete_one(
                {
                    "enterprise_id": enterprise_id,
                    "team_id": team_id,
                    "user_id": user_id,
                }
            )
        else:
            self.db.slack_installations.delete_one(
                {"enterprise_id": enterprise_id, "team_id": team_id}
            )

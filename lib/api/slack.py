import logging
import os

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from lib.api.mongodb import OauthMongoDAL

load_dotenv()


class Slack:
    def __init__(self, team_id=None):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.oauth = OauthMongoDAL()
        if team_id is None:
            self.api_key = os.getenv("SLACK_BOT_TOKEN")
        else:
            self.api_key = os.getenv("SLACK_BOT_TOKEN")

        self.client = WebClient(token=self.api_key)

    @staticmethod
    def private_slack_text(text):
        return {"text": text}

    def get_channel_id(self):
        """
        Fetch the channel ID for the channel name specified in the environment variable.
        """
        try:
            response = self.client.conversations_list()
            channels = response.get("channels", [])

            for channel in channels:
                if channel["name"] == os.getenv("SLACK_CHANNEL_NAME"):
                    return channel["id"]

            self.logger.warning(
                "Channel not found: %s", os.getenv("SLACK_CHANNEL_NAME")
            )
            return None
        except SlackApiError as e:
            self.logger.error(f"Error fetching channel list: {e.response['error']}")
            raise

    def send_public_message(self, text, username, attachments=None):
        """
        Send a public message to the specified Slack channel.
        """
        channel_id = self.get_channel_id()
        if not channel_id:
            self.logger.error("Unable to send message: Channel ID not found.")
            return

        try:
            self.client.chat_postMessage(
                channel=channel_id,
                text=text,
                username=username,
                attachments=attachments,
            )
        except SlackApiError as e:
            self.logger.error(f"Error sending message: {e.response['error']}")
            raise

    def update_chat_message(self, channel, ts, text):
        """
        Update an existing chat message in a Slack channel.
        """
        try:
            self.client.chat_update(channel=channel, ts=ts, text=text)
        except SlackApiError as e:
            self.logger.error(f"Error updating message: {e.response['error']}")
            raise

    def open_dialog(self, trigger_id, dialog):
        """
        Open a Slack dialog using the provided trigger ID and dialog payload.
        """
        try:
            response = self.client.dialog_open(trigger_id=trigger_id, dialog=dialog)
            return response
        except SlackApiError as e:
            self.logger.error(f"Error opening dialog: {e.response['error']}")
            raise

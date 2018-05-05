import logging
import os

from slacker import Slacker
from slackclient import SlackClient

from lib.api.dynamodb import OauthDAL


class Slack:
    def __init__(self, team_id=None):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.oauth = OauthDAL()
        if team_id is None:
            self.apiKey = os.environ['apiKey']
        else:
            self.apiKey = self.oauth.getTokenForTeam(team_id)
        self.slack = Slacker(self.apiKey)
        self.slack_client = SlackClient(self.apiKey)

    @staticmethod
    def private_slack_text(text):
        return {
            'text': text
        }

    def get_channel_id(self):
        channel_list = self.slack.channels.list()

        channel_id = 0

        for channel in channel_list.body['channels']:
            if channel['name'] == os.environ['channelName']:
                channel_id = channel['id']
                break

        return channel_id

    def send_public_message(self, text, username, attachments=None):
        self.slack.chat.post_message(
            text=text,
            attachments=attachments,
            channel=self.get_channel_id(),
            username=username
        )

    def update_chat_message(self, channel, ts, text):
        self.slack.chat.update(
            channel=channel,
            ts=ts,
            text=text
        )

    def open_dialog(self, trigger_id, dialog):
        open_dialog = self.slack_client.api_call(
            "dialog.open",
            trigger_id=trigger_id,
            dialog=dialog
        )

        return open_dialog

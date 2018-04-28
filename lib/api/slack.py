import logging
import os

from slacker import Slacker


class Slack:
    def __init__(self, api_key=None):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.slack = Slacker(api_key or None)

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

    def send_public_message(self, text, username):
        self.slack.chat.post_message(
            text=text,
            channel=self.get_channel_id(),
            username=username
        )

    def update_chat_message(self, channel, ts, text):
        self.slack.chat.update(
            channel=channel,
            ts=ts,
            text=text
        )

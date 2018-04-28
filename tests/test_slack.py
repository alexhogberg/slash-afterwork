import json
import os
import unittest
from mock import Mock, patch
from lib.api.slack import Slack

slack = Slack()


class SlackTestCase(unittest.TestCase):
    @staticmethod
    def test_private_slack_text():
        text = slack.private_slack_text('test message')
        expected = {
            'text': 'test message'
        }

        assert text == expected

    @patch('slacker.requests')
    def test_get_channel_id(self, mock_requests):
        os.environ['channelName'] = 'test'
        text = {
            'ok': 'true',
            'channels': [
                {'name': 'test', 'id': '0'}
            ]
        }
        json_to_text = json.dumps(text)

        mock_requests.get.return_value = Mock(
            status_code=200, text=json_to_text
        )

        self.assertEqual(
            '0', slack.get_channel_id()
        )

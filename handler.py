import os
from afterwork import Afterwork

afterwork_handler = Afterwork()


def index(event, context):
    if 'token' in event['body'] and event['body']['token'] == os.environ['apiKey']:
        return afterwork_handler.parse_command(event['body']['text'], event['body'])
    else:
        return afterwork_handler.slack_text("HEY YOU'RE NOT THE ONE, OK?!")


import os
from afterwork import Afterwork

afterwork_handler = Afterwork()


def index(event, context):
    if 'body' in event and 'token' in event['body'] and event['body']['token'] == os.environ['authKey']:
        return afterwork_handler.parse_command(event['body']['text'], event['body'])
    elif 'triggerToken' in event and event['triggerToken'] == os.environ['authKey']:
        return afterwork_handler.todays_afterwork()
    else:
        return "HEY YOU'RE NOT THE ONE, OK?!"


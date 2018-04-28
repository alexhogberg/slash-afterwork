# coding=utf-8
import json
import os
import logging

from lib.afterwork import Afterwork

afterwork_handler = Afterwork()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def validate_token(token):
    return token == os.environ['authKey']


def handle_command(event):
    token = event.get('token', None)
    ssl_check = event.get('ssl_check', None)
    challenge = event.get('challenge', None)
    text = event.get('text', None)
    payload = event.get('payload', None)

    if payload is not None:
        return afterwork_handler.handle_interactive_event(payload)
    if not validate_token(token):
        return "Unauthorized"
    if challenge is not None:
        return {'challenge': challenge}
    if ssl_check is not None:
        return {'ssl_check': ssl_check}
    if text is not None:
        return afterwork_handler.parse_command(text, event)


def index(event, context):
    logger.info(json.dumps(event))
    if bool(event['body']) is not False:
        return handle_command(event['body'])
    elif 'triggerToken' in event and event['triggerToken'] == os.environ['authKey']:
        return afterwork_handler.todays_afterwork()
    else:
        return "HEY YOU'RE NOT THE ONE, OK?!"

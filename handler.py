# coding=utf-8
import json
import os
import logging

import requests

from lib.afterwork import Afterwork
from lib.api.dynamodb import OauthDAL
from lib.api.slack import Slack

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
        parsed_payload = json.loads(payload)
        afterwork_handler = Afterwork(parsed_payload.get('team').get('id'))
        return afterwork_handler.handle_interactive_event(parsed_payload)
    if not validate_token(token):
        return "Unauthorized"
    if challenge is not None:
        return {'challenge': challenge}
    if ssl_check is not None:
        return {'ssl_check': ssl_check}
    if text is not None:
        afterwork_handler = Afterwork(event.get('team_id'))
        return afterwork_handler.parse_command(text, event)


def index(event, context):
    logger.info(json.dumps(event))

    if bool(event['body']) is not False:
        return handle_command(event['body'])
    else:
        return "HEY YOU'RE NOT THE ONE, OK?!"

def authorize(event, context):
    slack = Slack()
    logger.info(event)
    auth_response = slack.slack_client.api_call(
        "oauth.access",
        client_id=os.environ['client_id'],
        client_secret=os.environ['client_secret'],
        code=event.get('query').get('code'),
        redirect_uri='https://f1pgh8ehhi.execute-api.eu-west-1.amazonaws.com/dev/afterwork'
    )

    oauth = OauthDAL()

    team_id = auth_response.get('team_id')
    bot_access_token = auth_response.get('bot').get('bot_access_token')
    access_token = auth_response.get('access_token')

    logger.info(auth_response)

    if team_id and bot_access_token and access_token:
        oauth.addApp(team_id, bot_access_token, access_token)
    else:
        return "Missing required parameters"


    return auth_response
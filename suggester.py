# coding=utf-8
import json
import os
import logging

from lib.api.google_places import GooglePlaces

google_places = GooglePlaces()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def validate_token(token):
    return token == os.environ['authKey']


def handle_command(event):
    payload = json.loads(event.get('payload'))
    token = payload.get('token', None)
    value = payload.get('value')
    logger.info(payload)
    logger.info(value)

    if not validate_token(token):
        logger.info('Unauthorized')
        return "Unauthorized"

    if value is not None:
        suggestions = google_places.get_place_suggestions(value)
        logger.info(suggestions)
        return suggestions


def index(event, context):
    if bool(event['body']) is not False:
        return handle_command(event['body'])
    else:
        return "HEY YOU'RE NOT THE ONE, OK?!"

import logging
import os
from lib.bolt.MongoDBBoltOAuth import MongoInstallationStore
from lib.api.mongodb import OauthMongoDAL
from slack_sdk.oauth.state_store import FileOAuthStateStore
from slack_bolt.oauth.oauth_settings import OAuthSettings
from lib.bolt.MongoDBBoltOAuthStateStore import MongoDBOAuthStateStore
from lib.utils.helpers import build_create_dialog, validate_token
from lib.event import Event
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt import App
from dotenv import load_dotenv

from lib.api import google_places

load_dotenv()


logging.basicConfig(level=logging.DEBUG)
state_store = FileOAuthStateStore(
    expiration_seconds=600, base_dir="/app/data/state")
oauth_settings = OAuthSettings(
    client_id=os.environ["SLACK_CLIENT_ID"],
    client_secret=os.environ["SLACK_CLIENT_SECRET"],
    installation_store=MongoInstallationStore(),
    state_store=MongoDBOAuthStateStore(expiration_seconds=600),
    scopes=["channels:history", "channels:join", "chat:write", "chat:write.customize", "chat:write.public", "commands", "groups:history", "im:history",
            "im:read", "im:write", "im:write.topic", "incoming-webhook", "mpim:history", "mpim:read", "mpim:write", "mpim:write.topic", "channels:read"],
    user_scopes=["channels:write.invites"]
)

app = App(
    token=os.environ.get('SLACK_APP_TOKEN'),
    signing_secret=os.environ.get('SLACK_SIGNING_SECRET'),
    oauth_settings=oauth_settings
)
google_places = google_places.GooglePlaces()
oauth_dal = OauthMongoDAL()


@app.middleware  # Middleware to dynamically set the bot token
def set_bot_token(context, next, logger):
    team_id = context.get("team_id")
    if not team_id:
        logger.error("No team_id found in the context.")
        return

    workspace = oauth_dal.get_workspace(team_id)
    if workspace:
        context["bot_token"] = workspace["BotAccessToken"]
        logger.info(f"Bot token set for team {team_id}")
    else:
        logger.error(f"No token found for team {team_id}")
    next()


def handle_command(command, respond, say, client):
    print(command)
    token = command.get('token', None)
    type = command.get('type', None)
    ssl_check = command.get('ssl_check', None)
    challenge = command.get('challenge', None)
    text = command.get('text', None)

    if not validate_token(token):
        return respond("Unauthorized")

    if type is not None and type == 'block_actions':
        event_handler = Event(command.get('user').get(
            'team_id'), client, say, respond)
        return event_handler.handle_interactive_event(command)
    if challenge is not None:
        return {'challenge': challenge}
    if ssl_check is not None:
        return {'ssl_check': ssl_check}
    if text is not None:
        event_handler = Event(command.get('team_id'), client, say, respond)
        return event_handler.parse_command(text, command)


@app.command("/event")
def command_event(ack, respond, command, say, client):
    ack()
    handle_command(command, respond, say, client)


@app.options("suggest_place")
def suggest_place(ack, payload):
    suggestions = google_places.get_place_suggestions(payload['value'])
    ack(options=suggestions)


@app.action("suggest_place")
def handle_suggest_place(ack):
    ack()


@app.action("create_event_suggest")
def handle_some_action(ack, body, payload, client):
    ack()
    client.views_open(trigger_id=body['trigger_id'], view=build_create_dialog(
        value=payload['value']))


@app.action("create_event_action")
def handle_create_event_action(ack, body, client):
    ack()
    client.views_open(
        trigger_id=body['trigger_id'], view=build_create_dialog())


@app.action("join_event")
def handle_join_action(ack, body, respond, say, client):
    ack()
    handle_command(body, respond, say, client)


@app.action("leave_event")
def handle_leave_action(ack, body, respond, say, client):
    ack()
    handle_command(body, respond, say, client)


@app.action("delete_event")
def handle_delete_action(ack, body, respond, say, client):
    ack()
    handle_command(body, respond, say, client)


@app.view("create_event_dialog|")
def handle_view_submission_events(ack, body, client, say, respond):
    ack()
    event_handler = Event(body.get('team').get('id'), client, say, respond)
    event_handler.create_event_response(body)
    if body.get('view', {}).get('id'):
        user_id = body.get('user').get('id')
        event_handler.update_events_view(user_id)


@app.event("app_home_opened")
def show_home_tab(ack, client, event, body):
    ack()
    if event.get('view', {}).get('id'):
        event_handler = Event(event.get('view', {}).get('team_id'), client)
        user_id = event.get('user')
        event_handler.update_events_view(user_id)


# Initialize Flask app
from flask import Flask, request
flask_app = Flask(__name__)

# SlackRequestHandler translates WSGI requests to Bolt's interface
# and builds WSGI response from Bolt's response.
from slack_bolt.adapter.flask import SlackRequestHandler
handler = SlackRequestHandler(app)

# Register routes to Flask app
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    # handler runs App's dispatch method
    return handler.handle(request)

if __name__ == '__main__':
    flask_app.run(port=int(os.environ.get("PORT", 3000)), host='0.0.0.0')

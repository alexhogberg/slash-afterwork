# coding=utf-8
import logging
import os

from datetime import datetime

import pymongo
from lib.api.google_places import GooglePlaces
from lib.api.mongodb import EventMongoDAL
from lib.utils.helpers import extract_values, get_date, print_event_list, get_valid_commands, \
    print_possible_commands, \
    print_event_created, print_event_today, build_create_dialog, print_event_create
from lib.models.event_place import EventPlace
from lib.api.slack import Slack


class Event:
    def __init__(self, team_id, bolt_client=None, say_func=None, respond_func=None, current_view=None):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        self.slack = Slack(team_id)
        self.bolt_client = bolt_client
        self.current_view_id = current_view
        self.say = say_func
        self.respond = respond_func
        if team_id is None:
            self.logger.error("No team id specified")
        self.event_dal = EventMongoDAL(team_id)
        self.google_places = GooglePlaces()

    def parse_command(self, command, event):
        """
        Parses the input command given from the slack slash command
        :param command: the command to be parsed
        :param event: the full lambda event
        :return: the action done or error if incorrect command was specified
        """
        self.logger.info("Handling command: {command}".format(command=command))
        if command == "":
            return self.respond("No command given, {possible_commands}".format(
                possible_commands=print_possible_commands()
            ))
        elif command.split(" ")[0] in get_valid_commands():
            operation = command.split(" ")

            action = getattr(self, operation[0] + "_event")
            return action(operation, event)

        else:
            return self.respond("Invalid command given, {possible_commands}".format(
                possible_commands=print_possible_commands()
            ))

    def handle_interactive_event(self, payload):
        """
        Handles the interactive events from slack
        :param payload: the payload from the slack event
        :return: None
        """
        self.logger.info(
            "Handling interactive event: {payload}".format(payload=payload))
        if payload.get('type') == 'block_actions':
            action = payload.get('actions')[0]
            user = payload.get('user').get('id')
            channel_id = payload.get('container').get('channel_id')
            if action.get('action_id') == 'suggest_place':
                self.suggest_event(action.get('value'), payload)
            elif action.get('action_id') == 'join_event':
                self.join_event(user, action.get('value'), channel_id)
            elif action.get('action_id') == 'leave_event':
                self.leave_event(action.get('value'), user, channel_id)
            elif action.get('action_id') == 'delete_event':
                self.delete_event(action.get('value'), user, channel_id)
            elif action.get('action_id') == 'create_event_dialog':
                self.create_event_response(payload)

        update_view = self.show_events_view(payload.get('user').get('id'))

        if 'view_id' in payload.get('container'):
            self.logger.info("Updating view with ID: {view_id}".format(
                view_id=payload.get('container').get('view_id')))
            self.bolt_client.views_update(
                view_id=payload.get('container').get('view_id'),
                view=update_view
            )

        # if 'message_ts' in payload.get('container') and 'channel_id' in payload.get('container') and not 'is_ephemeral' in payload.get('container'):
        #     self.logger.info("Updating message with timestamp: {ts}".format(ts=payload.get('container').get('message_ts')))
        #     self.bolt_client.chat_update(
        #         channel=payload.get('container').get('channel_id'),
        #         ts=payload.get('container').get('message_ts'),
        #         text=json.dumps(update_view)
        #     )

    def send_epemeral_message(self, text, user_id, channel_id):
        """
        Sends an ephemeral message to a user in slack
        :param text: the text to be sent
        :param user_id: the user id of the user to send the message to
        :return: None
        """
        if text and user_id and channel_id:
            self.bolt_client.chat_postEphemeral(
                channel=channel_id,
                text=text,
                user=user_id
            )

    def update_events_view(self, user_id):
        """
        Updates the view in slack
        :param view_id: the view id to be updated
        :param view: the view to be updated
        :return: None
        """
        if user_id:
            event_view = self.show_events_view(user_id)
            self.bolt_client.views_publish(
                user_id=user_id,
                view=event_view
            )

    def list_event(self, command, event):
        """
        Gets a list of events
        :param command: Not used
        :param event: Not used
        :return: A slack message containing the upcoming events
        """
        results = self.event_dal.list_events()
        events = print_event_list(results, event.get('user_id'))
        self.logger.info("Found events: {events}".format(events=events))
        if results and len(results) > 0:
            self.respond(events)
        else:
            self.respond(print_event_create())

    def create_event(self, command, event):
        """
        Creates a new event.
        :param command: parse this to get day, time and place
        :param event: the full lambda event
        :return:
        """

        trigger_id = event.get('trigger_id')
        self.bolt_client.views_open(
            trigger_id=trigger_id, view=build_create_dialog())
        return self.respond('Please follow the instructions in the dialog!')

    def join_event(self, author, id, channel_id):
        if id is not None:
            if self.event_dal.join_event(id, author):
                self.send_epemeral_message(
                    "*Great!* You've joined the event!", author, channel_id)
                self.logger.info("*Great!* You've joined the event!")
                return True
            else:
                err_msg = "*Oops!* I couldn't join you to that event. Maybe you are already participating?"
                self.send_epemeral_message(err_msg, author, channel_id)
                self.logger.error(err_msg)
                return None, err_msg

    def leave_event(self, id, author, channel_id):
        if id is not None:
            if self.event_dal.leave_event(id, author):
                self.send_epemeral_message(
                    "*Done!* You are now removed from the event!", author, channel_id)
                self.logger.info("*Done!* You are now removed from the event!")
                return True
            else:
                err_msg = "*Oops!* Are you really joined to that event?"
                self.send_epemeral_message(err_msg, author, channel_id)
                self.logger.error(err_msg)
                return None, err_msg

        return "Couldn't find any event on that day."

    def delete_event(self, id, author, channel_id):
        if id is not None:
            # Fetch the event details before deleting
            event = self.event_dal.get_event(id)
            if not event:
                self.send_epemeral_message(
                    "*Sorry!* I couldn't find the event to delete.", author, channel_id)
                return None, "Event not found."

            if event['Author'] != author:
                self.send_epemeral_message(
                    "*Sorry!* You can only delete events you created.", author, channel_id)
                return None, "Unauthorized to delete the event."

            # Proceed to delete the event
            if self.event_dal.delete_event(id, author):
                event_details = f"*{event['Location']['name']}* on *{event['Date'].split("|")[1]}* at *{event['Time']}*"
                self.say(
                    text=f"The event has been cancelled: {event_details}",
                    channel=self.slack.get_channel_id()
                )
                self.send_epemeral_message(
                    f"*Gotcha!* Event deleted: {event_details}", author, channel_id)
                return True
            else:
                self.send_epemeral_message(
                    "*Sorry!* I was unable to delete the event.", author, channel_id)
                return None, "Failed to delete the event."

        return "Couldn't find any event on that day."

    def suggest_event(self, command, event):
        area = " ".join(command[1:])

        if area is None or area == "":
            return self.bolt_client.chat_postEphemeral("Please specify a location to search for")
        suggestions = self.google_places.get_suggestions(area)

        return_value = {
            'text': 'Suggestions for {place}'.format(place=area),
            'blocks': []
        }

        places = sorted(suggestions, key=lambda p: p.rating, reverse=True)

        for p in places[:5]:
            return_value['blocks'] = return_value['blocks'] + \
                EventPlace(p).format_block()

        if len(return_value['blocks']) == 0:
            return self.bolt_client.chat_postEphemeral('No suggestions found for {area}'.format(area=area))

        self.respond(return_value)

    def todays_event(self):
        """
        Runs automatically on a cloudwatch schedule each day to look for any events today
        :return: A message in the slack channel notifying anyone of an upcoming event
        """
        event = self.event_dal.get_event(datetime.today().strftime("%Y-%m-%d"))

        if event is not None:
            event = print_event_today(event)

            try:
                self.say(
                    text=event
                )
            except Exception as e:
                self.logger.error(e)

    def create_event_from_event(self, date, place_id, time, author, channel_id):
        place = self.google_places.get_place_information(place_id)
        try:
            id = self.event_dal.insert_event(
                date=date,
                place=self.google_places.format_place(place),
                place_id=place_id,
                event_time=time,
                author=author,
                channel_id=channel_id
            )

            self.logger.info('Created a new event from suggestion')
            message = print_event_created(
                author, get_date(date), EventPlace(place), time, id)
            self.say(
                text=message['text'],
                blocks=message['blocks'],
                channel=channel_id
            )

            return {}
        except pymongo.errors.DuplicateKeyError:
            self.respond({
                'errors': [
                    {
                        'name': 'event_day',
                        'error': 'Sorry this day seems occupied'
                    }
                ]
            })
        except Exception as e:
            self.logger.error(e)
            self.logger.error('Something went horribly wrong')
            raise e

    def create_event_response(self, payload):
        # Find the state from the payload and extract the values we want
        # to use in the event creation
        extracted = extract_values(payload.get('view').get('state'))
        # Find if we already have a place id in suggest_place block
        suggested_place = next(block['block_id'] for block in payload['view']
                               ['blocks'] if block['block_id'].startswith('suggest_place'))
        if '|' in suggested_place:
            place_id = suggested_place.split('|')[1]
        else:
            place_id = None

        date = get_date(extracted['event_day'])
        time = extracted['event_time']

        channel_id = self.slack.get_channel_id()
        print(f"Channel ID: {channel_id}")

        if payload.get('view').get('callback_id') is not None:
            split_callback = payload.get('view').get('callback_id').split('|')

            if place_id is None:
                if split_callback[0] == 'create_event_dialog':
                    place_id = extracted.get('suggest_place')

            return self.create_event_from_event(
                date=date,
                place_id=place_id,
                time=time,
                author=payload.get('user').get('id'),
                channel_id=channel_id
            )

    def show_events_view(self, user_id):
        """
        Show the events view in the Slack app home tab.
        :param user_id: The ID of the user to show the events view to.
        """
        self.logger.info(f"Showing events view for user: {user_id}")

        base_view = {
            "type": "home",
            "callback_id": "home_view",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Welcome to Event Bot!* :tada:\n\nEvent Bot helps you plan and manage events with your team. Use the button below to create a new event or browse the upcoming events."
                    }
                },
                {
                    "type": "actions",
                    "block_id": "create_event_block",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Create Event",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": "create_event",
                            "action_id": "create_event_action"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Upcoming Events*"
                    }
                },
                {
                    "type": "divider"
                },
            ]
        }

        # Fetch and append the list of events
        results = self.event_dal.list_events()
        events = print_event_list(results, user_id)
        base_view['blocks'] = base_view['blocks'] + events['blocks']

        return base_view

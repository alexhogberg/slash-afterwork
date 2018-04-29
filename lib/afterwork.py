# coding=utf-8
import json

import logging
import os
import googlemaps

from datetime import datetime
from lib.api.dynamodb import AfterworkDAL
from lib.api.google_places import GooglePlaces
from lib.utils.helpers import get_user_name, get_date, parse_date_to_weekday, print_afterwork_list, get_valid_commands, \
    print_possible_commands, \
    print_afterwork_created, print_afterwork_today, get_user_name_from_event, build_create_dialog
from lib.models.place import Place
from lib.api.slack import Slack


class Afterwork:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        self.slack = Slack(api_key=os.environ['apiKey'])
        self.afterwork_dal = AfterworkDAL()
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
            return self.slack.private_slack_text("No command given, {possible_commands}".format(
                possible_commands=print_possible_commands()
            ))
        elif command.split(" ")[0] in get_valid_commands():
            operation = command.split(" ")

            action = getattr(self, operation[0] + "_afterwork")
            return action(operation, event)

        else:
            return self.slack.private_slack_text("Invalid command given, {possible_commands}".format(
                possible_commands=print_possible_commands()
            ))

    def list_afterwork(self, command, event):
        """
        Gets a list of after work events
        :param command: Not used
        :param event: Not used
        :return: A slack message containing the upcoming after work events
        """

        # Assume that we only need to scan once and no partial result will be returned.
        # I mean come on, how many after works can you plan?
        results = self.afterwork_dal.list_afterworks()
        events = print_afterwork_list(results)
        if 'Items' in results and len(results['Items']) > 0:
            return events
        else:
            return self.slack.private_slack_text("No upcoming after work.. Perhaps you want to create one?")

    def create_afterwork(self, command, event):
        """
        Creates a new after work event.
        :param command: parse this to get day, time and place
        :param event: the full lambda event
        :return:
        """

        trigger_id = event.get('trigger_id')
        self.slack.open_dialog(trigger_id=trigger_id, dialog=build_create_dialog())
        return self.slack.private_slack_text('Please follow the instructions in the dialog!')

    def join_afterwork_event(self, author, date):
        if date is not None:
            try:
                self.afterwork_dal.join_afterwork(date, author)
                return self.slack.private_slack_text("*Great!* You've joined the after work on {weekday}!".format(
                    weekday=parse_date_to_weekday(date)
                ))
            except:
                return self.slack.private_slack_text(
                    "*Oops!* I couldn't join you to that after work. Maybe you are already participating?")
        else:
            return self.slack.private_slack_text("*Sorry!* I couldn't find an after work that day.")

    def join_afterwork(self, command, event):
        """
        Join an already existing afterwork
        :param command: parse the date of the command
        :param event: the full lambda event
        :return:
        """
        author = get_user_name(event)
        date = get_date(command[1])
        return self.join_afterwork_event(author, date)


    def leave_afterwork_event(self, author, date):
        if date is not None:
            try:
                if self.afterwork_dal.leave_afterwork(date, author):
                    return self.slack.private_slack_text(
                        "*Done!* You are now removed from the after work on {weekday}!".format(
                            weekday=parse_date_to_weekday(date)
                        ))
                else:
                    return self.slack.private_slack_text("*Oops!* Are you really joined to that after work?")
            except:
                return self.slack.private_slack_text("Something went horribly wrong")

        return "Couldn't find any after work on that day."

    def leave_afterwork(self, command, event):
        """
        Leave an upcoming after work event
        :param command: used to parse the date
        :param event: the full lambda event
        :return:
        """
        author = get_user_name(event)
        date = get_date(command[1])
        return self.leave_afterwork_event(author, date)


    def delete_afterwork(self, command, event):
        """
        Try to delete an after work event
        :param command: the input command given
        :param event: the full lambda event
        :return:
        """
        author = get_user_name(event)
        date = get_date(command[1])

        if date is not None:
            try:
                self.afterwork_dal.delete_afterwork(date, author)
                self.slack.send_public_message(
                    text="The after work on {date} has been cancelled, sorry!".format(
                        date=parse_date_to_weekday(date)
                    ),
                    username=os.environ['botName']
                )
                return self.slack.private_slack_text("*Gotcha*! After work event deleted.")
            except Exception as e:
                self.logger.error(e)
                return self.slack.private_slack_text("*Sorry!* I was unable to remove you from the after work event.")
        else:
            return self.slack.private_slack_text("*Oops!* That date seems incorrect!")

    def suggest_afterwork(self, command, event):
        area = "".join(command[1:])
        suggestions = self.google_places.get_suggestions(area)

        return_value = {
            'text': 'Suggestions for {place}'.format(place=area),
            'attachments': []
        }

        places = sorted(suggestions['results'], key=lambda p: p.get('rating', None), reverse=True)

        for p in places[:5]:
            return_value['attachments'].append(Place(p).format_attachment())

        if not return_value['attachments']:
            return self.slack.private_slack_text('No suggestions found for {area}'.format(area=area))

        return return_value

    def todays_afterwork(self):
        """
        Runs automatically on a cloudwatch schedule each day to look for any after work events today
        :return: A message in the slack channel notifying anyone of an upcoming after work event
        """
        afterwork = self.afterwork_dal.get_afterwork(datetime.today().strftime("%Y-%m-%d"))

        if afterwork is not None:
            event = print_afterwork_today(afterwork)

            try:
                self.slack.send_public_message(
                    text=event,
                    username=os.environ['botName']
                )
            except Exception as e:
                self.logger.error(e)

    def create_afterwork_from_event(self, date, place_id, time, author, channel_id):
        place = self.google_places.get_place_information(place_id)
        try:
            self.afterwork_dal.insert_afterwork(
                date=date,
                place=place.name(),
                place_id=place_id,
                afterwork_time=time,
                author=author,
                channel_id=channel_id
            )

            self.logger.info('Created a new after work from suggestion')
            full_place = "{name} at {address}".format(name=place.name(), address=place.address())
            self.slack.send_public_message(
                text=print_afterwork_created(author, get_date(date), full_place),
                username=os.environ['botName'])

            return {}
        except:
            self.logger.error('Something went horribly wrong')
            return {
                'errors': [
                    {
                        'name': 'afterwork_day',
                        'error': 'Sorry this day seems occupied'
                    }
                ]
            }

    def handle_interactive_event(self, payload):
        parsed_payload = json.loads(payload)
        callback_id = parsed_payload.get('callback_id')
        event_type = parsed_payload.get('type', None)
        print(parsed_payload)

        print("got type {type}".format(type=event_type))

        if event_type == 'interactive_message':
            trigger_id = parsed_payload.get('trigger_id')
            actions = parsed_payload.get('actions')
            place_id = actions[0]['value']
            author = get_user_name_from_event(parsed_payload.get('user'))

            if callback_id == 'create_afterwork':
                place = self.google_places.get_place_information(place_id)
                dialog = place.build_place_dialog()
                self.slack.open_dialog(trigger_id=trigger_id, dialog=dialog)
                return self.slack.private_slack_text("We're creating your afterwork now, please use the dialog!")

            elif callback_id == 'handle_afterwork':
                action = actions[0]['value'].split('|')

                if action[0] == 'join_afterwork':
                    return self.join_afterwork_event(author, action[1])

                elif action[0] == 'leave_afterwork':
                    return self.leave_afterwork_event(author, action[1])

                return self.slack.private_slack_text('Well this is awkward, something weird happened')

        elif event_type == 'dialog_submission':
            submission = parsed_payload.get('submission')
            date = get_date(submission['afterwork_day'])
            time = submission['afterwork_time']

            channel_id = self.slack.get_channel_id()
            place_id = None

            if callback_id is not None:
                split_callback = callback_id.split('|')

                if split_callback[0] == 'create_afterwork_dialog':
                    place_id = submission.get('afterwork_place')

                elif split_callback[0] == 'create_afterwork_suggest':
                    place_id = split_callback[1]

                return self.create_afterwork_from_event(
                    date=date,
                    place_id=place_id,
                    time=time,
                    author=author,
                    channel_id=channel_id
                )

import boto3
import calendar
import logging
import os
import time

from boto3.dynamodb.conditions import Attr
from datetime import datetime, timedelta
from botocore import exceptions
from slacker import Slacker


class Afterwork:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        self.dynamodb = boto3.resource('dynamodb')
        self.afterwork_table = self.dynamodb.Table(os.environ['tableName'])

        self.slack = Slacker(os.environ['apiKey'])

        self.valid_commands = ['list', 'create', 'join', 'leave', 'delete']

    @staticmethod
    def __private_slack_text(text):
        return {
            "text": text
        }

    @staticmethod
    def __get_user_name(user):
        return "<@" + user['user_id'] + "|" + user['user_name'] + ">"

    @staticmethod
    def __is_day_formatted_as_date(day):
        try:
            datetime.strptime(day, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    @staticmethod
    def __get_next_weekday_as_date(weekday_number):
        start = datetime.strptime(datetime.now().strftime("%Y-%m-%d"), '%Y-%m-%d')
        day = timedelta((7 + weekday_number - start.weekday()) % 7)

        return (start + day).strftime("%Y-%m-%d")

    @staticmethod
    def __parse_date_to_weekday(date):
        return calendar.day_name[datetime.strptime(date, "%Y-%m-%d").weekday()]

    def __get_channel_id(self):
        channel_list = self.slack.channels.list()

        channel_id = 0

        for channel in channel_list.body['channels']:
            if channel['name'] == os.environ['channelName']:
                channel_id = channel['id']
                break

        return channel_id

    def __get_day_number(self, weekday_name):
        weekday = weekday_name.lower().capitalize()

        try:
            # User should be able to write tuesday or tue, both should work
            if len(weekday) is 3:
                operator = '%a'
            else:
                operator = '%A'

            day_num = time.strptime(weekday, operator).tm_wday

            if 0 <= day_num < 5:
                return day_num
        except ValueError:
            self.logger.info("Invalid weekday specified: {weekday}".format(
                weekday=weekday
            ))
            return None

        return None

    def __get_date(self, date):
        if self.__is_day_formatted_as_date(date):
            # Make sure date is in the future
            if datetime.today() >= datetime.strptime(date, "%Y-%m-%d"):
                return None

            weekday_name = self.__parse_date_to_weekday(date)
            day_number = self.__get_day_number(weekday_name)
            if day_number is not None:
                return date
        else:
            day_number = self.__get_day_number(date)
            if day_number is not None:
                return self.__get_next_weekday_as_date(day_number)

        return None

    def parse_command(self, command, event):
        """
        Parses the input command given from the slack slash command
        :param command: the command to be parsed
        :param event: the full lambda event
        :return: the action done or error if incorrect command was specified
        """
        if command == "":
            return self.__private_slack_text(
                """No command given, Possible commands are:
                \nlist \ncreate <day> <time> <place>\njoin <day>\nleave <day>\ndelete <day>""")
        elif command.split(" ")[0] in self.valid_commands:
            operation = command.split(" ")

            action = getattr(self, operation[0] + "_afterwork")
            return action(operation, event)

        else:
            return self.__private_slack_text(
                """Incorrect command specified. Possible commands are:
                \nlist \ncreate <day> <time> <place>\njoin <day>\nleave <day>\ndelete <day>""")

    def list_afterwork(self, command, event):
        """
        Gets a list of after work events
        :param command: Not used
        :param event: Not used
        :return: A slack message containing the upcoming after work events
        """

        # Assume that we only need to scan once and no partial result will be returned.
        # I mean come on, how many after works can you plan?
        results = self.afterwork_table.scan(
            FilterExpression=Attr('Date').gte(datetime.now().strftime("%Y-%m-%d"))
        )

        if 'Items' in results and len(results['Items']) > 0:
            events = "Upcoming after work: \n"
            for item in results['Items']:
                weekday = datetime.strptime(item['Date'], "%Y-%m-%d").weekday()

                events += "*" + calendar.day_name[weekday] + "*"

                if 'Time' in item:
                    events += " at *" + item['Time'] + "*"

                if 'Location' in item:
                    events += " by *" + item['Location'] + "*"

                events += " started by *" + item['Author'] + "*"

                if 'Participants' in item and len(item['Participants']) > 0:
                    events += "\n *Participants:* \n"
                    for participant in item['Participants']:
                        events += participant + "\n"
                else:
                    events += "\nNo one is participating in this after work, *yet...*"

                events += "\n To join type */afterwork join %s*" % calendar.day_name[weekday].lower()
                events += "\n"
            return self.__private_slack_text(events)
        else:
            return self.__private_slack_text("No upcoming after work.. Perhaps you want to create one?")

    def create_afterwork(self, command, event):
        """
        Creates a new after work event.
        :param command: parse this to get day, time and place
        :param event: the full lambda event
        :return:
        """
        day = command[1]

        try:
            afterwork_time = command[2]
        except IndexError:
            afterwork_time = "17:30"

        if len(command) > 3:
            place = " ".join(command[3:])
        else:
            place = 'Unspecified location'

        channel_id = self.__get_channel_id()
        author = self.__get_user_name(event)
        date = self.__get_date(day)

        self.logger.info(date)

        if date is not None:
            try:
                self.afterwork_table.put_item(
                    Item={
                        'Date': date,
                        'Location': place,
                        'Time': afterwork_time,
                        'Author': author,
                        'Channel': channel_id,
                        'Participants': [author]
                    },
                    ConditionExpression="attribute_not_exists(#d)",
                    ExpressionAttributeNames={
                        '#d': 'Date'
                    }
                )
            except exceptions.ClientError as e:
                self.logger.error(e)
                return self.__private_slack_text(
                    "Couldn't create after work. It seems as if there is already an after work planned that day.")

            self.logger.info('Created a new after work')
            self.slack.chat.post_message(
                text="Hi! {author} created an after work! \n *{weekday} ({date})* at *{place}* \n To join type */afterwork join {date}* or */afterwork join {weekday}* if is within this or next week.".format(
                    author=author, weekday=self.__parse_date_to_weekday(date), date=date, place=place,
                ),
                channel=channel_id,
                username=os.environ['botName']
            )
            return self.__private_slack_text(
                "*Sweet*! After work event created!")
        else:
            return self.__private_slack_text(
                "You cannot create an afterwork on that day! Valid days are monday to friday (today or in the future)")

    def join_afterwork(self, command, event):
        """
        Join an already existing afterwork
        :param command: parse the date of the command
        :param event: the full lambda event
        :return:
        """
        author = self.__get_user_name(event)
        date = self.__get_date(command[1])

        if date is not None:
            try:
                self.afterwork_table.update_item(
                    Key={
                        'Date': date
                    },
                    UpdateExpression="SET Participants = list_append(Participants, :i)",
                    ConditionExpression="NOT contains (Participants, :iStr)",
                    ExpressionAttributeValues={
                        ':i': [author],
                        ':iStr': author
                    },
                    ReturnValues="UPDATED_NEW"
                )

                return self.__private_slack_text("*Great!* You've joined the after work on {weekday}!".format(
                    weekday=self.__parse_date_to_weekday(date)
                ))
            except exceptions.ClientError as e:
                self.logger.error(e)
                return self.__private_slack_text(
                    "*Oops!* I couldn't join you to that after work. Maybe you are already participating?")
        else:
            return self.__private_slack_text("*Sorry!* I couldn't find an after work that day.")

    def leave_afterwork(self, command, event):
        """
        Leave an upcoming after work event
        :param command: used to parse the date
        :param event: the full lambda event
        :return:
        """
        author = self.__get_user_name(event)
        date = self.__get_date(command[1])

        if date is not None:

            result = self.afterwork_table.get_item(
                Key={
                    'Date': date
                }
            )

            if 'Item' in result and len(result['Item']) > 0:
                try:
                    result['Item']['Participants'].remove(author)
                except ValueError:
                    pass
                try:
                    self.afterwork_table.update_item(
                        Key={
                            'Date': date
                        },
                        UpdateExpression="SET Participants = :i",
                        ExpressionAttributeValues={
                            ':i': result['Item']['Participants']
                        },
                        ReturnValues="UPDATED_NEW"
                    )
                    return self.__private_slack_text("*Done!* You are now removed from the after work on {weekday}!".format(
                        weekday=self.__parse_date_to_weekday(date)
                    ))
                except exceptions.ClientError as e:
                    self.logger.error(e)
                    return self.__private_slack_text(
                        "*Oops!* Something went wrong when removing you from the after work!")
            else:
                return self.__private_slack_text("*Oops!* Are you really joined to that after work?")
        return "Couldn't find any after work on that day."

    def delete_afterwork(self, command, event):
        """
        Try to delete an after work event
        :param command: the input command given
        :param event: the full lambda event
        :return:
        """
        author = self.__get_user_name(event)
        date = self.__get_date(command[1])

        if date is not None:
            try:
                self.afterwork_table.delete_item(
                    Key={
                        'Date': date
                    },
                    ConditionExpression="Author = :i",
                    ExpressionAttributeValues={
                        ':i': author
                    }
                )
                self.slack.chat.post_message(
                    text="The after work on {date} has been cancelled, sorry!".format(
                        date=self.__parse_date_to_weekday(date)
                    ),
                    channel=self.__get_channel_id(),
                    username=os.environ['botName']
                )
                return self.__private_slack_text("*Gotcha*! After work event deleted.")
            except Exception as e:
                self.logger.error(e)
                return self.__private_slack_text("*Sorry!* I was unable to remove you from the after work event.")
        else:
            return self.__private_slack_text("*Oops!* That date seems incorrect!")

    def todays_afterwork(self):
        """
        Runs automatically on a cloudwatch schedule each day to look for any after work events today
        :return: A message in the slack channel notifying anyone of an upcoming after work event
        """
        response = self.afterwork_table.get_item(
            Key={
                'Date': datetime.today().strftime("%Y-%m-%d")
            }
        )

        if 'Item' in response and len(response['Item']) > 0:

            if 'Participants' in response['Item'] and len(response['Item']['Participants']) > 0:
                event = "*Reminder * Today there's an after work planned! \n"

                event += "*" + self.__parse_date_to_weekday(response['Item']['Date']) + "*"

                if 'Time' in response['Item']:
                    event += " at *" + response['Item']['Time'] + "*"

                if 'Location' in response['Item']:
                    event += " by *" + response['Item']['Location'] + "*"

                event += " started by *" + response['Item']['Author'] + "*"
                event += "\n *Participants:* \n"
                for participant in response['Item']['Participants']:
                    event += participant + "\n"

                event += "\n *Don't be late!*"
            else:
                event = "Hey guys, there was an after work planned for today, but no one wants to go :("

            try:
                self.slack.chat.post_message(
                    channel=self.__get_channel_id(),
                    text=event,
                    username=os.environ['botName']
                )
            except Exception as e:
                self.logger.error(e)

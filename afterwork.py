import boto3
from boto3.dynamodb.conditions import Attr, Key
from datetime import datetime, timedelta
import calendar
from botocore import exceptions

def default(x, e, y):
    try:
        return x()
    except e:
        return y

class Afterwork():
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.awtable = self.dynamodb.Table('afterworks')

        self.valid_commands = ['list', 'create', 'join', 'leave', 'delete']

        self.valid_days = ['mo', 'tue', 'wed', 'thur', 'fri',
                      'monday', 'tuesday', 'wednesday', 'thursday', 'friday']

    def parse_command(self, command, event):
        if command == "":
            return "No command given, Possible commands are: list, create <day> <time> <place>, join <day>, leave <day>, delete <day>"
        elif command.split(" ")[0] in self.valid_commands:
            operation = command.split(" ")

            action = getattr(self, operation[0] + "_afterwork")
            return action(operation, event)

        else:
            return self.private_slack_text(
                "Incorrect command specified, Possible commands are: list, create <day> <time> <place>, join <day>, leave <day>")

    def private_slack_text(self, text):
        return {
            "text" : text
        }

    def public_slack_text(self, text, channel):
        return {
            "response_type": "in_channel",
            "text": "<@" + channel + "|channel>: " + text
        }

    def is_day_valid(self, day_string):
        print(day_string)
        if day_string in self.valid_days:
            if day_string in ['mo', 'monday']:
                day_num = 0
            elif day_string in ['tue', 'tuesday']:
                day_num = 1
            elif day_string in ['wed', 'wednesday']:
                day_num = 2
            elif day_string in ['thur', 'thursday']:
                day_num = 3
            elif day_string in ['fri', 'friday']:
                day_num = 4
            return day_num
        else:
            return None

    def get_next_weekday(self, startdate, weekday):
        start = datetime.strptime(startdate, '%Y-%m-%d')
        day = timedelta((7 + weekday - start.weekday()) % 7)

        return (start + day).strftime("%Y-%m-%d")

    def list_afterwork(self, command, event):
        results = self.awtable.scan(
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
                        events += participant
                events += "\n"
            return self.private_slack_text(events)
        else:
            return self.private_slack_text("No upcoming after work.. Perhaps you want to create one?")

    def create_afterwork(self, command, event):

        day = command[1]
        time = default(lambda: command[2], IndexError, '17')
        place = default(lambda: " ".join(command[3:]), IndexError, 'Unspecified')
        channel = event['channel_id']

        author = self.__get_user_name(event)

        day_num = self.is_day_valid(day)
        if day_num is not None:
            date = self.get_next_weekday(datetime.now().strftime("%Y-%m-%d"), day_num)
            try:
                self.awtable.put_item(
                    Item={
                        'Date': date,
                        'Location': place,
                        'Time': time,
                        'Author': author,
                        'Participants' : [author]
                    },
                    ConditionExpression="attribute_not_exists(#d)",
                    ExpressionAttributeNames={
                        '#d': 'Date'
                    }
                )
            except exceptions.ClientError as e:
                return self.private_slack_text("Couldn't create after work. It seems as if there is already an after work planned that day.")

            return self.public_slack_text("Hi! %s created an after work on %s at %s by %s! To join type /afterwork join %s" % (author, date, time, place, day), channel)
        else:
            return self.private_slack_text("You cannot create an afterwork on that day! Valid days are monday to friday")

    def join_afterwork(self, command, event):
        day = command[1]
        author = self.__get_user_name(event)

        day_num = self.is_day_valid(day)
        if day_num is not None:
            date = self.get_next_weekday(datetime.now().strftime("%Y-%m-%d"), day_num)
            try:
                self.awtable.update_item(
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

                return self.private_slack_text("Great! You've joined the after work on " + day + "!")
            except Exception as e:
                return self.private_slack_text("I'm sorry, I couldn't join you to that after work. Perhaps you are already participating?")
        else:
            return self.private_slack_text("Sorry, I couldn't find an after work that day.")



    def leave_afterwork(self, command, event):
        day = command[1]
        author = self.__get_user_name(event)

        day_num = self.is_day_valid(day)
        if day_num is not None:
            date = self.get_next_weekday(datetime.now().strftime("%Y-%m-%d"), day_num)

            result = self.awtable.get_item(
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
                    self.awtable.update_item(
                        Key={
                            'Date': date
                        },
                        UpdateExpression="SET Participants = :i",
                        ExpressionAttributeValues={
                            ':i': result['Item']['Participants']
                        },
                        ReturnValues="UPDATED_NEW"
                    )
                    return self.private_slack_text("You are now removed from the after work!")
                except Exception:
                    return self.private_slack_text("Oops. Something went wrong when removing you from the after work!")
            else:
                return self.private_slack_text("Are you really joined to that after work?")
        return "Couldn't find any after work on that day."

    def delete_afterwork(self, command, event):
        day = command[1]
        author = self.__get_user_name(event)
        channel = event['channel_id']

        day_num = self.is_day_valid(day)
        if day_num is not None:
            date = self.get_next_weekday(datetime.now().strftime("%Y-%m-%d"), day_num)
            try:
                self.awtable.delete_item(
                    Key={
                        'Date': date
                    },
                    ConditionExpression="Author = :i",
                    ExpressionAttributeValues={
                        ':i' : author
                    }
                )
                return self.public_slack_text("The after work on %s has now been cancelled, sorry!" % day, channel)
            except Exception as e:
                return self.private_slack_text(e)
        else:
            return self.private_slack_text("That after work doesn't seem to exist")

    def __get_user_name(self, event):
        return "<@" + event['user_id'] + "|" + event['user_name'] + ">"
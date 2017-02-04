import boto3
from boto3.dynamodb.conditions import Attr, Key
from datetime import datetime, timedelta

class Afterwork():
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.awtable = self.dynamodb.Table('afterworks')

        self.valid_commands = ['list', 'create', 'join', 'leave']

        self.valid_days = ['mo', 'tue', 'wed', 'thur', 'fri',
                      'monday', 'tuesday', 'wednesday', 'thursday', 'friday']

    def parse_command(self, command, event):
        if command == "":
            return "No command given, Possible commands are: list, create <day> <time> <place>, join <day>, leave <day>"
        elif command.split(" ")[0] in self.valid_commands:
            operation = command.split(" ")

            action = getattr(self, operation[0] + "_afterwork")
            return action(operation, event)

        else:
            return self.slack_text(
                "Incorrect command specified, Possible commands are: list, create <day> <time> <place>, join <day>, leave <day>")

    def slack_text(self, text):
        return {
            "text" : text
        }

    def is_day_valid(self, day_string):
        print(day_string)
        if day_string in self.valid_days:
            if day_string in ['mo', 'monday']:
                day_num = 0
            elif day_string in ['tu', 'tuesday']:
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
                events += "*" + item['Date'] + "*"

                if 'Time' in item:
                    events += " at *" + item['Time'] + "*"

                if 'Location' in item:
                    events += " by *" + item['Location'] + "*"

                events += " started by *" + item['Author'] + "*"

                if 'Participants' in item:
                    events += "\n *Participants:* \n"
                    for participant in item['Participants']:
                        events += participant
                events += "\n"
            return self.slack_text(events)
        else:
            return self.slack_text("No upcoming after work.. Perhaps you want to create one?")

    def create_afterwork(self, command, event):

        day = command[1]
        time = command[2]
        place = command[3]
        author = "<@" + event['user_id'] + "|" + event['user_name'] + ">"

        day_num = self.is_day_valid(day)
        if day_num is not None:
            date = self.get_next_weekday(datetime.now().strftime("%Y-%m-%d"), day_num)

            self.awtable.put_item(
                Item={
                    'Date': date,
                    'Location': place,
                    'Time': time,
                    'Author': author,
                    'Participants' : [author]
                }
            )

            return self.slack_text("You created an after work on %s at %s" % (date, place))
        else:
            return self.slack_text("You cannot create an afterwork on that day!")

    def join_afterwork(self, command, event):
        return self.slack_text("Join a certain afterwork")

    def leave_afterwork(self, command, event):
        return self.slack_text("Leave a certain afterwork")

    def delete_afterwork(self, command, event):
        return self.slack_text("Delete an upcoming after work... for reasons...")
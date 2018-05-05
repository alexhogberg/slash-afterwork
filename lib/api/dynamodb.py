import logging
import os
from datetime import datetime

import boto3
from botocore import exceptions
from boto3.dynamodb.conditions import Attr


class OauthDAL:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.dynamodb = boto3.resource('dynamodb', 'eu-west-1')
        self.oauth_table = self.dynamodb.Table('authorizedApps')

    def addApp(self, team_id, bot_access_token, access_token):
        self.logger.info('Adding a new team {team_id}'.format(team_id=team_id))
        item = {
            'TeamId': team_id,
            'BotAccessToken': bot_access_token,
            'AccessToken': access_token
        }

        try:
            self.oauth_table.put_item(
                Item=item
            )
        except exceptions.ClientError as e:
            self.logger.error(e)
            raise e

    def getTokenForTeam(self, team_id):
        response = self.oauth_table.get_item(
            Key={
                'TeamId': team_id
            }
        )

        if 'Item' in response and len(response['Item']) > 0:
            return response['Item']['BotAccessToken']
        else:
            return None


class AfterworkDAL:
    def __init__(self, team_id):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.dynamodb = boto3.resource('dynamodb', 'eu-west-1')
        self.afterwork_table = self.dynamodb.Table(os.environ['tableName'])
        self.team_id = team_id

    def get_formatted_date(self, date):
        return self.team_id + '|' + date

    def insert_afterwork(self, date, place, place_id, afterwork_time, author, channel_id):
        self.logger.info('Trying to create afterwork at {day} for user {author} in {team}'.format(
            day=date,
            author=author,
            team=self.team_id
        ))
        item = {
            'Date': self.get_formatted_date(date),
            'TeamId': self.team_id,
            'Location': place,
            'Time': afterwork_time,
            'Author': author,
            'Channel': channel_id,
            'Participants': [author]
        }

        if place_id is not None:
            item['PlaceId'] = place_id

        try:
            self.afterwork_table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(#d)",
                ExpressionAttributeNames={
                    '#d': 'Date'
                }
            )
        except exceptions.ClientError as e:
            self.logger.error(e)
            raise e

    def list_afterworks(self):
        try:
            results = self.afterwork_table.scan(
                FilterExpression=Attr('Date').begins_with(self.team_id)
            )
            return results

        except exceptions.ClientError as e:
            raise e

    def get_afterwork(self, date):
        response = self.afterwork_table.get_item(
            Key={
                'Date': self.get_formatted_date(date)
            }
        )

        if 'Item' in response and len(response['Item']) > 0:
            return response
        else:
            return None

    def join_afterwork(self, date, author):
        self.logger.info('Trying to join afterwork at {day} for user {author} in {team}'.format(
            day=date,
            author=author,
            team=self.team_id
        ))
        try:
            self.afterwork_table.update_item(
                Key={
                    'Date': self.get_formatted_date(date)
                },
                UpdateExpression="SET Participants = list_append(Participants, :i)",
                ConditionExpression="NOT contains (Participants, :iStr)",
                ExpressionAttributeValues={
                    ':i': [author],
                    ':iStr': author
                },
                ReturnValues="UPDATED_NEW"
            )
        except exceptions.ClientError as e:
            raise e

    def leave_afterwork(self, date, author):
        self.logger.info('Trying to leave afterwork at {day} for user {author}'.format(
            day=date,
            author=author
        ))

        result = self.afterwork_table.get_item(
            Key={
                'Date': self.get_formatted_date(date)
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
                        'Date': self.get_formatted_date(date)
                    },
                    UpdateExpression="SET Participants = :i",
                    ExpressionAttributeValues={
                        ':i': result['Item']['Participants']
                    },
                    ReturnValues="UPDATED_NEW"
                )
                return True
            except exceptions.ClientError as e:
                self.logger.error(e)
                raise e
        else:
            return False

    def delete_afterwork(self, date, author):
        self.logger.info('Trying to delete afterwork at {day} for user {author}'.format(
            day=date,
            author=author
        ))
        try:
            self.afterwork_table.delete_item(
                Key={
                    'Date': self.get_formatted_date(date)
                },
                ConditionExpression="Author = :i",
                ExpressionAttributeValues={
                    ':i': author
                }
            )
        except Exception as e:
            raise e
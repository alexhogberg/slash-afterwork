import logging
import os
from datetime import datetime

import boto3
from botocore import exceptions
from boto3.dynamodb.conditions import Attr


class AfterworkDAL:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.dynamodb = boto3.resource('dynamodb', 'eu-west-1')
        self.afterwork_table = self.dynamodb.Table(os.environ['tableName'])

    def insert_afterwork(self, date, place, place_id, afterwork_time, author, channel_id):
        try:
            self.afterwork_table.put_item(
                Item={
                    'Date': date,
                    'Location': place,
                    'PlaceId': place_id,
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
            raise e

    def list_afterworks(self):
        try:
            results = self.afterwork_table.scan(
                FilterExpression=Attr('Date').gte(datetime.now().strftime("%Y-%m-%d"))
            )
            return results

        except exceptions.ClientError as e:
            raise e

    def get_afterwork(self, date):
        response = self.afterwork_table.get_item(
            Key={
                'Date': date
            }
        )

        if 'Item' in response and len(response['Item']) > 0:
            return response
        else:
            return None

    def join_afterwork(self, date, author):
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
        except exceptions.ClientError as e:
            raise e

    def leave_afterwork(self, date, author):
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
                return True
            except exceptions.ClientError as e:
                self.logger.error(e)
                raise e
        else:
            return False

    def delete_afterwork(self, date, author):
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
        except Exception as e:
            raise e
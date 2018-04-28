import os
from afterwork import Afterwork

os.environ['tableName'] = 'test'
os.environ['apiKey'] = 'test'

afterwork_handler = Afterwork()

def test_private_slack_message():
    assert afterwork_handler.private_slack_text("test") == {"text": "test"}

def test_get_user_name():
    assert afterwork_handler.get_user_name({'user_id': 'test', 'user_name': 'test'}) == "<@test|test>"

def test_is_day_formatted_as_date():
    assert afterwork_handler.is_day_formatted_as_date('Tue') == False
    assert afterwork_handler.is_day_formatted_as_date('2018-02-05') == True
    assert afterwork_handler.is_day_formatted_as_date(200) == False

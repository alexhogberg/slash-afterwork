# coding=utf8
from lib.utils.helpers import is_day_formatted_as_date, get_user_name


def test_get_user_name():
    assert get_user_name({'user_id': 'test', 'user_name': 'test'}) == "<@test|test>"


def test_is_day_formatted_as_date():
    assert is_day_formatted_as_date('Tue') is False
    assert is_day_formatted_as_date('2018-02-05') is True
    assert is_day_formatted_as_date(200) is False
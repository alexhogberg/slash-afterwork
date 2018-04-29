# coding=utf-8
from lib.utils.helpers import get_date


def test_get_date():
    get_date('tomorrow')
    get_date('next thursday')
    get_date('next Sunday')
    get_date('yesterday')
    get_date('last week')

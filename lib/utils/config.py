# coding=utf-8
import anyconfig
import os

class Config:
    def __init__(self):
        self.config = anyconfig.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'conf.yml'))

    def __getitem__(self, item):
        return self.config[item]

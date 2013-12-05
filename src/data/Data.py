#!/usr/bin/python -tt
'''
Created on Dec 4, 2013

@author: jdelgad
'''
import abc
import logging


class Data(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, data, parser):
        self.data = data
        self.parser = parser

        self.logger = logging.getLogger("automover2")

    @abc.abstractmethod
    def get_episode_name(self, show, season, episode):
        pass

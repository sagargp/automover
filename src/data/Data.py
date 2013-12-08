#!/usr/bin/python2.7 -tt
# coding=utf-8
"""
Created on Dec 4, 2013

@author: jdelgad
"""
import abc
import logging


class Data(object):
    """
   New style class
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, data, parser):
        """


        @rtype : object
        @type data: __builtin__.NoneType
        @type parser: parsers.EpGuidesParser.EpGuidesParser
        """
        self.data = data
        self.parser = parser

        self.logger = logging.getLogger("automover2")

    @abc.abstractmethod
    def get_episode_name(self, show, season, episode):
        """

        @rtype : object
        @param show:
        @param season:
        @param episode:
        """
        pass

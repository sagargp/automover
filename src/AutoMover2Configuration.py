#!/usr/bin/python -tt
# coding=utf-8
"""
Created on Dec 4, 2013

@author: jdelgad
"""
import json


class AutoMover2Configuration(object):
    """
    New style class

    """

    def __init__(self, configuration_file):
        self.config = json.load(open(configuration_file))

    @property
    def get_destination(self):
        """


        @type self: object
        @rtype : object
        @return: @rtype: list
        """
        return self.config["destination"]

    @property
    def get_patterns(self):
        """

        @return: @rtype: list
        """
        return self.config["patterns"]

    @property
    def get_exclusions(self):
        """

        @return: @rtype: list
        """
        return self.config["exclude"]

    @property
    def get_patterns(self):
        """

        @rtype : object
        @return: @rtype: list
        """
        return self.config["patterns"]

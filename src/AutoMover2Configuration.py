#!/usr/bin/python -tt
'''
Created on Dec 4, 2013

@author: jdelgad
'''
import ConfigParser


class AutoMoverConfiguration(ConfigParser.RawConfigParser):
    def __init__(self):
        ConfigParser.RawConfigParser.__init__(self)

        self.add_section('main')
        self.set('main', 'destination', 'test/dest/')

        self.add_section('patterns')
        self.set('patterns', 'pattern_1', '(.*)s(\d+)e(\d+).*(mkv|avi)')
        self.set('patterns', 'pattern_2',
                 '(.*)\.?(\d{1,2})(\d\d).*(mkv|avi)')
        self.set('patterns', 'exclude', '.*sample.*')

#!/usr/bin/python -tt
'''
Created on Dec 5, 2013

@author: jdelgad
'''
import sgmllib


class AutoMover2Parser(sgmllib.SGMLParser):
    def __init__(self, verbose):
        sgmllib.SGMLParser.__init__(self, verbose)

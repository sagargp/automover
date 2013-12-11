#!/usr/bin/python -tt
# coding=utf-8
"""
Created on Dec 5, 2013

@author: jdelgad
"""

import abc

class abstract_parser(object):
  """
  Abstract base class used for parsing data
  """
  __metaclass__ = abc.ABCMeta

  def __init__(self):
    """
    @rtype : object
    """
    pass

  @abc.abstractmethod
  def parse(self, data):
    """
    @rtype : object
    @param data:
    """
    pass

  @abc.abstractmethod
  def reset_data(self):
    """
    @rtype : object
    """
    pass

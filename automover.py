import re
from configuration import DummyConfigParser
from episode import Episode

class Automover(object):
  def __init__(self, configuration):
    if not isinstance(configuration, RawConfigParser):
      raise TypeError("configuration argument must be a RawConfigParser object")

  def process(self, filename):
    pass

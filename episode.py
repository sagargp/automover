import re
import os

class Episode(object):
  def __init__(self):
    self.series   = None
    self.season   = 0
    self.episode  = 0
    self.title    = None
  
  def __str__(self):
    return "%s S%02dE%02d %s" % (self.series, self.season, self.episode, self.title)

  @property
  def series(self):
    return self._series

  @series.setter
  def series(self, value):
    self._series = value

  @property
  def season(self):
    return self._season

  @season.setter
  def season(self, value):
    self._season = value

  @property
  def episode(self):
    return self._episode

  @episode.setter
  def episode(self, value):
    self._episode = value

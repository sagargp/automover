import re
import os

class Episode(object):
  def __init__(self, filename, logger):
    self.series   = 0
    self.season   = 0
    self.episode  = 0
    self.title    = None
    self.filename = filename
    self.logger   = logger
  
  def parse(self, library, searcher, patterns, cache=None):
    if type(patterns) is not list:
      raise TypeError("parse() takes a list of compiled regex patterns")

    self.logger.info("Parsing %s" % self.filename)
    match = None
    for pattern in patterns:
      try:
        search = pattern.search(self.filename)
      except AttributeError:
        self.logger.info("Compiling pattern: %s" % pattern)
        p = re.compile(pattern, flags=re.IGNORECASE)
        search = p.search(self.filename)

      if search is not None:
        match = search
        break

    if match:
      # extract info from the regex match
      groups = match.groups()

      self.logger.info("Looking up %s" % groups[0])
      show = self._library_lookup(library, groups[0])

      if show:
        season  = int(groups[1].lstrip("0"))
        episode = int(groups[2].lstrip("0"))

        self.logger.info("It's %s season %d, episode %d" % (show, season, episode))

        # look up the episode title online if needed
        self.title   = searcher.get_episode_name(show, season, episode)
        self.series  = show
        self.season  = season
        self.episode = episode
      else:
        self.logger.warning("Didn't find it!")
    else:
      self.debug.warning("Nothing matched for %s" % self.filename)
    return self

  def _library_lookup(self, library, name):
    name = name.replace(".", " ").lower().replace("the", "").strip()
    for series in library:
      x = series.lower().replace("the", "")
      if name.startswith(x):
        return series
    return None

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

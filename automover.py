import os
import re
from configuration import DummyConfigParser
from ConfigParser import RawConfigParser
from episode import Episode

class Automover(object):
  def __init__(self, configuration, library, searcher, logger):
    if not isinstance(configuration, RawConfigParser):
      raise TypeError("configuration argument must be a RawConfigParser object")

    self.library  = library
    self.searcher = searcher
    self.logger   = logger

    self.destination       = configuration.get("main", "destination")
    patterns               = [configuration.get("patterns", p) for p in configuration.options('patterns') if p.startswith('pattern')]
    self.compiled_patterns = [re.compile(p, flags=re.IGNORECASE) for p in patterns]
    self.exclude_pattern   = re.compile(configuration.get("patterns", "exclude"))

  def run(self, path):
    lines = []
    for root, subs, files in os.walk(path):
      for filename in files:
        if self.exclude_pattern.search(filename):
          continue
        match = None
        for pattern in self.compiled_patterns:
          search = pattern.search(filename)

          if search is not None:
            match = search
            break
        if match:
          path = "%s/%s" % (root, filename)
          episode = self.process(path)

          if episode.series:
            extension = filename.split('.')[-1]
            new_filename = "%s.%s" % (str(episode), extension)
            lines.append((path, new_filename))
            self.logger.info("Appended pair: %s" % str(lines[-1]))

  def process(self, filename):
    ret = Episode()
    self.logger.info("Parsing %s" % filename)

    match = None
    for pattern in self.compiled_patterns:
      search = pattern.search(filename)

      if search is not None:
        match = search
        break

    if match:
      # extract info from the regex match
      groups = match.groups()
      matched_series = groups[0].split('/')[-1]

      self.logger.info("Looking up %s in the library" % matched_series)
      show = self._library_lookup(self.library, matched_series)

      if show:
        season  = int(groups[1].lstrip("0"))
        episode = int(groups[2].lstrip("0"))

        self.logger.info("It's %s season %d, episode %d" % (show, season, episode))

        # look up the episode title online if needed
        ep_title    = self.searcher.get_episode_name(show, season, episode)

        ret.series  = show
        ret.season  = season
        ret.episode = episode
      else:
        self.logger.warning("Didn't find it!")
    else:
      self.debug.warning("Nothing matched for %s" % filename)
    return ret

  def _library_lookup(self, library, name):
    name = name.replace(".", " ").lower().replace("the", "").strip()
    for series in library:
      x = series.lower().replace("the", "")
      if name.startswith(x):
        return series
    return None

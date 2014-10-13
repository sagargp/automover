#!/usr/bin/python

import re
import os
import logging
import warnings

class File(object):
  def __init__(self, path, name):
    self._name   = name
    self._path   = path
    self._log    = logging.getLogger(__name__)
    self.title   = None
    self.season  = None
    self.episode = None
  
  def detect(self):
    m = re.match("([\w\.\s]*)(S(\d+)E(\d+)|(\d+)x(\d+))(.*)", self._name)
    if m: 
      title, season_group, s1, e1, s2, e2, _ = m.groups()
      d = {"name": self._name, "title": title, "season": None, "episode": None}
      if s1 and e1:
        d["season"]  = int(s1)
        d["episode"] = int(e1)
      elif s2 and e2:
        d["season"]  = int(s2)
        d["episode"] = int(e2)
      self._log.info("{title} S{season:0>2d}E{episode:0>2d}".format(**d))
      self.title   = d["title"]
      self.season  = d["season"]
      self.episode = d["episode"]
    else:
      warnings.warn("%s doesn't appear to be a valid TV show" % self._name)
      return None
    return self

  def find_movie_file(self):
    path = os.path.join(self._path, self._name)
    for f in os.listdir(path):
      if f.endswith(("mkv", "avi")) and "sample" not in f:
        return f
    return None

  def __str__(self):
    if self.title and self.season and self.episode:
      d = {"title": self.title, "season": self.season, "episode": self.episode}
      return "{title} S{season:0>2d}E{episode:0>2d}".format(**d)
    return self._name

  def __eq__(self, other):
    return self.title == other.title and self.season == other.season and self.episode == other.episode

  def __hash__(self):
    return hash(str(self))

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("path", action="store", help="The path to the root of all the files")
  args = parser.parse_args()

  log = logging.getLogger(__name__)
  logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")
  logging.captureWarnings(True)

  all_shows = {}
  for dir in os.listdir(args.path):
    f = File(args.path, dir).detect()
    if f:
      try:
        all_shows[f.title].add(f)
      except:
        all_shows[f.title] = set([f])

  log.info("-" * 20)
  log.info("Summary")
  log.info("-" * 20)

  for show, eps in all_shows.iteritems():
    for ep in eps:
      log.info("%s S%02dE%02d --> %s" % (ep.title.replace(".", " ").strip(), ep.season, ep.episode, ep.find_movie_file()))

#!/usr/bin/python
import re
import os
import logging
import warnings
import tvdb_api
import tvdb_exceptions
from collections import OrderedDict

class File(object):
  def __init__(self, path, name):
    self._name    = name
    self._path    = path
    self._log     = logging.getLogger(__name__)
    self.fullpath = os.path.join(path, name)
    self.title    = None
    self.season   = None
    self.episode  = None
  
  def detect(self):
    m = re.match("([\w\.\s]*)(S(\d+)E(\d+)|(\d+)x(\d+))(.*)", self._name)
    if m: 
      title, season_group, s1, e1, s2, e2, _ = m.groups()
      d = {"name": self._name, "title": title.replace(".", " ").strip(), "season": None, "episode": None}
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
      if f.endswith(("mkv", "avi", "mp4")) and "sample" not in f:
        return f
    return None

  def __str__(self):
    if self.title and self.season and self.episode:
      d = {"title": self.title.replace(".", " ").strip(), "season": self.season, "episode": self.episode}
      return "{title} S{season:0>2d}E{episode:0>2d}".format(**d)
    return _name

  def __eq__(self, other):
    return self.title == other.title and self.season == other.season and self.episode == other.episode

  def __hash__(self):
    return  hash(str(self))

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("--verbose", "-v", action="store_true", default=False, help="Print out debug info")
  parser.add_argument("path", action="store", help="The path to the root of all the files")
  parser.add_argument("dest", action="store", help="The path to destination of the files")
  args = parser.parse_args()

  log = logging.getLogger(__name__)
  logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
  logging.captureWarnings(True)

  if not args.verbose:
    log.disabled = True

  problems  = []
  TVDB      = tvdb_api.Tvdb()
  shopts    = OrderedDict()
  all_shows = {}

  shopts["cd \"%s\"" % args.path] = None
  shopts["mkdir -p done"] = None

  for _dir in os.listdir(args.path):
    movie_file = File(args.path, _dir).detect()
    if movie_file:
      try: all_shows[movie_file.title].add(movie_file)
      except: all_shows[movie_file.title] = set([movie_file])

  for title, eps in all_shows.iteritems():
    results = TVDB.search(title.replace(".", " "))
    if len(results) == 0:
      log.warn("Show not found! Giving up. (%s)" % title)
      problems.append(eps.pop().fullpath)
      continue

    if len(results) > 1:
      log.warn("Multiple matches for %s!" % title)
      for result in results:
        log.warn(" * %s" % result["seriesname"])
      log.warn("Going with the first one, which is %s" % (results[0]["seriesname"]))

    proper_name = results[0]["seriesname"]
    show = TVDB[proper_name]
    for ep in eps:
      try:
        episode_name  = show[ep.season][ep.episode]["episodename"]
        src_file      = os.path.join(ep._name, ep.find_movie_file())
        dest_path     = os.path.join(args.dest, proper_name, "Season %d" % ep.season)
        dest_filename = "%s S%02dE%02d %s%s" % (proper_name, ep.season, ep.episode, episode_name, os.path.splitext(src_file)[-1])

        if not os.path.exists(dest_path):
          shopts["\nmkdir -p \"%s\"" % dest_path] = None
        shopts["cp -lbv \"%s\" \"%s\"" % (src_file, os.path.join(dest_path, dest_filename))] = None
        shopts["mv -v \"%s\" done" % ep._name] = None

      except tvdb_exceptions.tvdb_episodenotfound:
        log.warn("Episode not found! Giving up. (%s)" % (proper_name, ep.fullpath))
        problems.append(title)
      #except Exception, e:
      #  log.warn("Unexpected error! (%s): %s" % (ep.fullpath, str(e)))
      #  problems.append(ep.fullpath)

  print "#!/bin/bash"
  print
  print "# Problem files:"
  for f in problems:
    print "#  * ", f

  print
  print "\n".join(shopts.keys())

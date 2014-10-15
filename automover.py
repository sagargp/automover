#!/usr/bin/python
import re
import os
import logging
import warnings
import tvdb_api
import tvdb_exceptions
from collections import OrderedDict

class EpisodeFileRepr(object):
  def __init__(self, path, name):
    self._log       = logging.getLogger(__name__)
    self._name      = name
    self._path      = path
    self._file_info = None
  
  def fetch_episode_name(self, tvdb_instance):
    search_results = tvdb_instance.search(self._file_info["title"])
    if not search_results:
      raise tvdb_exceptions.tvdb_shownotfound, "Show not found! Giving up. (%s)" % self._file_info["name"]
    if len(search_results) > 1:
      log.warn("Multiple matches for %s:" % self._file_info["title"])
      for result in search_results:
        log.warn(" * %s" % result["seriesname"])
      log.warn("Going with the first one, which is %s" % (search_results[0]["seriesname"]))
    proper_name                    = search_results[0]["seriesname"]
    self._file_info["title"]       = proper_name
    self._file_info["episodename"] = tvdb_instance[proper_name][self._file_info["season"]][self._file_info["episode"]]["episodename"]
  
  def get_move_command(self, dest):
    source        = self.find_movie_file()
    dest_path     = os.path.join(dest, self._file_info["title"], "Season %d" % self._file_info["season"])
    dest_filename = "%s%s" % (self._file_info["episodename"], os.path.splitext(source)[-1])
    destination   = os.path.join(dest_path, dest_filename)
    return 'cp -lbv "{source}" "{destination}"'.format(source=source, destination=destination)

  def get_original_path(self):
    return os.path.join(self._path, self._name)

  def get_info(self):
    if self._file_info:
      return self._file_info

    m = re.match("([\w\.\s]*)(S(\d+)E(\d+)|(\d+)x(\d+))(.*)", self._name)
    if m: 
      title, season_group, s1, e1, s2, e2, _ = m.groups()
      self._file_info = {"name": self._name, "title": title.replace(".", " ").strip(), "season": None, "episode": None}
      if s1 and e1:
        self._file_info["season"]  = int(s1)
        self._file_info["episode"] = int(e1)
      elif s2 and e2:
        self._file_info["season"]  = int(s2)
        self._file_info["episode"] = int(e2)
      self._log.info(str(self))
      return self._file_info
    else:
      warnings.warn("%s doesn't appear to be a valid TV show" % self._name)
      return None

  def find_movie_file(self):
    path = os.path.join(self._path, self._name)
    if os.path.isdir(path):
      for f in os.listdir(path):
        if f.lower().endswith(("mkv", "avi", "mp4")) and "sample" not in f.lower():
          return os.path.join(self._path, f)
    else:
      if path.lower().endswith(("mkv", "avi", "mp4")) and "sample" not in path.lower():
        return path
    return None

  def __str__(self):
    if self._file_info:
      try:
        return "{title} S{season:0>2d}E{episode:0>2d} {episodename}".format(**self._file_info)
      except:
        return "{title} S{season:0>2d}E{episode:0>2d}".format(**self._file_info)
    return None

  def __eq__(self, other):
    return self._file_info == other._file_info

  def __hash__(self):
    return  hash(str(self))

def find_episode_files(path):
  episodes = []
  for f in os.listdir(path):
    episode = EpisodeFileRepr(path, f)
    episode.get_info()
    if episode in episodes:
      first = episodes.index(episode)
      if os.stat(episodes[first].find_movie_file()).st_size > os.stat(episode.find_movie_file()).st_size:
        continue
    episodes.append(episode)
  return episodes

def main():
  TVDB   = tvdb_api.Tvdb()
  shopts = OrderedDict()

  # commands
  shopts['#!/bin/bash']         = None
  shopts['cd "%s"' % args.path] = None

  # get files
  all_episodes = find_episode_files(args.path)

  # get all the ep names from TVDB
  for episode in all_episodes:
    episode.fetch_episode_name(TVDB)
    episode.moved = True

  # generate move commands
  for episode in all_episodes:
    move_command = episode.get_move_command(args.dest)
    shopts[move_command] = None
  
  # clean up
  shopts['mkdir -p finished/']  = None
  for episode in all_episodes:
    try:
      if episode.moved:
        shopts['mv -v "%s" finished/' % episode.find_movie_file()] = None
    except:
      pass

  print "\n".join(shopts.keys())

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("--verbose", "-v", action="store_true", default=False, help="Print out debug info")
  parser.add_argument("--force", action="store", help="Assume every file is the show given here")
  parser.add_argument("path", action="store", help="The path to the root of all the files that need to be renamed")
  parser.add_argument("dest", action="store", help="The path to destination of the files after they've been renamed")
  args = parser.parse_args()

  log = logging.getLogger(__name__)
  logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
  logging.captureWarnings(True)

  if not args.verbose:
    log.disabled = True

  main()

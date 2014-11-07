#!/usr/bin/python
import re
import os
import logging
import warnings
import tvdb_api
import tvdb_exceptions
from collections import OrderedDict

class EpisodeFileRepr(object):
  def __init__(self, path, name, transform=False):
    self._log     = logging.getLogger(__name__)
    self._name    = name
    self._path    = path

    # might throw an exception
    self._file_info = self._get_info(transform)

  def move(self, tvdb_instance, dest, cleanup=None):
    self._fetch_episode_name(tvdb_instance)

    og_path       = self.get_original_path()
    dest_dir      = os.path.join(dest, self._file_info["title"], "Season %d" % self._file_info["season"])
    dest_filename = "%s%s" % (str(self), os.path.splitext(og_path)[-1])
    dest_file     = os.path.join(dest_dir, dest_filename)

    print '# %s' % str(self)
    if not os.path.exists(dest_dir):
      self._log.info("Making destination directory %s" % dest_dir)
      print 'mkdir -p "%s"' % dest_dir
    self._log.info("Moving %s to %s" % (og_path, dest_file))

    print 'cp -blv "%s" "%s"' % (og_path, dest_file)

    if cleanup:
      print 'mv -v "%s" "%s"' % (os.path.join(self._path, self._name), cleanup)
    print
  
  def _fetch_episode_name(self, tvdb_instance):
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
  
  def _get_info(self, transform=None):
    m = re.match("([\w\.\s]*)(S(\d+)E(\d+)|(\d+)x(\d+))(.*)", self._name)
    if m: 
      title, season_group, s1, e1, s2, e2, _ = m.groups()

      if transform:
        for transformation in transform:
          try:
            this, that = transformation.split("=")
          except:
            self._log.warn("Bad transformation string! Needs to be in A=B format.")
            continue

          if this in title:
            self._log.info("Transforming %s to %s..." % (this, that))

            new_title = title.replace(this, that)
            self._log.info("%s became %s" % (title, new_title))
            title = new_title

      self._file_info = {"name": self._name, "title": title.replace(".", " ").strip(), "season": None, "episode": None}
      if s1 and e1:
        self._file_info["season"]  = int(s1)
        self._file_info["episode"] = int(e1)
      elif s2 and e2:
        self._file_info["season"]  = int(s2)
        self._file_info["episode"] = int(e2)
      return self._file_info
    else:
      raise TypeError, "%s doesn't appear to be a valid TV show" % self._name

  def get_original_path(self):
    path = os.path.join(self._path, self._name)
    self._log.info("Finding movie file for %s" % path)
    if os.path.isdir(path):
      for f in os.listdir(path):
        if f.lower().endswith(("mkv", "avi", "mp4")) and "sample" not in f.lower():
          return os.path.join(path, f)
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
    return str(self) == str(other)

  def __hash__(self):
    return  hash(str(self))

def main(args):
  log  = logging.getLogger(__name__)
  TVDB = tvdb_api.Tvdb()

  print "#!/bin/bash"
  print

  # get all the episodes in args.path
  all_eps = []
  for node in os.listdir(args.path):
    try:
      e = EpisodeFileRepr(args.path, node, args.transform)
      og_path = e.get_original_path()
      log.info("Found %s --> %s" % (str(e), og_path))
      if e in all_eps:
        log.info("Detected duplicate!")
        first = all_eps[all_eps.index(e)]
        if os.path.getsize(og_path) > os.path.getsize(first.get_original_path()):
          log.info("Removing the smaller of the two matches")
          all_eps.remove(e)
          all_eps.append(e)
      else:
        all_eps.append(e)
    except:
      pass

  print "# move everything here after we're done"
  print 'mkdir -p "%s"' % args.cleanup_dir
  print 

  print "# do the move!"

  # move
  for episode in all_eps:
    try:
      episode.move(TVDB, args.dest, args.cleanup_dir)
    except tvdb_exceptions.tvdb_shownotfound, e:
      log.warn(str(e))

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("--verbose", "-v", action="store_true", default=False, help="Print out debug info")
  parser.add_argument("--transform", "-t", metavar="A=B", action="append", help="Transform A into B before doing TV show detection")
  parser.add_argument("--cleanup-dir", "-c", metavar="DIR", action="store", help="Where to move the files after copying them to their destination", default="./finished")
  parser.add_argument("path", action="store", help="The path to the root of all the files that need to be renamed")
  parser.add_argument("dest", action="store", help="The path to destination of the files after they've been renamed")
  args = parser.parse_args()

  logging.addLevelName(logging.WARNING, "\033[1;31mWARN\033[1;0m")
  logging.addLevelName(logging.INFO, "\033[1;33mINFO\033[1;0m")

  log = logging.getLogger(__name__)
  logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
  logging.captureWarnings(True)

  if not args.verbose:
    log.disabled = True

  main(args)

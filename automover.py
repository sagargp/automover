import re
import os
import logging
import ConfigParser
from datetime import datetime
from parsers import *
from searchers import *

class Automover:
  def __init__(self, search_path, config, searcher, logger):
    """
    Create a new Automover object that will look under search_path.
    """
    self.search_path = os.path.abspath(search_path)
    self.config      = config
    self.searcher    = searcher
    self.logger      = logger

    self.move_command = "mv -vn"

    self.logger.info("Initializing...")

    patterns = [p for p in self.config.options('patterns') if p.startswith('pattern')]

    self.logger.info("Compiling regular expressions")
    self.patterns = [re.compile(self.config.get('patterns', p), flags=re.IGNORECASE) for p in patterns]
    self.exclude = re.compile(self.config.get('patterns', 'exclude'), flags=re.IGNORECASE)

    self.show_list = []
    for show in os.listdir(self.config.get('main', 'destination')):
      self.show_list.append(show)

    self.logger.info("Saved list of %d shows" % len(self.show_list))
    self.logger.info("Done initializing")

  def get_move_script(self):
    """
    Run Automover.
    """
    self.logger.info("Finding files in %s" % self.search_path)
    all_files = []
    for root, subs, files in os.walk(self.search_path):
      for filename in files:
        all_files.append((root, filename))

    lines = []
    lines.append('#!/bin/bash\n')
    for src, dest in self._filter_files(all_files):
      lines.append(self._move(src, dest))
    return '\n'.join(lines)

  def _move(self, src, dest):
    return '%s "%s" "%s"' % (self.move_command, src, dest)

  def _rename(self, show, season, episode, episode_title, extension):
    return "%s S%02dE%02d %s.%s" % (show, season, episode, episode_title, extension)

  def _filter_files(self, full_list):
    """
    Given a list of files, filter out the ones that aren't media files and 
    match them to episode names.
    """
    matched_files = []
    destination_root = os.path.abspath(self.config.get('main', 'destination'))
    
    self.logger.info("Filtering files")
    for root, filename in full_list:
      match = self._match(filename)
      if match:
        self.logger.info("Looking for %s" % filename)
        # extract info from the regex match
        groups  = match.groups()
        show    = self._get_show_name(groups[0])
        season  = int(groups[1].lstrip("0"))
        episode = int(groups[2].lstrip("0"))

        # lookup the episode title online if needed
        ep_title    = self.searcher.get_episode_name(show, season, episode)
        source_path = os.path.join(root, filename)

        self.logger.info("%s is %s Season %s Episode %s %s" % (filename, show, season, episode, ep_title))

        # construct the new name
        extension = filename.split('.')[-1]
        new_title = self._rename(show, season, episode, ep_title, extension)

        # find the full path of the new destination
        destination = os.path.join(destination_root, show, new_title)

        # save the src and dest into a list for return later
        matched_files.append((source_path, destination))
    return matched_files

  def _match(self, filename):
    if self.exclude.search(filename):
      return None

    for pattern in self.patterns:
      search = pattern.search(filename)
      if search is not None:
        return search
    return None

  def _get_show_name(self, name):
    name = name.replace(".", " ").lower().replace("the", "").strip()
    for show in self.show_list:
      s = show.lower().replace("the", "").replace(",", "").strip()
      if name.startswith(s):
        return show
    return None
  
if __name__ == "__main__":
  import pickle
  import argparse
  import sys

  argparser = argparse.ArgumentParser(description="Automatically rename and move TV shows")
  argparser.add_argument("searchpath", nargs=1, help="The file or directory to process")
  argparser.add_argument("--conf", nargs=1, default="/etc/automover.conf", help="Path to the config file")
  argparser.add_argument("--script", nargs="?", default="automover.sh", help="Write a bash script")
  argparser.add_argument("--verbose", action="store_true", help="Verbose output") 
  argparser.add_argument("--cache", nargs="?", default="cache_file.pyo", help="Location of the show cache") 
  args = argparser.parse_args(sys.argv[1:])

  try:
    with open(args.cache, "r") as cache_file:
      cache = pickle.load(cache_file)
  except:
    cache = {}

  logger  = logging.getLogger(__name__)
  handler = logging.StreamHandler()
  if args.verbose:
    logger.setLevel(logging.DEBUG)
    handler.setLevel(logging.DEBUG)

  formatter = logging.Formatter("%(asctime)s %(filename)s:%(lineno)s - %(funcName)s() %(levelname)s - %(message)s", datefmt="%m/%d/%Y %H:%M:%S")
  handler.setFormatter(formatter)
  logger.addHandler(handler)

  c = ConfigParser.RawConfigParser()
  c.read(args.conf)

  e = EpGuidesSearcher(logger=logger, cache=cache)
  a = Automover(search_path=args.searchpath[0], config=c, searcher=e, logger=logger)
  script = a.get_move_script()
  
  with open(args.script, "w") as move_file:
    move_file.write(script)

  with open("cache_file.pyo", "w") as cache_file:
    pickle.dump(e.cache, cache_file)

import re
import os
from datetime import datetime
from parsers import *
from searchers import *

class Debug:
  def __init__(self, verbose=0):
    self.verbose = verbose

  def out(self, message, tag, level=1):
    if self.verbose >= level or level == -1:
      print "[%s] %s - %s" % (datetime.now(), tag, message)

  def info(self, message, level=1):
    self.out(message, "INFO", level)

  def warn(self, message, level=1):
    self.out(message, "WARN", level)

  def fatal(self, message):
    self.output(message, "FATAL", -1)

class Automover:
  def __init__(self, search_path, config, searcher, debug):
    self.search_path = os.path.abspath(search_path)
    self.config      = config
    self.searcher    = searcher
    self.debug       = debug
    self.debug.info("Initializing...")

    patterns = [p for p in self.config.options('patterns') if p.startswith('pattern')]

    self.debug.info("Compiling regular expressions")
    self.patterns = [re.compile(self.config.get('patterns', p), flags=re.IGNORECASE) for p in patterns]
    self.alnum_pattern = re.compile('[\W_]+')

    self.show_list = []
    for show in os.listdir(self.config.get('main', 'destination')):
      self.show_list.append(show)
    self.debug.info("Saved list of %d shows" % len(self.show_list))
    self.debug.info("Done initializing")

  def run(self):
    files = self._get_files()

    for src, dest in files:
      self._move(src, dest)

  def _move(self, src, dest):
    self.debug.info('move "%s" to "%s"' % (src, dest))

  def _rename(self, show, season, episode, episode_title, extension):
    return "%s S%02dE%02d %s.%s" % (show, season, episode, episode_title, extension)

  def _get_files(self):
    matched_files = []
    self.debug.info("Finding files in %s" % self.search_path)
    destination_root = os.path.abspath(self.config.get('main', 'destination'))
    
    for root, subs, files in os.walk(self.search_path):
      for filename in files:
        match = self._match(filename)
        if match:
          # extract info from the regex match
          groups      = match.groups()
          show        = self._get_show_name(groups[0])
          season      = int(groups[1].lstrip("0"))
          episode     = int(groups[2].lstrip("0"))

          # lookup the episode title online if needed
          ep_title    = self.searcher.get_episode_name(show, season, episode)
          source_path = os.path.join(root, filename)

          self.debug.info("%s is %s Season %s Episode %s %s" % (filename, show, season, episode, ep_title))

          # construct the new name
          extension   = filename.split('.')[-1]
          new_title = self._rename(show, season, episode, ep_title, extension)

          # find the full path of the new destination
          destination = os.path.join(destination_root, show, new_title)

          # save the src and dest into a list for return later
          matched_files.append((source_path, destination))
    return matched_files

  def _match(self, filename):
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

  try:
    with open("cache_file.pyo", "r") as cache_file:
      cache = pickle.load(cache_file)
  except:
    cache = {}

  d = Debug(verbose=1)
  c = DummyConfigParser()
  e = DummySearcher(debug=d, cache=cache)
  a = Automover(search_path='.', config=c, searcher=e, debug=d)
  a.run()

  with open("cache_file.pyo", "w") as cache_file:
    pickle.dump(e.cache, cache_file)

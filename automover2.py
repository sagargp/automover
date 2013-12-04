import re
import os
import urllib
import json
import socket
import sgmllib
from datetime import datetime
from ConfigParser import RawConfigParser

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

class DummyConfigParser(RawConfigParser):
  def __init__(self):
    RawConfigParser.__init__(self)

    self.add_section('main')
    self.set('main', 'destination', 'test/dest/')

    self.add_section('patterns')
    self.set('patterns', 'pattern_1', '(.*)s(\d+)e(\d+).*(mkv|avi)')
    self.set('patterns', 'pattern_2', '(.*)\.?(\d{1,2})(\d\d).*(mkv|avi)')
    self.set('patterns', 'exclude', '.*sample.*')

class EpGuidesParser(sgmllib.SGMLParser):
  def __init__(self, verbose=0):
    sgmllib.SGMLParser.__init__(self, verbose)
    self.hyperlinks = []
    self.epcsv = ''
    self.inside_pre = 0

  def parse(self, s):
    self.feed(s)
    self.close()

  def handle_data(self, data):
    if self.inside_pre:
      self.epcsv = self.epcsv + data

  def start_pre(self, attributes):
    self.inside_pre = 1

  def end_pre(self):
    self.inside_pre = 0

  def start_a(self, attributes):
    for name, value in attributes:
      if name == 'href':
        self.hyperlinks.append(value)

  def get_hyperlinks(self):
    return self.hyperlinks

  def get_eps_csv(self):
    return self.epcsv.splitlines()

  def reset_data(self):
    self.inside_pre = 0
    self.epcsv = ''
    self.hyperlinks = []

class DummySearcher:
  def __init__(self):
    pass

  def get_episode_name(self, show, season, episode):
    return '"Unknown episode of %s, S%02dE%02d"' % (show, int(season), int(episode))

class EpGuidesSearcher:
  def __init__(self, debug, cache=None):
    # Search cache. Nested dictionary that stores ShowName -> Season mappings
    # and Season maps to Episode and Title.
    # Eg.
    # {The Simpsons: 
    #   {1:
    #     {3:
    #       "Homer's Odyssey"
    #     }
    #   }
    # }
    self.cache = cache
    self.debug = debug

    if self.cache is None:
      self.cache = {}

  def get_episode_name(self, show, season, episode):
    try:
      ep = self.cache[show][season][episode]
      self.debug.info("Returning episodes for %s from cache" % show)
      return ep
    except:
      self.debug.info("%s is not cached, fetching from the internet" % show)

    query = {"q": "allintitle: site:epguides.com %s" % show, "userip": socket.gethostbyname(socket.gethostname())}
    search_url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s" % urllib.urlencode(query)

    self.debug.info("Searching at %s" % search_url)
    search_results = json.loads(self._get_url_contents(search_url))

    if search_results['responseStatus'] != 200 or 'estimatedResultCount' not in search_results['responseData']['cursor']:
      self.debug.fatal("Show not found! Response details: %s" % search_results['responseDetails'])
      return None

    epguides_url = search_results['responseData']['results'][0]['url']
    self.debug.info("Looking for CSV listing at %s" % epguides_url)

    parser = EpGuidesParser()
    parser.parse(self._get_url_contents(epguides_url))

    try:
      links = parser.get_hyperlinks()
      csv_link = links[["exportToCSV" in link for link in links].index(True)]
    except ValueError:
      self.debug.fatal("Couldn't find CSV listing for %s at %s. Aborting." % (show, epguides_url))
      return None

    self.debug.info("Downloading show data for %s..." % show)
    parser.reset_data()
    parser.parse(self._get_url_contents(csv_link))

    csv = parser.get_eps_csv()
    if "" in csv:
      csv.remove("")

    eps = {}
    for i in range(0, len(csv)):
      if i == 0:
        headers = csv[0].split(",")
        continue
      row = csv[i].split(",")
      if len(row) < 2:
        continue

      rowdict = {}
      for j in range(0, len(headers)):
        rowdict[headers[j]] = row[j]

      title = rowdict["title"]
      try:
        _season = int(rowdict["season"])
        _episode = int(rowdict["episode"])
      except ValueError:
        self.debug.warn("Season or episode number are missing. Skipping this episode: %s" % rowdict["title"])
        continue

      if _season not in eps:
        eps[_season] = {}
      eps[_season][_episode] = title.replace('"', '')

    self.debug.info("Done downloading data for %s" % show)
    self.cache[show] = eps
    return eps[season][episode]

  def _get_url_contents(self, url):
    page = urllib.urlopen(url)
    results = page.read()
    page.close()
    return results

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
      self._rename(src, dest)

  def _rename(self, src, dest):
    self.debug.info('move "%s" to "%s"' % (src, dest))

  def _get_files(self):
    matched_files = []
    self.debug.info("Finding files in %s" % self.search_path)
    destination_root = os.path.abspath(self.config.get('main', 'destination'))
    
    for root, subs, files in os.walk(self.search_path):
      for filename in files:
        match = self._match(filename)
        if match:
          groups = match.groups()
          show = self._get_show_name(groups[0])
          season = int(groups[1].lstrip("0"))
          episode = int(groups[2].lstrip("0"))
          ep_title = self.searcher.get_episode_name(show, season, episode)
          self.debug.info("%s is %s Season %s Episode %s %s" % (filename, show, season, episode, ep_title))
          source_path = os.path.join(root, filename)
          extension = filename.split('.')[-1]
          new_title = "%s S%02dE%02d %s.%s" % (show, season, episode, ep_title, extension)
          destination = os.path.join(destination_root, show, new_title)
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
  with open("cache_file.pyo", "r") as cache_file:
    cache = pickle.load(cache_file)

  d = Debug(verbose=1)
  c = DummyConfigParser()
  e = EpGuidesSearcher(debug=d, cache=cache)
  a = Automover(search_path='.', config=c, searcher=e, debug=d)
  a.run()

  with open("cache_file.pyo", "w") as cache_file:
    pickle.dump(e.cache, cache_file)

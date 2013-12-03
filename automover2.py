import re
import os
import string
import urllib
import json
import socket
import sgmllib
from datetime import datetime
from ConfigParser import RawConfigParser

class Debug:
  def __init__(self, verbose=False):
    self.verbose = verbose

  def out(self, string, tag):
    if self.verbose:
      print "[%s] %s - %s" % (datetime.now(), tag, string)

  def info(self, string):
    self.out(string, "INFO")

  def warn(self, string):
    self.out(string, "WARN")

class DefaultConfigParser(RawConfigParser):
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

class Automover:
  def __init__(self, search_path='.', config=None, debug=None):
    self.search_path = os.path.abspath(search_path)
    self.config = config
    self.debug = debug

    if self.debug is None:
      self.debug = Debug()

    self.debug.info("Initializing...")

    if self.config is None:
      self.debug.warn("Config parser is empty, using default options")
      self.config = DefaultConfigParser()

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

  def _get_files(self):
    matched_files = []
    self.debug.info("Finding files in %s" % self.search_path)
    
    for root, subs, files in os.walk('.'):
      for filename in files:
        match = self._match(filename)
        if match:
          groups = match.groups()
          show = self._get_show_name(groups[0])
          season = int(groups[1].lstrip("0"))
          episode = int(groups[2].lstrip("0"))

          title = self._get_episode_name(show, season, episode)
          self.debug.info("%s is %s Season %s Episode %s %s" % (filename, show, season, episode, title))
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
  
  def _get_episode_name(self, title, season, episode):
    query = {"q": "allintitle: site:epguides.com %s" % title, "userip": socket.gethostbyname(socket.gethostname())}
    search_url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s" % urllib.urlencode(query)

    self.debug.info("Searching at %s" % search_url)

    page = urllib.urlopen(search_url)
    json_results = page.read()
    results = json.loads(json_results)
    page.close()

    if results['responseStatus'] != 200 or 'estimatedResultCount' not in results['responseData']['cursor']:
      self.debug.warn("Show not found! Response details: %s" % results['responseDetails'])
      return None

    epguides_url = results['responseData']['results'][0]['url']
    self.debug.info("Looking for CSV listing at %s" % epguides_url)

    page = urllib.urlopen(epguides_url)

    parser = EpGuidesParser()
    parser.parse(page.read())
    page.close()

    csv_link = None
    for link in parser.get_hyperlinks():
      if "exportToCSV" in link:
        csv_link = link
        break

    if csv_link is None:
      self.debug.warn("Couldn't find CSV listing for %s at %s. Aborting." % (self.title, epguides_url))
      return None

    self.debug.info("Downloading show data...")
    page = urllib.urlopen(csv_link)
    parser.reset_data()
    parser.parse(page.read())
    page.close()

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

      try:
        season = int(rowdict["season"])
        episode = int(rowdict["episode"])
      except ValueError:
        self.debug.warn("Season or episode number are missing. Skipping this episode: %s" % rowdict["title"])
        continue

      title = rowdict["title"]

      if season not in eps:
        eps[season] = {}
      eps[season][episode] = title

    self.debug.info("Done downloading data")
    return eps[season][episode]

if __name__ == "__main__":
  d = Debug(verbose=True)
  a = Automover(debug=d)
  a.run()

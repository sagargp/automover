#!/usr/bin/python2.7 -tt
# coding=utf-8
"""
Data from epguides.com
"""

import json
import socket
import urllib
import Data

def get_url_contents(url):
  """
  @rtype : object
  @type url: unicode or str
  @return: @rtype: 
  """
  page = urllib.urlopen(url)
  results = page.read()
  page.close()
  return results

class EpGuidesData(Data.Data):
  """
  Search data. Nested dictionary that stores ShowName -> Season mappings and
  Season maps to Episode and Title.
  
  For example:
  {The Simpsons:
    {1:
      {3:
        "Homer's Odyssey"
      }
    }
  }
  """

  def __init__(self, data, parser):
    """
    @rtype : object
    @type data: __builtin__.NoneType
    @type parser: parsers.EpGuidesParser.EpGuidesParser
    """
    super(EpGuidesData, self).__init__(data, parser)

    if self.data is None:
      self.data = {}

  def get_episode_name(self, show, season, episode):
    """
    @rtype : object
    @type show: unicode
    @type season: int
    @type episode: int
    @return:
    """
    self.logger.info(u"Retrieving show {0:s} from season {1:d} episode {2:d}".format(show, season, episode))

    try:
      ep = self.data[show][season][episode]
      self.logger.info(u"Returning episodes for {0:s} from data".format(show))
      return ep
    except KeyError:
      self.logger.info(u"{0:s} is not cached, fetching from the internet".format(show))

    query = {"q": u"allintitle: site:epguides.com {0:s}".format(show), "userip": socket.gethostbyname(socket.gethostname())}
    search_url = u"http://ajax.googleapis.com/ajax/services/search/web?v=1.0&{0:s}".format(urllib.urlencode(query))

    self.logger.info(u"Searching at {0:s}".format(search_url))
    search_results = json.loads(get_url_contents(search_url))

    if not 200 == search_results["responseStatus"] and not "estimatedResultCount" not in search_results["responseData"]["cursor"]:
      self.logger.error(u"Show not found! Response details: {0:s}".format(search_results["responseDetails"]))
      return None

    epguides_url = search_results["responseData"]["results"][0]["url"]
    self.logger.info(u"Looking for CSV listing at {0:s}".format(epguides_url))
    self.parser.parse(get_url_contents(epguides_url))

    try:
      links = self.parser.get_hyperlinks
      csv_link = links[["exportToCSV" in link for link in links].index(True)]
    except ValueError:
      self.logger.error("Couldn't find CSV listing for {0:s} at {1:s}. Aborting.".format(show, epguides_url))
      return None

    self.logger.info("Downloading show data for %s..." % show)
    self.parser.reset_data()
    self.parser.parse(get_url_contents(csv_link))

    csv = self.parser.get_eps_csv
    if "" in csv:
      csv.remove("")

    eps = {}
    for i in xrange(0, len(csv)):
      if i == 0:
        headers = csv[0].split(",")
        continue
      row = csv[i].split(",")
      if len(row) < 2:
        continue

      rowdict = {}
      for j in xrange(0, len(headers)):
        rowdict[headers[j]] = row[j]

      title = rowdict["title"]
      try:
        _season = int(rowdict["season"])
        _episode = int(rowdict["episode"])
      except ValueError:
        self.logger.warning(u"Season or episode number are missing. Skipping this episode: {0:s}".format(rowdict["title"]))
        continue

      if _season not in eps:
        eps[_season] = {}
      eps[_season][_episode] = title.replace("\"", '')

    self.logger.info("Done downloading data for %s" % show)
    self.data[show] = eps
    return eps[season][episode]

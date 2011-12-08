import sgmllib, urllib, json, re, time, socket
from EpGuidesParser import EpGuidesParser

class EpGuidesSearch:
  def __init__(self, title, debugfile='debug.log', debug=False, verbose=False):
    self.title = title
    self.eps = None

    self.cache = dict()

    if debug:
      self.debugfile = debugfile
      self.debughandle = open(self.debugfile, 'a')

    self.doDebug = debug
    self.verbose = verbose
    self.debug('Show name: %s' % title)

  def debug(self, str):
    out = '%s -- %s\n' % (time.ctime(), str)

    if self.doDebug:
      self.debughandle.write(out)
    
    if self.verbose:
      print out,

  def getEpisodes(self):
    if self.cache.has_key(self.title):
      self.debug('Returning cached data...')
      return self.cache[self.title]

    query = {"q": "allintitle: site:epguides.com %s" % self.title, "userip": socket.gethostbyname(socket.gethostname())}
    search_url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s" % urllib.urlencode(query)

    self.debug('Searching for show at %s' % search_url)

    page = urllib.urlopen(search_url)
    json_results = page.read()
    results = json.loads(json_results)
    page.close()

    if results['responseStatus'] == 200 and results['responseData']['cursor'].has_key('estimatedResultCount'):
      self.epguides_url = results['responseData']['results'][0]['url']
    else:
      self.debug('Show not found! Dumping search results object:')
      self.debug(results)
      self.debug('<<<')
      return None

    self.debug('Looking for CSV listing at %s' % self.epguides_url)
    page = urllib.urlopen(self.epguides_url)

    parser = EpGuidesParser()
    parser.parse(page.read())
    page.close()

    csv_link = ''
    for link in parser.get_hyperlinks():
      if link.find('exportToCSV') > 0:
        csv_link = link
        break

    if csv_link == '':
      self.debug('Error! Can\'t find CSV listing for %s at %s! Bailing out...' % (self.title, self.epguides_url))
      return None
   
    self.debug('Downloading show data...')
    page = urllib.urlopen(csv_link)
    parser.reset_data()
    parser.parse(page.read())
    page.close()

    csv = parser.get_eps_csv()
    if '' in csv:
      csv.remove('')
    eps = []

    for i in range(0, len(csv)):
      if i == 0:
        headers = csv[0].split(',')
        continue

      row = csv[i].split(',')
      rowdict = dict()

      for key in range(0, len(headers)):
        rowdict[headers[key]] = row[key]
      
      eps.append(rowdict)

    self.debug('Done')
    self.cache[self.title] = eps
    return eps

  def search(self, season, ep):
    results = []
    
    if self.getEpisodes():
      for episode in self.cache[self.title]:
        if episode['season'] == season and episode['episode'] == ep:
          results.append(episode)
    
    return results

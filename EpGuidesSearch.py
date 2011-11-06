import sgmllib, urllib, json, re, time
from EpGuidesParser import EpGuidesParser
	
class EpGuidesSearch(object):
	def __init__(self, title, includeSpecials=False, cachefile='cache.p', debugfile='debug.log'):
		self.__title__ = title
		self.__eps__ = None
		self.__includeSpecials__ = includeSpecials
		
		self.__debugfile__ = debugfile
		self.__debughandle__ = open(self.__debugfile__, 'a')

		self.DEBUG('>> Show: %s <<' % title)

		self.__cachefile__ = cachefile
		self.__cache__ = dict()
		self.__cacheused__ = False
		self.__cacheLoad__()

	def DEBUG(self, str):
		self.__debughandle__.write("%s -- %s\n" % (time.ctime(), str))

	def __cacheWrite__(self):
		import pickle
		
		d = 'Writing cache...'

		self.__cache__[self.__title__] = self.__eps__
		f = open(self.__cachefile__, 'w')
		pickle.dump(self.__cache__, f)

		self.DEBUG('%s done.' % d)
	
	def __cacheLoad__(self):
		import pickle

		d = 'Loading cache...'
		
		try:
			f = open(self.__cachefile__, 'r')
		except IOError:
			return False 

		self.__cache__ = pickle.load(f)
		
		self.DEBUG('%s %d shows loaded.' % (d, len(self.__cache__)))
		return True

	def __getEpisodes__(self):
		if self.__cache__ and self.__cache__.has_key(self.__title__):
			self.DEBUG('Using cache.')
			self.__cacheused__ = True
			return self.__cache__[self.__title__]

		self.DEBUG('Show not found in cache, or cache not found.')
		query = {"q": "allintitle: site:epguides.com %s" % self.__title__}
		search_url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s" % urllib.urlencode(query)

		self.DEBUG('Searching %s' % search_url) 
		f = urllib.urlopen(search_url)
		json_results = f.read()
		results = json.loads(json_results)

		if results['responseStatus'] == 200 and results['responseData']['cursor'].has_key('estimatedResultCount'):
			self.__epguidesUrl__ = results['responseData']['results'][0]['url']
		else:
			return None

		self.DEBUG('Looking for show CSV listing at %s' % self.__epguidesUrl__)
		f = urllib.urlopen(self.__epguidesUrl__)

		myparser = EpGuidesParser()
		myparser.parse(f.read())
		f.close()

		csv_link = ''
		for link in myparser.get_hyperlinks():
			if link.find("exportToCSV") > 0:
				csv_link = link

		self.DEBUG('Downloading show data from %s' % csv_link)
		f = urllib.urlopen(csv_link)
		myparser.reset_data()
		myparser.parse(f.read())
		f.close()

		eps_csv = myparser.get_eps_csv()
		if '' in eps_csv:
			eps_csv.remove('')
		eps = []

		for i in range(0, len(eps_csv)):
			if i == 0:
				headers = eps_csv[0].split(',')
				continue

			row = eps_csv[i].split(',')
			row_dict = dict()

			for key in range(0, len(headers)):
				row_dict[headers[key]] = row[key]

			eps.append(row_dict)
		
		self.DEBUG('Done downloading episode data')
		return eps

	def search(self, season, ep):
		return self.__search__(season, ep)
	
	def reg_search(self, query):
		pattern = re.search("s(\d+)e(\d+)", query, flags=re.IGNORECASE)
		matched = pattern.groups()

		season = matched[0].lstrip('0')
		ep = matched[1].lstrip('0')
		
		return self.search(season, ep)
		
	def __search__(self, season, ep):
		self.getEpisodes()
		
		append = True
		results = []

		for episode in self.__cache__[self.__title__]:
			if season:
				if episode['season'] == season:
					if ep:
						if ep == episode['episode']:
							append = True
						else:
							append = False
					else:
						append = True
				else:
					append = False

			if not self.__includeSpecials__:
				if episode['special?'] == 'y':
					append = False

			if append:
				results.append(episode)

		return results

	def getEpguidesURL(self):
		if not self.__epguidesUrl__:
			self.__eps__ = self.__getEpisodes__()

		return self.__epguidesUrl__

	def getEpisodes(self):
		if not self.__eps__:
			self.__eps__ = self.__getEpisodes__()
		
		if not self.__cacheused__:
			self.__cacheWrite__()
		return self.__eps__

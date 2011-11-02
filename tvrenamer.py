#!/usr/bin/python

import sgmllib, urllib, json, re
from EpGuidesParser import EpGuidesParser

class EpGuidesSearch(object):
	
	def __init__(self, title, includeSpecials=False):
		self.__title__ = title
		self.__eps__ = None
		self.__includeSpecials__ = includeSpecials
	
	def __getEpisodes__(self):
		query = {"q": "allintitle: site:epguides.com %s" % self.__title__}
		search_url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s" % urllib.urlencode(query)

		f = urllib.urlopen(search_url)
		json_results = f.read()
		results = json.loads(json_results)

		if results['responseStatus'] == 200 and results['responseData']['cursor'].has_key('estimatedResultCount'):
			self.__epguidesUrl__ = results['responseData']['results'][0]['url']

		else:
			return None

		f = urllib.urlopen(self.__epguidesUrl__)

		myparser = EpGuidesParser()
		myparser.parse(f.read())
		f.close()

		csv_link = ''
		for link in myparser.get_hyperlinks():
			if link.find("exportToCSV") > 0:
				csv_link = link

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

		for episode in self.__eps__:
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
			self.__getEpisodes__()

		return self.__epguidesUrl__

	def getEpisodes(self):
		if not self.__eps__:
			self.__eps__ = self.__getEpisodes__()

		return self.__eps__

if __name__ == '__main__':
	import sys, os, argparse
	
	arg_parser = argparse.ArgumentParser(description='Get episode info given a TV show name')
	arg_parser.add_argument('--title', nargs='+',help='The title of the show')
	arg_parser.add_argument('--filename', nargs=1, help='The filename')
	arg_parser.add_argument('--directory', nargs=1, help='A directory')

	args = arg_parser.parse_args(sys.argv[1:])

	show = EpGuidesSearch(''.join(args.title))
	mappings = []

	files = os.listdir(''.join(args.directory))
	reg = re.compile("s(\d+)e(\d+)", flags=re.IGNORECASE)

	for file in files:
		pattern = reg.search(file)
		extension = file.split('.')[-1]
		if pattern:
			ref = pattern.groups()
			season = ref[0].lstrip('0')
			episode = ref[1].lstrip('0')
			result = show.search(season, episode)

			newname = "%s S%sE%s %s.%s" % (''.join(args.title), ref[0], ref[1], result[0]['title'].lstrip('"').rstrip('"'), extension)
			mappings.append( [file, newname] )

	for mapping in mappings:
		print "%s \"%s\"" % (mapping[0], mapping[1])

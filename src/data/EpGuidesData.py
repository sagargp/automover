#!/usr/bin/python2.7 -tt

import json
import socket
import urllib

from data.Data import Data


class EpGuidesData(Data):
    def __init__(self, data, parser):
        # Search data. Nested dictionary that stores ShowName ->
        #   Season mappings and Season maps to Episode and Title.
        # Eg.
        # {The Simpsons:
        #     {1:
        #         {3:
        #             "Homer's Odyssey"
        #         }
        #     }
        # }
        Data.__init__(self, data, parser)

        if self.data is None:
            self.data = {}

    def get_episode_name(self, show, season, episode):
        self.logger.info("Retrieving show %s from season %s episode %s" %
                         (show, season, episode))
        try:
            ep = self.data[show][season][episode]
            self.logger.info("Returning episodes for %s from data" % show)
            return ep
        except KeyError, ex:
            self.logger.info("%s is not cached, fetching from the internet" %
                             show)

        query = {"q": "allintitle: site:epguides.com %s" % show,
                 "userip": socket.gethostbyname(socket.gethostname())}
        search_url = "http://ajax.googleapis.com/ajax/services/" \
                     "search/web?v=1.0&%s" % urllib.urlencode(query)

        self.logger.info("Searching at %s" % search_url)
        search_results = json.loads(self.__get_url_contents(search_url))

        if search_results['responseStatus'] != 200 or \
            'estimatedResultCount' not in \
            search_results['responseData']['cursor']:
            self.logger.error("Show not found! Response details: %s" %
                              search_results['responseDetails'])
            return None

        epguides_url = search_results['responseData']['results'][0]['url']
        self.logger.info("Looking for CSV listing at %s" % epguides_url)

        self.parser.parse(self.__get_url_contents(epguides_url))

        try:
            links = self.parser.get_hyperlinks()
            csv_link = links[["exportToCSV" in link
                              for link in links].index(True)]
        except ValueError:
            self.logger.error("Couldn't find CSV listing for %s at %s. " \
                              "Aborting." % (show, epguides_url))
            return None

        self.logger.info("Downloading show data for %s..." % show)
        self.parser.reset_data()
        self.parser.parse(self.__get_url_contents(csv_link))

        csv = self.parser.get_eps_csv()
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
                self.logger.warning("Season or episode number are missing. " \
                                    "Skipping this episode: %s" %
                                    rowdict["title"])
                continue

            if _season not in eps:
                eps[_season] = {}
            eps[_season][_episode] = title.replace('"', '')

        self.logger.info("Done downloading data for %s" % show)
        self.data[show] = eps
        return eps[season][episode]

    def __get_url_contents(self, url):
        page = urllib.urlopen(url)
        results = page.read()
        page.close()
        return results

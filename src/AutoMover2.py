'''
Created on Dec 4, 2013

@author: jdelgad
'''
import logging
import os
import re


class Automover2(object):
    def __init__(self, search_path, config, data):
        self.search_path = os.path.abspath(search_path)
        self.config = config
        self.data = data

        self.show_list = []
        self.patterns = []

        self.logger = logging.getLogger("automover2")

        self.__configure()

    def run(self):
        files = self.__get_files()

        for src, dest in files:
            self.__rename(src, dest)

    def __configure(self):
        self.logger.info("Initializing...")
        patterns = [p for p in self.config.options('patterns')
                    if p.startswith('pattern')]

        self.logger.info("Compiling regular expressions")
        self.patterns = [re.compile(self.config.get('patterns', p),
                                    flags=re.IGNORECASE)
                         for p in patterns]

        for show in os.listdir(self.config.get('main', 'destination')):
            self.show_list.append(show)
        self.logger.info("Saved list of %d shows" % len(self.show_list))

        self.logger.info("Done initializing")

    def __get_files(self):
        matched_files = []
        self.logger.info("Finding files in %s" % self.search_path)
        destination_root = os.path.abspath(self.config.get('main',
                                                           'destination'))

        for root, subs, files in os.walk(self.search_path):
            for filename in files:
                match = self.__match(filename)
                if match:
                    groups = match.groups()
                    show = self.__get_show_name(groups[0])
                    season = int(groups[1].lstrip("0"))
                    episode = int(groups[2].lstrip("0"))
                    ep_title = self.data.get_episode_name(show,
                                                          season,
                                                          episode)
                    self.logger.info("%s is %s Season %s Episode %s %s" %
                                      (filename, show, season,
                                       episode, ep_title))
                    source_path = os.path.join(root, filename)
                    extension = filename.split('.')[-1]
                    new_title = "%s S%02dE%02d %s.%s" % \
                        (show, season, episode, ep_title, extension)
                    destination = os.path.join(destination_root,
                                               show,
                                               new_title)
                    matched_files.append((source_path, destination))
        return matched_files

    def __get_show_name(self, name):
        name = name.replace(".", " ").lower().replace("the", "").strip()
        for show in self.show_list:
            s = show.lower().replace("the", "").replace(",", "").strip()
            self.logger.info("s = %s" % s)
            if name.startswith(s):
                return show
        return None

    def __match(self, filename):
        for pattern in self.patterns:
            search = pattern.search(filename)
            if search is not None:
                return search
        return None

    def __rename(self, src, dest):
        self.logger.info('move "%s" to "%s"' % (src, dest))

#!/usr/bin/python2.7 -tt
# coding=utf-8
"""
Created on Dec 4, 2013

@author: jdelgad
"""
import logging
import os
import re


class Automover2(object):
    """
    
    @type search_path: str
    @type config: AutoMover2Configuration.AutoMover2Configuration
    @type data: data.EpGuidesData.EpGuidesData
    """

    def __init__(self, search_path, config, data):
        self.search_path = os.path.abspath(search_path)
        self.config = config
        self.data = data

        self.show_list = []
        self.patterns = []

        self.logger = logging.getLogger("automover2")

        self.__configure()

    def run(self):
        """

        

        @rtype : object
        """
        files = self.__match_files

        for src, dest in files:
            self.__rename(src, dest)

    def __configure(self):
        self.logger.info("Initializing...")

        self.logger.info("Compiling regular expressions")
        self.patterns = []
        for p in self.config.get_patterns:
            self.patterns.append(re.compile(p, flags=re.IGNORECASE))

        for show in os.listdir(self.config.get_destination):
            self.show_list.append(show)
        self.logger.info("Saved list of %d shows" % len(self.show_list))

        self.logger.info("Done initializing")

    @property
    def __match_files(self):
        matched_files = []
        self.logger.info(u"Finding files in {0:s}".format(self.search_path))
        destination_root = os.path.abspath(self.config.get_destination)

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
                    self.logger.info("{0:s} is {1:s} Season {2:d} Episode " +
                                     "{3:d}".format(filename,
                                                    show,
                                                    season,
                                                    episode))
                    source_path = os.path.join(root, filename)
                    extension = filename.split('.')[-1]
                    new_title = "{0:s} S{1:02d}E{2:0d} {3:s}.{4:s}" \
                        .format(show, season, episode, ep_title, extension)
                    destination = os.path.join(destination_root,
                                               show,
                                               new_title)
                    matched_files.append((source_path, destination))
        return matched_files

    def __get_show_name(self, name):
        name = name.replace(".", " ").lower().replace("the", "").strip()
        for show in self.show_list:
            s = show.lower().replace("the", "").replace(",", "").strip()
            if name.startswith(s):
                return show
        return None

    def __match(self, filename):
        """


        @rtype : object
        @type filename: str
        @return: @rtype:
        """
        for pattern in self.patterns:
            search = pattern.search(filename)
            if search is not None:
                return search
        return None

    def __rename(self, src, dest):
        self.logger.info('move "%s" to "%s"' % (src, dest))

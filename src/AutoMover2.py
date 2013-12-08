#!/usr/bin/python2.7 -tt
# coding=utf-8
"""
Moves files from a source directory to a target directory, naming them
according to the the users convention
"""

import logging
import os

import AutoMover2
import AutoMover2Configuration
import parsers.EpGuidesParser
import data.EpGuidesData

if "__main__" == __name__:
    #     import pickle
    #     with open("cache_file.pyo", "r") as cache_file:
    #         cache = pickle.load(cache_file)

    logging.basicConfig(format="[%(asctime)s] [%(levelname)s] - %(message)s",
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)
    logging.getLogger("automover2")

    # debug = Debug(verbose=1)
    am2_config = AutoMover2Configuration.AutoMover2Configuration(
        "{0}/../cfg/automover2.cfg".format(os.path.dirname(__file__)))
    am2_parser = parsers.EpGuidesParser.EpGuidesParser()
    am2_data = data.EpGuidesData.EpGuidesData(None, am2_parser)
    automover2 = AutoMover2.Automover2(os.getcwd(),
                                       am2_config,
                                       am2_data)
    automover2.run()

    import pickle

    with open("cache_file.pyo", "w") as cache_file:
        pickle.dump(am2_data.data, cache_file)

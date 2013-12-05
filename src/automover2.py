#!/usr/bin/python2.7 -tt

import logging
import os

import AutoMover2
import AutoMover2Configuration
import parsers.EpGuidesParser
import data.EpGuidesData

if __name__ == "__main__":
    #     import pickle
    #     with open("cache_file.pyo", "r") as cache_file:
    #         cache = pickle.load(cache_file)

    logging.basicConfig(format='[%(asctime)s] [%(levelname)s] - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)
    logging.getLogger("automover2")

    # debug = Debug(verbose=1)
    am2_config = AutoMover2Configuration.AutoMoverConfiguration()
    am2_parser = parsers.EpGuidesParser.EpGuidesParser(1)
    am2_data = data.EpGuidesData.EpGuidesData(None, am2_parser)
    automover2 = AutoMover2.Automover2(os.getcwd(),
                              am2_config,
                              am2_data)
    automover2.run()

    import pickle
    with open("cache_file.pyo", "w") as cache_file:
        pickle.dump(am2_data.data, cache_file)

#!/usr/bin/env python
import logging
import re
from episode import Episode
from configuration import DummyConfigParser
from searchers import DummySearcher
from automover import Automover

if __name__ == "__main__":
  verbose = True
  logger  = logging.getLogger(__name__)
  handler = logging.StreamHandler()

  if verbose:
    logger.setLevel(logging.DEBUG)
    handler.setLevel(logging.DEBUG)

  formatter = logging.Formatter("%(asctime)s %(levelname).4s - %(message)s", datefmt="%m/%d/%Y %H:%M:%S")
  handler.setFormatter(formatter)
  logger.addHandler(handler)

  # set up the patterns
  config_parser = DummyConfigParser()

  # set up the library
  #logger.info("Destination will be %s" % destination)
  library = ("Moone Boy", "How I Met Your Mother", "Community")
  logger.info("Built library with %d series" % len(library))

  # set up the searcher
  searcher  = DummySearcher(logger)
  automover = Automover(config_parser, library, searcher, logger)

  # parse
  #moone_boy = Episode("Moone.Boy.S01E04.HDTV.x264-TLA/moone.boy.s01e04.hdtv.x264-tla.mp4", logger).parse(patterns)
  moone_boy = automover.process("moone.boy.s01e04.hdtv.x264-tla.mp4")

  assert moone_boy.series == "Moone Boy", "Bad show name: %s" % moone_boy.series
  assert moone_boy.season == 1, "Bad season: %s" % str(moone_boy.season)
  assert moone_boy.episode == 4, "Bad episode: %s" % str(moone_boy.episode)

  automover.run('.')

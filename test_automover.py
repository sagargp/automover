#!/usr/bin/env python
import logging
import re
from episode import Episode
from configuration import DummyConfigParser
from searchers import DummySearcher
from searchers import EpGuidesSearcher

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
  config_parser     = DummyConfigParser()
  patterns          = [config_parser.get("patterns", p) for p in config_parser.options('patterns') if p.startswith('pattern')]
  compiled_patterns = [re.compile(p, flags=re.IGNORECASE) for p in patterns]

  # set up the library
  #destination = config_parser.get("main", "destination")
  #logger.info("Destination will be %s" % destination)
  library = ("Moone Boy", "Firefly", "Modern Family", "Friends", "The Simpsons", "Adventure Time")
  logger.info("Built library with %d series" % len(library))

  # set up the searcher
  # searcher = DummySearcher(logger)
  searcher = EpGuidesSearcher(logger)

  # parse
  #moone_boy = Episode("Moone.Boy.S01E04.HDTV.x264-TLA/moone.boy.s01e04.hdtv.x264-tla.mp4", logger).parse(patterns)
  moone_boy      = Episode("moone.boy.s01e04.hdtv.x264-tla.mp4", logger).parse(library, searcher, patterns)
  adventure_time = Episode("adventure.time.s05e49.720p.hdtv.x264-mtg.mkv", logger).parse(library, searcher, patterns)

  assert moone_boy.series == "Moone Boy", "Bad show name: %s" % moone_boy.series
  assert moone_boy.season == 1, "Bad season: %s" % str(moone_boy.season)
  assert moone_boy.episode == 4, "Bad episode: %s" % str(moone_boy.episode)
  assert moone_boy.title == "Dark Side of the Moone", "Bad title: %s" % str(moone_boy.title)

  assert adventure_time.series  == "Adventure Time", "Bad show name: %s" % adventure_time.series
  assert adventure_time.season  == 5, "Bad show name: %s" % str(adventure_time.season)
  assert adventure_time.episode == 49, "Bad show name: %s" % str(adventure_time.episode)
  assert adventure_time.title   == "Bad Timing", "Bad show name: %s" % str(adventure_time.title)

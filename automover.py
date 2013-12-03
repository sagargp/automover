import pickle
import re
import os
import sys
import argparse
import ConfigParser
from time import ctime
from editDistance import editDistance
from EpGuidesSearch import EpGuidesSearch

class Debug:
  def __init__(self, verbose):
    self.verbose = verbose

  def out(self, verbose, kind, string):
    debug_message = "%s -- %s -- %s" % (ctime(), kind, string)

    if self.verbose:
      print debug_message

  def info(self, string):
    self.out(self.verbose, "INFO", string)

  def warn(self, string):
    self.out(self.verbose, "WARN", string)

  def __call__(self, *args, **kwargs):
    self.info(*args, **kwargs)

class automover:
  def __init__(self, args, debug, dictionary):
    self.args = args
    self.dictionary = dictionary
    self.debug = debug

  def getEpisodeTitle(self, name):
    mindist = None
    bestMatch = ""
    for file in self.dictionary:
      match = editDistance(name, file.lower().replace('the', ''))
      if match < mindist or mindist is None:
        mindist = match
        bestMatch = file
    return bestMatch, mindist

  def doRename(self, root, file):
    # skip files that match the exclude pattern
    if exc.search(file) is not None:
      return None

    # skip files that do not match the search pattern
    search = None
    for pattern in pattern_regs:
      search = pattern.search(file)
      if search is not None:
        break
    if search is None:
      return None
    
    # extract media information from the filename
    groups = search.groups()

    title = groups[0].replace('.', ' ').lower().replace('the', '').strip()
    season = groups[1].lstrip('0')
    episode = groups[2].lstrip('0')

    # use a cache to avoid repeat online searches
    if title in titlecache:
      bestMatch = titlecache[title]
      dist = 0
    else:
      bestMatch, dist = self.getEpisodeTitle(title)
      titlecache[title] = bestMatch

    if bestMatch in showcache:
      show = showcache[bestMatch]
    else:
      show = EpGuidesSearch(bestMatch, self.debug)
      showcache[bestMatch] = show

    result = show.search(season, episode)

    if len(result) == 0 or dist > 3:
      self.debug.warn("No results for %s Season %s episode %s" % (bestMatch, season, episode))
      return None
    else:
      newname     = "%s S%02dE%02d %s.%s" % (bestMatch, int(season), int(episode), result[0]['title'].strip('"'), groups[-1])
      destpath    = "%s/%s/Season %s" % (dest, bestMatch, season)
      destination = "%s/%s" % (destpath, newname)

    fullpath = '/'.join([root, file])

    return bestMatch, fullpath, destpath, destination

## Main
if __name__ == '__main__':
  argparser = argparse.ArgumentParser(description="Automatically rename and move TV shows")
  argparser.add_argument("searchpath", nargs=1, help="The file or directory to process")
  argparser.add_argument("--conf", nargs=1, default="/etc/automover.conf", help="Path to the config file")
  argparser.add_argument("--read", action="store_true", help="Take filenames from STDIN") 
  argparser.add_argument("--script", nargs="?", default="automover.sh", help="Write a bash script")
  argparser.add_argument("--verbose", action="store_true", help="Verbose output") 
  argparser.add_argument("--hint", nargs="+", help="Give a hint to the file name, if it isn't in the destination location")
  argparser.add_argument("--logfile", nargs="?", default="automover.log", help="Debug logfile")
  args = argparser.parse_args(sys.argv[1:])


  # parse the config file and grab settings from it
  config = ConfigParser.RawConfigParser()
  config.read(args.conf)

  patterns     = [x for x in config.options('patterns') if x.startswith('pattern')]
  dest         = config.get('main', 'destination')
  pattern_regs = [re.compile(config.get('patterns', x), flags=re.IGNORECASE) for x in patterns]
  exc          = re.compile(config.get('patterns', 'exclude'), flags=re.IGNORECASE)

  #
  path = args.searchpath[0]

  # Build a "dictionary" of TV show names. This is used later to look up names.
  dictionary = [f for f in os.listdir(dest)]

  # Add the hint as a key in the dictionary so that the algorithm will find it for sure
  if args.hint is not None:
    dictionary.append(' '.join(args.hint))

  # initialize the debug printer
  debug = Debug(args.verbose)

  # initialize the automover object
  automover = automover(args, debug, dictionary)

  # prepare the caches
  try:
    cachefile = open('caches.pyo', 'r')
    showcache, titlecache = pickle.load(cachefile)
    cachefile.close()
  except:
    debug('Initializing caches')
    showcache = dict()
    titlecache = dict()
  destpathcache = dict()

  # prepare the list of files to rename
  filelist = []
  if args.read:
    # either from stdin
    for file in sys.stdin.read().splitlines():
      root = os.path.dirname(file)
      filename = os.path.basename(file)
      filelist.append((root, filename))
  else:
    # or from the path given
    for root, subs, files in os.walk(path):
      for file in files:
        filelist.append((root, file))
  
  shows = dict()
  for root, file in filelist:
    move = automover.doRename(root, file)
    debug(move)

    if move is not None:
      title, fullpath, destpath, destination = move

      if title not in shows.keys():
        shows[title] = list()
      shows[title].append((fullpath, destpath, destination))

  script = open(args.script, 'a')

  script.write('#!/bin/bash\n\n')
  script.write('# Shows present in this file:\n# ')
  script.write('\n# '.join(shows.keys()))
  script.write('\n\n')

  for show in shows.keys():
    episodes = sorted(shows[show], key=lambda episode: episode[2])
    script.write('# %s\n' % show)
    for fullpath, destpath, destination in episodes:
      if destpath not in destpathcache:
        destpathcache[destpath] = False

      if not os.path.isdir(destpath) and not destpathcache[destpath]:
        script.write('mkdir -p "%s"\n' % destpath)
        destpathcache[destpath] = True
      script.write('mv -vb "%s" "%s"\n' % (fullpath, destination))
    script.write('\n') 

  script.close()

  cachefile = open('caches.pyo', 'w')
  pickle.dump((showcache, titlecache), cachefile)
  cachefile.close()

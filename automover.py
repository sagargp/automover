if __name__ == '__main__':
  from editDistance import editDistance
  from EpGuidesSearch import EpGuidesSearch
  import re
  import os
  import sys
  import argparse
  import ConfigParser

  argparser = argparse.ArgumentParser(
    description='Automatically rename and move TV shows')

  argparser.add_argument('searchpath',
                         nargs=1,
                         help='The file or directory to process')

  argparser.add_argument('--conf',
                         nargs=1,
                         help='Path to the config file',
                         default='/etc/automover.conf')

  argparser.add_argument('--confirm',
                         action='store_true', help='Ask before doing anything')

  argparser.add_argument('--debug',
                         nargs=1,
                         help='Write output to a debug files')

  argparser.add_argument('--forcetitle',
                         nargs=1,
                         help='Force a TV show match')

  argparser.add_argument('--inplace',
                         action='store_true',
                         help='Rename files in place')

  argparser.add_argument('--read',
                         action='store_true',
                         help='Take filenames from STDIN')

  argparser.add_argument('--script',
                         nargs='?',
                         help='Write a bash script')

  argparser.add_argument('--verbose',
                         action='store_true',
                         help='Verbose output')

  args = argparser.parse_args(sys.argv[1:])

  config = ConfigParser.RawConfigParser()
  config.read(args.conf)

  patterns = [x for x in config.options('patterns') if x.startswith('pattern')]

  if args.debug is not None:
    debugfile = args.debug[0]
  else:
    debugfile = 'automover.log'

  dest = config.get('main', 'destination')
  path = args.searchpath[0]

  dictionary = []
  for file in os.listdir(dest):
    dictionary.append(file)

  showcache = dict()
  titlecache = dict()
  destpathcache = dict()

  pattern_regs = [re.compile(config.get('patterns', x), flags=re.IGNORECASE)
                  for x in patterns]

  exc = re.compile(config.get('patterns', 'exclude'), flags=re.IGNORECASE)

  def getYesNo(str):
    while True:
      yn = raw_input(str)

      if (yn == 'y'):
        return True
      elif (yn == 'n'):
        return False

      print "Please answer 'y' or 'n'"

  def getEpisodeTitle(dictionary, name):
    mindist = None
    bestMatch = ""
    for file in dictionary:
      match = editDistance(name, file)
      if match < mindist or mindist is None:
        mindist = match
        bestMatch = file
    return bestMatch

  def doRename(root, file):
    # skip anything that matches the exclude pattern
    e = exc.search(file)
    if e != None:
      return

    # skip anything that doesn't match the search pattern
    p = None
    for pattern in pattern_regs:
      p = pattern.search(file)
      if p != None:
        break

    if p == None:
      return

    fullpath = '/'.join([root, file])

    groups = p.groups()

    if args.forcetitle:
      title = ' '.join(args.forcetitle)
    else:
      title = groups[0]

    season = groups[1].lstrip('0')
    episode = groups[2].lstrip('0')

    # use a cache to avoid repeating searches
    if title in titlecache:
      bestMatch = titlecache[title]
    else:
      bestMatch = getEpisodeTitle(dictionary, title)
      titlecache[title] = bestMatch

    if bestMatch in showcache:
      show = showcache[bestMatch]
    else:
      show = EpGuidesSearch(bestMatch,
                            debugfile=debugfile,
                            debug=(args.debug is not None),
                            verbose=args.verbose)
      showcache[bestMatch] = show

    # search epguides.com for the specific episode
    result = show.search(season, episode)

    if len(result) == 0:
      print 'No results for %s Season %s episode %s' % (bestMatch,
                                                        season,
                                                        episode)
      return

    newname = "%s S%02dE%02d %s.%s" % (bestMatch,
                                       int(season),
                                       int(episode),
                                       result[0]['title'].strip('"'),
                                       groups[-1])

    destpath = "%s/%s/Season %s" % (dest, bestMatch, season)
    destination = "%s/%s" % (destpath, newname)

    if args.confirm:
      rename = getYesNo("Move %s to %s? " % (file, destination))
    else:
      rename = True

    if args.inplace:
      destination = "%s/%s" % (os.path.dirname(fullpath), newname)

    if rename:
      if args.script:
        s = open(args.script, 'a')
        cmd = '# %s' % newname

        if destpath not in destpathcache:
          destpathcache[destpath] = False

        if not os.path.isdir(destpath) and not destpathcache[destpath]:
          cmd = cmd + '\nmkdir -p "%s"' % destpath
          destpathcache[destpath] = True

        cmd = cmd + '\nmv "%s" "%s"\n\n' % (fullpath, destination)
        s.write(cmd)
      else:
        if not os.path.isdir(destpath):
          os.mkdir(destpath)
        os.rename(fullpath, destination)

  if args.read:
    for file in sys.stdin.read().splitlines():
      root = os.path.dirname(file)
      filename = os.path.basename(file)
      doRename(root, filename)

  else:
    for root, subs, files in os.walk(path):
      for file in files:
        doRename(root, file)

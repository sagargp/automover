if __name__ == '__main__':
  import re, os, sys, argparse, ConfigParser
  from EpGuidesSearch import EpGuidesSearch
  from editDistance import editDistance
  
  def getYesNo(str):
    while True:
      yn = raw_input(str)
      
      if (yn == 'y'):
        return True
      elif (yn == 'n'):
        return False  
      else:
        print "Please answer 'y' or 'n'"
  
  argparser = argparse.ArgumentParser(description='Automatically rename and move TV shows')
  argparser.add_argument('searchpath', nargs=1, help='The file or directory to process')
  argparser.add_argument('--conf', nargs=1, help='Path to the config file', default='/home/sagar/Projects/Github/tvrenamer/automover.conf')
  argparser.add_argument('--confirm', action='store_true', help='Ask before doing anything')
  argparser.add_argument('--script', nargs='?', help='Write a bash script')
  argparser.add_argument('--verbose', action='store_true', help='Verbose output')
  argparser.add_argument('--debug', nargs=1, help='Write output to a debug files')
  args = argparser.parse_args(sys.argv[1:])

  config = ConfigParser.RawConfigParser()
  config.read(args.conf)

  if args.debug is not None:
    debugfile = args.debug[0]
  else:
    debugfile = 'automover.log'

  dest = config.get('default', 'destination')
  path = args.searchpath[0]
  
  dictionary = []
  for file in os.listdir(dest):
    dictionary.append(file)

  def getEpisodeTitle(name):
    mindist = None
    bestMatch = ""
    for file in dictionary:
      match = editDistance(name, file)
      if match < mindist or mindist is None:
        mindist = match
        bestMatch = file 
    return bestMatch

  showcache = dict()
  titlecache = dict()
  destpathcache = dict()
  reg = re.compile(config.get('default', 'pattern'), flags=re.IGNORECASE)
  exc = re.compile(config.get('default', 'exclude'), flags=re.IGNORECASE)
  for root, subs, files in os.walk(path):
    for file in files:
      # skip anything that matches the exclude pattern
      e = exc.search(file)
      if e != None:
        continue

      # skip anything that doesn't match the search pattern
      p = reg.search(file)
      if p == None:
        continue

      fullpath = '/'.join([root, file])

      groups = p.groups()
      title = groups[0]
      season = groups[1].lstrip('0')
      episode = groups[2].lstrip('0')

      # use a cache to avoid repeating searches
      if titlecache.has_key(title):
        bestMatch = titlecache[title]
      else:
        bestMatch = getEpisodeTitle(title)
        titlecache[title] = bestMatch
      
      if showcache.has_key(bestMatch):
        show = showcache[bestMatch]
      else:
        show = EpGuidesSearch(bestMatch, debugfile=debugfile, debug=(args.debug is not None), verbose=args.verbose)
        showcache[bestMatch] = show

      # search epguides.com for the specific episode
      result = show.search(season, episode)
      
      if len(result) == 0:
        print 'No results for %s Season %s episode %s' % (bestMatch, season, episode)
        continue

      newname = "%s S%sE%s %s.%s" % (bestMatch, groups[1], groups[2], result[0]['title'].lstrip('"').rstrip('"'), groups[-1])

      destpath = "%s/%s/Season %s" % (dest, bestMatch, season)
      destination = "%s/%s" % (destpath, newname)

      if args.confirm:
        rename = getYesNo("Move %s to %s? " % (file, destination))
      else:
        rename = True

      if rename:
        if args.script:
          s = open(args.script, 'a')
          cmd = '# %s' % newname
          
          if not destpathcache.has_key(destpath):
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

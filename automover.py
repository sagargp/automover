if __name__ == '__main__':
	import re, os, sys, argparse
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
	
	arg_parser = argparse.ArgumentParser(description='Automatically rename and move a downloaded TV show')
	arg_parser.add_argument('--dest', nargs=1, help='The destination directory')
	arg_parser.add_argument('--file', nargs='+', help='The filename of the TV show to move')
	arg_parser.add_argument('--title', nargs='+', help='Optionally hint the title of the show')
	arg_parser.add_argument('--confirm', action='store_true', help='Ask before processing a file (for use in batch scripts)')
	arg_parser.add_argument('--yes' , action='store_true', help='Answer yes to questions (except --confirm questions)')
	arg_parser.add_argument('--script', nargs='?', help='Write a move script instead of performing the moves')
	args = arg_parser.parse_args(sys.argv[1:])

	dest = ''.join(args.dest)
	fullpath = ' '.join(args.file)
	fullpath = fullpath.split('/')
	filename = fullpath[-1]
	filepath = ''.join(fullpath[0:-1])

	if args.confirm:
		if not getYesNo("Process %s? " % filename):
			exit()

	if not args.title:
		mindist = None
		bestMatch = ""
		for file in os.listdir(dest):
			match = editDistance(filename, file)
			if match < mindist or mindist is None:
				mindist = match
				bestMatch = file
	else:
		bestMatch = ''.join(args.title)
	
	reg = re.compile("s(\d+)e(\d+)", flags=re.IGNORECASE)
	pattern = reg.search(filename)
	extension = filename.split('.')[-1]
	ref = pattern.groups()
	season = ref[0].lstrip('0')
	episode = ref[1].lstrip('0')

	show = EpGuidesSearch(bestMatch)

	result = show.search(season, episode)
	newname = "%s S%sE%s %s.%s" % (bestMatch, ref[0], ref[1], result[0]['title'].lstrip('"').rstrip('"'), extension)

	destinationpath = "%s/%s/Season %s" % (dest, bestMatch, season)
	destination = "%s/%s" % (destinationpath, newname)

	if args.yes:
		rename = True
	else:
		rename = getYesNo("Move %s to %s? " % (filename, destination))

	if rename:
		if args.script:
			s = open(args.script, 'a')
			cmd = '# %s' % newname 

			if not os.path.isdir(destinationpath):
				cmd = cmd + '\nmkdir -p "%s"' % destinationpath

			cmd = cmd + '\nmv "%s" "%s"\n\n' % ('/'.join(fullpath), destination)
			
			s.write(cmd)
		else:
			if not os.path.isdir(destinationpath):
				os.mkdir(destinationpath)
			os.rename('/'.join(fullpath), destination)	
	else:
		print "Ok... doing nothing"


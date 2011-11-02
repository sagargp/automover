import re, os, sys
import tvrenamer as T
from editDistance import editDistance

if __name__ == '__main__':
	import sys, os, argparse
	
	arg_parser = argparse.ArgumentParser(description='Automatically rename and move a downloaded TV show')
	arg_parser.add_argument('--dest', nargs=1, help='The destination directory')
	arg_parser.add_argument('--file', nargs=1, help='The filename of the TV show to move')
	args = arg_parser.parse_args(sys.argv[1:])

	dest = ''.join(args.dest)
	fullpath = ''.join(args.file)
	fullpath = fullpath.split('/')
	filename = fullpath[-1]
	filepath = ''.join(fullpath[0:-1])

	mindist = None
	bestMatch = ""
	for file in os.listdir(dest):
		match = editDistance(filename, file)
		if match < mindist or mindist is None:
			mindist = match
			bestMatch = file
	
	reg = re.compile("s(\d+)e(\d+)", flags=re.IGNORECASE)
	pattern = reg.search(filename)
	extension = filename.split('.')[-1]
	ref = pattern.groups()
	season = ref[0].lstrip('0')
	episode = ref[1].lstrip('0')

	show = T.EpGuidesSearch(bestMatch)
	result = show.search(season, episode)
	newname = "%s S%sE%s %s.%s" % (bestMatch, ref[0], ref[1], result[0]['title'].lstrip('"').rstrip('"'), extension)

	destination = "%s/%s/Season %s/%s" % (dest, bestMatch, season, newname)
	print "I want to move the input file to %s" % destination
	
	while True:
		yn = raw_input("Should I do this? ")
		
		if (yn == 'y'):
			rename = True
			break
		elif (yn == 'n'):
			rename = False
			break
		else:
			rename = False
			print "Please answer 'y' or 'n'"

	if rename
		os.rename('/'.join(fullpath), destination)	
	else:
		print "Ok... doing nothing"


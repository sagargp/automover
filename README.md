Automover tries to figure out what show, season, and episode a file represents. It them renames the file as "Show S01E02 Episode Title.avi" and moves it to a configurable destination. To help figure out the title of the show, Automover uses the destination path as a dictionary and checks which folder most closely matches the filename.

    usage: automover.py [-h] [--conf CONF] [--confirm] [--debug DEBUG]
                        [--forcetitle FORCETITLE] [--inplace] [--read]
                        [--script [SCRIPT]] [--verbose]
                        searchpath
    
    Automatically rename and move TV shows
    
    positional arguments:
      searchpath            The file or directory to process
    
    optional arguments:
      -h, --help            show this help message and exit
      --conf CONF           Path to the config file
      --confirm             Ask before doing anything
      --debug DEBUG         Write output to a debug files
      --forcetitle FORCETITLE
                            Force a TV show match
      --inplace             Rename files in place
      --read                Take filenames from STDIN
      --script [SCRIPT]     Write a bash script
      --verbose             Verbose output

**Examples:**

    $ automover --script move.sh
    $ sh mover.sh

---

    $ find . -iname "Arrested Development*.avi" -not -iname "*sample*" | \
    automover --script move.sh --forcetitle ArrestedDevelopment --read
    $ sh mover.sh

**Make sure to check mover.sh for errors before running it!**

Future plans:
* Also output an 'undo' script that unmoves the object.
* Check that we're not overwriting any destination files, if so, utter a warning and back it up.
* ~~Handle formats like modern.family.302.hdtv.xvid-lol.avi~~ DONE!

import sgmllib
from ConfigParser import RawConfigParser

class DummyConfigParser(RawConfigParser):
  """
  Returns a configuration object with default values without
  actually parsing a real config file. Used for testing.
  """
  def __init__(self):
    RawConfigParser.__init__(self)

    self.add_section('main')
    self.set('main', 'destination', 'test/dest/')

    self.add_section('patterns')
    self.set('patterns', 'pattern_1', '(.*)s(\d+)e(\d+).*(mkv|avi)')
    self.set('patterns', 'pattern_2', '(.*)\.?(\d{1,2})(\d\d).*(mkv|avi)')
    self.set('patterns', 'exclude', '.*sample.*')

class EpGuidesParser(sgmllib.SGMLParser):
  """
  Parses an epguides.com TV show page and enables retrieving
  a CSV listing of all the episodes of the given show.
  """
  def __init__(self):
    sgmllib.SGMLParser.__init__(self)
    self.hyperlinks = []
    self.epcsv = ''
    self.inside_pre = 0

  def parse(self, s):
    self.feed(s)
    self.close()

  def handle_data(self, data):
    if self.inside_pre:
      self.epcsv = self.epcsv + data

  def start_pre(self, attributes):
    self.inside_pre = 1

  def end_pre(self):
    self.inside_pre = 0

  def start_a(self, attributes):
    for name, value in attributes:
      if name == 'href':
        self.hyperlinks.append(value)

  def get_hyperlinks(self):
    return self.hyperlinks

  def get_eps_csv(self):
    return self.epcsv.splitlines()

  def reset_data(self):
    self.inside_pre = 0
    self.epcsv = ''
    self.hyperlinks = []

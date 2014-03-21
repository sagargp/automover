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
    self.set('patterns', 'pattern_1', '(.*)s(\d+)e(\d+).*(mkv|avi|mp4)')
    self.set('patterns', 'pattern_2', '(.*)\.?(\d{1,2})(\d\d).*(mkv|avi|mp4)')
    self.set('patterns', 'exclude', '.*sample.*')

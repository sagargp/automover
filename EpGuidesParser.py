import sgmllib


class EpGuidesParser(sgmllib.SGMLParser):
  def __init__(self, verbose=0):
    sgmllib.SGMLParser.__init__(self, verbose)
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

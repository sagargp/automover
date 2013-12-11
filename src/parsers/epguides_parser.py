#!/usr/bin/python -tt
# coding=utf-8
"""
Parser for the data from epguides.com
"""
import abstract_parser.abstract_parser
import HTMLParser

# noinspection PyClassicStyleClass
class EpGuidesHTMLParser(HTMLParser.HTMLParser):
  """
  Class to be used for aggregation to keep it separate from the ABC Parser
  """
  def __init__(self):
    HTMLParser.HTMLParser.__init__(self)
    self.hyperlinks = []
    self.epcsv = ""
    self.inside_pre = False

  def handle_starttag(self, tag, attrs):
    """
    @rtype : object
    @type tag: str
    @type attrs: list
    """
    if tag.upper() == "PRE":
      self.inside_pre = True
    elif tag.upper() == "A":
      for attr in attrs:
        if attr[0].upper() == "HREF":
          self.hyperlinks.append(attr[1])

  def handle_endtag(self, tag):
    """
    @type tag: str
    """
    if tag.upper() == "PRE":
      self.inside_pre = False

  def handle_data(self, data):
    """
    @rtype : object
    @type data: str
    """
    if self.inside_pre:
      self.epcsv += data

  @property
  def get_hyperlinks(self):
    """
    @return: @rtype:
    """
    return self.hyperlinks

  @property
  def get_eps_csv(self):
    """
    @rtype : object
    @return:
    """
    return self.epcsv.splitlines()

  def parse(self, data):
    """
    @type data: str
    """
    self.feed(data)
    self.close()

  def reset(self):
    # noinspection PyCallByClass,PyTypeChecker
    """
    @rtype : object
    """
    HTMLParser.HTMLParser.reset(self)
    self.inside_pre = 0
    self.epcsv = ""
    self.hyperlinks = []

class EpGuidesParser(abstract_parser):
  """
  New-style class used to implement the Parser abstract base class interface
  """
  def __init__(self):
    """
    @rtype : object
    """
    super(EpGuidesParser, self).__init__()
    self.data = None
    self.html_parser = EpGuidesHTMLParser()

  def parse(self, data):
    """
    @rtype : object
    @type data: str
    """
    self.data = data
    self.html_parser.parse(self.data)

  @property
  def get_hyperlinks(self):
    """
    @rtype : object
    @return:
    """
    return self.html_parser.get_hyperlinks

  @property
  def get_eps_csv(self):
    """
    @rtype : object
    @return:
    """
    return self.html_parser.get_eps_csv

  def reset_data(self):
    """
    @rtype : object
    @return:
    """
    self.html_parser.reset()

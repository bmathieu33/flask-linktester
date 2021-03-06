# -*- coding: utf-8 -*-
"""
Test a Flask application by following on all the links.

Some links may be blacklisted to avoid side effects.
"""

from HTMLParser import HTMLParser
import urlparse
from fnmatch import fnmatch


__all__ = ['LinkTester']


class LinkExtractor(HTMLParser):

  def __init__(self):
    HTMLParser.__init__(self)
    self.links = set()

  def handle_starttag(self, tag, attrs):
    for attr_name, attr_value in attrs:
      if (tag, attr_name) in [('a', 'href'), ('link', 'href'),
                              ('script', 'src'), ('img', 'src')]:
        url = attr_value
        scheme = urlparse.urlparse(url).scheme
        if scheme != '':
          continue
        link = urlparse.urldefrag(url)[0]
        self.links.add(link)


class LinkTester(object):

  _black_list = set(["/logout"])

  def __init__(self, client):
    self.client = client
    self.link_map = {}
    self.to_visit = set()
    self.black_list = self._black_list.copy()
    self.visited = set()
    self.allowed_codes = set([200, 301])
    self.verbosity = 0
    self.max_links = 100

  def crawl(self, root):
    self.to_visit = set([root])

    while self.to_visit and len(self.visited) <= self.max_links:
      url = self.to_visit.pop()
      if url in self.visited:
        continue

      if self.verbosity >= 1:
        print "Crawling URL:", url

      try:
        response = self.client.get(url)
      except:
        print "Error fetching URL:", url
        raise

      if self.verbosity >= 2:
        print "  Got response:", response

      status_code = response.status_code
      assert status_code in self.allowed_codes,\
        "Response from URL %s was %s" % (url, response.status_code)

      if self.verbosity >= 2:
        print "  Got content-type:", response.content_type
      if self.verbosity >= 3:
        print "  Got body:", response.data

      if not response.content_type.startswith('text/html'):
        continue

      charset = (response.content_type.rsplit('=', 1)[1]
                 if 'charset=' in response.content_type
                 else 'ISO-8859-1')

      self.visited.add(url)
      parser = LinkExtractor()
      parser.feed(response.data.decode(charset))

      if self.verbosity >= 2:
        print "  Found links:", parser.links

      for new_link in parser.links:
        if not new_link.startswith("/"):
          new_link = urlparse.urljoin(url, new_link)
        if self.blacklisted(new_link):
          continue
        if new_link not in self.visited:
          self.add_link(url, new_link)

  def blacklisted(self, url):
    for path in self.black_list:
      if fnmatch(url, path):
        return True
    return False

  def add_link(self, current_url, link):
    if not link in self.to_visit:
      self.to_visit.add(link)
      if self.verbosity >= 1:
        print "Adding new link:", link, "from page:", current_url

    self.link_map.setdefault(current_url, set()).add(link)

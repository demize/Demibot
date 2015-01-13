"""
Thanks to robert at StackOverflow, who posted [this answer ](http://stackoverflow.com/a/13703994/1394898) for this code!
"""

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def handle_entityref(self, name):
        self.fed.append('&%s;' % name)
    def get_data(self):
        return ''.join(self.fed)

def html_to_text(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

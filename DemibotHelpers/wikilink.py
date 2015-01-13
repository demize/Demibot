class Wikilink(object):
    def __init__(self, wikilink):
        if not isinstance(wikilink, str):
            raise BadWikilinkException("Wikilink not a string")
        if not wikilink[:2] == "[[" or not wikilink[-2:] == "]]":
            raise BadWikilinkException("No wikilink in supplied string")
        self.wikilink = wikilink

    def getLinkText(self):
        if "|" not in self.wikilink:
            return self.wikilink[2:-2]
        text = self.wikilink.split("|", 1)[1][:-2]
        if text == "":
            return self.wikilink.split("|", 1)[0].split(":", 1)[1]
        return text

    def getLinkTarget(self):
        if "|" not in self.wikilink:
            return self.wikilink[2:-2]
        else:
            return self.wikilink.split("|")[0][2:]

class BadWikilinkException(Exception):
    pass

#!/usr/bin/python

##########################
#Main Demibot source file#
#     Copyright 2014     #
#    See LICENSE file    #
##########################

from wikitools import wiki, categoty, page, pagelist
from DemibotHelpers.utc import UTC
import re
import datetime
import urllib


# Important variables
pword = ""
uname = "Demibot"
regex1 = re.compile("^== ?(.*?) ?==$([\\n\\S\\s]*?)(?=(?:^== ?.*? ?==$)|(?:\\Z))", re.M | re.U) # regex for finding headers and replies
regex2 = re.compile(".*?(?P<hours>\\d{1,2}):(?P<minutes>\\d{1,2}), (?P<day>\\d{1,2}) (?P<month>[\\w]*) (?P<year>\\d{4}) \\(?UTC\\)?") # regex for finding timestamps
lowDate = datetime.datetime(1, 1, 1, 0, 0, 0, 0, UTC())
highDate = datetime.datetime(9999, 12, 31, 23, 59, 59, 0, UTC())
unixDate = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, UTC())

# Important functions
def parsemonth(m):
    m = m.lower()
    return {
        'january' : 1,
        'february' : 2,
        'march' : 3,
        'april' : 4,
        'may' : 5,
        'june' : 6,
        'july' : 7,
        'august' : 8,
        'september' : 9,
        'october' : 10,
        'november' : 11,
        'december' : 12,
    }[m]

def dotalkpage(talkpage, rowformat):
    for (topic, replies) in regex1.findall(talkpage.getWikiText()):
        out = out + "\n" + rowformat
        numReplies = 1
        lowestDate = highDate
        highestDate = lowDate
        for line in replies.splitlines():
            if line.startswith(":"):
                numReplies = numReplies +1
            m = regex2.match(line)
            if m is not None:
                currentDate = datetime.datetime(int(m.group("year")), parsemonth(m.group("month")), int(m.group("day")), int(m.group("hours")), int(m.group("minutes")), 0, 0, UTC())
                if currentDate < lowestDate:
                    lowestDate = currentDate
                if currentDate > highestDate:
                    highestDate = currentDate
        link = "[[" + talkpage.title + "#" + urllib.quote_plus(topic).replace("+", "_") + "]]"
        fmt = "%Y-%m-%d %H:%M:%S"
        first = lowestDate.strftime(fmt)
        firstepoch = (lowestDate - unixDate).total_seconds()
        lastepoch = (highestDate - unixDate).total_seconds()
        last = highestDate.strftime(fmt)
        duration = highestDate - lowestDate
        out.replace("%%topic%%:", topic)
        out.replace("%%replies%%:", numReplies)
        out.replace("%%link%%:", link)
        out.replace("%%first%%:", first)
        out.replace("%%firstepoch%%:", firstepoch)
        out.replace("%%lastepoch%%:", lastepoch)
        out.replace("%%last%%:", last)
        out.replace("%%duration%%:", duration)
    return out

# The main program itself

with open("password.secret", "r") as pwfile:
    pword = pwfile.readline().split('\n', 1)[0]

site = wiki.Wiki("https://en.wikipedia.org/w/api.php")
site.setUserAgent("Demibot/0.1 (https://github.com/demize/Demibot; demize on enwiki) using Python and Wikitools")
site.login(uname, pword)

logpage = page.Page(site, title="User:Demibot/log")
#logpage.edit(appendtext="~~~~~: Logged in to Wikipedia<br />\n")

params = {"action" : "query", "generator" : "prefixsearch", "gpssearch" : "User_Talk:Demize/Archive"}
request = api.APIRequest(site, params)
result = request.query()
pages = pagelist.listFromQuery(site, result["query"]["pages"])
rowformat = "|-\n| %%topic%% || %%replies%% || %%link%%"

for talkpage in pages:
    print dotalkpage(talkpage, rowformat)

exit(0)

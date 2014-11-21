#!/usr/bin/python

##########################
#Main Demibot source file#
#     Copyright 2014     #
#    See LICENSE file    #
##########################

from wikitools import wiki
from wikitools import category
from wikitools import page
from DemibotHelpers.utc import UTC
import re
import datetime
import urllib

#Doesn't do anything yet other than log that it logged in and quit.
#Planned: modify template {{User:HBC Archive Indexerbot/OptIn}} to add
# a category to each page 
# ("Category:Wikipedia talk pages requiring archive indexing" maybe?)
# then have the bot sort through that and generate an index.


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

pword = ""
uname = "Demibot"
regex1 = re.compile("^== ?(.*?) ?==$([\\n\\S\\s]*?)(?=(?:^== ?.*? ?==$)|(?:\\Z))", re.M | re.U) # regex for finding headers and replies
regex2 = re.compile(".*?(?P<hours>\\d{1,2}):(?P<minutes>\\d{1,2}), (?P<day>\\d{1,2}) (?P<month>[\\w]*) (?P<year>\\d{4}) \\(?UTC\\)?") # regex for finding timestamps
lowDate = datetime.datetime(1, 1, 1, 0, 0, 0, 0, UTC())
highDate = datetime.datetime(9999, 12, 31, 23, 59, 59, 0, UTC())
unixDate = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, UTC())

with open("password.secret", "r") as pwfile:
    pword = pwfile.readline().split('\n', 1)[0]

site = wiki.Wiki("https://en.wikipedia.org/w/api.php")
site.login(uname, pword)

logpage = page.Page(site, title="User:Demibot/log")
#logpage.edit(appendtext="~~~~~: Logged in to Wikipedia<br />\n")

talkpage = page.Page(site, title="User Talk:Demize/Archive 1")

for (topic, replies) in regex1.findall(talkpage.getWikiText()):
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
    print "%%topic%%:", topic
    print "%%replies%%:", numReplies
    print "%%link%%:", link
    print "%%first%%:", first
    print "%%firstepoch%%:", firstepoch
    print "%%lastepoch%%:", lastepoch
    print "%%last%%:", last
    print "%%duration%%:", duration

exit(0)

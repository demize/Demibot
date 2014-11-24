#!/usr/bin/python

##########################
#Main Demibot source file#
#     Copyright 2014     #
#    See LICENSE file    #
##########################

from wikitools import wiki, category, page, pagelist, api
from DemibotHelpers.utc import UTC
import re
import datetime
import urllib


# Important variables
pword = ""
uname = "Demibot"
regex1 = re.compile("^== ?(.*?) ?==$([\\n\\S\\s]*?)(?=(?:^== ?.*? ?==$)|(?:\\Z))", re.M | re.U) # regex for finding headers and replies
regex2 = re.compile(".*?(?P<hours>\\d{1,2}):(?P<minutes>\\d{1,2}), (?P<day>\\d{1,2}) (?P<month>[\\w]*) (?P<year>\\d{4}) \\(?UTC\\)?") # regex for finding timestamps
regex3 = re.compile("{{User:HBC Archive Indexerbot/OptIn(?P<arguments>[\\s\\S]*?)}}")
regex4 = re.compile("^<!-- (?P<section>[\\S\\s]*?) -->$\n*(?P<form>[\\n\\S\\s]*?)\\n*?(?=(?:<!-- [\\S\\s]*? -->$)|(?:\\Z))", re.M | re.U)
lowDate = datetime.datetime(1900, 1, 1, 0, 0, 0, 0, UTC()) # Hopefully no comment dates are lower than January 1st, 1900
highDate = datetime.datetime(9999, 12, 31, 23, 59, 59, 0, UTC()) # Or higher than 23:59:59 December 31st, 9999
unixDate = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, UTC()) # Used for getting the epoch time of comments

# Log in and set up logging

with open("password.secret", "r") as pwfile:
    pword = pwfile.readline().split('\n', 1)[0]

site = wiki.Wiki("https://en.wikipedia.org/w/api.php")
site.setUserAgent("Demibot/0.1 (https://github.com/demize/Demibot; demize on enwiki) using Python and Wikitools")
site.login(uname, pword)

logpage = page.Page(site, title="User:Demibot/log")
logpage.edit(appendtext="~~~~~: Logged in to Wikipedia<br />\n")

# Important functions

# Write to the log page

def log(logtext):
    logpage.edit(appendtext="~~~~~: " + logtext + "<br />\n")

# Returns a numeric value for each month
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

# Creates table rows for a talkpage based on two defined row formats
def dotalkpage(talkpage, rowformat1, rowformat2):
    out = ""
    row = 1
    for (topic, replies) in regex1.findall(talkpage.getWikiText()):
        if row == 1:
            out = out + "\n" + rowformat1
            row = 2
        elif row == 2:
            out = out + "\n" + rowformat2
            row = 1
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
        out = out.replace("%%topic%%", str(topic))
        out = out.replace("%%replies%%", str(numReplies))
        out = out.replace("%%link%%", str(link))
        out = out.replace("%%first%%", str(first))
        out = out.replace("%%firstepoch%%", str(firstepoch))
        out = out.replace("%%lastepoch%%", str(lastepoch))
        out = out.replace("%%last%%", str(last))
        out = out.replace("%%duration%%", str(duration))
    return out

def parsetemplate(templatepage):
    template = {}
    for (section, form) in regex4.findall(templatepage.getWikiText()):
        if section == "END":
            continue
        elif section == "LEAD":
            template['lead'] = form
        elif section == "HEADER":
            template['header'] = form
        elif section == "ROW":
            template['row'] = form
        elif section == "ALT ROW":
            template['altrow'] = form
        elif section == "FOOTER":
            template['footer'] = form
        elif section == "TAIL":
            template['tail'] = form
        else:
            continue

    if not template.has_key('lead'):
        template['lead'] = ""
    if not template.has_key('header'):
        template['header'] = ""
    if not template.has_key('row'):
        template['row'] = ""
    if not template.has_key('altrow'):
        template['altrow'] = template['row']
    if not template.has_key('footer'):
        template['footer'] = ""
    if not template.has_key('tail'):
        template['tail'] = ""
    return template

# The main program itself

params = {"action" : "query", "generator" : "embeddedin", "geititle" : "User:HBC_Archive_Indexerbot/OptIn", "geinamespace" : "1|3|5|7|9", "geilimit" : "500", "rawcontinue" : ""}
request = api.APIRequest(site, params)
log("Building list of talk pages to index the archives of...")
result = request.query()
list = pagelist.listFromQuery(site, result['query']['pages'])

log("List of pages contains " + str(len(list)) + " pages.")
log("Generating index for User Talk:Demize only.")

currentpage = page.Page(site, title="User Talk:Demize")
arguments = regex3.search(currentpage.getWikiText()).group(0).replace("\n", "").replace("}", "").replace("{", "").split("|")


target = ""
pages = []
masks = ""
zeros = 0
indexhere = False
templatepage = page.Page(site, title="User:HBC_Archive_Indexerbot/default_template")

# Make sure we get the leading zeros first
for arg in arguments:
    argparts = arg.split("=", 1)
    argparam = argparts[0].lower()
    if argparam == "leading_zeros":
        zeros = int(argparts[1])
        break

# Now loop through everything else
for arg in arguments:
    argparts = arg.split("=", 1)
    argparam = argparts[0].lower()
    if len(argparts) < 2:
        continue

    if argparam == "target":
        if argparts[1].startswith("/"):
            target = currentpage.title + argparts[1]
        else:
            target = argparts[1]
    elif argparam == "mask": # Multiple masks are supported
        if "<#>" not in argparts[1]:
            pages.append(page.Page(site, title=argparts[1]))
            masks = masks + ", " + argparts[1]
        else:
            archivenum = 1
            prefix = ""
            if argparts[1].startswith("/"):
               prefix = currentpage.title
            archivepage = page.Page(site, title=prefix + argparts[1].replace("<#>", str(archivenum).zfill(zeros + 1)))
            while archivepage.exists:
                pages.append(archivepage)
                archivenum = archivenum + 1
                archivepage = page.Page(site, title=prefix + argparts[1].replace("<#>", str(archivenum).zfill(zeros + 1)))
            masks = masks + ", " + argparts[1]
    elif argparam == "indexhere" and not indexhere:
        if argparts[1] == "yes":
            indexhere = True
            pages.append(currentpage)
        masks = masks + ", " + currentpage.title
    elif argparam == "template":
        newtemplate = argparts[1].replace("[", "").replace("]", "")
        if newtemplate.startswith("/"):
            templatepage = page.Page(site, title=currentpage+newtemplate)
        elif newtemplate.startswith("./"):
            templatepage = page.Page(site, title=currentpage+newtemplate[1:])
        else:
            templatepage = page.Page(site, title=newtemplate)

if masks.startswith(","):
    masks = masks[2:]

targetpage = page.Page(site, title=target)

template = parsetemplate(templatepage)

rowformat1 = template['row']
rowformat2 = template['altrow']

boilerplate = "This is report was generated because of the request on " + currentpage.title + ". It matches the masks '''" + masks + "'''.<br />\n"
boilerplate = boilerplate + "This report was generated at ~~~~~ by [[User:Demibot|Demibot]].<br />\n"

outbuf = str(template['lead'] + "<br />\n" + boilerplate + template['header'] + "\n")

for talkpage in pages:
    outbuf = str(outbuf + dotalkpage(talkpage, rowformat1, rowformat2))

outbuf = str(outbuf +"\n" + template['footer'] + "<br />\n" + template['tail'])

log("Writing archive index to " + targetpage.title + "...")

targetpage.edit(text=outbuf)

exit(0)

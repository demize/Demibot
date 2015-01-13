#!/usr/bin/python

##########################
#Main Demibot source file#
#     Copyright 2014     #
#    See LICENSE file    #
##########################

from wikitools import wiki, category, page, pagelist, api
from wikitools.page import NoPage, Page
from DemibotHelpers.utc import UTC
from DemibotHelpers.wikilink import Wikilink, BadWikilinkException
from DemibotHelper import MLStripper
import sys, os
import re
from datetime import datetime, timedelta
import urllib


# Important variables
pword = ""
uname = "Demibot"
regex1 = re.compile("^={2,} ?(.*?) ?={2,}$([\\n\\S\\s]*?)(?=(?:^={2,} ?.*? ?={2,}$)|(?:\\Z))", re.M | re.U) # regex for finding headers and replies
regex2 = re.compile(".*?(?P<hours>\\d{1,2}):(?P<minutes>\\d{1,2}), (?P<day>\\d{1,2}) (?P<month>[\\w]*) (?P<year>\\d{4}) \\(?UTC\\)?") # regex for finding timestamps
regex3 = re.compile("{{User:HBC Archive Indexerbot/OptIn(?P<arguments>[\\s\\S]*?)}}") # regex for processing the Optin template
regex4 = re.compile("^<!-- (?P<section>[\\S\\s]*?) -->$\n*(?P<form>[\\n\\S\\s]*?)\\n*?(?=(?:<!-- [\\S\\s]*? -->$)|(?:\\Z))", re.M | re.U) # regex for processing the index template
regex5 = re.compile("(\\[\\[.*?\\]\\])")
lowDate = datetime(1900, 1, 1, 0, 0, 0, 0, UTC()) # Hopefully no comment dates are lower than January 1st, 1900
highDate = datetime(9999, 12, 31, 23, 59, 59, 0, UTC()) # Or higher than 23:59:59 December 31st, 9999
unixDate = datetime(1970, 1, 1, 0, 0, 0, 0, UTC()) # Used for getting the epoch time of comments

# Log in and set up logging

with open("password.secret", "r") as pwfile:
    pword = pwfile.readline().split('\n', 1)[0]

site = wiki.Wiki("https://en.wikipedia.org/w/api.php")
site.setUserAgent("Demibot/0.1 (https://github.com/demize/Demibot; demize on enwiki) using Python and Wikitools")
site.login(uname, pword)

logpage = page.Page(site, title="User:Demibot/log")
logpage.edit(text="~~~~~: Logged in to Wikipedia<br />\n", summary="Restarting log for new run")

# Important functions

# Parse wikilinks using the Wikilink class.
def replWikilink(match):
    return Wikilink(match.group(0)).getLinkText()

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

def formatduration(duration):
    if isinstance(duration, str):
        return duration
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days > 30:
        weeks, days = divmod(days, 7)
        return "{0} weeks, {1} days, {2} hours, {3} minutes".format(weeks, days, hours, minutes)
    return "{0} days, {1} hours, {2} minutes".format(days, hours, minutes)

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
                currentDate = datetime(int(m.group("year")), parsemonth(m.group("month")), int(m.group("day")), int(m.group("hours")), int(m.group("minutes")), 0, 0, UTC())
                if currentDate < lowestDate:
                    lowestDate = currentDate
                if currentDate > highestDate:
                    highestDate = currentDate
        link = "[[" + talkpage.title + "#" + urllib.quote_plus(topic).replace("+", "_") + "]]"
        fmt = "%Y-%m-%d %H:%M:%S"

        if lowestDate == highDate or highestDate == lowDate:
            first = "Not Applicable"
            firstepoch = "Not Applicable"
            last = "Not Applicable"
            lastepoch = "Not Applicable"
            duration = "Not Applicable"
        else:
            first = lowestDate.strftime(fmt)
            firstepoch = (lowestDate - unixDate).total_seconds()
            lastepoch = (highestDate - unixDate).total_seconds()
            last = highestDate.strftime(fmt)
            duration = highestDate - lowestDate
        out = out.replace("%%topic%%", str(topic))
        out = out.replace("%%replies%%", str(numReplies))
        out = out.replace("%%link%%", MLStripper.html_to_text(regex5.sub(replWikilink, str(link))))
        out = out.replace("%%first%%", str(first))
        out = out.replace("%%firstepoch%%", str(firstepoch))
        out = out.replace("%%lastepoch%%", str(lastepoch))
        out = out.replace("%%last%%", str(last))
        out = out.replace("%%duration%%", formatduration(duration))
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

# Make a list of all the pages to index the archives of
'''params = {"action" : "query", "generator" : "embeddedin", "geititle" : "User:HBC_Archive_Indexerbot/OptIn", "geinamespace" : "1|3|5|7|9", "geilimit" : "500", "rawcontinue" : ""}
request = api.APIRequest(site, params)
log("Building list of talk pages to index the archives of...")
result = request.query()
list = pagelist.listFromQuery(site, result['query']['pages'])'''

titles = ["User_Talk:Demize", "User_Talk:-revi", "User_talk:Addshore"]
log("Building manual list of talk pages to index the archives of...")
list = pagelist.listFromTitles(site, titles)

log("List of pages contains " + str(len(list)) + " pages.")
log("Beginning index generation...")

for currentpage in list:
    try:
        # Get the list of arguments provided in the template on the talk page
        arguments = regex3.search(currentpage.getWikiText()).group(0).replace("\n", "").replace("}", "").replace("{", "").split("|")
        # Set up variables for processing
        target = "" # The target page
        pages = [] # The list of pages to generate indexes of
        masks = "" # The list of masks used
        zeros = 0 # The number of leading zeros
        indexhere = False # Whether or not to index currentpage
        templatepage = page.Page(site, title="User:HBC_Archive_Indexerbot/default_template") # The template to use
        skip = False # Whether or not we've had any reason to skip the talk page

        # Make sure we get the leading zeros first
        for arg in arguments:
            argparts = arg.split("=", 1)
            argparam = argparts[0].lower() # Much easier to compare if it's all lowercase
            if argparam == "leading_zeros":
                zeros = int(argparts[1])
                break

        # Now loop through everything else
        for arg in arguments:
            argparts = arg.split("=", 1)
            argparam = argparts[0].lower()
            if len(argparts) < 2: # No use for us to check parameters if they're empty
                continue
            if argparam == "target":
                if argparts[1].startswith("/"):
                    target = page.Page(site, currentpage.title + argparts[1].rstrip())
                else:
                    target = page.Page(site, argparts[1].rstrip())
                if not target.exists:
                    log("Not creating page " + target.title + "...")
                    skip = True
                    break
                elif not ("<!-- Demibot can blank this -->" in target.getWikiText() or "<!-- Legobot can blank this -->" in target.getWikiText() or "<!-- HBC Archive Indexerbot can blank this -->" in target.getWikiText()):
                    log("Target index page " + target.title + " doesn't have the permission tag on it, skipping...")
                    skip = True
                    break
            elif argparam == "mask": # Multiple masks are supported
                if "<#>" not in argparts[1]:
                    prefix = ""
                    if argparts[1].startswith("/"):
                       prefix = currentpage.title
                    pages.append(page.Page(site, title=prefix + argparts[1].rstrip()))
                    masks = masks + ", " + argparts[1].rstrip()
                else:
                    archivenum = 1
                    prefix = ""
                    if argparts[1].startswith("/"):
                       prefix = currentpage.title
                    archivepage = page.Page(site, title=prefix + argparts[1].rstrip().replace("<#>", str(archivenum).zfill(zeros + 1)))
                    while archivepage.exists:
                        pages.append(archivepage)
                        archivenum = archivenum + 1
                        archivepage = page.Page(site, title=prefix + argparts[1].rstrip().replace("<#>", str(archivenum).zfill(zeros + 1)))
                    masks = masks + ", " + argparts[1]
            elif argparam == "indexhere" and not indexhere: # Only add the current page to the list once
                if argparts[1].rstrip() == "yes":
                    indexhere = True
                    pages.append(currentpage)
                masks = masks + ", " + currentpage.title
            elif argparam == "template":
                newtemplate = argparts[1].rstrip().replace("[", "").replace("]", "")
                if newtemplate.startswith("/"):
                    templatepage = page.Page(site, title=currentpage+newtemplate)
                elif newtemplate.startswith("./"):
                    templatepage = page.Page(site, title=currentpage+newtemplate[1:])
                else:
                    templatepage = page.Page(site, title=newtemplate)
        if not isinstance(target, Page):
            log("No target specified on page " + currentpage.title + ", skipping...")
            continue
        if skip:
            continue

        if masks.startswith(","): # Fairly tautologic, but good to check anyway
            masks = masks[2:]
        try:
            template = parsetemplate(templatepage)
        except NoPage as error:
            log("Template provided on " + currentpage.title + " does not exist, skipping generation of index...")
            continue
        boilerplate = "<!-- Demibot can blank this -->\nThis report was generated because of the request on " + currentpage.title + ". It matches the masks '''" + masks + "'''.<br />\n"
        boilerplate = boilerplate + "This report was generated at ~~~~~ by [[User:Demibot|Demibot]].<br />\n"
        outbuf = str(template['lead'] + "<br />\n" + boilerplate + template['header'] + "\n")
        for talkpage in pages:
            try:
                outbuf = str(outbuf + dotalkpage(talkpage, template['row'], template['altrow']))
            except NoPage as error:
                log("The page " + talkpage.title + " does not exist. Typo?")
        outbuf = str(outbuf +"\n" + template['footer'] + "<br />\n" + template['tail'])
        log("Writing archive index to " + target.title + "...")
        target.edit(text=outbuf, summary="Generating archive index due to user request) (bot")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log("An unexpected error occurred, skipping page" + currentpage.title)
        log("The details of the error are: " + str(exc_type) + " at " + str(exc_tb.tb_lineno) + "(\"" + str(e) + "\")")
        continue

exit(0)

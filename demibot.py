#!/usr/bin/python

##########################
#Main Demibot source file#
#     Copyright 2014     #
#    See LICENSE file    #
##########################

from wikitools import wiki
from wikitools import category
from wikitools import page

#Doesn't do anything yet other than log that it logged in and quit.
#Planned: modify template {{User:HBC Archive Indexerbot/OptIn}} to add
# a category to each page 
# ("Category:Wikipedia talk pages requiring archive indexing" maybe?)
# then have the bot sort through that and generate an index.

pword = ""
uname = "Demibot"

with open("password.secret", "r") as pwfile:
    pword = pwfile.readline().split('\n', 1)[0]

site = wiki.Wiki("https://en.wikipedia.org/w/api.php")
site.login(uname, pword)

logpage = page.Page(site, title="User:Demibot/log")
logpage.edit(appendtext="~~~~~: Logged in to Wikipedia<br />\n")

exit(0)

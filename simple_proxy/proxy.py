#! /usr/bin/env python
#
# This will route a webpage and all of it's included url
# calls through this proxy.
#
# Usage (URL Format): [ip address]:[port]/[website address]
# e.g. localhost:8000/www.example.com/file/path?query

import logging
import requests
import time

import click
import cssutils
from bs4 import BeautifulSoup
from tornado import web
from uritools import urisplit, urijoin

class MainHandler(web.RequestHandler):
    def initialize(self, verbosity):
        self.verbosity = verbosity

    def get(self, *args, **kwargs):
        url = self.request.uri[1:] # strip the preceding forward slash
        if self.verbosity:
            click.echo(':::: %s' % url) # Keep. Let's the user know what step we're at.
        if 'http' not in url:
            url = 'http://' + url
        self.host = urisplit(url)[0] + '://' +  urisplit(url)[1]
        self.proxy = self.request.protocol + '://' + self.request.host
         # Initialize to empty string in case we need to return with it unset
        self.data = ""

        try:
            r = requests.get(url)
        except requests.ConnectionError as e:
            if self.verbosity >= 2:
                click.echo("\nFailed to establish a connection with %s\n" % url)
                raise e
            else:
                return

        if "html" in r.headers['content-type']:
            soup = BeautifulSoup(r.text, 'lxml') # lxml - don't correct any messed up html
            attrs_to_check = [
                'data-src',
                'data-url',
                'href',
                'src',
            ]
            for tag in soup.find_all():
                if tag.name == 'style':
                    tag.string = str(self.css_fix(tag.string))
                else:
                    for attr in attrs_to_check:
                        if tag.has_attr(attr): # e.g. <img src="...">
                            self.html_fix(tag, attr)
                    if tag.has_attr('style'):
                        tag['style'] = self.css_fix(tag['style'], inline=True)

            self.data = soup.prettify() # soup ingested and parsed html. Urls modified.

        elif "css" in r.headers['content-type']:
            self.data = self.css_fix(r.text)

        else: # unparsed raw data (css, js, png, ...). All urls unmodified.
            self.data = r.content # content is binary, not txt.


        # critical to have resource files interpreted correctly
        self.set_header('content-type', r.headers['content-type'])

#        click.echo("   = ", time.process_time() - t) # Time since beginning of proxy query.
        self.write(self.data)

    def html_fix(self, tag, attr):
        '''
        Take self, tags (the html element), and their attrs (src or href),
        and set the corrected attr by making fixing their links.
        '''
        url = tag[attr]
        tag[attr] = self.url_fix(url)
        return

    def css_fix(self, css, inline=False):
        # Disable cssusilt warnings and errors for imperfect css source
        cssutils.log.setLevel(logging.CRITICAL)

        if inline:
            declaration = cssutils.parseStyle(css)
            cssutils.replaceUrls(declaration, self.url_fix)
            rv = declaration.cssText
        else: # style tag or external stylesheet
            sheet = cssutils.parseString(css)
            cssutils.replaceUrls(sheet, self.url_fix)
            rv = sheet.cssText
        return rv

    def url_fix(self, url):
        if url == "": # Null case
            rv = url
        elif url.startswith('data:'): # data uri, not actually a link, leave it alone
            # e.g. data:text/html,<script>alert('hi');</script>
            rv = url
        elif urisplit(url)[0]: # absolute / has scheme
            # e.g http://example.com/path
            rv = self.proxy +'/' + url
        elif urisplit(url)[1]: # protocol relatives prefixed with '//' / no scheme but has authority
            # e.g. //example.com/path
            # PRs should be able to be either http or https. In practice some sites are turning off
            # support for http, so just force everything through https
            rv = self.proxy + '/https://' + url.lstrip('/')
        elif not urisplit(url)[1] and urisplit(url)[2]: # relative / no authority but path
            # e.g. ../path
            rv = self.proxy + '/' + urijoin(self.host, url)
        elif url == '#' or (not urisplit(url)[2] and not urisplit(url)[3] and urisplit(url)[4]): # fragment
            # e.g. #id-12345
            # fragments are left alone
            rv = url
        else:
            click.echo('\n\nUnknown url protocol with url: %s' % url)
            rv = url
        return rv

def make_app(verbosity):
    return web.Application([
        (r"^.*", MainHandler, {'verbosity':verbosity}),
    ])

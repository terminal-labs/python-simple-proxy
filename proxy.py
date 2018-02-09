#! /usr/bin/env python
#
# This will route a webpage and all of it's included src and hrefs
# calls through this proxy.
#
# This is meant to be used in a virtualenv with pip installed packages:
# tornado beautifulsoup4 requests lxml
# Note: the proxy terminal output will display errors related to
# urllib3 and SSL unless python >= 2.7.9 is used
#
# Usage (URL Format): [ip address]:[port]/[website address]
# e.g. localhost:8000/www.example.com/file/path?query

import logging
import requests

import cssutils
from bs4 import BeautifulSoup
from tornado import ioloop, web
from uritools import urisplit, urijoin

PORT = 8000 # change me if you want

class MainHandler(web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super(MainHandler, self).__init__(*args, **kwargs)

        url = self.request.uri[1:] # strip the preceding forward slash
        if 'http' not in url:
            url = 'http://' + url
        self.host = urisplit(url)[0] + '://' +  urisplit(url)[1]
        self.proxy = self.request.protocol + '://' + self.request.host
         # Initialize to empty string in case we need to return with it unset
        self.data = ""

        try:
            r = requests.get(url)
        except requests.ConnectionError as e:
            # Ignore special cases where browsers look for something automatically
            if url == "http://favicon.ico":
                return
            else:
                print("\nFailed to establish a connection with %s\n" % url)
                raise e

        if "html" in r.headers['content-type']:
            soup = BeautifulSoup(r.text, 'lxml') # lxml - don't correct any messed up html
            for asset in soup.find_all(['img', 'script', 'link']):
                if asset.has_attr('data-src'): # e.g. inside <script> and <img> tags
                    attr = 'data-src'
                    self.html_fix(asset, attr)
                elif asset.has_attr('data-url'): # e.g. inside <script> and <img> tags
                    attr = 'data-url'
                    self.html_fix(asset, attr)
                elif asset.has_attr('src'): # e.g. inside <script> and <img> tags
                    attr = 'src'
                    self.html_fix(asset, attr)
                elif asset.has_attr('content'): # e.g. inside <script> and <img> tags
                    attr = 'content'
                    self.html_fix(asset, attr)
                elif asset.has_attr('name'): # e.g. inside <script> and <img> tags
                    attr = 'name'
                    self.html_fix(asset, attr)
                elif asset.has_attr('href'): # e.g. inside <link> tags
                    attr = 'href'
                    self.html_fix(asset, attr)
                else: # no attrs need fixing
                    attr = None
            self.data = soup.prettify() # soup ingested and parsed html. Urls modified.

        elif "css" in r.headers['content-type']:
            self.data = self.css_fix(r.text)

        else: # unparsed raw data (css, js, png, ...). All urls unmodified.
            self.data = r.content # content is binary, not txt.


        # critical to have resource files interpreted correctly
        self.set_header('content-type', r.headers['content-type'])

p    def html_fix(self, asset, attr):
        '''
        Take self, assets (the html element), and their attrs (src or href),
        and set the corrected attr by making fixing their links.
        '''
        url = asset[attr]
        asset[attr] = self.url_fix(url)
        return

    def css_fix(self, css):
        # Disable cssusilt warnings and errors for imperfect css source
        cssutils.log.setLevel(logging.CRITICAL)

        sheet = cssutils.parseString(css)
        cssutils.replaceUrls(sheet, self.url_fix)
        return sheet.cssText

    def url_fix(self, url):
        if url.startswith('data:'): # data uri, not actually a link, leave it alone
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
        else:
            raise 'Unknown url protocol'
        return rv

    def get(self):
        self.write(self.data)

def make_app():
    return web.Application([
        (r"^.*", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(PORT, address="0.0.0.0")
    ioloop.IOLoop.current().start()

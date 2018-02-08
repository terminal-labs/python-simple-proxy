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

from urlparse import urlparse

from tornado import ioloop, web, template
from tornado.httputil import HTTPHeaders
from bs4 import BeautifulSoup
import requests
import tinycss
import cssselect
import ipdb
PORT = 8000 # change me if you want

class MainHandler(web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super(MainHandler, self).__init__(*args, **kwargs)

        url = self.request.uri[1:] # strip the preceding forward slash
        if 'http' not in url:
            url = 'http://' + url
        self.host = urlparse(url).scheme + '://' + urlparse(url).netloc
        self.proxy = self.request.protocol + '://' + self.request.host
        r = requests.get(url)

        if "html" in r.headers['content-type']:
            soup = BeautifulSoup(r.text, 'lxml') # lxml - don't correct any messed up html
            for asset in soup.find_all(['img', 'script', 'link']):
                # if asset.has_attr('src'): # e.g. inside <script> and <img> tags
                #     attr = 'src'
                #     self.html_url_fix(asset, attr)
                if asset.has_attr('href'): # e.g. inside <link> tags
                    attr = 'href'
                    self.html_url_fix(asset, attr)
                else: # no attrs need fixing
                    attr = None
            self.data = soup.prettify() # soup ingested and parsed html. Urls modified.
        else:
            self.data = r.text # unparsed raw data (css, js, png, ...). All urls unmodified.
        if "css" in r.headers['content-type']:
            rv = ''
            for line in r.content.splitlines():
                if 'url' in line:
                    line = self.css_url_fix(line)
                rv = rv + line + '\n'
            self.data = r.content

        # critical to have resource files interpreted correctly
        self.set_header('content-type', r.headers['content-type'])

    def html_url_fix(self, asset, attr):
        '''
        Take self, assets (the html element), and their attrs (src or href),
        and set the corrected attr by making all links absolute and run them
        through this proxy.
        '''
        if not urlparse(asset[attr]).hostname: # relative url - make it absolute
            asset[attr] = '{0}{1}'.format(self.host, asset[attr])
        elif asset[attr][0:2] == '//': # protocol relatives prefixed with '//'
            asset[attr] = self.request.protocol + '://' + asset[attr][2:]

        asset[attr] = '{0}/{1}'.format(self.proxy, asset[attr]) # proxify all urls
        return

    def css_url_fix(self, line):
        print 'line = ', line
        beginning = 'url('
        end = ')'
        prefix = line.split(beginning)[0] + beginning
        url_to_fix = line.split(beginning)[1].split(end)[0]
        suffix = line.split(beginning)[1].split(end)[1]

        if not urlparse(url_to_fix).hostname: # relative url - make it absolute
            url_fixed = '{0}{1}'.format(self.host, url_to_fix)
        elif url_to_fix[0:2] == '//': # protocol relatives prefixed with '//'
            url_fixed = self.request.protocol + '://' + url_to_fix[2:]

        print prefix + url_fixed + suffix
        return prefix + url_fixed + suffix

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

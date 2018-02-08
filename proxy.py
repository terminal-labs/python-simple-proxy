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
from uritools import uricompose, urijoin, urisplit, uriunsplit

from tornado import ioloop, web, template
from tornado.httputil import HTTPHeaders
from bs4 import BeautifulSoup
import requests
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
        try:
            r = requests.get(url)
        except requests.ConnectionError as e:
            print("\nFailed to establish a connection with %s\n" % url)
            raise e

        if "html" in r.headers['content-type']:
            soup = BeautifulSoup(r.text, 'lxml') # lxml - don't correct any messed up html
            for asset in soup.find_all(['img', 'script', 'link']):
                # if asset.has_attr('src'): # e.g. inside <script> and <img> tags
                #     attr = 'src'
                #     self.html_url_fix(asset, attr)
                if asset.has_attr('href'): # e.g. inside <link> tags
                    attr = 'href'
                    self.html_parse(asset, attr)
                else: # no attrs need fixing
                    attr = None
            self.data = soup.prettify() # soup ingested and parsed html. Urls modified.
        else:
            self.data = r.text # unparsed raw data (css, js, png, ...). All urls unmodified.
        if "css" in r.headers['content-type']:
            rv = ''
            for line in r.content.splitlines():
                if 'url' in line:
                    line = self.css_parse(line)
                rv = rv + line + '\n'
            self.data = rv

        # critical to have resource files interpreted correctly
        self.set_header('content-type', r.headers['content-type'])

    def html_parse(self, asset, attr):
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

    def css_parse(self, line):
        print "#### begin ####"
        print 'line = ', line
        beginning = 'url('
        end = ')'
        prefix = line.split(beginning)[0] + beginning
        url_to_fix = line.split(beginning)[1].split(end)[0].strip('\'').strip('\"')
        suffix = ')'.join(line.split(beginning)[1].split(end)[1:])

        url_fixed = self.url_fix(url_to_fix)
        rv = prefix + '\'' + url_fixed + '\')' + suffix
        print rv
        print "##### end #####"
        return rv

    def url_fix(self, url):
        if url.startswith('data:'): # data uri, not actually a link, leave it alone
            rv = url
        elif urisplit(url)[0]: # external / has scheme
            print 'external'
            rv = self.proxy + url
        elif urisplit(url)[1]: # protocol relatives prefixed with '//' / no scheme but has authority
            print 'protocol relative'
        elif not urisplit(url)[1] and urisplit(url)[2]: # relative or absolute / no authority but path
            print 'relative or absolute'
            rv = self.proxy + '/' + urijoin(self.host, url)
        else:
            raise 'Unknown url protocol'
        print rv
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

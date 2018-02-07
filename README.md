# simple-proxy
A simple Python proxy built with Tornado and BeautifulSoup

Requires Python > 2.7.9 atm

`pip install tornado beautifulsoup4 requests lxml`

Then run `python proxy.py`. Next open a browser and tell it where to look:


Usage (URL Format): [ip address]:[port]/[website address]

e.g. localhost:8000/www.example.com/file/path?query

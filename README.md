# simple-proxy

A simple reverse proxy built with Tornado and Python

Requires Python > 2.7.9, Python > 3.

`pip install -r requirements.txt`

Then run `python proxy.py`. Next open a browser and tell it where to look:


Usage (URL Format): [ip address]:[port]/[website address]

e.g. localhost:8000/www.example.com/file/path?query

## About

**Why** make this? A few times now I've needed a reverse proxy. The most common use I've run into is to strip away ssl / https when developing / qaing a website. For example, if you have a self-signed cert, you may get an ssl warning when you access the site in a browser. If that site is your own staging server though, that's annoying, and sometimes obtrusive. This removes it.

**How?** This proxy grabs a web page and parses it's html and css to rewrite the uri's inside them, so that all of these resources and links are proxied too. In general this is fast enough, except for the css parsing. The current implementation for that is pretty slow, unfortunately, but it does the job if you're patient.

This proxy has trouble with sites that use js to construct URIs, because we're not doing anything with them. Those URIs may be all wrong.

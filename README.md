# simple-proxy

A simple reverse proxy built with Tornado and Python

Requires Python > 2.7.9, Python > 3.

`pip install -e .`

Then run `simple-proxy`. Next open a browser and tell it where to look:


Usage (URL Format): [ip address]:[port]/[website address]

e.g. PUT THIS IN YOUR BROWSER --> `localhost:8000/www.example.com/`

## About

**Why** make this? A few times now I've needed a reverse proxy. The most common use I've run into is to strip away ssl / https when developing / qaing a website. For example, if you have a self-signed cert, you may get an ssl warning when you access the site in a browser. If that site is your own staging server though, that's annoying, and sometimes obtrusive. This removes it. This is not the fastest or best proxy, but it was pretty easy to make, and easy to run, making it nice for occaisional use.

**How?** This proxy grabs a web page and parses it's html and css to rewrite the uri's inside them, so that all of these resources and links are proxied too. In this way you will access the main url that's in your browser's url bar, and every successive link for resources that page needs recursively until the page is loaded.

**Limitations:**

- This method of proxying involves high-level rewrites of html to change links. It is not low-level, and thus many things more complicated than loading sites probably won't work, such as:
  - authentication
  - session tracking
  - fancy js

- CSS Parsing is slow. Namely, `cssutils.replaceUrls()` is a slow operation, especially if there is a lot of CSS. I've seen CSS files parse in 1s, and in 30s. It just depends.

- This looks for urls to change by parsing to find them. I only changed urls in locations that typically matter. E.g., if a site does logic on a url in content meta tag (`<meta content='...'`), it won't be modified and that logic probably won't work.

- JS is untouched. JS can have links that maybe we can parse for and find, but we aren't right now. JS can also certainly constructed in a way that we can't parse for. JS links are most prone to breaking things, and this can clutter up the terminal output with tracebacks as requests fails to find nonsense urls like `http://lib.js`.

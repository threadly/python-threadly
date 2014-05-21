#!/usr/bin/env python
from distutils.core import setup

setup (# Distribution meta-data
       name = "threadly",
       version = "0.1.0",
       author = "Luke Wahlmeier",
       author_email = "lwahlmeier@gmail.com",
       url = "threadly.org",
       license = "lgpl",
       description = "Threading pool and scheduler for python",
       py_modules =  ['threadly'],
      )

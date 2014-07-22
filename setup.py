#!/usr/bin/env python
from setuptools import setup

setup (
       name = "threadly",
       version = "0.1.2",
       author = "Luke Wahlmeier",
       author_email = "lwahlmeier@gmail.com",
       url = "https://github.com/lwahlmeier/python-threadly",
       download = "https://github.com/lwahlmeier/python-threadly/tarball/0.1.2",
       license = "lgpl",
       description = "Threading pool and scheduler for python",
       py_modules =  ['threadly'],
       test_suite='tests',
      )

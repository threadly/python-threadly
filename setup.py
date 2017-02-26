#!/usr/bin/env python
from setuptools import setup

VERSION = "0.7.1"

setup(name="threadly",
       version=VERSION,
       author="Luke Wahlmeier",
       author_email="lwahlmeier@gmail.com",
       url="http://threadly.github.io/python-threadly/",
       download_url="https://github.com/threadly/python-threadly/tarball/%s"%(VERSION),
       license="unlicense",
       description="Thread pool and scheduler for python",
       keywords=['threading', 'scheduling'],
       classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'License :: Public Domain'
        ],
       packages=['threadly'],
       test_suite='tests',
      )

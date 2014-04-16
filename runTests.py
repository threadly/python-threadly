#!/usr/bin/python
import os, sys



for root, dirs, files in os.walk("./tests/"):
  break


tests = list()
for f in files:
  if f == "__init__.py":
    continue
  if f[-2:] == "py":
    print "Running Test:",f[:-3], 
    X = __import__("tests.%s"%(f[:-3]), fromlist=['tests'])
    if X.PASSED:
      print ": PASSED!"
    else:
      print ": FAILED!"
    tests.append(X)

for i in tests:
  if not i.PASSED:
    sys.exit(1)

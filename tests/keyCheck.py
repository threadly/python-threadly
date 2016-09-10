from __future__ import print_function
import threadly, time, random, logging
import unittest

try:
    xrange(1)
except:
    xrange = range


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')



PASSED = False
SLEEP = True
CALL = 0


def TEST1():
  global SLEEP
  global CALL
  if SLEEP:
    SLEEP = False
    time.sleep(1)
  if CALL > 0:
    CALL-=1
  else:
    CALL+=1

ADD = 1
def TEST2():
  global ADD
  time.sleep(random.random()*.001)
  ADD+=ADD

class TestKeys(unittest.TestCase):

  def test_keyTest(self):
    global CALL
    global PASSED
    p = threadly.Executor(10)

    LASTRUN = time.time()
    threads = list()
    for i in xrange(1001):
      p.schedule(TEST1, key="TEST")

    for k in p._Scheduler__keys:
      while p._Scheduler__keys[k].size() > 0:
        time.sleep(.1)

    p.shutdown_now()
    self.assertEquals(1,CALL)

  def test_keyTest2(self):
    global ADD
    p = threadly.Executor(10)
    for i in xrange(100):
      p.schedule(TEST2, key="BLAH")
    for k in p._Scheduler__keys:
      while p._Scheduler__keys[k].size() > 0:
        time.sleep(.1)
    self.assertEquals(1267650600228229401496703205376,ADD)
    print("DONE")
    p.shutdown()
    



if __name__ == '__main__':
  unittest.main()

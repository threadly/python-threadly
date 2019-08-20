from __future__ import print_function
import threadly, time, random, logging
import threading
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
#  print(threading.current_thread().name)
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
    self.assertEqual(1,CALL)

  def test_keyTest2(self):
    global ADD
    p = threadly.Executor(10)
    for i in xrange(100):
      p.schedule(TEST2, key="BLAH")
    for k in p._Scheduler__keys:
      while p._Scheduler__keys[k].size() > 0:
        time.sleep(.1)
    self.assertEqual(1267650600228229401496703205376,ADD)
    print("DONE")
    p.shutdown().get()
    
  def test_keyTest3(self):
    global ADD
    ADD = 1
    p = threadly.Executor(10)
    fl = []
    for i in xrange(100):
      f = p.schedule_with_future(TEST2, key="BLAH", delay=10*i)
      fl.append(f)
    for f in fl:
      f.get(100)
    self.assertEqual(1267650600228229401496703205376,ADD)
    p.shutdown().get()



if __name__ == '__main__':
  unittest.main()

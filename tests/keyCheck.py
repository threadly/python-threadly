import threadly, time, random
import unittest

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

  def keyTest(self):
    global CALL
    global PASSED
    p = threadly.Executor(10)

    LASTRUN = time.time()
    threads = list()
    for i in xrange(1001):
      p.schedule(TEST1, key="TEST")

    for k in p.keys:
      while len(p.keys[k].run) > 0:
        time.sleep(.1)

    p.shutdown_now()
    self.assertEquals(1,CALL)

  def test_keyTest2(self):
    global ADD
    p = threadly.Executor(10)
    for i in xrange(100):
      p.schedule(TEST2, key="BLAH")
    for k in p.keys:
      while len(p.keys[k].run) > 0:
        time.sleep(.1)
    self.assertEquals(1267650600228229401496703205376,ADD)
    p.shutdown_now()
    



if __name__ == '__main__':
  unittest.main()

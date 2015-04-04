import threadly, time, random
import unittest

clf = 0
llf = 0

def callLF(lf):
#  print "CALLED"
  lf.setter(True)

def listenFromFuture():
  global llf
#  print "GotCalled"
  llf +=1

def callFromFuture(s):
  global clf
#  print "GotCalled", s
  clf +=1

def listenException():
  raise Exception("TEST1")
def callException(s):
  raise Exception("TEST1")

class TestFutures(unittest.TestCase):

  def test_futureTest1(self):
    global clf, llf
    sch = threadly.Scheduler(10)
    LF1 = threadly.ListenableFuture()
    LF2 = sch.schedule_with_future(callLF, delay=100, args=(LF1,))
    LF2.add_listener(listenFromFuture)
    LF2.add_callable(callFromFuture)
    LF1.add_listener(listenFromFuture)
    LF1.add_callable(callFromFuture)
    self.assertTrue(LF1.get())
    self.assertTrue(LF2.get())
    self.assertEquals(2, llf)
    self.assertEquals(2, clf)
    LF2.add_listener(listenFromFuture)
    LF2.add_callable(callFromFuture)
    LF1.add_listener(listenFromFuture)
    LF1.add_callable(callFromFuture)
    self.assertEquals(4, llf)
    self.assertEquals(4, clf)
    sch.shutdown()

  def test_futureCallerExceptions(self):
    global clf, llf
    sch = threadly.Scheduler(10)
    LF1 = threadly.ListenableFuture()
    LF1.add_listener(listenException)
    LF1.add_listener(listenException)
    LF1.add_callable(callException)
    LF2 = sch.schedule_with_future(callLF, delay=100, args=(LF1,))
    self.assertTrue(LF1.get())
    self.assertTrue(LF2.get())
    sch.shutdown()

  def test_futureDoubleSet(self):
    global clf, llf
    sch = threadly.Scheduler(10)
    LF1 = threadly.ListenableFuture()
    LF2 = sch.schedule_with_future(callLF, delay=100, args=(LF1,))
    self.assertTrue(LF1.get())
    self.assertTrue(LF2.get())
    LF3 = sch.schedule_with_future(callLF, delay=100, args=(LF1,))
    self.assertFalse(LF3.get())
    self.assertEquals(10, sch.get_poolsize())
    sch.shutdown()


if __name__ == '__main__':
  unittest.main()

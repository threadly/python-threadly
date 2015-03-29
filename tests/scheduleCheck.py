import threadly, time, random, unittest


LASTRUN = 0
RUNS = list()

def TEST():
  global LASTRUN
  global RUNS
  RUNS.append(time.time() - LASTRUN)
  LASTRUN = time.time()

def EXP():
  raise Exception("BLAH EXP")

class TestSchedule(unittest.TestCase):
  def test_timeingTest1(self):
    global LASTRUN
    global RUNS
    p = threadly.Executor(2)

    LASTRUN = time.time()
    p.schedule(TEST, delay=10, recurring=True)
    time.sleep(.500)
    p.remove(TEST)

    p.shutdown_now()

    AVG = sum(RUNS) / float(len(RUNS))
    self.assertTrue(AVG < .0105)
    self.assertTrue(AVG > .0099)

  def test_exptTest1(self):
    p = threadly.Executor(1)
    p.execute(EXP)
    time.sleep(.1)

  def test_shutdownTest1(self):
    p = threadly.Executor(1)
    p.schedule(time.sleep, recurring=True, args=(.1,))
    p.schedule(time.sleep, recurring=True, args=(.1,))
    p.schedule(time.sleep, recurring=True, args=(.1,))
    p.schedule(time.sleep, recurring=True, args=(.1,))
    p.schedule(time.sleep, recurring=True, args=(.1,))
    p.schedule(time.sleep, recurring=True, args=(.1,))
    p.schedule(time.sleep, recurring=True, args=(.1,))
    p.schedule(time.sleep, recurring=True, args=(.1,))
    p.schedule(time.sleep, recurring=True, args=(.1,))
    time.sleep(.1)
    p.shutdown_now()
    

  def test_removeScheduledTest2(self):
    p = threadly.Executor(30)

    LASTRUN = time.time()
    p.schedule(time.time, delay=10, recurring=True)
    p.schedule(TEST, delay=10000, recurring=True)
    p.schedule(TEST, delay=10000, recurring=True)
    p.schedule(TEST, delay=10000, recurring=True)
    p.schedule(TEST, delay=10000, recurring=True)
    p.remove(TEST)
    self.assertEquals(4, p._Scheduler__delayed_tasks.size())
    p.remove(TEST)
    self.assertEquals(3, p._Scheduler__delayed_tasks.size())
    p.remove(TEST)
    self.assertEquals(2, p._Scheduler__delayed_tasks.size())
    p.remove(TEST)
    self.assertEquals(1, p._Scheduler__delayed_tasks.size())
    p.remove(TEST)
    self.assertEquals(1, p._Scheduler__delayed_tasks.size())
    p.shutdown()
    

if __name__ == '__main__':
  unittest.main()


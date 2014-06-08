import threadly, time, random, unittest


LASTRUN = 0
RUNS = list()

def TEST():
  global LASTRUN
  global RUNS
  RUNS.append(time.time() - LASTRUN)
  LASTRUN = time.time()

class TestSchedule(unittest.TestCase):
  def test_Test1(self):
    global LASTRUN
    global RUNS
    p = threadly.Executor(30)

    LASTRUN = time.time()
    p.schedule(TEST, delay=100, recurring=True)
    time.sleep(1)
    p.removeScheduled(TEST)

    p.shutdown()

    AVG = sum(RUNS) / float(len(RUNS))
    if AVG > .101 or AVG < .099:
      PASSED = False
    else:
      PASSED = True

if __name__ == '__main__':
  unittest.main()


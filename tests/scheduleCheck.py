import threadly, time, random
import logging, threading


logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
log = logging.getLogger("root")
log.setLevel(logging.DEBUG)


PASSED = False
LASTRUN = 0
RUNS = list()

def TEST():
  global LASTRUN
  global RUNS
  RUNS.append(time.time() - LASTRUN)
  LASTRUN = time.time()

p = threadly.Executor(30)

LASTRUN = time.time()
p.schedule( TEST, delay=100, recurring=True)
time.sleep(1)
p.removeScheduled(TEST)

p.shutdown()

AVG = sum(RUNS) / float(len(RUNS))
if AVG > .101 or AVG < .099:
  PASSED = False
else:
  PASSED = True

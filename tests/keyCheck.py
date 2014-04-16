import threadly, time, random
import logging, threading


logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
log = logging.getLogger("root")
log.setLevel(logging.DEBUG)


PASSED = False
SLEEP = True
CALL = 0

def TEST():
  global SLEEP
  global CALL
  if SLEEP:
    SLEEP = False
    time.sleep(1)
  if CALL > 0:
    CALL-=1
  else:
    CALL+=1


p = threadly.Executor(10)

LASTRUN = time.time()
threads = list()
for i in xrange(1001):
  p.schedule(TEST, key="TEST")

while p.MAINQUEUE.qsize() > 0:
  time.sleep(.1)

p.shutdown()
if CALL == 1:
  PASSED = True
else:
  PASSED = False


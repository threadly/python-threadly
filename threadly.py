import threading
import Queue
import logging
import time

class Executor():
  """
  Main Executor Object.  This starts up a thread pool, and a scheduler.
  """
  def __init__(self, PoolSize):
    """
      Construct an Executor instance.  It will make one extra thread then the number spesified, as it needs it for scheduling.  
    
      Arguments:
      PoolSize -- spesify the number of threads wanted for this pool.
    """
    self.log = logging.getLogger("root.threadly")
    self.KeyLock = threading.Condition()
    self.PoolSize = PoolSize
    self.RUNNING = True
    self.MAINQUEUE = Queue.Queue()
    self.delayTasks = list()
    self.threads = list()
    self.delayLock = threading.Condition()
    self.keys = dict()
    self.clock = Clock()
    for i in xrange(self.PoolSize):
      t = threading.Thread(target=self.__threadPool)
      t.name = "Executor-Pool-Thread-%d"%(i)
      t.daemon = True
      t.start()
      self.threads.append(t)
    self.delayThread = threading.Thread(target=self.__delayCheckThread)
    self.delayThread.name = "Executor-DelayThread"
    self.delayThread.daemon = True
    self.delayThread.start()

  def getPoolSize(self):
    return len(self.threads)

  def execute(self, task):
    self.schedule(task)

  def schedule(self, task, delay=0, recurring=False, key=None):
    if delay > 0:
      T = int(self.clock.accurateTime()*1000)+delay
      self.delayLock.acquire()
      self.delayTasks.append((T, task, delay, recurring, key))
      self.delayLock.notify()
      self.delayLock.release()
    else:
      if key != None:
        self.KeyLock.acquire()
        if key not in self.keys:
          X = runQueue()
          self.keys[key] = X
        self.KeyLock.release()
        r = self.keys[key]
        r.add(task)
        r.Lock.acquire()
        if not r.inQueue and len(r.run) > 0:
          r.inQueue = True
          self.MAINQUEUE.put(r.runAll)
        r.Lock.release()
      else:
        self.MAINQUEUE.put(task)

  def removeScheduled(self, task):
      self.delayLock.acquire()
      count = 0
      found = False
      for t in self.delayTasks:
        if t[1] == task:
          found = True
          break
        else:
          count+=1
      if found:
        self.delayTasks.pop(count)
      self.delayLock.release()

  def shutdown(self):
    self.RUNNING = False
    #Flush the Queues
    self.delayLock.acquire()
    self.delayTasks = list()
    self.delayLock.release()
    while not self.MAINQUEUE.empty():
      self.MAINQUEUE.get(False)
    while self.delayThread.isAlive():
      self.delayLock.acquire()
      self.delayLock.notify()
      self.delayLock.release()
    #Add empty tasks till all threads Die
    for t in self.threads:
      while t.isAlive():
        self.MAINQUEUE.put(self.__empty)

  def __empty(self):
    pass
        

  def __delayCheckThread(self):
    while self.RUNNING:
      self.delayLock.acquire()
      X = self.__getNextWait()
      if X == 0:
        T = self.delayTasks.pop(0)
        #timer is up, so we add to queue now
        self.schedule(T[1], key=T[4])
        #T[3] is recurring, if so we add again as a scheduled event
        if T[3] == True:
          self.schedule(T[1], T[2], T[3], T[4])
      else:
        self.delayLock.wait(X)
      self.delayLock.release()

  def __getNextWait(self):
    if len(self.delayTasks) == 0:
      return 1000
    self.delayTasks.sort()
    X = self.delayTasks[0][0] - int(self.clock.accurateTime()*1000)
    if X >= 1: #this is actuallu .005, if we have this or less we just run it now
      #We return as a float, and we want to wake up right before the next task needs to run
      return (X/1000.0)-.0005
    else:
      return 0.0

  def __threadPool(self):
    while self.RUNNING:
      try:
          X = self.MAINQUEUE.get()
          X()
      except IndexError, e:
        pass
      except Exception, e:
        print "Problem running ", e


#been having a lot of problems with concurrency here
#Which is why we are locking around pretty much anything 
#having to do with the run list.
class runQueue():
  def __init__(self):
    self.run = list()
    self.Lock = threading.Condition()
    self.inQueue = False

  def add(self, task):
    self.Lock.acquire()
    self.run.append(task)
    self.Lock.release()

  def runNext(self):
    self.Lock.acquire()
    X = self.run.pop(0)
    self.Lock.release()
    X()

  def runAll(self):
#    print "Start On Thread %s"%(threading.current_thread())
    while len(self.run) > 0:
      self.runNext()
      if len(self.run) == 0:
        self.Lock.acquire()
        if len(self.run) == 0:
          self.inQueue = False
          self.Lock.release()
#          print "Stop  On Thread %s"%(threading.current_thread())
          break
        self.Lock.release()

def singleton(cls):
  instances = {}
  def getinstance():
    if cls not in instances:
      instances[cls] = cls()
    return instances[cls]
  return getinstance

@singleton
class Clock(object):
  def __init__(self):
    self.current = int(time.time()*1000)
    self.run = False
    self.thread = None
    self.getTime = time.time
    self.sleep = time.sleep
    self.__startClockUpdateThread()
  
  def __del__(self):
    self.__stopClockUpdateThread()

  def __updateClock(self):
    while self.run:
      self.accurateTime()
      self.sleep(.1)

  def accurateTime(self):
    self.current = self.getTime()
    return self.current

  def lastKnownTimeMillis(self):
    return int(self.current*1000)

  def lastKnownTime(self):
    return self.current

  def __startClockUpdateThread(self):
    if self.thread == None or not self.thread.is_alive():
      self.run = True
      self.thread = threading.Thread(target=self.__updateClock)
      self.thread.name = "Clock Thread"
      self.thread.daemon = True
      self.thread.start()

  def __stopClockUpdateThread(self):
      self.run = False



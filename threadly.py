import threading
import Queue
import logging
import time

"""threadly a simple threadpool and schduler.
"""

class Executor():
  """Main Executor Object. 
  This starts up a thread pool and scheduler.  Please note 1 extra thread is used for scheduling.

  @undocumented: __empty
  @undocumented: __delayCheckThread
  @undocumented: __getNextWait
  @undocumented: __threadPool
  """
  def __init__(self, PoolSize):
    """
    Construct an Executor instance.  It will make one extra thread then the number spesified, as it needs it for scheduling.  
    
    @type  PoolSize: number
    @param PoolSize: The number of threads wanted for this pool.
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
    """
    Gets the number of threads used in this Pool

    @rtype:  number
    @return: The number of threads in the pool
    """
    return len(self.threads)

  def execute(self, task):
    """
    Execute a given task as soon as possible

    @type  task: function pointer
    @param task: the function to run
    """
    self.schedule(task)

  def schedule(self, task, delay=0, recurring=False, key=None):
    """
    Schedule a task for execution.

    @type  delay: number
    @param delay: amount of time to delay the task from running.
    @type  recurring: boolean
    @param recurring: set to True if the task is to we rerun.  We will rerun it after every delay time
    @type  key: Object
    @param key: This sets a key to the task.  Any task with this key will be executed in a single threaded manor.
    """
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
          X = KeyRunner()
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
      """
      Remove a scheduled task from the queue.  This is a best effort remove, the task could still possibly run.  This is most useful to cancel recurring tasks.
      If there is more then one task of this type scheduled only the first one is removed.
      
      @type  task: function pointer
      @param task: task to remove from the queue
      """
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
    """
    Shutsdown the threadpool.  Any task currently being executed will still complete, but nothing in the queue will run.
    """
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


class KeyRunner():
  """A class to wrap key objects
  Items can be added to the KeyRunner while its running.  This is used to keep all tasks for a given key in one thread.
  """
  def __init__(self):
    self.run = list()
    self.Lock = threading.Condition()
    self.inQueue = False

  def add(self, task):
    """
    Add a task to this runner set.
    
    @type  task: function pointer
    @param task: will add to the current keyrunner set.
    """
    self.Lock.acquire()
    self.run.append(task)
    self.Lock.release()

  def runNext(self):
    """
    Run the next item for this key."""
    self.Lock.acquire()
    X = self.run.pop(0)
    self.Lock.release()
    X()

  def runAll(self):
    """
    Run all items in this keyRunner."""
    while len(self.run) > 0:
      self.runNext()
      if len(self.run) == 0:
        self.Lock.acquire()
        if len(self.run) == 0:
          self.inQueue = False
          self.Lock.release()
          break
        self.Lock.release()

class Singleton(object):
  """A Simple inheratable singleton"""

  __single = None

  def __new__(classtype, *args, **kwargs):
    if classtype != type(classtype.__single):
      classtype.__single = object.__new__(classtype, *args, **kwargs)
    return classtype.__single

  def __init__(self,name=None):
    self.name = name

  def display(self):
    print self.name,id(self),type(self)



class Clock(Singleton):
  """A Simple clock class to allow for retrival of time from multipule threads to be more efficient.
  This class is a singleton so anyone using it will be using the same instance.

  The clock updates every 100ms so calls to get time often can be more performant if they dont need to be exact.

  @undocumented: __init__
  @undocumented: __del__
  @undocumented: __updateClock
  @undocumented: __startClockUpdateThread
  @undocumented: __stopClockUpdateThread
  """
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
    """
    Get the actual current time.  This should be called as little as offten, and only when exact times are needed.

    @rtype: float
    @return: returns a float with whole numbers being seconds. Pretty much identical to time.time()
    """
    self.current = self.getTime()
    return self.current

  def lastKnownTimeMillis(self):
    """
    Gets the last ran time in milliseconds.  This is accurate to 100ms.

    @rtype: int
    @return: an integer representing the last known time in millis.
    """
    return int(self.current*1000)

  def lastKnownTime(self):
    """
    Gets the last ran time seconds.milliseconds.  This is accurate to 100ms.

    @rtype: float
    @return: represents the last known time.
    """
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



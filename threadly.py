import threading, sys
import Queue
from Queue import Empty as EmptyException
import logging
import time

"""threadly a simple threadpool and scheduler.
"""


class Scheduler(object):
  """Main Executor Object.
  This starts up a thread pool and scheduler.  Please note 1 extra thread is used for scheduling.

  @undocumented: __empty
  @undocumented: __delay_check_thread
  @undocumented: __get_next_wait_time
  @undocumented: __thread_pool
  """
  def __init__(self, poolsize):
    """
    Construct an Executor instance.  It will make one extra thread then the number specified, as it needs it for scheduling.  

    @type  poolsize: number
    @param poolsize: The number of threads wanted for this pool.
    """
    self.log = logging.getLogger("root.threadly")
    self.clock = Clock()
    self.key_lock = threading.Condition()
    self.poolsize = poolsize
    self.running = True
    self.in_shutdown = False
    self.main_queue = Queue.Queue()
    self.delayed_tasks = list()
    self.threads = list()
    self.delay_lock = threading.Condition()
    self.keys = dict()
    for i in xrange(self.poolsize):
      tmp_thread = threading.Thread(target=self.__thread_pool)
      tmp_thread.name = "Executor-Pool-Thread-%d"%(i)
      tmp_thread.daemon = True
      tmp_thread.start()
      self.threads.append(tmp_thread)

  def get_poolsize(self):
    """
    Gets the number of threads used in this Pool

    @rtype:  number
    @return: The number of threads in the pool
    """
    return len(self.threads)

  def get_queue_size(self):
    return self.main_queue.qsize()

  def execute(self, task, args=(), kwargs={}):
    """
    Execute a given task as soon as possible

    @type  task: function pointer
    @param task: the function to run
    """
    self.schedule(task, args=args, kwargs=kwargs)

  def __add_delay_task(self, task):
    self.delay_lock.acquire()
    try:
      c = len(self.delayed_tasks)
      if c == 0:
        self.delayed_tasks.append(task)
        self.execute(self.__empty)
        return
      elif self.delayed_tasks[0][0] > task[0]:
        self.delayed_tasks.insert(0, task)
        return
      elif self.delayed_tasks[c-1][0] < task[0] or c == 1:
        self.delayed_tasks.append(task)
        return

      l = self.delayed_tasks
      c = len(l)
      ch = c/2
      while True:
        if l[ch][0] < task[0]:
          if ch == 0:
            l.insert(ch, task)
            break
          else:
            ch = ch/2
        elif l[ch][0] > task[0]:
          if ch == c:
            l.append(task)
            break
          else:
            ch = ch/2
        else:
          l.insert(ch, task)
          break
    finally:
      self.delay_lock.release()

  def schedule_with_future(self, task, delay=0, key=None, args=(), kwargs={}):
    job=(task, args, kwargs)
    future = ListenableFuture()
    self.schedule(futureJob, delay=delay, key=key, args=(future, job))
    return future

  def schedule(self, task, delay=0, recurring=False, key=None, args=(), kwargs={}):
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
      s_task = int(self.clock.accurate_time() * 1000) + delay
      self.__add_delay_task((s_task, task, delay, recurring, key, args, kwargs))
    else:
      if key != None:
        self.key_lock.acquire()
        if key not in self.keys:
          tmp = KeyRunner()
          self.keys[key] = tmp
        self.key_lock.release()
        run_key = self.keys[key]
        run_key.add((task, args, kwargs))
        run_key.lock.acquire()
        if not run_key.in_queue and len(run_key.run) > 0:
          run_key.in_queue = True
          self.main_queue.put((run_key.run_all, (), {}))
        run_key.lock.release()
      else:
        self.main_queue.put((task, args, kwargs))

  def remove(self, task):
      """
      Remove a scheduled task from the queue.  This is a best effort remove, the task could still possibly run.  This is most useful to cancel recurring tasks.
      If there is more then one task of this type scheduled only the first one is removed.

      @type  task: function pointer
      @param task: task to remove from the queue
      """
      self.delay_lock.acquire()
      count = 0
      found = False
      for tasks in self.delayed_tasks:
        if tasks[1] == task:
          found = True
          break
        else:
          count+=1
      if found:
        self.delayed_tasks.pop(count)
      self.delay_lock.release()

  def shutdown(self):
    """
    Shuts down the threadpool.  Any task currently on the queue will be ran.  No more Scheduled events will be added to the queue.
    """
    self.delay_lock.acquire()
    self.delayed_tasks = list()
    self.delay_lock.release()
    self.execute(self.__internal_shutdown)

  def shutdown_now(self):
    """
    Shuts down the threadpool.  Any task currently being executed will still complete, but the queue will be emptied out.
    """
    self.running = False
    #Flush the Queues
    self.delay_lock.acquire()
    self.delayed_tasks = list()
    self.delay_lock.release()
    while not self.main_queue.empty():
      self.main_queue.get_nowait()
    self.__internal_shutdown()

  def __internal_shutdown(self):
    self.running = False
    for tmp_thread in self.threads:
      while tmp_thread != None and tmp_thread.isAlive() and threading != None and tmp_thread != threading.current_thread():
        self.main_queue.put((self.__empty, (), {}))

  def __empty(self):
    pass

  def __get_next_wait_time(self):
    if len(self.delayed_tasks) == 0:
      return 2**32
    else:
      task = self.delayed_tasks[0][0] - int(self.clock.accurate_time()*1000)
      return (task/1000.0)-.0005

  def __thread_pool(self):
    while self.running:
      try:
          runner = None
          to = None
          if len(self.delayed_tasks) > 0:
            self.delay_lock.acquire()
            if len(self.delayed_tasks) > 0:
              to = self.__get_next_wait_time()
              while to <= 0:
                run_task = self.delayed_tasks.pop(0)
                self.schedule(run_task[1], key=run_task[4], args=run_task[5], kwargs=run_task[6])
                #run_task[3] is recurring, if so we add again as a scheduled event
                if run_task[3] == True and not self.in_shutdown:
                  self.schedule(run_task[1], run_task[2], run_task[3], run_task[4], run_task[5], run_task[6])
                to = self.__get_next_wait_time()
            self.delay_lock.release()
          if runner == None:
            runner = self.main_queue.get(True, to)
          if runner != None:
            runner[0](*runner[1], **runner[2])
      except IndexError as exp:
        pass
      except EmptyException as exp:
        pass
      except Exception as exp:
        print "Exception when Running:", sys.exc_info()
        print "1", runner
        print "2", exp


class Executor(Scheduler):
  """A class for backwards compatibility, Scheduler should be used instead now.
  """
  pass

class KeyRunner(object):
  """A class to wrap key objects
  Items can be added to the KeyRunner while its running.  This is used to keep all tasks for a given key in one thread.
  """
  def __init__(self):
    self.run = list()
    self.lock = threading.Condition()
    self.in_queue = False

  def add(self, task):
    """
    Add a task to this runner set.

    @type  task: function pointer
    @param task: will add to the current keyrunner set.
    """
    self.lock.acquire()
    self.run.append(task)
    self.lock.release()

  def run_next(self):
    """
    Run the next item for this key."""
    self.lock.acquire()
    runner = self.run.pop(0)
    self.lock.release()
    runner[0](*runner[1], **runner[2])

  def run_all(self):
    """
    Run all items in this keyRunner."""
    while len(self.run) > 0:
      self.run_next()
      if len(self.run) == 0:
        self.lock.acquire()
        if len(self.run) == 0:
          self.in_queue = False
          self.lock.release()
          break
        self.lock.release()

def futureJob(future, job):
  try:
    job[0](*job[1], **job[2])
    future.setter(True)
  except Exception as e:
    print "Error running futureJob:", e
    future.setter(False)


class ListenableFuture():
  def __init__(self):
    self.lock = threading.Condition()
    self.settable = None
    self.listeners = list()
    self.callables = list()
  
  def addListener(self, listener, args=(), kwargs={}):
    if self.settable == None:
      self.listeners.append((listener, args, kwargs))
    else:
      listener(*args, **kwargs)

  def addCallable(self, cable, args=(), kwargs={}):
    if self.settable is None:
      self.callables.append((cable, args, kwargs))
    else:
      cable(self.settable, *args, **kwargs)

  def get(self, timeout=2**32):
    if self.settable is not None:
      return self.settable
    start = time.time()
    while self.settable is None and time.time() - start < timeout:
      self.lock.acquire()
      self.lock.wait(timeout - (time.time() - start))
      self.lock.release
    return self.settable

  def setter(self, obj):
    if self.settable is None:
      self.settable = obj
      self.lock.acquire()
      self.lock.notify_all()
      self.lock.release()
      while len(self.listeners) > 0:
        i = self.listeners.pop(0)
        try:
          i[0](*i[1], **i[2])
        except Exception as e:
          print "Exception calling listener", i[0], e
      while len(self.callables) > 0:
        i = self.callables.pop(0)
        try:
          i[0](self.settable, *i[1], **i[2])
        except Exception as e:
          print "Exception calling listener", i[0], e
    else:
      raise Exception("Already Set!")
      

class Singleton(object):
  """A Simple inheritable singleton"""

  __single = None

  def __new__(cls, *args, **kwargs):
    if cls != type(cls.__single):
      cls.__single = object.__new__(cls, *args, **kwargs)
    return cls.__single


class Clock(Singleton):
  """A Simple clock class to allow for retrieval of time from multiple threads to be more efficient.
  This class is a singleton so anyone using it will be using the same instance.
  The clock updates every 100ms so calls to get time often can be more per formant if they don't need to be exact.
  @undocumented: __init__
  @undocumented: __del__
  @undocumented: __update_clock
  @undocumented: __start_clock_thread
  @undocumented: __stop_clock_thread
  """
  def __init__(self):
    self.current = int(time.time()*1000)
    self.run = False
    self.thread = None
    self.get_time = time.time
    self.sleep = time.sleep
    self.__start_clock_thread()

  def __del__(self):
    self.__stop_clock_thread()

  def __update_clock(self):
    while self.run:
      self.accurate_time()
      self.sleep(.1)
      
  def accurate_time_millis(self):
    """
    Get the actual current time. This should be called as little as often, and only when exact times are needed.
    @rtype: int
    @return: returns a float with whole numbers being seconds. Pretty much identical to time.time()
    """
    self.current = self.get_time()
    return int(self.current*1000)

  def accurate_time(self):
    """
    Get the actual current time. This should be called as little as often, and only when exact times are needed.
    @rtype: float
    @return: returns a float with whole numbers being seconds. Pretty much identical to time.time()
    """
    self.current = self.get_time()
    return self.current

  def last_known_time_millis(self):
    """
    Gets the last ran time in milliseconds. This is accurate to 100ms.
    @rtype: int
    @return: an integer representing the last known time in millis.
    """
    return int(self.current*1000)

  def last_known_time(self):
    """
    Gets the last ran time seconds.milliseconds. This is accurate to 100ms.
    @rtype: float
    @return: represents the last known time.
    """
    return self.current

  def __start_clock_thread(self):
    if self.thread == None or not self.thread.is_alive():
      self.run = True
      self.thread = threading.Thread(target=self.__update_clock)
      self.thread.name = "Clock Thread"
      self.thread.daemon = True
      self.thread.start()

  def __stop_clock_thread(self):
    self.run = False


"""
threadly a simple threadpool and scheduler for python.
"""

import threading
import Queue
from Queue import Empty as EmptyException
import logging
import time



class Scheduler(object):
  """
  Main Scheduler Object.
  """

  def __init__(self, poolsize):
    """
    Construct an Scheduler instance with the set thread pool size.
    
    `poolsize` positive integer for the number of threads you want in this pool .
    """

    self.__log = logging.getLogger("root.threadly")
    self.__clock = Clock()
    self.__key_lock = threading.Condition()
    self.__poolsize = poolsize
    self.__running = True
    self.__in_shutdown = False
    self.__main_queue = Queue.Queue()
    self.__delayed_tasks = SortedLockingList()
    self.__in_delay = False
    self.__threads = list()
    self.__delay_lock = threading.Condition()
    self.__keys = dict()
    for i in xrange(self.__poolsize):
      tmp_thread = threading.Thread(target=self.__thread_pool)
      tmp_thread.name = "Executor-Pool-Thread-%d"%(i)
      tmp_thread.daemon = True
      tmp_thread.start()
      self.__threads.append(tmp_thread)

  def get_poolsize(self):
    """
    Returns the number of threads used in this Pool.
    """
    return len(self.__threads)

  def get_queue_size(self):
    """
    Returns the number of items currently awaiting Execution.
    """
    return self.__main_queue.qsize()

  def execute(self, task, args=(), kwargs={}):
    """
    Execute a given task as soon as possible.
    
    `task` is a callable to be called on the Scheduler.

    `args` are the arguments to pass to the callable when called.

    `kwargs` are the keyword args to be passed to the callable when called.
    """
    self.schedule(task, args=args, kwargs=kwargs)

  def schedule_with_future(self, task, delay=0, key=None, args=(), kwargs={}):
    """
    Returns a `ListenableFuture` for this task.  Once the task is completed the future will also be completed. 
    This works pretty much exactly like `schedule` except you can not make a task recurring.
    
    `task` is a callable to be called on the Scheduler.

    `delay` this is the time to wait (in milliseconds!!) before scheduler will call the passed task.

    `key` this is any python object to use as a key.  All tasks using this key will be ran in a single threaded manor.

    `args` are the arguments to pass to the callable when called.

    `kwargs` are the keyword args to be passed to the callable when called.
    """
    job=(task, args, kwargs)
    future = ListenableFuture()
    self.schedule(futureJob, delay=delay, key=key, args=(future, job))
    return future

  def schedule(self, task, delay=0, recurring=False, key=None, args=(), kwargs={}):
    """
    This schedules a task to be executed.  It can be delayed, and set to a key.  It can also be marked
    as recurring. 
    
    `task` is a callable to be called on the Scheduler.

    `delay` this is the time to wait (in milliseconds!!) before scheduler will call the passed task.

    `recurring` set this to True if this should be a recurring.  You should be careful that delay is > 0 when setting this to True

    `key` this is any python object to use as a key.  All tasks using this key will be ran in a single threaded manor.

    `args` are the arguments to pass to the callable when called.

    `kwargs` are the keyword args to be passed to the callable when called.
    """
    if delay > 0:
      s_task = int(self.__clock.accurate_time() * 1000) + delay
      send = False
      if delay/1000.0 <= self.__get_next_wait_time():
        send = True
      self.__delayed_tasks.add((s_task, task, delay, recurring, key, args, kwargs))
      if send:
        self.__main_queue.put((self.__empty, (), {}))
    else:
      if key != None:
        self.__key_lock.acquire()
        if key not in self.__keys:
          tmp = KeyRunner()
          self.__keys[key] = tmp
        self.__key_lock.release()
        run_key = self.__keys[key]
        run_key.add((task, args, kwargs))
        run_key.lock.acquire()
        if not run_key.in_queue and run_key.size() > 0:

          run_key.in_queue = True
          self.__main_queue.put((run_key.run_all, (), {}))
        run_key.lock.release()
      else:
        self.__main_queue.put((task, args, kwargs))

  def remove(self, task):
    """
    Remove a scheduled task from the queue.  This is a best effort remove, the task could still possibly run.  This is most useful to cancel recurring tasks.
    If there is more then one task with this callable scheduled only the first one is removed.

    `task` callable task to remove from the scheduled tasks list.
    """
    count = 0
    found = False
    for tasks in self.__delayed_tasks.safeIterator():
      if tasks[1] == task:
        found = True
        break
      else:
        count+=1
    if found:
      self.__delayed_tasks.pop(count)
      return True
    return False

  def shutdown(self):
    """
    Shuts down the threadpool.  Any task currently on the queue will be ran, but all Scheduled tasks 
    will removed and no more tasks can be added.
    """
    self.__running = False
    self.__delayed_tasks.clear()
    self.execute(self.__internal_shutdown)

  def shutdown_now(self):
    """
    Shuts down the threadpool.  Any task currently being executed will still complete, 
    but the queue will be emptied out.
    """
    self.__running = False
    self.__delayed_tasks.clear()
    while not self.__main_queue.empty():
      self.__main_queue.get_nowait()
    self.__internal_shutdown()

  def __internal_shutdown(self):
    self.__running = False
    for tmp_thread in self.__threads:
      while tmp_thread != None and tmp_thread.isAlive() and threading != None and tmp_thread != threading.current_thread():
        self.__main_queue.put((self.__empty, (), {}))

  def __empty(self):
    pass

  def __get_next_wait_time(self):
    tmp = self.__delayed_tasks.peek()
    if tmp == None or self.__delayed_tasks.size() == 0:
      return 2**32
    else:
      task = tmp[0] - int(self.__clock.accurate_time()*1000)
      return (task/1000.0)-.0005

  def __check_delay_queue(self):
    dl = self.__delayed_tasks.lock()
    if dl:
      try:
        to = self.__get_next_wait_time()
        while to <= 0:
          run_task = self.__delayed_tasks.pop(0)
          self.schedule(run_task[1], key=run_task[4], args=run_task[5], kwargs=run_task[6])
          #run_task[3] is recurring, if so we add again as a scheduled event
          if run_task[3] == True and not self.__in_shutdown:
            self.schedule(run_task[1], run_task[2], run_task[3], run_task[4], run_task[5], run_task[6])
          to = self.__get_next_wait_time()
      finally:
        self.__delayed_tasks.unlock()
    return dl


  def __thread_pool(self):
    while self.__running:
      try:
        runner = None
        to = self.__get_next_wait_time()
        if to <= 0 and self.__check_delay_queue():
          to = self.__get_next_wait_time()
        if to <= 0:
          to = 5
        if runner == None:
          runner = self.__main_queue.get(True, to)
        if runner != None:
          runner[0](*runner[1], **runner[2])
      except IndexError as exp:
        pass
      except EmptyException as exp:
        pass
      except Exception as exp:
        self.__log.error("Exception while Executing: %s, %s"%(runner, exp))


class SortedLockingList:
  def __init__(self):
    self.slist = list()
    self.uslist = list()
    self.__lock = threading.Condition()

  def clear(self):
    self.__lock.acquire()
    self.slist = list()
    self.uslist = list()
    self.__lock.release()


  def lock(self):
    return self.__lock.acquire(False)

  def unlock(self):
    self.__lock.release()

  def size(self):
    return len(self.slist) + len(self.uslist)

  def peek(self):
    self.__lock.acquire()
    self.__combine()
    if len(self.slist) == 0:
      tmp = None
    else:
      tmp = self.slist[0]
    self.__lock.release()
    return tmp

  def pop(self, i=0):
    self.__lock.acquire()
    self.__combine()
    tmp = self.slist.pop(i)
    self.__lock.release()
    return tmp
  
  def add(self, item):
    self.uslist.append(item)
  
  def __combine(self):
    try:
      self.__lock.acquire()
      while len(self.uslist) > 0:
        item = self.uslist.pop(0)
        c = len(self.slist)
        if c == 0:
          self.slist.append(item)
        elif item < self.slist[0]:
          self.slist.insert(0, item)
        elif c == 1 or item > self.slist[c-1]:
          self.slist.append(item)
        else:
          l = self.slist
          lmax = len(l)-1
          ch = c/2
          while True:
            if item < l[ch]:
              if ch == 0:
                print "ERROR:"
                return
              else:
                lmax = ch-1
                ch = ch/2
            elif item > l[ch]:
              if ch >= lmax:
                self.slist.insert(ch+1, item)
                break
              else:
                diff = lmax-ch
                ch = ch+((diff/2)+1)
            else:
              l.insert(ch, item)
              break
    finally:
      self.__lock.release()

  def remove(self, item):
    try:
      self.__lock.acquire()
      self.__combine()
      self.slist.remove(item)
    except:
      pass
    finally:
      self.__lock.release()

  def safeIterator(self):
    local = list(self.slist)
    for i in local:
      yield i


class Executor(Scheduler):
  """
  A class for backwards compatibility, Scheduler should be used instead now.
  """
  pass


class KeyRunner(object):
  """
  A class to wrap keys objects for the executer.
  Items can be added to the KeyRunner while its running.  
  This is used to keep all tasks for a given key in one thread.
  """
  def __init__(self):
    self.__run = list()
    self.lock = threading.Condition()
    self.in_queue = False

  def size(self):
    return len(self.__run)

  def add(self, task):
    """
    Add a task to this runner set.

    `task` adds callable task to the current keyrunner set.
    """
    self.lock.acquire()
    self.__run.append(task)
    self.lock.release()

  def run_next(self):
    """
    Run the next item for this key.
    """
    self.lock.acquire()
    runner = self.__run.pop(0)
    self.lock.release()
    runner[0](*runner[1], **runner[2])

  def run_all(self):
    """
    Run all items in this keyRunner.
    """
    while len(self.__run) > 0:
      self.run_next()
      if len(self.__run) == 0:
        self.lock.acquire()
        if len(self.__run) == 0:
          self.in_queue = False
          self.lock.release()
          break
        self.lock.release()

def futureJob(future, job):
  """
  This is a simple helper function used to wrap a task on the Scheduler in a future.  Once
  the job runs the future will complete. 
  
  `future` The future that will be completed once the job finishes.
  `job` The job to run before completing the future.
  """
  try:
    job[0](*job[1], **job[2])
    future.setter(True)
  except Exception as e:
    print "Error running futureJob:", e
    future.setter(False)


class ListenableFuture():
  """
  This class i used to make a Future that can have listeners and callbacks added to it.
  Once setter(object) is called all listeners/callbacks are also called.  Callbacks will 
  be given the set object, and .get() will return said object.
  """
  def __init__(self):
    self.lock = threading.Condition()
    self.settable = None
    self.listeners = list()
    self.callables = list()
  
  def addListener(self, listener, args=(), kwargs={}):
    """
    Add a listener function to this ListenableFuture.  Once set is called on this future
    all listeners will be ran.  Arguments for the listener can be given if needed.
    
    `listener` a callable that will be called when the future is completed
    `args` tuple arguments that will be passed to the listener when called.
    `kwargs` dict keyword arguments to be passed to the passed listener when called.
    """
    if self.settable == None:
      self.listeners.append((listener, args, kwargs))
    else:
      listener(*args, **kwargs)

  def addCallable(self, cable, args=(), kwargs={}):
    """
    Add a callable function to this ListenableFuture.  Once set is called on this future
    all callables will be ran.  This works the same as the listener except the set object is passed 
    as the first argument when the callable is called. Arguments for the listener can be given if needed.
    
    `cable` a callable that will be called when the future is completed, it must have at least 1 argument.
    `args` tuple arguments that will be passed to the listener when called.
    `kwargs` dict keyword arguments to be passed to the passed listener when called.
    """
    if self.settable is None:
      self.callables.append((cable, args, kwargs))
    else:
      cable(self.settable, *args, **kwargs)

  def get(self, timeout=2**32):
    """
    This is a blocking call that will return the set object once it is set.
    
    `timeout` The max amount of time to wait for get (in seconds).  If this is reached a null is returned
    `returns` the set object.  This can technically be anything so know what your listening for.
    """
    if self.settable is not None:
      return self.settable
    start = time.time()
    try:
      self.lock.acquire()
      while self.settable is None and time.time() - start < timeout:
        self.lock.wait(timeout - (time.time() - start))
      return self.settable
    finally:
      self.lock.release()

  def setter(self, obj):
    """
    This is used to complete this future. Whatever thread sets this will be used to call all 
    listeners and callables for this future.
    
    `obj` The object you want to set on this future (usually use just True if you dont care)
    """
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
  """
  A Simple clock class to allow for retrieval of time from multiple threads to be more efficient.
  This class is a singleton so anyone using it will be using the same instance.
  The clock updates every 100ms so calls to get time often can be more per formant if they don't need to be exact.
  """
  def __init__(self):
    self.__current = int(time.time()*1000)
    self.__run = False
    self.__thread = None
    self.__get_time = time.time
    self.__sleep = time.sleep
    self.__start_clock_thread()

  def __del__(self):
    self.__stop_clock_thread()

  def __update_clock(self):
    while self.__run:
      self.accurate_time()
      self.__sleep(.1)
      
  def accurate_time_millis(self):
    """
    Get the actual current time. This should be called as little as often, and only 
    when exact times are needed.
    
    `returns` an Integer of the current time in millis.
    """
    self.__current = self.__get_time()
    return int(self.__current*1000)

  def accurate_time(self):
    """
    Get the actual current time. This should be called as little as 
    often, and only when exact times are needed.
    
    `returns` a float with whole numbers being seconds. Pretty much identical to time.time()
    """
    self.__current = self.__get_time()
    return self.__current

  def last_known_time_millis(self):
    """
    Gets the last ran time in milliseconds. This is accurate to 100ms.
    
    `returns` an integer representing the last known time in millis.
    """
    return int(self.__current*1000)

  def last_known_time(self):
    """
    Gets the last ran time seconds.milliseconds. This is accurate to 100ms.
    
    `returns` a float that represents the last known time with seconds as the whole numbers.
    """
    return self.__current

  def __start_clock_thread(self):
    if self.__thread == None or not self.__thread.is_alive():
      self.__run = True
      self.__thread = threading.Thread(target=self.__update_clock)
      self.__thread.name = "Clock Thread"
      self.__thread.daemon = True
      self.__thread.start()

  def __stop_clock_thread(self):
    self.__run = False


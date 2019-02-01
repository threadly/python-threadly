import threading
import logging


class KeyedExecutor(object):
  """
  A class to wrap keys objects for the executer.
  Items can be added to the KeyRunner while its running.
  This is used to keep all tasks for a given key in one thread.
  """
  def __init__(self):
    self.__log = logging.getLogger("root.threadly")
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
    try:
      runner[0](*runner[1], **runner[2])
    except Exception as exp:
      self.__log.error("Exception while Executing function:\"{}\" with args:\"{}\" and kwargs:\"{}\"".format(runner[0].__name__, runner[1],runner[2]))
      self.__log.exception(exp)


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

"""
threadly a simple threadpool and scheduler for python.
"""

import threading
import logging
try:
    from Queue import Queue
    from Queue import Empty as EmptyException
except:
    from queue import Queue, Empty as EmptyException

from threadly.Structures import SortedLockingList
from threadly.KeyedExecutor import KeyedExecutor
from threadly.Futures import ListenableFuture
from threadly.Futures import future_job
from threadly.Clock import Clock

try:
    xrange(1)
except:
    xrange = range

class Scheduler(object):
    """
    Main Scheduler Object.
    """

    def __init__(self, poolsize):
        """
        Construct an Scheduler instance with the set thread pool size.

        `poolsize` positive integer for the number of threads you want
        in this pool .
        """

        self.__log = logging.getLogger("root.threadly")
        self.__clock = Clock()
        self.__key_lock = threading.Condition()
        self.__poolsize = poolsize
        self.__running = True
        self.__in_shutdown = False
        self.__main_queue = Queue()
        self.__delayed_tasks = SortedLockingList()
        self.__in_delay = False
        self.__threads = list()
        self.__delay_lock = threading.Condition()
        self.__keys = dict()
        for i in xrange(self.__poolsize):
            tmp_thread = threading.Thread(target=self.__thread_pool)
            tmp_thread.name = "Executor-Pool-Thread-%d" % (i)
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

    def execute(self, task, args=None, kwargs=None):
        """
        Execute a given task as soon as possible.

        `task` is a callable to be called on the Scheduler.

        `args` are the arguments to pass to the callable when called.

        `kwargs` are the keyword args to be passed to the callable when called.
        """
        args = args or ()
        kwargs = kwargs or {}
        self.schedule(task, args=args, kwargs=kwargs)

    def schedule_with_future(self, task, delay=0, key=None, args=None, kwargs=None):
        """
        Returns a `ListenableFuture` for this task. Once the task is
        completed the future will also be completed.  This works pretty much
        exactly like `schedule` except you can not make a task recurring.

        `task` is a callable to be called on the Scheduler.

        `delay` this is the time to wait (in milliseconds!!) before scheduler
        will call the passed task.

        `key` this is any python object to use as a key.    All tasks using
        this key will be ran in a single threaded manor.

        `args` are the arguments to pass to the callable when called.

        `kwargs` are the keyword args to be passed to the callable when called.
        """
        args = args or ()
        kwargs = kwargs or {}
        job = (task, args, kwargs)
        future = ListenableFuture()
        self.schedule(future_job, delay=delay, key=key, args=(future, job))
        return future

    def schedule(self, task, delay=0, recurring=False, key=None, args=None, kwargs=None):
        """
        This schedules a task to be executed.    It can be delayed, and set
        to a key.  It can also be marked as recurring.

        `task` is a callable to be called on the Scheduler.

        `delay` this is the time to wait (in milliseconds!!) before scheduler
        will call the passed task.

        `recurring` set this to True if this should be a recurring.
        You should be careful that delay is > 0 when setting this to True.

        `key` this is any python object to use as a key.  All tasks using this
        key will be ran in a single threaded manor.

        `args` are the arguments to pass to the callable when called.

        `kwargs` are the keyword args to be passed to the callable when called.
        """
        args = args or ()
        kwargs = kwargs or {}
        if delay > 0:
            s_task = int(self.__clock.accurate_time() * 1000) + delay
            send = False
            if delay / 1000.0 <= self.__get_next_wait_time():
                send = True
            self.__delayed_tasks.add((s_task, task, delay, recurring, key, args, kwargs))
            if send:
                self.__main_queue.put((self.__empty, (), {}))
        else:
            if key is not None:
                self.__key_lock.acquire()
                if key not in self.__keys:
                    tmp = KeyedExecutor()
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
        Remove a scheduled task from the queue.  This is a best effort remove,
        the task could still possibly run.  This is most useful to cancel
        recurring tasks.  If there is more then one task with this callable
        scheduled only the first one is removed.

        `task` callable task to remove from the scheduled tasks list.
        """
        count = 0
        found = False
        for tasks in self.__delayed_tasks.safeIterator():
            if tasks[1] == task:
                found = True
                break
            else:
                count += 1
        if found:
            self.__delayed_tasks.pop(count)
            return True
        return False

    def shutdown(self):
        """
        Shuts down the threadpool.  Any task currently on the queue will be
        ran, but all Scheduled tasks will removed and no more tasks can be
        added.
        """
        self.__running = False
        self.__delayed_tasks.clear()
        self.execute(self.__internal_shutdown)

    def shutdown_now(self):
        """
        Shuts down the threadpool.  Any task currently being executed will
        still complete, but the queue will be emptied out.
        """
        self.__running = False
        self.__delayed_tasks.clear()
        while not self.__main_queue.empty():
            try:
                self.__main_queue.get_nowait()
            except:
                pass
        self.__internal_shutdown()

    def __internal_shutdown(self):
        self.__running = False
        for tmp_thread in self.__threads:
            if tmp_thread is not None and tmp_thread.isAlive() and threading is not None and tmp_thread != threading.current_thread():
                self.__main_queue.put((self.__empty, (), {}))
                self.__main_queue.put((self.__empty, (), {}))
                self.__main_queue.put((self.__empty, (), {}))
                self.__main_queue.put((self.__empty, (), {}))

    def __empty(self):
        pass

    def __get_next_wait_time(self):
        tmp = self.__delayed_tasks.peek()
        if tmp is None or self.__delayed_tasks.size() == 0:
            return 2 ** 32
        else:
            task = tmp[0] - int(self.__clock.accurate_time() * 1000)
            return (task / 1000.0) - .0005

    def __check_delay_queue(self):
        dl = self.__delayed_tasks.lock()
        if dl:
            try:
                time_out = self.__get_next_wait_time()
                while time_out <= 0:
                    run_task = self.__delayed_tasks.pop(0)
                    self.schedule(run_task[1], key=run_task[4], args=run_task[5], kwargs=run_task[6])
                    #run_task[3] is recurring, if so we add again as a scheduled event
                    if run_task[3] == True and not self.__in_shutdown:
                        self.schedule(run_task[1], run_task[2], run_task[3], run_task[4], run_task[5], run_task[6])
                    time_out = self.__get_next_wait_time()
            finally:
                self.__delayed_tasks.unlock()
        return dl

    def __thread_pool(self):
        while self.__running:
            try:
                runner = None
                time_out = self.__get_next_wait_time()
                if time_out <= 0 and self.__check_delay_queue():
                    time_out = self.__get_next_wait_time()
                if time_out <= 0:
                    time_out = 5
                if runner is None:
                    runner = self.__main_queue.get(True, time_out)
                if runner is not None:
                    runner[0](*runner[1], **runner[2])
            except IndexError as exp:
                pass
            except EmptyException as exp:
                pass
            except Exception as exp:
                self.__log.error("Exception while Executing: %s, %s"%(runner, exp))


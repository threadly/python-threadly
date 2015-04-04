"""
Futures tools for threadly
"""

import threading
import time


class ListenableFuture(object):
    """
    This class i used to make a Future that can have listeners and callbacks
    added to it.  Once setter(object) is called all listeners/callbacks are
    also called.  Callbacks will be given the set object, and .get() will
    return said object.
    """
    def __init__(self):
        self.lock = threading.Condition()
        self.settable = None
        self.listeners = list()
        self.callables = list()

    def add_listener(self, listener, args=None, kwargs=None):
        """
        Add a listener function to this ListenableFuture.  Once set is called
        on this future all listeners will be ran.  Arguments for the listener
        can be given if needed.

        `listener` a callable that will be called when the future is completed
        `args` tuple arguments that will be passed to the listener when called.
        `kwargs` dict keyword arguments to be passed to the passed listener
        when called.
        """
        args = args or ()
        kwargs = kwargs or {}
        if self.settable is None:
            self.listeners.append((listener, args, kwargs))
        else:
            listener(*args, **kwargs)

    def add_callable(self, cable, args=None, kwargs=None):
        """
        Add a callable function to this ListenableFuture.  Once set is called
        on this future all callables will be ran.  This works the same as the
        listener except the set object is passed as the first argument when
        the callable is called. Arguments for the listener can be given if
        needed.

        `cable` a callable that will be called when the future is completed,
        it must have at least 1 argument.
        `args` tuple arguments that will be passed to the listener when called.
        `kwargs` dict keyword arguments to be passed to the passed listener
        when called.
        """
        args = args or ()
        kwargs = kwargs or {}
        if self.settable is None:
            self.callables.append((cable, args, kwargs))
        else:
            cable(self.settable, *args, **kwargs)

    def get(self, timeout=2 ** 32):
        """
        This is a blocking call that will return the set object once it is set.

        `timeout` The max amount of time to wait for get (in seconds).
        If this is reached a null is returned.
        `returns` the set object.  This can technically be anything so know
        what your listening for.
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
        This is used to complete this future. Whatever thread sets this will
        be used to call all listeners and callables for this future.

        `obj` The object you want to set on this future
        (usually use just True if you dont care)
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
                except Exception as exp:
                    print("Exception calling listener", i[0], exp)
            while len(self.callables) > 0:
                i = self.callables.pop(0)
                try:
                    i[0](self.settable, *i[1], **i[2])
                except Exception as exp:
                    print("Exception calling listener", i[0], exp)
        else:
            raise Exception("Already Set!")


def future_job(future, job):
    """
    This is a simple helper function used to wrap a task on the Scheduler
    in a future.  Once the job runs the future will complete.

    `future` The future that will be completed once the job finishes.
    `job` The job to run before completing the future.
    """
    try:
        job[0](*job[1], **job[2])
        future.setter(True)
    except Exception as exp:
        print("Error running futureJob:", exp)
        future.setter(False)



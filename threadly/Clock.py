"""
Clock tools for threadly
"""

import threading
import time

def clockSingleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

@clockSingleton
class Clock(object):
    """
    A Simple clock class to allow for retrieval of time from multiple threads
    to be more efficient.  This class is a singleton so anyone using it will
    be using the same instance.  The clock updates every 100ms so calls to get
    time often can be more per formant if they don't need to be exact.
    """
    def __init__(self):
        self.__current = int(time.time() * 1000)
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
        Get the actual current time. This should be called as little as often,
        and only when exact times are needed.

        `returns` an Integer of the current time in millis.
        """
        self.__current = self.__get_time()
        return int(self.__current * 1000)

    def accurate_time(self):
        """
        Get the actual current time. This should be called as little as
        often, and only when exact times are needed.

        `returns` a float with whole numbers being seconds.
        Pretty much identical to time.time()
        """
        self.__current = self.__get_time()
        return self.__current

    def last_known_time_millis(self):
        """
        Gets the last ran time in milliseconds. This is accurate to 100ms.

        `returns` an integer representing the last known time in millis.
        """
        return int(self.__current * 1000)

    def last_known_time(self):
        """
        Gets the last ran time seconds.milliseconds. This is accurate to 100ms.

        `returns` a float that represents the last known time with seconds as
        the whole numbers.
        """
        return self.__current

    def __start_clock_thread(self):
        if self.__thread is None or not self.__thread.is_alive():
            self.__run = True
            self.__thread = threading.Thread(target=self.__update_clock)
            self.__thread.name = "Clock Thread"
            self.__thread.daemon = True
            self.__thread.start()

    def __stop_clock_thread(self):
        self.__run = False


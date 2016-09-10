"""
Data strutures used in threadly.
"""
from threading import Condition


class SortedLockingList(object):
    """
    This is a sortedList implementation for multiThreads.
    One main goal is to make adds as cheap as possible.
    """
    def __init__(self):
        self.slist = list()
        self.uslist = list()
        self.__lock = Condition()

    def clear(self):
        """
        clears out the list
        """
        self.__lock.acquire()
        self.slist = list()
        self.uslist = list()
        self.__lock.release()


    def lock(self):
        """
        Returns `True` if you get the lock `False` if you dont.

        Non-Blocking lock request, returns True if you get the lock
        false if you dont.  This is the main lock for the list once
        acquired you must release before any other thread can access the list.
        """
        return self.__lock.acquire(False)

    def unlock(self):
        """
        Releases the lists lock.
        """
        self.__lock.release()

    def size(self):
        """
        Returns and `int` of the current size of the list.
        """
        return len(self.slist) + len(self.uslist)

    def peek(self):
        """
        Returns the first entry in the list, this does not remove the entry
        from the list.
        """
        self.__lock.acquire()
        self.__combine()
        if len(self.slist) == 0:
            tmp = None
        else:
            tmp = self.slist[0]
        self.__lock.release()
        return tmp

    def pop(self, i=0):
        """
        Returns either the first entry from the list or the spesified entry.
        """
        self.__lock.acquire()
        self.__combine()
        tmp = self.slist.pop(i)
        self.__lock.release()
        return tmp

    def add(self, item):
        """
        Adds an entry to the list.

        `item` entry to add to the list.
        """
        self.uslist.append(item)

    def __combine(self):
        try:
            self.__lock.acquire()
            while len(self.uslist) > 0:
                item = self.uslist.pop(0)
                llen = len(self.slist)
                if llen == 0:
                    self.slist.append(item)
                elif item < self.slist[0]:
                    self.slist.insert(0, item)
                elif llen == 1 or item > self.slist[llen - 1]:
                    self.slist.append(item)
                else:
                    lmax = len(self.slist) - 1
                    cur_pos = llen // 2
                    while True:
                        if item < self.slist[cur_pos]:
                            if cur_pos == 0:
                                return
                            else:
                                lmax = cur_pos - 1
                                cur_pos = cur_pos // 2
                        elif item > self.slist[cur_pos]:
                            if cur_pos >= lmax:
                                self.slist.insert(cur_pos + 1, item)
                                break
                            else:
                                diff = lmax - cur_pos
                                cur_pos = cur_pos + ((diff // 2) + 1)
                        else:
                            self.slist.insert(cur_pos, item)
                            break
        finally:
            self.__lock.release()

    def remove(self, item):
        """
        Removes an item from the list.

        `item` item to remove from the list.
        """
        try:
            self.__lock.acquire()
            self.__combine()
            self.slist.remove(item)
        except ValueError:
            pass
        finally:
            self.__lock.release()

    def safeIterator(self):
        """
        This is a non-Blocking safe iterator for the list.  It is essentially
        just a copy of the sorted lists entries at the time it was called.
        """
        try:
            self.__lock.acquire()
            self.__combine()
        finally:
            self.__lock.release()
        local = list(self.slist)
        for i in local:
            yield i



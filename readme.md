# Threadly

Threadly is a threadpool/scheduler for python.  It allows execution of function pointers for easy periodic task scheduleing, keyed execution, or just regular thread pooling.

This project is loosely based off the java Threadly threadpool library [threadly.org](http://threadly.org).

##Documentation:

Documentation can be found [here](http://lwahlmeier.github.io/python-threadly/doc/)

##Basics:


Threadly is very easy to use.  Here are some basic examples.

----
```python
import threadly

def testFoo():
    print "Thread %s Executed"%(threading.current_thread())

executor = threadly.Scheduler(10) #starts a thread pool with 10 threads

#this will Execute a task in 100 ms
executor.schedule(testFoo, delay=100)

#this will Execute a task every second until removed
executor.schedule(testFoo, delay=1000, recurring=True)

#these execute the task asap
executor.execute(testFoo)
executor.execute(testFoo)
executor.execute(testFoo)

#this will run a task, any other tasks using the same key will be executed as though they are single threaded
executor.schedule(testFoo, key="someObject")

#this removes/stops the first scheduled task for this callable, if it was recurring it will no longer be
executor.removeScheduled(testFoo)

#this shuts down the threadpool
executor.shutdown()
```

##Clock:

Threadly has a Clock class.  This is used to make getting time from multipule threads often a little more efficient. It is a singleton and only one can ever exist.  It keep 100 millisecond resolution, but can be more accurate if needed.

----
```python
from threadly import Clock

c = Clock()

#this outputs the time in millis.  Note this is an int/long not a float
print c.last_known_time_millis()
        
#this outputs time like time.time() as a float where everything less then 1 is less then a second
print c.last_known_time()

#This gets accurate time, just like time.time()
print c.accurate_time()
```        
        
>__NOTE:__ There is an __stop() function but it should only be used if you know what your doing as it will stop the clock updating thread, and since there is only one instance it stops for everyone.

import threadly, time, logging, sys, traceback, cProfile, pstats, StringIO

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')


sch = threadly.Scheduler(100)
llf = list()

def pstack():
  code = []
  for threadId, stack in sys._current_frames().items():
    code.append("\n# ThreadID: %s" % threadId)
    for filename, lineno, name, line in traceback.extract_stack(stack):
      code.append('File: "%s", line %d, in %s' % (filename,lineno, name))
      if line:
        code.append("  %s" % (line.strip()))

  for line in code:
    print line

def blah():
 pass
 

pr = cProfile.Profile()
pr.enable()
start = time.time()
for i in xrange(20000):
  #sch.execute(blah)
  lf =  sch.schedule_with_future(blah, delay=10000)
  #sch.schedule(blah, delay=100)
  #lf =  sch.schedule_with_future(time.time)
  llf.append(lf)
  if i%100 == 0:
    print i
print time.time() - start

#start = time.time()
while len(llf) > 0:
  X = llf[0].get(5)
  if X != None:
    llf.pop(0)
#  else:
#    print "-"*30
#    print sch._Scheduler__delayed_tasks.size(), len(llf)
#    print pstack()

while sch.get_queue_size() > 0 or sch._Scheduler__delayed_tasks.size() > 0:
  print sch._Scheduler__delayed_tasks.size()
  time.sleep(.1)
print sch._Scheduler__delayed_tasks.size()
for lf in llf:
  lf.get()
print time.time() - start
pr.disable()
s = StringIO.StringIO()
sortby = 'cumulative'
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()
print s.getvalue()


import threadly, time

sch = threadly.Scheduler(202)
llf = list()

start = time.time()
for i in xrange(200000):
  sch.execute(time.time)
  #lf =  sch.schedule_with_future(time.time, delay=50)
  #lf =  sch.schedule_with_future(time.time)
  #llf.append(lf)
print time.time() - start

start = time.time()
#for lf in llf:
#  lf.get()
while sch.get_queue_size() > 0:
  time.sleep(10)
print time.time() - start



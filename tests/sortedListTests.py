import threadly, random, time, logging, unittest



class TestSchedule(unittest.TestCase):
  def test_SortCheck1(self):
    slist = threadly.SortedLockingList()
    slist.add(10)
    slist.add(15)
    slist.add(1)
    slist.add(1)
    slist.add(6)
    slist.add(0)
    slist.add(2)
    slist.add(3)
    slist.add(18)
    slist.remove(6)
    self.assertEquals(0, slist.pop())
    self.assertEquals(1, slist.pop())
    self.assertEquals(1, slist.pop())
    self.assertEquals(2, slist.pop())
    self.assertEquals(3, slist.pop())
    self.assertEquals(10, slist.pop())
    self.assertEquals(15, slist.pop())
    self.assertEquals(18, slist.pop())
    self.assertEquals(0, slist.size())
    



if __name__ == '__main__':
  unittest.main()



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
    self.assertEqual(0, slist.pop())
    self.assertEqual(1, slist.pop())
    self.assertEqual(1, slist.pop())
    self.assertEqual(2, slist.pop())
    self.assertEqual(3, slist.pop())
    self.assertEqual(10, slist.pop())
    self.assertEqual(15, slist.pop())
    self.assertEqual(18, slist.pop())
    self.assertEqual(0, slist.size())
    



if __name__ == '__main__':
  unittest.main()



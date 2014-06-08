import threadly, time, random, unittest

class TestSchedule(unittest.TestCase):
  def test_Singleton(self):
    X = threadly.Clock()
    Q = threadly.Clock()
    self.assertEquals(X, Q)
  def test_clockUpdateCheck(self):
    C = threadly.Clock()
    t = C.lastKnownTimeMillis()
    t1 = C.lastKnownTimeMillis()
    self.assertEquals(t, t1)
    t2 = C.accurateTime()
    self.assertTrue(t2!=t1)

if __name__ == '__main__':
  unittest.main()


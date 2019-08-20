import threadly, time, random, unittest

class TestSchedule(unittest.TestCase):
  
  def test_Singleton(self):
    X = threadly.Clock()
    Q = threadly.Clock()
    self.assertEqual(X, Q)
    
  def test_clockUpdateCheck(self):
    C = threadly.Clock()
    t = C.last_known_time_millis()
    t1 = C.last_known_time_millis()
    self.assertEqual(t, t1)
    t2 = C.accurate_time()
    self.assertTrue(t2!=t1)

if __name__ == '__main__':
  unittest.main()


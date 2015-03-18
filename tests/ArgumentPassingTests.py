import threadly, time, random
import unittest
  

class TestAugumentParsing(unittest.TestCase):
  
  def arguments(self, arg1, key=None):
    self.assertNotEqual(arg1, None)
    self.assertNotEqual(key, None)
    self.arg1 = arg1
    self.keys = {"key":key}


  def test_keyTestExecute(self):
    self.arg1 = None
    self.keys = {}
    sch = threadly.Scheduler(10)
    sch.execute(self.arguments, args=("test", ), kwargs={"key":"test"})
    time.sleep(.1)
    self.assertEqual(self.arg1, "test")
    self.assertEqual(self.keys["key"], "test")

  def test_keyTestSchedule(self):
    self.arg1 = None
    self.keys = {}
    sch = threadly.Scheduler(10)
    sch.schedule(self.arguments, recurring=True, delay=10, args=("test", ), kwargs={"key":"test"}, key="TEST")
    time.sleep(.1)
    self.assertEqual(self.arg1, "test")
    self.assertEqual(self.keys["key"], "test")


if __name__ == '__main__':
  unittest.main()

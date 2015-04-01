
import unittest

__author__ = 'jpercent'


class RuntimeTest(unittest.TestCase):

    def runTest(self):
        self.test_common_configure()
        self.another_test()

    def test_common_configure(self):
        #self.assertTrue(False)
        pass

    def another_test(self):
        self.assertTrue(True)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(RuntimeTest())
    unittest.TextTestRunner().run(suite)
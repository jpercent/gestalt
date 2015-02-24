
import gestalt.configuration
import json
import os
import shutil
import sys
import unittest

__author__ = 'jpercent'


class ConfigurationTest(unittest.TestCase):
    def setUp(self):
        try:
            os.mkdir('tmp')
        except:
            pass

        os.chdir('tmp')

    def tearDown(self):
        os.chdir('..')
        shutil.rmtree('tmp', ignore_errors=True)

    def create_json_file(self, file_name):
        self.assertFalse(os.path.isfile(file_name))
        json_test = {"1": "one", "two": 2}
        with open(file_name, "w+") as test_file:
            json.dump(json_test, test_file)

        common_str = ''
        with open('..{0}common.json'.format(os.path.sep), "r+") as common:
            json.load(common, common_str)

        self.assertTrue(os.path.isfile(file_name))
        json_test.update(common_str)
        return json_test

    def test_dash_dash_conf(self):
        print("ConfigurationTest.test_dash_dash_conf")
        json_test = self.create_json_file('file.json')
        conf = gykaa.configuration.Configuration()
        parsed_conf = conf.parse()
        self.assertDictEqual(json_test, parsed_conf, "")

    def test_dash_c(self):
        print("ConfigurationTest.test_dash_c")
        json_test = self.create_json_file('file.json')
        conf = gykaa.configuration.Configuration()
        parsed_conf = conf.parse()
        self.assertDictEqual(json_test, parsed_conf, "")


    def test_default_conf(self):
        print("ConfigurationTest.test_default")
        conf = gykaa.configuration.Configuration()
        parsed_conf = conf.parse()
        self.assertEquals(parsed_conf['test'], True)

    def runTest(self):
        if '--conf' and 'file.json' in sys.argv:
            self.test_dash_dash_conf()
        elif '-c' and 'file.json' in sys.argv:
            self.test_dash_c()
        else:
            self.test_default_conf()

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(ConfigurationTest())
    unittest.TextTestRunner().run(suite)

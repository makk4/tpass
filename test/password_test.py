import os
import shutil
import unittest
try:
    import simplejson as json
except:
    import json
from src import password

TEST_PATH = os.path.join(os.path.expanduser('~'), 'tpassword-store-test')
PWD = None
file_name = None

class Tests_main(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global PWD; global file_name
        if not os.path.exists(TEST_PATH):
            os.mkdir(TEST_PATH)
        temp = password.PasswordStore.fromInit()
        PWD = temp[0]; file_name = temp[1]
        PWD.write_pwd_file(TEST_PATH)

    def test_init(self):
        pwd = password.PasswordStore(PWD.db_json['entries'], PWD.db_json['tags'])
        assert pwd.entries == {}
        assert pwd.tags == {'0': {'title': 'All', 'icon': 'home'},}
        assert pwd.db_json == {'version': '0.0.1', 'extVersion': '0.6.0', 'config': {'orderType': 'date'}, 'tags': pwd.tags, 'entries': pwd.entries}
    
    def test_init_fromInit(self):
        pwd_file = os.path.join(TEST_PATH)
        pwd = password.PasswordStore.fromInit()
        pwd = pwd[0]
        assert pwd.entries == {}
        assert pwd.tags == {'0': {'title': 'All', 'icon': 'home'},}
        assert pwd.db_json == {'version': '0.0.1', 'extVersion': '0.6.0', 'config': {'orderType': 'date'}, 'tags': pwd.tags, 'entries': pwd.entries}

    def test_init_fromPwdFile(self):
        pwd = password.PasswordStore.fromPwdFile(TEST_PATH)
        assert pwd.entries == {}
        assert pwd.tags == {'0': {'title': 'All', 'icon': 'home'},}
        assert pwd.db_json == {'version': '0.0.1', 'extVersion': '0.6.0', 'config': {'orderType': 'date'}, 'tags': pwd.tags, 'entries': pwd.entries}

    def test_write_pwd_file(self):
        path = os.path.join(TEST_PATH, 'write-test')
        assert os.path.isfile(path) == False
        PWD.write_pwd_file(path)
        assert os.path.isfile(path) == True
        if os.path.exists(path):
            shutil.rmtree(path)

if __name__ == '__main__':
    unittest.main()
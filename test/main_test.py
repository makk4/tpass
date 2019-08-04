#!/usr/bin/env python3
from src import main
from src import trezor as trezorapi
from trezorlib.client import get_default_client
import os
import json

import unittest
import click
from click.testing import CliRunner
import tempfile
import shutil

INIT_PASS = {"version": "0.0.1", "extVersion": "0.6.0", "config": {"orderType": "date"}, "tags": {"0": {"title": "All", "icon": "home"}, "1": {"title": "Social", "icon": "person-stalker"}, "2": {"title": "Bitcoin", "icon": "social-bitcoin"}}, "entries": {}}
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.tpass')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
DROPBOX_PATH = os.path.join(os.path.expanduser('~'), 'Dropbox', 'Apps', 'TREZOR Password Manager')
entries = {}
t_all = {"title": "All", "icon": "home"}
tags = {"0": t_all, }
db_json = {"version": "0.0.1", "extVersion": "0.6.0", "config": {"orderType": "date"}, "tags": tags, "entries": entries}
config = { 'file_name': '', 'store_path': DROPBOX_PATH, 'cloud_provider': 'dropbox', 'pinentry': 'false'}
newEntry_plain = {"title": "", "username": "", "password": "", "note": "", "tags": [], "safe_note": "", "note": "", "success": 'true', "export": 'true'}
newEntry_plain_failed = {"title": "", "username": "", "password": "", "note": "", "tags": [], "safe_note": "", "note": "", "success": 'false', "export": 'true'}
newEntry = {"title": "", "username": "", 'password': {'type': 'Buffer', 'data': []}, "nonce": "", "tags": [], "safe_note": {'type': 'Buffer', 'data': []}, "note": "", "success": 'true', "export": 'false'}
newEntry_failed = {"title": "", "username": "", 'password': {'type': 'Buffer', 'data': []}, "nonce": "", "tags": [], "safe_note": {'type': 'Buffer', 'data': []}, "note": "", "success": 'false', "export": 'false'}

class Tests_main(unittest.TestCase):

    def test_core(self):
        """
        Testing Core Helper Methods
        """

        # loadConfig
        if os.path.isfile(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        result = main.loadConfig()
        assert result == 0
        # writeConfig
        main.writeConfig()
        assert os.path.isfile(CONFIG_FILE) is True
        with open(CONFIG_FILE) as f:
            c = json.load(f)
            #assert c == config
        # unlockStorage
        # saveStorage

        result = main.unlockStorage()
        # getEntry 
        result = main.getEntry('coinbase.com')
        assert result[0] is '0
        assert result[1] is e_coinbase
        # getTag
        result = main.getTag(tags, 'all')
        assert result[1] == t_all
        result = main.getTag(tags, 'all/')
        assert result[1] == t_all
        result = main.getTag(tags, 'All')
        assert result[1] == t_all
        result = main.getTag(tags, 'AlL')
        assert result[1] == t_all
        result = main.getTag(tags, 'AlL/')
        assert result[1] == t_all
        result = main.getTag(tags, 'AlL1')
        assert result[1] == None
        result = main.getTag(tags, 'Social')
        assert result[1] == None
        # printEntries
        # printTags
        # tagsToString
        result = main.tagsToString(tags, False)
        assert '🏠  All' in result
        # unlockEntry
        result = main.saveEntry(newEntry_plain_failed)
        assert result == -1
        # lockEntry
        # editEntry
        # saveEntry
        # result = main.saveEntry(newEntry)
        # assert result == 0
        # result = main.saveEntry(newEntry_failed)
        # assert result == -1
        # result = main.saveEntry(newEntry_plain)
        # assert result == -1
        # result = main.saveEntry(newEntry_plain_failed)
        # assert result == -1

    """
    Testing CLI Methods
    """

    def test_init(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            path = '~/test_dropbox'
            if os.path.exists(path):
                shutil.rmtree(path)
            result = runner.invoke(main.conf, 'reset')
            result = runner.invoke(main.init, '-p ~/test_dropbox')
            assert result.exit_code == 0
            assert 'Please confirm action on your Trezor device' in result.output
            assert 'password store initialized in ' + path in result.output
            result = runner.invoke(main.init, '-p ~/test_dropbox')
            # Test for detecting existing TMP File
            assert 'Please confirm action on your Trezor device' not in result.output
            assert "is not empty, not initialized" in result.output

            path = '~/test_git'
            if os.path.exists(path):
                shutil.rmtree(path)
            result = runner.invoke(main.conf, 'reset')
            result = runner.invoke(main.init, '-p ~/test_git -c git')
            assert 'password store initialized with git in ' + path in result.output

            path = '~/test_googledrive'
            if os.path.exists(path):
                shutil.rmtree(path)
            result = runner.invoke(main.conf, 'reset')
            result = runner.invoke(main.init, '-p ~/test_googledrive')
            assert 'password store initialized in ' + path in result.output
            if os.path.exists(path):
                shutil.rmtree(path)

    def test_find(self):
        runner = CliRunner()
        result = runner.invoke(
            main.find, 'coin')
        assert 'coinbase.com' in result
        assert ' ₿  Bitcoin' in result
    
    def test_ls(self):
        runner = CliRunner()
        result = runner.invoke(
            main.ls, '')
        assert '🏠  All' in result
        result = runner.invoke(
            main.ls, 'all/')
        assert result.output in '🏠  All'

    def test_cat(self):
        return

    def test_cp(self):
        return

    def test_insert(self):
        return

    def test_remove(self):
        return

    def test_edit(self):
        return

    def test_generate(self):
        return

    def test_importdb(self):
        return
    
    def test_exportdb(self):
        return

    def test_lock(self):
        return

    def test_git(self):
        return

    def test_conf(self):
        return


if __name__ == '__main__':
    unittest.main()
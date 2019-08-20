#!/usr/bin/env python3
from click.testing import CliRunner
from trezorlib.client import get_default_client
import click
import json
import os
import tempfile
import shutil
import subprocess
import unittest
from src import main
from src import trezor as trezorapi

DEFAULT_PATH = os.path.join(os.path.expanduser('~'), '.tpassword-store')
DROPBOX_PATH = os.path.join(os.path.expanduser('~'), 'Dropbox', 'Apps', 'TREZOR Password Manager')
GOOGLE_DRIVE_PATH = os.path.join(os.path.expanduser('~'), 'Google Drive', 'Apps', 'TREZOR Password Manager')
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.tpass')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
DICEWARE_FILE = os.path.join(CONFIG_PATH, 'wordlist.txt')

class Tests_main(unittest.TestCase):
    """
    Testing CLI Methods
    """
    def setUp(self):
        if os.path.exists(DEFAULT_PATH):
            shutil.rmtree(DEFAULT_PATH)
        runner = CliRunner()
        result = runner.invoke(main.init)


    def tearDown(self):
        if os.path.exists(DEFAULT_PATH):
            shutil.rmtree(DEFAULT_PATH)
    

    def test_init(self):
        """
        Testing init
        """
        runner = CliRunner()

        with runner.isolated_filesystem():
            """
            tpass init
            """
            if os.path.exists(DEFAULT_PATH):
                shutil.rmtree(DEFAULT_PATH)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init)
            # Test for fresh init
            assert result.exit_code == 0
            assert 'Please confirm action on your Trezor device' in result.output
            assert 'password store initialized in ' + DEFAULT_PATH in result.output
            # Test for detecting existing pwd File
            result = runner.invoke(main.init)
            assert result.exit_code != 0
            assert 'Please confirm action on your Trezor device' not in result.output
            assert "is not empty, not initialized" in result.output
            # Test for detecting existing pwd File with reset
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init)
            assert result.exit_code != 0
            assert 'Please confirm action on your Trezor device' not in result.output
            assert "is not empty, not initialized" in result.output
            shutil.rmtree(DEFAULT_PATH)
            """
            tpass init --cloud dropbox
            """
            if os.path.exists(DROPBOX_PATH):
                shutil.rmtree(DROPBOX_PATH)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init, '--cloud dropbox')
            # Test for fresh init
            assert result.exit_code == 0
            assert 'password store initialized in ' + DROPBOX_PATH in result.output
            shutil.rmtree(DROPBOX_PATH)
            """
            tpass init --cloud git
            """
            if os.path.exists(DEFAULT_PATH):
                shutil.rmtree(DEFAULT_PATH)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init, '--cloud git')
            assert result.exit_code == 0
            assert 'password store initialized in ' + DEFAULT_PATH in result.output
            #assert '... Initialized empty Git repository in' in result.output
            #result = subprocess.call('git status', DEFAULT_PATH, shell=True)
            #assert 'fatal: not a git repository (or any of the parent directories): .git' not in result.output
            shutil.rmtree(DEFAULT_PATH)
            """
            tpass init --cloud googledrive
            """
            if os.path.exists(GOOGLE_DRIVE_PATH):
                shutil.rmtree(GOOGLE_DRIVE_PATH)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init, '--cloud googledrive')
            assert result.exit_code == 0
            assert 'password store initialized in ' + GOOGLE_DRIVE_PATH in result.output
            shutil.rmtree(GOOGLE_DRIVE_PATH)
            """
            tpass init --no-disk
            """
            if os.path.exists(DEFAULT_PATH):
                shutil.rmtree(DEFAULT_PATH)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init, '--nod-disk')
            #assert result.exit_code == 0 TODO
            #assert 'password store initialized in ' + DEFAULT_PATH in result.output
            if os.path.exists(DEFAULT_PATH):
                shutil.rmtree(DEFAULT_PATH)
            """
            tpass init --path <custom>
            """
            path = '~/.test_tpassword-store'
            if os.path.exists(path):
                shutil.rmtree(path)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init, '--path "~/.test_tpassword-store"')
            assert result.exit_code == 0
            assert 'password store initialized in ' + path in result.output
            shutil.rmtree(path)

    def test_insert(self):
        """
        tpass insert
        """
        runner = CliRunner()
        edit_entry = {'item/url*':'google.com', 'title':'google.com', 'username':'test@gmail.com', 'password':'1234', 'secret':'', 'tags': {"inUse:":[], "chooseFrom:": 'nothing'}}
        result = runner.invoke(main.insert, input=json.dumps(edit_entry))
        assert 'Error' in result.output
        assert result.exit_code == 0
        return
        """
        tpass insert -t
        """
        """
        tpass insert
        """
        assert result.exit_code == 0
        result = runner.invoke(
            main.insert, '', input=edit_entry)
        assert not result.exception
        assert result.output == 'Foo: wau wau\nfoo=wau wau\n'
        assert '🏠  All' in result.output

    # def test_remove(self):
    #     return

    # def test_edit(self):
    #     return

    # def test_find(self):
    #     """
    #     Testing find
    #     """
    #     return
    #     runner = CliRunner()
    #     if os.path.exists(DEFAULT_PATH):
    #         shutil.rmtree(DEFAULT_PATH)
    #     result = runner.invoke(main.config, '--reset')
    #     result = runner.invoke(main.init)
    #     return
    #     runner = CliRunner()
    #     result = runner.invoke(
    #         main.find, 'coin')
    #     assert 'coinbase.com' in result.output
    #     assert ' ₿  Bitcoin' in result.output
    #     shutil.rmtree(DEFAULT_PATH)
    
    # def test_ls(self):
    #     return
    #     runner = CliRunner()
    #     result = runner.invoke(
    #         main.ls, '')
    #     assert '🏠  All' in result.output
    #     result = runner.invoke(
    #         main.ls, 'all/')
    #     assert '🏠  All' in result.output

    # def test_cat(self):
    #     return

    # def test_cp(self):
    #     return

    # def test_generate(self):
    #     return

    # def test_importdb(self):
    #     return
    
    # def test_exportdb(self):
    #     return

    # def test_lock(self):
    #     return

    # def test_git(self):
    #     return

    # def test_conf(self):
    #     return


if __name__ == '__main__':
    unittest.main()
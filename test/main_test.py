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

DROPBOX_PATH = os.path.join(os.path.expanduser('~'), 'Dropbox', 'Apps', 'TREZOR Password Manager')
GOOGLE_DRIVE_PATH = os.path.join(os.path.expanduser('~'), 'Google Drive', 'Apps', 'TREZOR Password Manager')
DEFAULT_PATH = os.path.join(os.path.expanduser('~'), '.tpassword-store')
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.tpass')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
DICEWARE_FILE = os.path.join(CONFIG_PATH, 'wordlist.txt')

class Tests_main(unittest.TestCase):
    """
    Testing CLI Methods
    """

    def test_init(self):
        """
        Testing init
        """
        runner = CliRunner()

        with runner.isolated_filesystem():
            """
            tpass init
            """
            path = DEFAULT_PATH
            if os.path.exists(DEFAULT_PATH):
                shutil.rmtree(DEFAULT_PATH)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init)
            assert result.exit_code == 0
            assert 'Please confirm action on your Trezor device' in result.output
            assert 'password store initialized in ' + DEFAULT_PATH in result.output
            result = runner.invoke(main.init, '-p ~/test_dropbox')
            # Test for detecting existing TMP File
            assert 'Please confirm action on your Trezor device' not in result.output
            assert "is not empty, not initialized" in result.output
            shutil.rmtree(DEFAULT_PATH)
            """
            tpass init --cloud dropbox
            """
            if os.path.exists(DROPBOX_PATH):
                shutil.rmtree(DROPBOX_PATH)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init, '-p ~/test_dropbox')
            assert result.exit_code == 0
            assert 'Please confirm action on your Trezor device' in result.output
            assert 'password store initialized in ' + DROPBOX_PATH in result.output
            result = runner.invoke(main.init, '-p ~/test_dropbox')
            # Test for detecting existing TMP File
            assert 'Please confirm action on your Trezor device' not in result.output
            assert "is not empty, not initialized" in result.output
            shutil.rmtree(DROPBOX_PATH)
            """
            tpass init --cloud git
            """
            if os.path.exists(DEFAULT_PATH):
                shutil.rmtree(DEFAULT_PATH)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init, '-p ~/test_git -c git')
            assert 'password store initialized in ' + path in result.output
            assert 'fatal: not a git repository (or any of the parent directories): .git' not in result.output
            shutil.rmtree(DEFAULT_PATH)
            """
            tpass init --cloud googledrive
            """
            if os.path.exists(GOOGLE_DRIVE_PATH):
                shutil.rmtree(GOOGLE_DRIVE_PATH)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init, '--cloud googledrive')
            assert 'password store initialized in ' + GOOGLE_DRIVE_PATH in result.output
            shutil.rmtree(GOOGLE_DRIVE_PATH)
            """
            tpass init --no-disk
            """
            if os.path.exists(DEFAULT_PATH):
                shutil.rmtree(DEFAULT_PATH)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init, '--nod-disk')
            assert result.exit_code == 0
            assert 'Please confirm action on your Trezor device' in result.output
            assert 'password store initialized in ' + DEFAULT_PATH in result.output
            result = runner.invoke(main.init, '-p ~/test_dropbox')
            # Test not finding any tmp file
            assert 'Please confirm action on your Trezor device' not in result.output
            assert "is not empty, not initialized" in result.output
            shutil.rmtree(DEFAULT_PATH)
            """
            tpass init --path <custom>
            """
            path = '~/.test_tpassword-store'
            if os.path.exists(path):
                shutil.rmtree(path)
            result = runner.invoke(main.config, '--reset')
            result = runner.invoke(main.init, '--path "~/.tpassword-store"')
            assert result.exit_code == 0
            assert 'Please confirm action on your Trezor device' in result.output
            assert 'password store initialized in ' + path in result.output
            result = runner.invoke(main.init, '-p ~/test_dropbox')
            # Test for detecting existing TMP File
            assert 'Please confirm action on your Trezor device' not in result.output
            assert "is not empty, not initialized" in result.output
            shutil.rmtree(path)

    def test_find(self):
        """
        Testing find
        """
        runner = CliRunner()
        if os.path.exists(DEFAULT_PATH):
            shutil.rmtree(DEFAULT_PATH)
        result = runner.invoke(main.config, '--reset')
        result = runner.invoke(main.init)
        return
        runner = CliRunner()
        result = runner.invoke(
            main.find, 'coin')
        assert 'coinbase.com' in result.output
        assert ' ₿  Bitcoin' in result.output
        shutil.rmtree(DEFAULT_PATH)
    
    def test_ls(self):
        return
        runner = CliRunner()
        result = runner.invoke(
            main.ls, '')
        assert '🏠  All' in result.output
        result = runner.invoke(
            main.ls, 'all/')
        assert '🏠  All' in result.output

    def test_cat(self):
        return

    def test_cp(self):
        return

    def test_insert(self):
        return
        runner = CliRunner()
        if os.path.exists(path):
            shutil.rmtree(path)
        result = runner.invoke(main.conf, '-r')
        result = runner.invoke(main.init, '-p ~/test_dropbox')
        assert result.exit_code == 0
        result = runner.invoke(
            main.insert, '', input=edit_json)
        assert not result.exception
        assert result.output == 'Foo: wau wau\nfoo=wau wau\n'
        assert '🏠  All' in result.output
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
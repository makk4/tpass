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

if __name__ == '__main__':
    unittest.main()
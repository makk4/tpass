#!/usr/bin/env python3
from src import crypto as cryptomodul
from src import trezor as trezorapi
import unittest
import os
import json

CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.tpass')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
WORDLIST = os.path.join(CONFIG_PATH, 'wordlist.json')
client = None

class Tests_main(unittest.TestCase):

    def test_decryptEntryValue(self):
        client = trezorapi.getTrezorClient()
        plain_nonce = trezorapi.getDecryptedNonce(client, e_coinbase)
        pwd = cryptomodul.decryptEntryValue(plain_nonce, e_coinbase['password']['data'])
        assert pwd == '1234'
        safeNote = cryptomodul.decryptEntryValue(plain_nonce, e_coinbase['safe_note']['data'])
        assert safeNote == 'sadsadsad'

    def test_encryptEntryValue(self):
        client = trezorapi.getTrezorClient()
        e_coinbase['nonce'] = trezorapi.getEncryptedNonce(client, e_coinbase)
        plain_nonce = trezorapi.getDecryptedNonce(client, e_coinbase)
        pwd = cryptomodul.encryptEntryValue('1234', plain_nonce)
        assert pwd == e_coinbase['password']['data']
        safeNote = cryptomodul.encryptEntryValue('sadsadsad', plain_nonce)
        assert safeNote == e_coinbase['password']['safe_note']

    def test_decryptStorage(self):
        return

    def test_encryptStorage(self):
        return

    def test_generatePassword(self):
        pwd = cryptomodul.generatePassword(10)
        assert len(pwd) is 10

    def test_generatePassphrase(self):
        sep = ' '
        length = 10
        with open(WORDLIST) as f:  
            wordlist = json.load(f)      
        pwd = cryptomodul.generatePassphrase(length, wordlist['words'], ' ')
        pwd = pwd.split(sep)
        assert len(pwd) is length



if __name__ == '__main__':
    unittest.main()
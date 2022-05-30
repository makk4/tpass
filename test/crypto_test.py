#!/usr/bin/env python3
import pytest
import os
import json
from src import crypto
from src import trezor

client = trezor.TrezorDevice()
e_coinbase = {}

def test_decryptEntryValue():
    e_coinbase = {}
    plain_nonce = client.getDecryptedNonce(e_coinbase)
    pwd = crypto.decryptEntryValue(plain_nonce, e_coinbase['password']['data'])
    assert pwd == '1234'
    safeNote = crypto.decryptEntryValue(plain_nonce, e_coinbase['safe_note']['data'])
    assert safeNote == 'sadsadsad'

def test_encryptEntryValue():
    e_coinbase['nonce'] = client.getEncryptedNonce(e_coinbase)
    plain_nonce = client.getDecryptedNonce(e_coinbase)
    pwd = crypto.encryptEntryValue('1234', plain_nonce)
    assert pwd == e_coinbase['password']['data']
    safeNote = crypto.encryptEntryValue('sadsadsad', plain_nonce)
    assert safeNote == e_coinbase['password']['safe_note']

def test_decryptStorage():
    return

def test_encryptStorage():
    return

def test_generatePassword():
    return

def test_generatePassphrase():
    return

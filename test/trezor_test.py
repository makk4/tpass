#!/usr/bin/env python3
import pytest
from src import trezor

client = trezor.TrezorDevice()

def test_get_entropy():
    assert len(client.getEntropy(12)) == 12

def test_get_trezor_keys():
    keys = client.getTrezorKeys()
    assert len(keys[0]) > 0
    assert len(keys[1]) > 0
    assert len(keys[2]) > 0

def test_getEncryptedNonce():
    return

def test_getDecryptedNonce():
    return
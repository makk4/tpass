#!/usr/bin/env python3
import hashlib
import hmac
import os
import random
import sys
from trezorlib import misc, ui
from trezorlib.client import TrezorClient
from trezorlib.tools import parse_path
from trezorlib.transport import enumerate_devices
from trezorlib.transport import get_transport
from trezorlib.misc import get_entropy
from trezorlib.misc import encrypt_keyvalue
from urllib.parse import urlparse

BIP32_PATH = parse_path("10016h/0")

def askForPassword():
    return

# @author:satoshilabs
def wait_for_devices():
    devices = enumerate_devices()
    while not len(devices):
        sys.stderr.write("Please connect Trezor to computer and press Enter...")
        input()
        devices = enumerate_devices()

    return devices

# @author:satoshilabs
def choose_device(devices):
    if not len(devices):
        raise RuntimeError("No Trezor connected!")

    if len(devices) == 1:
        try:
            return devices[0]
        except IOError:
            raise RuntimeError("Device is currently in use")

    i = 0
    sys.stderr.write("----------------------------\n")
    sys.stderr.write("Available devices:\n")
    for d in devices:
        try:
            client = TrezorClient(d, ui=ui.ClickUI())
        except IOError:
            sys.stderr.write("[-] <device is currently in use>\n")
            continue

        if client.features.label:
            sys.stderr.write("[%d] %s\n" % (i, client.features.label))
        else:
            sys.stderr.write("[%d] <no label>\n" % i)
        client.close()
        i += 1

    sys.stderr.write("----------------------------\n")
    sys.stderr.write("Please choose device to use:")

    try:
        device_id = int(input())
        return devices[device_id]
    except Exception:
        raise ValueError("Invalid choice, exiting...")

# @author:satoshilabs
def getDecryptedNonce(client, entry):
    if 'item' in entry:
        item = entry['item']
    else:
        item = entry['title']

    pr = urlparse(item)
    if pr.scheme and pr.netloc:
        item = pr.netloc

    ENC_KEY = 'Unlock %s for user %s?' % (item, entry['username'])
    ENC_VALUE = entry['nonce']
    decrypted_nonce = misc.decrypt_keyvalue(
        client,
        BIP32_PATH,
        ENC_KEY,
        bytes.fromhex(ENC_VALUE),
        False,
        True
    )
    return decrypted_nonce.hex()

def getEncryptedNonce(client, entry):
    if 'item' in entry:
        item = entry['item']
    else:
        item = entry['title']

    pr = urlparse(item)
    if pr.scheme and pr.netloc:
        item = pr.netloc

    ENC_KEY = 'Unlock %s for user %s?' % (item, entry['username'])
    ENC_VALUE = getEntropy(client, 32)
    encrypted_nonce = misc.encrypt_keyvalue(
        client,
        BIP32_PATH,
        ENC_KEY,
        bytes.fromhex(ENC_VALUE.hex()),
        False,
        True
    )

    return encrypted_nonce.hex()

# @author:satoshilabs
def getFileEncKey(masterKey):
    filekey, enckey = masterKey[:len(masterKey) // 2], masterKey[len(masterKey) // 2:]
    FILENAME_MESS = b'5f91add3fa1c3c76e90c90a3bd0999e2bd7833d06a483fe884ee60397aca277a'
    digest = hmac.new(str.encode(filekey), FILENAME_MESS, hashlib.sha256).hexdigest()
    filename = digest + '.pswd'
    return [filename, filekey, enckey]

# @author:satoshilabs
def decryptMasterKey(client):
    ENC_KEY = 'Activate TREZOR Password Manager?'
    ENC_VALUE = bytes.fromhex('2d650551248d792eabf628f451200d7f51cb63e46aadcbb1038aacb05e8c8aee2d650551248d792eabf628f451200d7f51cb63e46aadcbb1038aacb05e8c8aee')
    key = misc.encrypt_keyvalue(
        client,
        BIP32_PATH,
        ENC_KEY,
        ENC_VALUE,
        True,
        True
    )
    return key.hex()

def getEntropy(client, length):
    trezor_entropy = misc.get_entropy(client, length)
    urandom_entropy = os.urandom(length)
    entropy = hashlib.sha256(trezor_entropy + urandom_entropy).digest()
    if len(entropy) != length:
        raise ValueError(length + ' bytes entropy expected')
    return entropy

def getTrezorKeys(client):
    masterKey = decryptMasterKey(client)  
    return getFileEncKey(masterKey)

def getTrezorClient():
    devices = wait_for_devices()
    transport = choose_device(devices)
    return TrezorClient(transport=transport, ui=ui.ClickUI())
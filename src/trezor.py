#!/usr/bin/env python3
import hashlib
import hmac
import logging
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

class TrezorDevice:
    client = None

    def __getClient(self):
        if self.client is None:
            devices = self.__waitForDevices()
            transport = self.__chooseDevice(devices)
            self.client = TrezorClient(transport=transport, ui=ui.ClickUI())

    # @author:satoshilabs
    def __waitForDevices(self):
        devices = enumerate_devices()
        while not len(devices):
            sys.stderr.write("Please connect Trezor to computer and press Enter...")
            input()
            devices = enumerate_devices()
        return devices

    # @author:satoshilabs
    def __chooseDevice(self, devices):
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
    def getDecryptedNonce(self, entry):
        self.__getClient()
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
            self.client,
            BIP32_PATH,
            ENC_KEY,
            bytes.fromhex(ENC_VALUE),
            False,
            True
        )
        return decrypted_nonce.hex()

    def getEncryptedNonce(self, entry, entropy):
        self.__getClient()
        if 'item' in entry:
            item = entry['item']
        else:
            item = entry['title']
            
        pr = urlparse(item)
        if pr.scheme and pr.netloc:
            item = pr.netloc

        ENC_KEY = 'Unlock %s for user %s?' % (item, entry['username'])
        ENC_VALUE = hashlib.sha256(entropy).digest()
        encrypted_nonce = misc.encrypt_keyvalue(
            self.client,
            BIP32_PATH,
            ENC_KEY,
            bytes.fromhex(ENC_VALUE.hex()),
            False,
            True
        )

        return encrypted_nonce.hex()

    # @author:satoshilabs
    def getFileEncKey(self, masterKey):
        filekey, enckey = masterKey[:len(masterKey) // 2], masterKey[len(masterKey) // 2:]
        FILENAME_MESS = b'5f91add3fa1c3c76e90c90a3bd0999e2bd7833d06a483fe884ee60397aca277a'
        digest = hmac.new(str.encode(filekey), FILENAME_MESS, hashlib.sha256).hexdigest()
        filename = digest + '.pswd'
        return [filename, filekey, enckey]

    # @author:satoshilabs
    def decryptMasterKey(self, client):
        self.__getClient()
        ENC_KEY = 'Activate TREZOR Password Manager?'
        ENC_VALUE = bytes.fromhex('2d650551248d792eabf628f451200d7f51cb63e46aadcbb1038aacb05e8c8aee2d650551248d792eabf628f451200d7f51cb63e46aadcbb1038aacb05e8c8aee')
        key = misc.encrypt_keyvalue(
            self.client,
            BIP32_PATH,
            ENC_KEY,
            ENC_VALUE,
            True,
            True
        )
        return key.hex()

    def getEntropy(self, length):
        self.__getClient()
        trezor_entropy = misc.get_entropy(self.client, length//2)
        urandom_entropy = os.urandom(length//2)
        entropy = trezor_entropy + urandom_entropy
        if len(entropy) != length:
            raise ValueError(str(length) + ' bytes entropy expected')
        return entropy

    def getTrezorKeys(self):
        self.__getClient()
        masterKey = self.decryptMasterKey(self.client)
        return self.getFileEncKey(masterKey)

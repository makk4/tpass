# Design Rationale

## Table of contents
* [Introduction](#Introduction)
* [Privacy](#Privacy)
* [Cryptography](#Cryptography)

## Introduction

Tpass is build with simplicity in mind. All should be 100% compatible with Trezor Password Manager. It is build with unix philosophy in mind, every output could be the input for another application, which means it's scriptable. The application is cross plattform and runs on Linux,Windows and MacOS. All the crypto implementation is handled by Trezor Device. The Input and CLI methods are implemented with click. 

## Privacy

There are two mods aviable for handling metadata

## Cryptography
Trezor has provided python implementations for the decryption functions of the TPM. Tpass has implented the complement encryption function. 

### Entropy

All the random data needed for generating the `initialization vector iv` is taken from os.random() and the trezor device 50:50, with the following function:

```python
def getEntropy(client, length):
    trezor_entropy = misc.get_entropy(client, length//2)
    urandom_entropy = os.urandom(length//2)
    entropy = trezor_entropy + urandom_entropy
    if len(entropy) != length:
        raise ValueError(str(length) + ' bytes entropy expected')
    return entropy
```

Storage decryption function is taking from trezorlib/python/tools/pwd_ready.py -> decryptStorage, the shown encrytion function is implemented by tpass.

```python
def encryptStorage(db_json, store_path, encKey, iv):
    cipherkey = bytes.fromhex(encKey)
    cipher = Cipher(algorithms.AES(cipherkey), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    cipherText = encryptor.update(json.dumps(db_json).encode("UTF-8", "replace")) + encryptor.finalize()
    cipherText = iv + encryptor.tag + cipherText
    with open(store_path, 'wb') as f:
        f.write(cipherText)
```

Similar entry decryption function is taking from trezorlib/python/tools/pwd_ready.py -> decryptEntryValue, the shown encrytion function is implemented by tpass.

```python
def encryptEntryValue(nonce, val, iv):
    cipherkey = bytes.fromhex(nonce)
    cipher = Cipher(algorithms.AES(cipherkey), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    cipherText = encryptor.update(val.encode("utf-8", "replace")) + encryptor.finalize()
    cipherText = iv + encryptor.tag + cipherText
    return [x for x in cipherText]
```
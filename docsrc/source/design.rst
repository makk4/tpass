Design
============================

.. sectnum::

.. contents::


Privacy
############################

There are two mods aviable for handling metadata

- write tempfile with metadata to disk

Unlocks the password file and writes the json file into **/dev/shm/** if aviable
otherwise prints a warning and uses tmp directory of OS, which would be the case
on **Windows** and **MacOS**. From now on on every access to the password store, the
metadata is read from this file. Provides simpler read access without require
unlocking every time. At no time the entry password or secret fields are stored
plaintext in tmp file.

- decrypt password file on every access

Unlocks the password file and reads the json file with metadata into ram.
After every operation this must be done again, but no metadata is stored on
disk.

Cryptography
############################

**Satoshilabs** has provided python implementations for the decryption functions for the
**Trezor Password manager**. tpass has implented the inverse encryption function. 

Entropy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All the random data needed for generating the initialization vector **iv** is
taken from **os.random()** and the trezor device 50:50, with the following function:

.. code-block:: python

    def getEntropy(client, length):
        trezor_entropy = misc.get_entropy(client, length//2)
        urandom_entropy = os.urandom(length//2)
        entropy = trezor_entropy + urandom_entropy
        if len(entropy) != length:
            raise ValueError(str(length) + ' bytes entropy expected')
        return entropy

- 12 byte of entropy are used for encryption functions
- 32 byte for getting the nonce

.. code-block:: python

    ENC_ENTROPY_BYTES = 12
    NONCE_ENTROPY_BYTES = 32
    

Password file encryption and decryption
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Storage decryption function is taking from **trezorlib/python/tools/pwd_ready.py**
-> **decryptStorage**, the shown encrytion function is implemented by tpass.

.. code-block:: python

    def encryptStorage(db_json, store_path, encKey, iv):
        cipherkey = bytes.fromhex(encKey)
        cipher = Cipher(algorithms.AES(cipherkey), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        cipherText = encryptor.update(json.dumps(db_json).encode("UTF-8", "replace")) + encryptor.finalize()
        cipherText = iv + encryptor.tag + cipherText
        with open(store_path, 'wb') as f:
            f.write(cipherText)

Entry encryption and decryption
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similar entry decryption function is taking from **trezorlib/python/tools/pwd_ready.py** 
-> **decryptEntryValue**, the shown encrytion function is implemented by tpass.

.. code-block:: python

    def encryptEntryValue(nonce, val, iv):
        cipherkey = bytes.fromhex(nonce)
        cipher = Cipher(algorithms.AES(cipherkey), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        cipherText = encryptor.update(val.encode("utf-8", "replace")) + encryptor.finalize()
        cipherText = iv + encryptor.tag + cipherText
        return [x for x in cipherText]

The **nonce** is re-generated every time an entry gets encrypted, triggert by a
change made to the entry. The implementation to get the nonce uses the provided
trezorlibs API. The inverse function to get the decrypted nonce was also taken
from **trezorlib/python/tools/pwd_ready.py**.

.. code-block:: python

    def getEncryptedNonce(client, entry, entropy):
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
        client,
        BIP32_PATH,
        ENC_KEY,
        bytes.fromhex(ENC_VALUE.hex()),
        False,
        True
    )

    return encrypted_nonce.hex()

Syncing
############################

There are three cloud options aviable and and also offline mode.

- Dropbox
- Goolge Drive
- git
- offline

By choosing Dropbox or Google Drive the password file is created in the 
according directories to be compatible with Trezor Password Manager. The Syncing 
process is handled by Dropbox or Google.

When using git the python module **subprocess** is used to provide git access from 
everywhere by appending tpass to every git command.

Sync error handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On tpass startup a lockfile is created **~/.tpass/lockfile** and is deleted on 
normal exit or when a exception occurs. If a second instance of tpass is trying 
to read the password file, it discovers the lockfile and exits. When saving 
changes to the password file, it is also checked by timestamp, if it changed in 
the meantime and only proceeds on an unchanged pwd file. 

Key Handling
############################

Currently the keys are never stored throughout a session, which means you hav to accept multiple times for some commands, 
unlike Trezor Password Manger. Future implementations could handle the keys more user friendly.
Manual
=========================

.. sectnum::

.. contents::

Usage
#########################

.. code-block:: bash

    tpass <option> <command>

When no command is provided, which is equivalent to **tpass list**

.. code-block:: bash

    ➜ ~ tpass
    All
    Social
    ├── facebook.com :tpass@gmail.com #0
    ├── instagram.com :tpass@gmail.com #2
    ├── signal app :tpass@gmail.com #3
    └── google.com :tpass@gmail.com #6
    Bitcoin
    ├── coinbase.com :tpass@gmail.com #1
    └── wallet 1 : #10
    development
    └── https://github.com :tpass@gmail.com #4
    Favorites
    ├── google.com :tpass@gmail.com #6
    ├── microsoft.com :tpass@gmail.com #7
    ├── ITEM :USERNAME #8
    └── url.com :username #9

Help option will give overview

.. code-block:: bash

    ➜ ~ tpass --help
    Usage: tpass [OPTIONS] COMMAND [ARGS]...

    \------------------------------------

            tpass

    \------------------------------------

    CLI for Trezor Password Manager

    WARNING: Untested Beta Software! - Do not use it

    Not from Satoshilabs!

    @author: makk4 <manuel.kl900@gmail.com>

    https://github.com/makk4/tpass

    Options:
    --debug    Show debug info
    --version  Show the version and exit.
    --help     Show this message and exit.

    Commands:
    clip      Decrypt and copy line of entry to clipboard
    config    Configuration settings
    edit      Edit entry or tag
    export    Export password store
    find      List entries and tags that match names
    generate  Generate new password
    git       Call git commands on password store
    grep      Search for names in decrypted entries
    import    Import password store
    init      Initialize new password store
    insert    Insert entry or tag
    list      List entries by tag
    lock      Remove metadata from disk
    remove    Remove entry or tag
    show      Show entries
    unlock    Unlock and write metadata to disk

Commands
#########################

init
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    tpass init [--path,-p <sub-folder>] [--cloud,-c <dropbox|git|googledrive|offline>] [--no-disk]

Example:

.. code-block:: bash

    ➜ ~ tpass init
    Please confirm action on your Trezor device
    password store initialized in /home/user/.tpassword-store

find
~~~~~~~~~~~~~~~~~~~~~~~~~

**Aliase:** search

.. code-block:: bash

    tpass find <search-string>

Example:

.. code-block:: bash

    ➜ ~ tpass find coin
    coinbase.com :tpass@gmail.com #1
    Bitcoin

grep
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    tpass grep <search-string>

Example:

.. code-block:: bash

    ➜ ~ tpass grep "tpass"
    Please confirm action on your Trezor device
    facebook.com:tpass@gmail.com#0//<username>//: tpass@gmail.com
    coinbase.com:tpass@gmail.com#1//<username>//: tpass@gmail.com
    https://github.com:tpass@gmail.com#4//<username>//: tpass@gmail.com
    google.com:tpass@gmail.com#6//<username>//: tpass@gmail.com
    microsoft.com:tpass@gmail.com#7//<username>//: tpass@gmail.com

list
~~~~~~~~~~~~~~~~~~~~~~~~~

**Aliase:** ls

.. code-block:: bash

    tpass list <tag>

Example:

.. code-block:: bash

    ➜ ~ tpass ls Social
    Social
    ├── facebook.com :tpass@gmail.com #0
    ├── instagram.com :tpass@gmail.com #2
    ├── signal app :tpass@gmail.com #3
    └── google.com :tpass@gmail.com #6

show
~~~~~~~~~~~~~~~~~~~~~~~~~

**Aliase:** cat

.. code-block:: bash

    tpass show [--json,-j] [--secrets,-s] <entry>

Example:

.. code-block:: bash

    ➜ ~ tpass -s show "signal app:tpass@gmail.com"
    Please confirm action on your Trezor device
    ------------------- (3)
    item/url*: signal app
    title:     signal app
    username:  tpass@gmail.com
    password:  #DA?2j
    secret:    d
    tags:      Social

clip 
~~~~~~~~~~~~~~~~~~~~~~~~~

**Aliase:** cp, copy

.. code-block:: bash

    tpass clip [--secret,-s] [--user,-u] [--url,-i] <entry>

Example:

.. code-block:: bash

    ➜ ~ tpass clip coinbase.com
    Please confirm action on your Trezor device
    Clipboard will clear  [==================-------------]   

generate 
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    tpass generate [--insert,-i <entry>] [--clip,-c] [--type,-t <wordlist|pin|password>] [--seperator,-s <symbols>] [--force,-f] <length>

Example:

.. code-block:: bash

    ➜ ~ tpass generate --type wordlist
    cold mortuary curtly reference splatter earpiece linoleum sheath tiling retail dreamland briskly net unlikable daisy

insert 
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    tpass insert

Example:

.. code-block:: bash

    ➜ ~ tpass insert

edit
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
        "item/url*": "google.com",
        "title": "google",
        "username": "tpass@google.com",
        "password": "1234",
        "secret": "this is a test account",
        "tags": {
            "inUse": [
                "Favorites"
            ],
            "chooseFrom": [
                "Social",
                "Bitcoin",
                "development",
                "Favorites"
            ]
        }
    }

Edit tag

.. code-block:: json

    {
        "title": "bitcoin",
        "icon": {
            "inUse": "social-bitcoin",
            "chooseFrom:": [
                "home",
                "person-stalker",
                "social-bitcoin",
                "person",
                "star",
                "flag",
                "heart",
                "settings", 
                "email",
                "cloud", 
                "alert-circled",
                "android-cart",
                "image",
                "card",
                "earth",
                "wifi"
            ]
        }
    }

remove
~~~~~~~~~~~~~~~~~~~~~~~~~

git
~~~~~~~~~~~~~~~~~~~~~~~~~

config
~~~~~~~~~~~~~~~~~~~~~~~~~

**Aliase:** conf

.. code-block:: bash

    tpass config [--edit,-e] [--reset,-r] <setting-name> <setting-value>

Example:

.. code-block:: bash

    ➜ ~ tpass config -e

Will open editor with config file that looks something like this:

.. code-block:: json

    {
        "fileName": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b.pswd",
        "path": "/home/user/.tpassword-store",
        "useGit": false,
        "clipboardClearTimeSec": 15,
        "storeMetaDataOnDisk": true,
        "showIcons": true
    }

unlock
~~~~~~~~~~~~~~~~~~~~~~~~~

Writes tmpfile to disk if **storeMetadataOnDisk** is set in config

.. code-block:: bash

    tpass unlock

Example:

.. code-block:: bash

    ➜ ~ tpass unlock
    Please confirm action on your Trezor device

lock
~~~~~~~~~~~~~~~~~~~~~~~~~

Deletes tmpfile with metadata from disk

.. code-block:: bash

    tpass lock

Example:

.. code-block:: bash

    ➜ ~ tpass lock
    metadata deleted: /dev/shm/a8c2e3c46e835541d2d465a9572930b908bc2ef3e05c51387f8ecc92ac340de9.pswd.json

export
~~~~~~~~~~~~~~~~~~~~~~~~~

CSV export

Example:

.. code-block:: json

    {
        "export.csv": {
            "orderAndChooseFields": [
                "title",
                "item/url*",
                "username",
                "password",
                "secret",
                "tags"
            ]
        }
    }

import
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    tpass import <path-to-file>

Example:

.. code-block:: bash

    ➜ ~ tpass import ~/export.csv

CSV import

.. code-block:: json

    {
        "import.csv": {
            "orderAndChooseFields": [
                "title",
                "item/url*",
                "username",
                "password",
                "secret",
                "tags"
            ]
        }
    }

Files
#########################

- **pwd-file** encrypted passowrd file, default path: ~/.tpassword-store/<file-name>.pwd

- **tmp-file** stores metadata, located: /dev/shm/<file-name>.pwd.json fallback to /tmp/

- **lockfile** is generated on every startup and deleted on exit, to make sure only one instance is accessing password store, located: ~/.tpass/lockfile

- **config file** stores config values, located: ~/.tpass/config.json

- **logfile** stores log info, located: ~/.tpass/tpass.log

- **wordlist** used for generating passphrases, default icluded is **EFF large**, place custom wordlist in: ~/.tpass/wordlist.txt

Config values
#########################

- **fileName**
- **path**
- **useGit**
- **storeMetadataOnDisk**


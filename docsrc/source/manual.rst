Manual
=========================

.. sectnum::

.. contents:: The tiny table of contents

Init
~~~~~~~~~~~~~~~~~~~~~~~~~



Config
~~~~~~~~~~~~~~~~~~~~~~~~~

Config file lokks like this:

.. code-block:: json

    {
        "fileName": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b.pswd",
        "path": "/home/user/.tpassword-store",
        "useGit": false,
        "pinentry": false,
        "clipboardClearTimeSec": 15,
        "storeMetaDataOnDisk": true,
        "showIcons": true
    }


Edit
~~~~~~~~~~~~~~~~~~~~~~~~~

Edit entry
#########################

.. code-block:: json

    {
        "item/url*": "google.com",
        "title": "google",
        "username": "tpass@google.com",
        "password": "1234",
        "secret": "this is a test account",
        "tags": {
            "inUse": [],
            "chooseFrom": "All"
        }
    }


Edit tag
#########################

.. code-block:: json

    {
        "title": "bitcoin",
        "icon": {
            "inUse": "social-bitcoin",
            "chooseFrom:": "home, person-stalker, social-bitcoin, person, star, flag, heart, settings, email, cloud, alert-circled, android-cart, image, card, earth, wifi"
        }
    }

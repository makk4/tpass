Contribute
=========================

.. sectnum::

.. contents:: The tiny table of contents

Build and upload
#########################

depencies
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    sudo apt install -y direnv
    python -m pip install --user setuptools wheel virtualenv pipenv
    sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv


Clone repository
~~~~~~~~~~~~~~~~~~~~~~~~~

clone repository

.. code-block:: bash

    git clone --recursive git@github.com:makk4/tpass.git

update

.. code-block:: bash

    git pull --recurse-submodules


Unittests
~~~~~~~~~~~~~~~~~~~~~~~~~

depencies

.. code-block:: bash

    sudo apt-get install scons libsdl2-dev libsdl2-image-dev

download emulator

.. code-block:: bash

    git clone --recursive https://github.com/trezor/trezor-firmware.git
    cd trezor-firmware/core
    make vendor
    ./build-docker.sh

update

.. code-block:: bash

    git pull --recurse-submodules

Upload to PyPi
~~~~~~~~~~~~~~~~~~~~~~~~~

depencies

.. code-block:: bash

    python3 -m pip install --user twine

Upload to Pypi using **twine**

.. code-block:: bash

    python3 setup.py sdist bdist_wheel
    twine check dist/*
    twine upload --repository-url https://test.pypi.org/legacy/ dist/*

Docs
~~~~~~~~~~~~~~~~~~~~~~~~~

depencies

.. code-block:: bash

    apt-get install python-sphinx

Docs are build with **sphinx** using the rst format. Github Pages are created also a
unix man page. The sphinx folder with Makefile and source is in **docsrc/**, the
**index.html** and all files for Github pages are located in **docs/**. This
hack is necessary to have source and page in one repository.

.. code-block:: bash

    cd docsrc/
    make clean
    make html
    make github
    make man


Code guidelines
#########################
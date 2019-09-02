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

Pytests
~~~~~~~~~~~~~~~~~~~~~~~~~

depencies

.. code-block:: bash

    pip3 install --user pytest pytest-cov

run tests with coverage

.. code-block:: bash

    pytest --cov=src test

Emulator
~~~~~~~~~~~~~~~~~~~~~~~~~

download emulator

depencies

.. code-block:: bash

    sudo apt-get install scons libsdl2-dev libsdl2-image-dev

install

.. code-block:: bash

    git clone --recursive https://github.com/trezor/trezor-firmware.git
    cd trezor-firmware/core
    make vendor
    ./emu.sh

activate 

.. code-block:: bash

    trezord -e 2221

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

HTML

.. code-block:: bash

    cd docsrc/
    make clean && make html && make github
    make man

Man Page

.. code-block:: bash

    cd docsrc/
    make clean && make man && make manpage

View man page

.. code-block:: bash

    man build/man/tpass.1

To view html locally, open **/docsrc/buld/html/intex.html** with in browser

Latex PDF

Depencies:

.. code-block:: bash

    sudo apt install texlive-full tlatexmk

.. code-block:: bash

    make latexpdf

Code guidelines
#########################


Contribute
=========================

.. sectnum::

.. contents:: The tiny table of contents

depencies
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    sudo apt install -y direnv
    python -m pip install --user setuptools wheel virtualenv pipenv
    sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv


pull from git
~~~~~~~~~~~~~~~~~~~~~~~~~

clone repository

.. code-block:: bash

    git clone --recursive git@github.com:makk4/tpass.git

update

.. code-block:: bash

    git pull --recurse-submodules


unittests
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

upload to pypi
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    python3 setup.py sdist bdist_wheel
    twine check dist/*
    twine upload --repository-url https://test.pypi.org/legacy/ dist/*

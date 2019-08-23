Install
=========================

.. sectnum::

.. contents::

Sources
##############

pip (recommend)
~~~~~~~~~~~~~~~

.. code-block:: bash

    pip3 install --user -i https://test.pypi.org/simple/ tpass

from source
~~~~~~~~~~~

.. code-block:: bash

    git clone git@github:makk4/tpass.git
    python3 setup.py install --user

Autocompletion
##############

bash
~~~~

.. code-block:: bash

    _TPASS_COMPLETE=source tpass > tpass-complete.sh

and add this to your **.bashrc**

.. code-block:: bash

    . /path/to/tpass-complete.sh

zsh
~~~

.. code-block:: bash

    _TPASS_COMPLETE=source_zsh tpass > tpass-complete.sh

and add this to your **.zshrc**

.. code-block:: bash

    . /path/to/tpass-complete.sh

oh-my-zsh
~~~~~~~~~

.. code-block:: bash

    _TPASS_COMPLETE=source_zsh tpass > ~/.oh-my-zsh/plugins/tpass/tpass-complete.sh

and add this to your **.zshrc**

.. code-block:: bash

    .  ~/.oh-my-zsh/plugins/tpass/tpass-complete.sh


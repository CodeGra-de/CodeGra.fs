Installation
=============
The Filesystem can be installed using ``pip``, using the command ``pip install CodeGra.fs``.
This installs two scripts, ``cgfs`` used to mount the Filesystem and ``cgapi-consumer`` used by editor plugins.
You can also install ``cgfs`` by giving ``pip`` the ``--user`` flag, however make sure ``$HOME/.local/bin`` is in your ``$PATH`` in this case.

.. note:: Please consult our ``PyPi`` page `here <https://pypi.org/project/CodeGra.fs/>`__.

Python **3.5** or higher is required to run the CodeGrade Filesystem and thus ``pip3`` has to be used to install it. Furthermore,
the filesystem depends on the ``fusepy`` and ``requests`` modules.

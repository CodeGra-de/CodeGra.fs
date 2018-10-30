Installation
=============
The CodeGrade Filesystem is compatible with all popular operating systems:

* :fa:`linux` GNU/Linux
* :fa:`apple` MacOS
* :fa:`windows` Windows

.. note:: The support for windows is currently experimental: we would love to hear your feedback!

GNU/Linux and MacOS
---------------------
The Filesystem can be installed on GNU/Linux or MacOS using ``pip``, with the command:
``sudo pip install CodeGra.fs``.
This installs three scripts, ``cgfs`` used to mount the file-system,
``cgfs-qt`` a GUI that can be used to mount the file-system, and ``cgapi-consumer``
used by editor plugins. You can also install ``cgfs`` by giving ``pip`` the ``--user``
flag, however make sure ``$HOME/.local/bin`` is in your ``$PATH`` in this case.

.. note:: Please consult our ``PyPi`` page `here <https://pypi.org/project/CodeGra.fs/>`__.

Please note that ``pip3`` is used, this because CodeGra.fs only with works with
python **3.5** or higher. For MacOS this will probably mean you need to install
Python3, you can do this using e.g. `homebrew <https://brew.sh/>`__
(``brew install python``).

On GNU/Linux and MacOS CodeGra.fs depends on:

* `fusepy <https://github.com/terencehonles/fusepy>`__
* `requests <http://docs.python-requests.org/en/master/>`__

.. note:: Please note that the newest version of FUSE for macOS is required for macOS Mojave, this has to be installed manually from `FUSE <https://osxfuse.github.io/>`__.

Windows
---------
Installation on Windows can also be done by using ``pip`` by following the steps
for GNU/Linux and MacOS above. Another easier way is however using our supplied
installer. You can download the installer for the latest release
`here <https://github.com/CodeGra-de/CodeGra.fs/releases>`__. The installer
does not install the command line ``cgfs`` script, if you need this script for
whatever reason simply install the package using ``pip``.

When using the Windows installer you still need to install
`WinFsp <https://github.com/billziss-gh/winfsp>`__ separately. Currently only
version 1.4B3 is supported (which is in beta), you can download it
`here <https://github.com/billziss-gh/winfsp/releases/tag/v1.4B3>`__.

When installing using pip CodeGra.fs depends on:

-  `fusepy`_
-  `requests`_
-  `cffi`_
-  `WinFsp`_ (installed with dev headers).
-  `winfspy`_

.. _fusepy: https://github.com/terencehonles/fusepy
.. _requests: http://docs.python-requests.org/en/master/
.. _cffi: https://bitbucket.org/cffi/cffi
.. _WinFsp: https://github.com/billziss-gh/winfsp
.. _winfspy: https://github.com/Scille/winfspy

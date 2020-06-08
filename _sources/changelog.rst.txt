Changelog
==========

Version 1.1.2
--------------
**Released**: March 9th, 2020

**Features & Updates**

- Make it possible to have course names with slashes in them `(#52)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/52>`__: This makes it possible
  to display courses with slashes in their names.

Version 1.1.1
--------------
**Released**: October 28th, 2019

**Features & Updates**

- Make it easier to use cgfs with legacy applications `(#47)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/42>`__: This Format dates
  differently. The ISO8061 date format uses colons, but colons are disallowed on
  some Windows systems. The new "ISO dates" option makes CGFS use the old
  format. Also adds option "ASCII only". The former replaces any non-ASCII
  character in filenames with a `-`.

Version 1.0.0
--------------
**Released**: August 19th, 2019

**Features & Updates**

- Update frontend `(#42)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/42>`__: Update the frontend of
  the CodeGrade Filesystem with Electron. Make more intuitive, easier to select
  institute and add better error notifications.
- Add Windows and MacOS installers `(#42)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/42>`__: Add installers for
  Windows and MacOS to make installing the Filesystem easier and to
  automatically install all dependencies.
- Add Debian/Ubuntu install script `(#42)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/42>`__: Add a script to
  install the CodeGrade Filesystem and all dependencies on Debian / Ubuntu.

Version 0.5.0
-------------

**Released**: February 14th, 2019

**Features & Updates**

- Support Python 3.5 & 3.6 `(#35)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/35>`__: Tests are now also run
  on Python 3.5 and 3.6 to ensure compatibility with older systems.
- Handle duplicate names better `(#35)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/35>`__: When two objects (i.e.
  submissions, assignments, etc.) had the same name, only one would be
  displayed in the filesystem. It was indeterminate which one would be shown,
  so this could cause a lot of confusion. This patch appends the creation
  date/time, so two objects with the same name can be distinguished.
- Handle group names `(#35)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/35>`__ `(#38)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/38>`__: When an assignment is
  a group assignment, the filesystem now shows the group names, and adds a
  special `.cg-group-members` file in submission directories.

Version 0.4.2
-------------

**Released**: October 30th, 2019

**Features & Updates**

- GUI to control CodeGra.fs `(#29)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/29>`__: The CodeGrade
  filesystem now comes with a graphical interface where various settings can be
  managed.
- Experimental Windows 10 support `(#29)
  <https://github.com/CodeGra-de/CodeGra.fs/pull/29>`__.

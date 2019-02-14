Changelog
==========

Version 0.5.0
-------------

**Released**: Februari 14th, 2019

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

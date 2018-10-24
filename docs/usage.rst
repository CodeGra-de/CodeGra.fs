Usage the Filesystem
======================
After installation, the CodeGrade Filesystem can be used with the ``cgfs`` command. Before mounting, an empty folder (``mnt``) to mount in has
to be created, this can be done by ``mkdir mnt``.

Now CodeGrade Filesystem can mount to this created folder (e.g. ``mnt``) with ``cgfs -p PASSWORD -u CODEGRADE_URL USERNAME mnt/``. In which
``PASSWORD`` and ``USERNAME`` should be replaced with valid CodeGrade account details for the CodeGrade instance found at the ``CODEGRADE_URL``.

.. note:: The CodeGrade URL given at the ``-u`` flag should direct to the API and should thus end with ``api/v1/`` (i.e. ``https://codegra.de`` will become ``https://codegra.de/api/v1/``).

.. note:: The ``CGFS_PASSWORD`` and ``CGAPI_BASE_URL`` environment variables can be set to respectively pass the password or CodeGrade URL. Additionally, leaving out the ``-p`` flag will force ``cgfs`` to prompt for your password.

After mounting the filesystem, navigate to the specified mount folder to find an overview of all visible courses to the logged in user. Navigate
to a course folder to find an overview of all assignment folders that hold all submissions. This results in the default format of
``/course/assignment/submission - submission_time``. All files and folders in the filesystem can be opened
as if they were real local files on your system. Editing these files as a teacher results in a new teacher revision, visible to the student.
Editing these files as a student enables automatic synchronisation to CodeGrade with each save.

.. warning:: Adding or modifying files as teacher when not mounted with ``--fixed`` flag makes changes public to the student if the student has the *View teacher revision* permission.

.. note:: For more information about the Filesystem and different flags, consult the help menu using the ``cgfs --help`` command.

Special Files
----------------
The filesystem contains a few special files, these are files that are not submitted by students but can be used to control CodeGrade instead.

.. note:: Special files are only editable with the right permissions.

These files are validated on a close, which fails if the file format is not correct. In the case the exact format of a special file is not followed and it cannot be easily recovered,
the ``__RESET__`` string can be written to any writable special file to reset it to its server state.

+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+
| Name                            | Editable | Location   | Use                                                    | Format                                                       |
+=================================+==========+============+========================================================+==============================================================+
| ``.api.socket``                 | ✗        | Root       | Location of the api socket                             | Single line with file location                               |
+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+
| ``.cg-mode``                    | ✗        | Root       | Mode file system                                       | ``FIXED`` or ``NOT_FIXED``                                   |
+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+
| ``.cg-assignment-id``           | ✗        | Assignment | Id of this assignment                                  | Single line with id                                          |
+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+
| ``.cg-assignment-settings.ini`` | ✓        | Assignment | Settings for this assignment                           | Ini file with settings                                       |
+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+
| ``.cg-edit-rubric.md``          | ✓        | Assignment | Rubric for this assignment, editing changes the rubric | See ``.cd-edit-rubric.help``                                 |
+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+
| ``.cg-edit-rubric.help``        | ✗        | Assignment | Help file for the rubric file                          | Plain text file                                              |
+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+
| ``.cg-feedback``                | ✓        | Submission | The general feedback for this submission               | Plain text file                                              |
+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+
| ``.cg-grade``                   | ✓        | Submission | The grade for this submission                          | Single float or empty to delete or reset the grade           |
+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+
| ``.cg-rubric.md``               | ✓        | Submission | The rubric for this submission                         | Markdown file where a ticked box means the item is selected. |
+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+
| ``.cg-submission-id``           | ✗        | Submission | Id of this submission                                  | Single line with id                                          |
+---------------------------------+----------+------------+--------------------------------------------------------+--------------------------------------------------------------+

.. warning:: Only the markdown checkboxes in the ``.cg-rubric.md`` file should be changed to fill in the rubric.

Automatic Grading
------------------
The filesystem is especially useful for assignments with automatic grading scripts.
Automatically generated grades and feedback can be written to respectively the ``.cg-grade`` and ``.cg-feedback`` file to submit automatically.

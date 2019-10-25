Using the Filesystem
======================

The CodeGrade Filesystem is a unique way to mount your CodeGrade instance
locally on your system. This provides the teacher much flexibility by allowing
to test, review and grade work from students locally, in your favourite editor
and using all required tools. After installing the CodeGrade Filesystem, open
the installed application to mount your CodeGrade instance.

To use the CodeGrade Filesystem, you have to sign in with your **CodeGrade**
account to your CodeGrade instance. If CodeGrade is integrated into your LMS at
your institution, you first have to set up a password by following `this guide <https://docs.codegra.de/guides/setup-password-for-codegrade-account.html>`_.

After selecting your institution from the dropdown list in the Filesystem, sign
in with your CodeGrade username and password.

.. note:: Select *Other* to sign in to a custom CodeGrade instance.

Some advanced options are available to further customise your CodeGrade mount:

- **Location:** The mount location defaults to the *Desktop*, but can be set anywhere else. A ``CodeGrade`` mount-folder will automatically be created in the selected directory.
- **Revision mode:** (Previously fixed mode) Turn on to sync all edits, deletions and additions of files in submissions, these will then be visible to the students as *Teacher Revisions*. Disabling will still allow adding files, however these files will not be synced with CodeGrade or shown to the student.
- **Assigned to me:** Only show submissions that are assigned to you. Only has effect if submissions are actually assigned and you are one of the assignees.
- **Latest submissions only:** Only show the most recent submission of each students. On by default, turn off to see all attempts by the student.
- **Notifications:** Verbosity of the notifications. Defaults to *All*, choose *Critical only* to only see critical notifications and use *Debug* to also log all notifications.

Finally press *Start* to mount the CodeGrade Filesystem. Press the path at the
top or manually navigate to the mount point to find the CodeGrade mount. All
mounts follow the structure of ``Course/Assignment/Student_Submission/``. All
folders with *student submissions* follow the naming format
``Full Student Name - DATE TIME``, with hand in time and date. Folders contain,
next to the handed in files by the student, special files to control the
Filesystem. Read more about these special files, and their usage, below.

To unmount the CodeGrade Filesystem, simply press *Stop* or close the
application.

.. note:: CodeGrade Filesystem usage logs can be manually exported to ``JSON`` by pressing *Export log*. It is useful to save the log if unexpected errors occurred, so we can better help you out and fix any problems that may occur while using the CodeGrade Filesystem.

Command Line Tools **(deprecated)**
-------------------------------------
Installing the filesystem automatically installs the ``cgfs`` command, which is
also used in the back-end of the GUI. Use ``cgfs --help`` for an overview of the
options of the ``cgfs`` command line tool.

.. warning:: The CodeGrade Filesystem Command Line Tools are deprecated, using the CodeGrade Filesystem GUI is highly recommended.

Create an empty folder to mount in before using the CodeGrade Filesystem, this
can be done with the ``mkdir mnt`` command. After creating this ``mnt`` folder,
use the CodeGrade Filesystem Command Line Tools to mount:
``cgfs -p PASSWORD -u CODEGRADE_URL USERNAME mnt/``. In which ``PASSWORD`` and
``USERNAME`` should be replaced with valid CodeGrade account details for the
CodeGrade instance found at the ``CODEGRADE_URL``.

.. note:: The CodeGrade URL given at the ``-u`` flag should direct to the API and should thus end with ``api/v1/`` (i.e. ``https://codegra.de`` will become ``https://codegra.de/api/v1/``).

.. note:: The ``CGFS_PASSWORD`` and ``CGAPI_BASE_URL`` environment variables can be set to respectively pass the password or CodeGrade URL. Additionally, leaving out the ``-p`` flag will force ``cgfs`` to prompt for your password.

.. warning:: Adding or modifying files as teacher when not mounted with ``--fixed`` flag makes changes public to the student if the student has the *View teacher revision* permission.

Special Files
----------------
The CodeGrade Filesystem also creates a few *special files*, these are files
that are not submitted by a student but can be used to control CodeGrade. The
format of these files is validated on each save, which fails if not correct. The
following special files exist in the CodeGrade Filesystem:

.. note:: Special files are only editable with the right permissions.

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

.. note:: In the case the exact format of a special file is not followed and it cannot be easily recovered, the ``__RESET__`` string can be written to any writable special file to reset it to its server state.

Automatic Grading
------------------
The filesystem is especially useful for assignments with automatic grading
scripts. Automatically generated grades and feedback can be written to the
``.cg-grade``, ``.cg-feedback`` and ``.cg-rubric`` files to submit
automatically to CodeGrade. This allows you to easily use existing grading
scripts with little editing. Please consult the CodeGrade AutoTest documentation
for more information on (more elaborate) automatic assessment in CodeGrade.

.. warning:: If the Filesystem is mounted in *revision mode* (previously *fixed mode*), any files added to submissions will be visible to students in the *Teacher Revision*. Do not mount in this mode to prevent testing scripts to be published to your students.

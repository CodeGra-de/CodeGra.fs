Editor Plug-ins
=================

Even though the CodeGrade filesystem works together with any editor by manually editing its special files,
it is recommended to use it in combination with editor plugins.

.. note:: The CodeGrade filesystem has to be installed and both the ``cgfs`` and the ``cgapi-consumer`` helper program must be available from the user's ``$PATH`` to successfully install and use the editor plugins.

Atom Plug-in
^^^^^^^^^^^^^^^
CodeGrade offers a package for `Atom <https://atom.io/>`__, a recent but popular open-source code editor from the GitHub team. This package is also known as *CodeGra.atom*.

Installation
~~~~~~~~~~~~~

Installing the CodeGrade Atom Plugin (or CodeGra.Atom) can be done via the command line or using the Atom GUI. Installation via the command
line is done with the following command: ``apm install codegra-atom``. Installing using the Atom GUI can be done in the ``Install`` tab
in the ``Settings`` or ``Preferences`` screen. Search for ``codegra-atom`` in the search dialog and press ``Install`` to install the plugin.

Usage
~~~~~~~~

After installation, the mounted folder (e.g. ``mnt/``) can be opened in Atom to make use of the plugin with the command ``atom mnt/``.
The following commands are available in Atom when editing a file in the CodeGrade filesystem:

+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| Command                              | ``--fixed`` | Description                                                                                 |
+======================================+=============+=============================================================================================+
| codegra-atom:edit-line-comment       | ✓           | Edit the comment(s) on the line(s) with a cursor on them.                                   |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| codegra-atom:delete-line-comment     | ✓           | Delete the comment(s) on the line(s) with a cursor on them.                                 |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| codegra-atom:open-rubric-editor      | ✗           | Edit the rubric of the assignment of the current file.                                      |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| codegra-atom:open-rubric-selector    | ✗           | Open the rubric selector file to fill in the rubric for the current submission.             |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| codegra-atom:edit-geedback           | ✗           | Edit the current submission's global feedback.                                              |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| codegra-atom:edit-grade              | ✗           | Edit the current submission's grade.                                                        |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| codegra-atom:select-rubric-item      | ✗           | Select the rubric item that the cursor is on, deselecting any other item in the same group. |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| codegra-atom:goto-prev-rubric-header | ✗           | Go to the previous header in a rubric file.                                                 |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| codegra-atom:goto-next-rubric-header | ✗           | Go to the next header in a rubric file.                                                     |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| codegra-atom:goto-prev-rubric-item   | ✗           | Go to the previous item in a rubric file.                                                   |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+
| codegra-atom:goto-next-rubric-item   | ✗           | Go to the next item in a rubric file.                                                       |
+--------------------------------------+-------------+---------------------------------------------------------------------------------------------+

.. note:: The ``--fixed`` flag when mounting is required to use line comment commands.

Vim Plug-in
^^^^^^^^^^^^^^^
CodeGrade offers a plugin for `Vim <https://www.vim.org/>`__, *the editor*. This plugin is also known as *CodeGra.vim*.

Installation
~~~~~~~~~~~~~

.. todo:: Add installation instructions.

Usage
~~~~~~~~

After installation, the mounted folder (e.g. ``mnt/``) can be opened in Vim to make use of the plugin with the command ``vim mnt/``.
The following commands are available in Vim when editing a file in the CodeGrade filesystem:

+----------------------+-------------+--------------------------------------------------------------------------------------------------+
| Command              | ``--fixed`` | Description                                                                                      |
+======================+=============+==================================================================================================+
| CGEditFeedback       | ✓           | Edit the current submission's global feedback.                                                   |
+----------------------+-------------+--------------------------------------------------------------------------------------------------+
| CGEditGrade          | ✓           | Edit the current submission's grade.                                                             |
+----------------------+-------------+--------------------------------------------------------------------------------------------------+
| CGShowLineFeedback   | ✗           | Show the line-feedback for the current buffer in the quickfix list and open the quickfix window. |
+----------------------+-------------+--------------------------------------------------------------------------------------------------+
| CGEditLineFeedback   | ✓           | Edit the comment for the current line in the current buffer.                                     |
+----------------------+-------------+--------------------------------------------------------------------------------------------------+
| CGDeleteLineFeedback | ✓           | Delete the comment for the current line in the current buffer.                                   |
+----------------------+-------------+--------------------------------------------------------------------------------------------------+
| CGOpenRubricEditor   | ✗           | Edit the rubric of the assignment of the current file.                                           |
+----------------------+-------------+--------------------------------------------------------------------------------------------------+
| CGOpenRubricSelector | ✓           | Open the rubric for the current submission.                                                      |
+----------------------+-------------+--------------------------------------------------------------------------------------------------+
| CGRubricPrevSection  | ✗           | Go to the previous header in a rubric file.                                                      |
+----------------------+-------------+--------------------------------------------------------------------------------------------------+
| CGRubricNextSection  | ✗           | Go to the next header in a rubric file.                                                          |
+----------------------+-------------+--------------------------------------------------------------------------------------------------+
| CGRubricSelectItem   | ✓           | Select the rubric item on the current line.                                                      |
+----------------------+-------------+--------------------------------------------------------------------------------------------------+

.. note:: The ``--fixed`` flag when mounting is required to use specific commands.

Emacs Plug-in
^^^^^^^^^^^^^^^
CodeGrade offers a plugin for the `Emacs <https://www.gnu.org/software/emacs/>`__ editor. This plugin is also known as *CodeGra.el*.

Installation
~~~~~~~~~~~~~
Now clone `this <https://github.com/CodeGra-de/CodeGra.el>`__ repository to some local folder (``git clone git@github.com:CodeGra-de/CodeGra.el.git``) and add this folder to your ``load-path`` in emacs.
After doing this you can add ``(require 'codegrade)`` to your emacs config.

.. warning:: In addition to the general dependencies for all plugins, the Emacs plugin depends on the `switch-buffer-functions <https://github.com/10sr/switch-buffer-functions-el>`__ package, which can be installed using ``MELPA``.

Usage
~~~~~~~~
There are two main functions in this package, editing rubrics and giving line feedback.

.. warning:: It is important to note that this package does not yet check if the file-system if mounted in ``--fixed`` mode, please make sure it is when giving line feedback.

Editing rubric
+++++++++++++++
To edit a rubric you call the ``codegrade-open-rubric`` function.
This opens a rubric in a new buffer with the major mode ``codegrade-rubric-mode`` that you can edit.
To toggle a rubric item you can call ``codegrade-toggle-rubric-item`` which is bound to ``c`` and ``,`` by default
in the ``codegrade-rubric-mode``. You can goto the next item with ``codegrade-goto-next-item``
(bound to n), to the previous item with ``codegrade-goto-previous-item`` (bound to p).
To goto next or previous headers use the ``codegrade-goto-*-header`` functions (bound to N and P by default).
To quit this rubric you should use the ``codegrade-rubric-close`` function, bound to q.

.. note:: The opened buffer follows you around. So if you open another submission by another user the rubric buffer automatically updates. See the first line of this buffer to see which person you are grading.

Line feedback
+++++++++++++++
To edit line feedback you can call the ``codegrade-add-feedback`` function on a line.
This opens a new buffer in the ``codegrade-feedback-mode`` mode. You can save the contents in this buffer and
quit by calling ``codegrade-feedback-close`` (bound to C-c C-c by default). To quit without saving you can call
``codegrade-feedback-quit``, bound to C-c C-k by default.

You can also delete a line of feedback by calling ``codegrade-delete-feedback``.
To see the feedback of a line you can call ``codegrade-get-feedback``.

Giving grades
+++++++++++++++
You can also give a grade using this plugin. Simply call ``codegrade-give-grade`` and input a number between 0 and 10.

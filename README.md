# CodeGra.fs

<p align="center">
  <a href="https://travis-ci.org/CodeGra-de/CodeGra.fs">
    <img src="https://travis-ci.org/CodeGra-de/CodeGra.fs.svg?branch=master"
      alt="Build Status">
  </a>
  <a href="https://codegra.de">
    <img src="https://img.shields.io/badge/style-%E2%9D%A4%EF%B8%8F%20&%20%F0%9F%8D%BB-ff69b4.svg?label=made%20with"
      alt="Made with ❤ & ️🍻">
  </a>
  <a href="https://codegra.de">
    <img src="https://img.shields.io/badge/style-CodeGra.de-blue.svg?label=website"
      alt="CodeGra.de">
  </a>
  <a href="https://semver.org">
    <img src="https://img.shields.io/badge/semVer-v0.4.2--beta-green.svg"
      alt="Semantic Version v0.4.2-beta">
  </a>
  <a href="https://github.com/CodeGra-de/CodeGra.de/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/license-AGPL--3.0--only-blue.svg"
      alt="License AGPL-3.0-only" title="License AGPL-3.0-only">
  </a>
</p>

# CodeGrade Filesystem
The CodeGrade Filesystem is the extension of CodeGrade that allows you to
test, review and grade all CodeGrade assignments locally from within your
favourite editor. The Filesystem application mounts a local CodeGrade instance
on your computer, which makes browsing through all your CodeGrade courses,
assignments and submissions very easy.

We aim to further enhance the grading experience and decrease overhead with the
CodeGrade Filesystem.

## Installation
The CodeGrade Filesystem is an external application that can be installed on
Windows, MacOS and GNU/Linux. Follow the install instructions for your operating
system below.

### Windows and MacOS
Installing the CodeGrade Filesystem on a Windows or MacOS system can be done
using the installers. Follow the instructions in the installers to successfully
install the CodeGrade Filesystem.

The supplied installers install all required dependencies for the CodeGrade
Filesystem to work, these are:
- Python 3
- [FUSE (MacOS)](https://osxfuse.github.io/)
- [WinFsp (Windows)](https://github.com/billziss-gh/winfsp)
- [requests](http://docs.python-requests.org/en/master/)
- [fusepy](https://github.com/terencehonles/fusepy)
- [cffi](https://bitbucket.org/cffi/cffi)
- [winfspy](https://github.com/Scille/winfspy)


### GNU/Linux
<!-- TODO: Add commands for apt repos -->
Installing the CodeGrade Filesystem can be done using the package manager in
your Linux distro. In Ubuntu `apt-get install codegrade-fs`.

## Usage
Open the CodeGrade Filesystem program to mount the CodeGrade server locally.
Follow the steps below to mount:
1. Select your institution, or select _Other_ to use a custom CodeGrade instance.
2. Fill in your CodeGrade username and password.
3. _Optional:_ Select the mount location (default is desktop).
4. _Optional:_ Set Revision mode, Assigned to me and Latest Only options.
5. _Optional:_ Set verbosity of the notifications of CodeGrade Filesystem.
6. Click mount to mount the CodeGrade Filesystem.

### Command line usage __(deprecated)__
Installing the filesystem automatically installs the `cgfs` command, which is
also used in the back-end of the GUI. Use `cgfs --help` for an overview of the
options of the `cgfs` command line tool. Using the GUI is highly recommended.

### Available files
The basic layout of the file-system is `/course/assignment/submission -
submission_time`. All files that a student submitted can be found in
the submission folder. Depending on the __Assigned to me__ and __Latest Only__
options, this shows respectively only the submissions assigned to you and only
the latest submissions.

The CodeGrade Filesystem also uses a few *special files*, these are files that are not submitted by a student but can be used to control CodeGrade. These files
are validated on a save, which fails if the file format is not correct. The
following special files exist:

| Name | Editable<a href="#footnote-1-b"><sup id="footnote-1-a">1</sup></a> | Location | Use | Format |
| ---- | -------- | -------- | --- | ------ |
| `.api.socket` | ✗ | Root | Location of the api socket | Single line with file location |
| `.cg-mode` | ✗ | Root | Mode file system | `FIXED` or `NOT_FIXED` |
| `.cg-assignment-id` | ✗ | Assignment | Id of this assignment | Single line with id |
| `.cg-assignment-settings.ini` | ✓ | Assignment | Settings for this assignment | Ini file with settings |
| `.cg-edit-rubric.md` | ✓ | Assignment | Rubric for this assignment, editing changes the rubric | See `.cd-edit-rubric.help` |
| `.cg-edit-rubric.help` | ✗ | Assignment | Help file for the rubric file | Plain text file |
| `.cg-feedback` | ✓ | Submission | The general feedback for this submission | Plain text file |
| `.cg-grade` | ✓ | Submission | The grade for this submission | Single float or empty to delete or reset<a href="#footnote-2-b"><sup id="footnote-2-a">2</sup></a> the grade |
| `.cg-rubric.md` | ✓<a href="#footnote-3-b"><sup id="footnote-3-a">3</sup></a> | Submission | The rubric for this submission | Markdown file where a ticked box means the item is selected. |
| `.cg-submission-id` | ✗ | Submission | Id of this submission | Single line with id |

<a href="#footnote-1-a"><sup id="footnote-1-b">1</sup></a>: Only if
you have the correct permissions.

<a href="#footnote-2-a"><sup id="footnote-2-b">2</sup></a>: The grade is reset
if a rubric grade is available, otherwise it is deleted.

<a href="#footnote-3-a"><sup id="footnote-3-b">3</sup></a>: Only
markdown checkboxes should be changed.

It can happen that you didn't follow the exact format of the special file and
can't easily recover anymore. This isn't a really big deal, you can write the
string `__RESET__` to any writable special file to reset it to its server state.

CodeGra.fs is best used in combination with an editor plugin, such plugins exist
for [emacs](https://github.com/CodeGra-de/CodeGra.el),
[atom](https://github.com/CodeGra-de/CodeGra.atom) and
[vim](https://github.com/CodeGra-de/CodeGra.vim) and more are being created
upon request.

## License
CodeGra.fs as a whole is licensed under the [GNU Affero General Public License
v3.0 (AGPL-3.0-only)](https://www.gnu.org/licenses/agpl-3.0.html). All license
identifiers used in this product are SPDX license identifiers.

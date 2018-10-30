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

## Installation
CodeGra.fs should work on all popular operating systems: GNU/Linux, MacOS and
Windows. The support for windows is currently experimental: we would love to
hear your feedback!

### GNU/Linux and MacOS
The installation for GNU/Linux and mac is done using `pip`: `sudo pip install
CodeGra.fs`. This installs three scripts, `cgfs` used to mount the file-system,
`cgfs-qt` a GUI that can be used to mount the file-system, and `cgapi-consumer`
used by editor plugins. You can also install `cgfs` by giving `pip` the `--user`
flag, however make sure `$HOME/.local/bin` is in your `$PATH` in this case.

Please note that `pip3` is used, this because CodeGra.fs only with works with
python **3.5** or higher. For MacOS this will probably mean you need to install
Python3, you can do this using [homebrew](https://brew.sh/) (`brew install
python`) or by doing python [here](https://www.python.org/downloads/mac-osx/).

On GNU/Linux and MacOS CodeGra.fs depends on:
- [fusepy](https://github.com/terencehonles/fusepy)
- [requests](http://docs.python-requests.org/en/master/)

### Windows (**experimental**)
Installation on windows can also be done by using `pip`, however we also supply
an installer. You can download the installer for the latest release
[here](https://github.com/CodeGra-de/CodeGra.fs/releases). The installer doesn't
install the command line `cgfs` script, if you need this script for whatever
reason simply install the package using `pip`.

When using the Windows installer you still need to install
[WinFsp](https://github.com/billziss-gh/winfsp) separately. Currently only
version 1.4B3 is supported (which is in beta), you can download it
[here](https://github.com/billziss-gh/winfsp/releases/tag/v1.4B3).

When installing using pip CodeGra.fs depends on:
- [fusepy](https://github.com/terencehonles/fusepy)
- [requests](http://docs.python-requests.org/en/master/)
- [cffi](https://bitbucket.org/cffi/cffi)
- [WinFsp](https://github.com/billziss-gh/winfsp) installed with dev headers.
- [winfspy](https://github.com/Scille/winfspy)

## Usage
### Command line usage
The basic used of the `cgfs` can be viewed by executing `cgfs --help`. The idea
behind `cgfs` is that you mount a CodeGra.de instance on you local computer, in
the mounted folder you can now browse, alter and delete files submitted by
yourself and people you have to grade.

### GUI usage
If you prefer to use a GUI you can use the `cgfs-qt` command. This is a simple
GUI to use CodeGra.fs. Please note that this GUI is still in alpha state. To use
the GUI fill in all required fields, you can get help for each field by clicking
the question mark, and click mount. You will now see a output field stating
'Mounting...' and a bit later 'Mounted...'. You can now use the file system as
normal. To unmount simply click 'Stop!'.

### Available files
The basic layout of the file-system is `/course/assingment/submission -
submission_time`, so for example `/datastructures/linked-list/Thomas Schaper -
2017-11-14T13:41:26.324712`. All files that a student submitted can be found in
the submission folder.

The file-system also contains a few *special* files, these are files that are
not submitted by a student but can be used to control CodeGra.de. These files
are validated on a close, which fails if the file format is not correct. The
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
for [emacs](https://github.com/CodeGra-de/CodeGra.el) and
[atom](https://github.com/CodeGra-de/CodeGra.atom) and more are being created.

## Privacy
You can use CodeGra.fs for any CodeGrade instance. The application does a
version check at every startup, this is done by doing a request to
`https://codegra.de/.cgfs.version`. We do not collect any personal information
at this route. It is currently not possible to disable this version check. If
this request is a problem for you, it is possible to block this host/url:
CodeGra.fs will continue to function normally; creating a pull request to make
this check optional is also possible of course!

## Support
Please report any issues by creating a GitHub issue
[here](https://github.com/CodeGra-de/CodeGra.fs/issues/new), if possible please
include link to uploaded a log output when encountering the bug using the
`verbose` mode (use the `--verbose` command line flag, or click 'verbose' in the
GUI). You can upload logs to any pastebin like website, for example
[glot.io](https://glot.io/new/plaintext).

Commercial support of CodeGra.fs is available and included in a commercial
CodeGrade instance. We would love to provide more information, please send an
e-mail to info@codegra.de!

## License
CodeGra.fs as a whole is licensed under the [GNU Affero General Public License
v3.0 (AGPL-3.0-only)](https://www.gnu.org/licenses/agpl-3.0.html). All license
identifiers used in this product are SPDX license identifiers.

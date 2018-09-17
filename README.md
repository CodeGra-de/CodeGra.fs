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
    <img src="https://img.shields.io/badge/semVer-v0.3.0--alpha-green.svg"
      alt="Semantic Version v0.1.0-alpha">
  </a>
  <a href="https://www.gnu.org/licenses/agpl-3.0.html">
    <img src="https://img.shields.io/badge/license-AGPL--3.0-blue.svg"
      alt="License AGPL-3.0">
  </a>
  <a href="https://matrix.to/#/#CodeGra.de:matrix.org">
    <img src="https://img.shields.io/badge/matrix-user-43ad8d.svg"
      alt="Chat on Matrix: #CodeGra.de:matrix.org">
  </a>
  <a href="https://matrix.to/#/#DevCodeGra.de:matrix.org">
    <img src="https://img.shields.io/badge/matrix-dev-4e42aa.svg"
      alt="Chat as developer on Matrix: #DevCodeGra.de:matrix.org">
  </a>
</p>

## Installation
You can install this package using `pip`. At the moment this package is not yet
in the pip repositories, however you can install it directly from git: `sudo pip
install CodeGra.fs`. This installs two scripts, `cgfs` used to mount the
file-system and `cgapi-consumer` used by editor plugins. You can also install
`cgfs` by giving `pip` the `--user` flag, however make sure `$HOME/.local/bin`
is in your `$PATH` in this case.

Please note that `pip3` is used, this because CodeGra.fs only with works with
python **3.5** or higher. It depends on:
- [fusepy](https://github.com/terencehonles/fusepy)
- [requests](http://docs.python-requests.org/en/master/)

## Usage
The basic used of the `cgfs` can be viewed by executing `cgfs --help`. The idea
behind `cgfs` is that you mount a CodeGra.de instance on you local computer, in
the mounted folder you can now browse, alter and delete files submitted by
yourself and people you have to grade.

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

## LICENSE
This code is licensed under AGPL-v3, see the license file for the exact
license as this information may be out of date.

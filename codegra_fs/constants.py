fixed_mode_help = """Mount the original files as read only. It is still
possible to create new files, but it is not possible to alter or delete
existing files. The files shown are always the student revision files. The
created new files are only visible during a single session, they are **NOT**
uploaded to the server."""

rubric_edit_help = """Make it possible to delete rubric items or categories
using the `.cg-edit-rubric.md` files.

Note: this feature is experimental and can lead to data loss!"""

assigned_only_help = """Only show submissions that are assigned to you. This
only has effect if submissions are assigned and you are one of the
assignees."""

mountpoint_help = """Mountpoint for the file system. This should be an existing
empty directory."""

password_help = """Your CodeGra.de password, don't pass this option if you want
to pass your password over stdin. You can also use the `CGFS_PASSWORD`
environment variable to pass your password."""


url_help = """The url to find the api. This defaults to
'https://codegra.de/api/v1/'. This is most likely
'https://{UNIVERSITY}.codegra.de/api/v1/' where '{UNIVERSITY}' is your
university (for example 'uva' for the University of Amsterdam and 'ut' for the
University of Twente).  This value can also be passed as an environment
variable 'CGAPI_BASE_URL'"""

all_submissions_help = """See all submissions not just the latest submissions
of students."""

cgfs_epilog = """supported environment variables:
 CGAPI_BASE_URL         Used as the value for the `--url` flag. It can be very
                        convenient to set this environment variable in your
                        `.bashrc` file (or equivalent).
 CGFS_PASSWORD          Used as your password. Please take care when using this
                        environment variable as all processes can read
                        environment variables meaning this could easily leak
                        your password. We recommend piping your password, see
                        the last example for how to do this.

examples:
  cgfs -u https://uva.codegra.de/api/v1/ -m user ~/mount
                        Mount the file system from https://uva.codegra.de/
                        showing only your assignments in the directory
                        "$HOME/mount".  You will be prompted for a password.
  cgfs -u https://uva.codegra.de/api/v1/ -fm user ~/mount
                        Same as above but mount in fixed mode, which means you
                        cannot change or add files. This is useful for
                        automatic grading as you cannot upload grade scripts by
                        mistake. You will be prompted for a password.
  CGFS_PASSWORD=mypass cgfs -u https://uva.codegra.de/api/v1/ -mf user ~/mount
                        Same as above but mount using an environment
                        variable. You will not be prompted for a password. This
                        option can be insecure!
  pass codegrade | cgfs -u https://uva.codegra.de/api/v1/ -mf user ~/mount
                        Same as above but pipe password from your password
                        manager. This is safer than above as your password will
                        not be saved to your history file.
"""

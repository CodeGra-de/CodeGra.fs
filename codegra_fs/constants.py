fixed_mode_help = """Mount the original files as read only. It is still
possible to create new files, but it is not possible to alter or delete
existing files. The files shown are always the student revision files."""

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
university (for example 'uva' for the University of Amsterdam).  This value can
also be passed as an environment variable 'CGAPI_BASE_URL'"""

all_submissions_help = """See all submissions not just the latest submissions
of students."""

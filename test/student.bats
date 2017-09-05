load common

username=$student_user
password=$student_pass

@test "list courses as student" {
	for course in "Inleiding Programmeren" "Programmeertalen"; do
		[ -d "$mount_dir/$course" ]
	done
}

@test "list assignments as student" {
	for assig in "Go" "Haskell" "Python" "Shell"; do
		[ -d "$mount_dir/Programmeertalen/$assig" ]
	done
}

@test "list submissions as student" {
	for submission in "$mount_dir/Programmeertalen"/*/*; do
		grep "^/.*/.*/.*/.*/Stupid1" <<<"$submission"
	done
}

@test "create files as student" {
	touch "$sub_open/file1"
	[ -f "$sub_open/file1" ]

	echo abc >"$sub_open/file2"
	[ -f "$sub_open/file2" ]

	run touch "$sub_done/file3"
	[ "$status" != 0 ]
	! [ -f "$sub_done/file3" ]

	run "echo abc >'$sub_open/file4'"
	[ "$status" != 0 ]
	! [ -f "$sub_done/file4" ]
}

@test "write & read files as student" {
	run "echo abc >'$sub_done/file1'"
	[ "$status" != 0 ]
	! [ -f "$sub_done/file1" ]

	echo abc >"$sub_open/file2"
	[ -f "$sub_open/file2" ]
	[ "$(cat "$sub_open/file2")" = $'abc' ]
	echo def >"$sub_open/file2"
	[ -f "$sub_open/file2" ]
	[ "$(cat "$sub_open/file2")" = $'def' ]
	echo def >>"$sub_open/file2"
	[ -f "$sub_open/file2" ]
	[ "$(cat "$sub_open/file2")" = $'def\ndef' ]
}

@test "delete files as student" {
	echo abc >"$sub_open/file1"
	[ "$status" != 0 ]
	rm "$sub_open/file1"
}

@test "read directories as student" {
	ls_done=$(ls -1 "$sub_done")
	grep '^dir$' <<<"$ls_done"
	grep '^dir2$' <<<"$ls_done"

	ls_done=$(ls -1 "$sub_done/dir")
	grep '^single_file_work$' <<<"$ls_done"
	grep '^single_file_work_copy$' <<<"$ls_done"

	ls_done=$(ls -1 "$sub_done/dir2")
	grep '^single_file_work$' <<<"$ls_done"
	grep '^single_file_work_copy$' <<<"$ls_done"

	ls_open=$(ls -1 "$sub_open")
	grep '^dir$' <<<"$ls_open"
	grep '^dir2$' <<<"$ls_open"

	ls_open=$(ls -1 "$sub_open/dir")
	grep '^single_file_work$' <<<"$ls_open"
	grep '^single_file_work_copy$' <<<"$ls_open"

	ls_open=$(ls -1 "$sub_open/dir2")
	grep '^single_file_work$' <<<"$ls_open"
	grep '^single_file_work_copy$' <<<"$ls_open"

	run ls "$sub_open/dir3"
	[ "$status" != 0 ]
}

@test "make directories as student" {
	run mkdir "$sub_done/dir"
	[ "$status" != 0 ]

	run mkdir "$sub_done/dir1"
	[ "$status" != 0 ]

	run mkdir "$sub_open/dir"
	[ "$status" != 0 ]

	mkdir "$sub_open/dir1"
	[ -d "$sub_open/dir1" ]

	mkdir -p "$sub_open/dir3/dir4"
	[ -d "$sub_open/dir3" ]
	[ -d "$sub_open/dir3/dir4" ]
}

@test "delete directories as student" {
	run rm "$sub_done/dir"
	[ "$status" != 0 ]
	[ -d "$sub_done/dir" ]

	run rm -r "$sub_done/dir"
	[ "$status" != 0 ]
	[ -d "$sub_done/dir" ]
	[ -f "$sub_done/dir/single_file_work" ]
	[ -f "$sub_done/dir/single_file_work_copy" ]

	run rm "$sub_open/dir"
	[ "$status" != 0 ]
	[ -d "$sub_open/dir" ]

	run rmdir "$sub_open/dir"
	[ "$status" != 0 ]
	[ -d "$sub_open/dir" ]

	# rm -r "$sub_open/dir"
	# ! [ -d "$sub_open/dir" ]

	# mkdir "$sub_open/dir"
	# [ -d "$sub_open/dir" ]
	# rmdir "$sub_open/dir"
	# ! [ -d "$sub_open/dir" ]
}

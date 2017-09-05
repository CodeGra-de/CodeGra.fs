load common

username=$teacher_user
password=$teacher_pass

@test "list courses as teacher" {
	ls "$mount_dir"
	for course in "Besturingssystemen" "Programmeertalen" "Project Software Engineering"; do
		[ -d "$mount_dir/$course" ]
	done
}

@test "list assignments as teacher" {
	for assig in "Security assignment" "Shell"; do
		[ -d "$mount_dir/Besturingssystemen/$assig" ]
	done

	for assig in "Erlang" "Go" "Haskell" "Python" "Shell"; do
		[ -d "$mount_dir/Programmeertalen/$assig" ]
	done

	for assig in "Final deadline"; do
		[ -d "$mount_dir/Project Software Engineering/$assig" ]
	done
}

@test "list submissions as teacher" {
	for course in "Besturingssystemen" "Programmeertalen"; do
		for submission in "$mount_dir/$course"/*/*; do
			grep "^/.*/.*/.*/.*/Stupid[1-4]" <<<"$submission"
		done
	done

	for submission in "$mount_dir/Project Software Engineering"/*/*; do
		grep "^/.*/.*/.*/.*/Thomas Schaper" <<<"$submission"
	done
}

@test "create files as teacher" {
	run touch "$sub_open/file1"
	[ "$status" != 0 ]
	! [ -f "$sub_open/file1" ]

	run "echo abc >'$sub_open/file2'"
	[ "$status" != 0 ]
	! [ -f "$sub_open/file2" ]

	echo "$sub_done/file3"
	touch "$sub_done/file3"
	[ -f "$sub_done/file3" ]

	echo abc >"$sub_done/file4"
	[ -f "$sub_done/file4" ]
}

@test "write & read files as teacher" {
	run "echo abc >'$sub_open/file1'"
	[ "$status" != 0 ]
	! [ -f "$sub_open/file1" ]

	echo abc >"$sub_done/file2"
	[ -f "$sub_done/file2" ]
	[ "$(cat "$sub_done/file2")" = $'abc' ]
	echo def >"$sub_done/file2"
	[ -f "$sub_done/file2" ]
	[ "$(cat "$sub_done/file2")" = $'def' ]
	echo def >>"$sub_done/file2"
	[ -f "$sub_done/file2" ]
	[ "$(cat "$sub_done/file2")" = $'def\ndef' ]
}

@test "delete files as teacher" {
	run rm "$sub_open/dir/single_file_work"
	[ "$status" != 0 ]
	[ -f "$sub_open/dir/single_file_work" ]

	run rm "$sub_done/nonexistant_file"
	[ "$status" != 0 ]

	rm "$sub_done/dir/single_file_work"
	! [ -f "$sub_done/dir/single_file_work" ]
}

@test "read directories as teacher" {
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

@test "make directories as teacher" {
	run mkdir "$sub_open/dir"
	[ "$status" != 0 ]

	run mkdir "$sub_open/dir1"
	[ "$status" != 0 ]

	run mkdir "$sub_done/dir"
	[ "$status" != 0 ]

	mkdir "$sub_done/dir1"
	[ -d "$sub_done/dir1" ]

	mkdir -p "$sub_done/dir3/dir4"
	[ -d "$sub_done/dir3" ]
	[ -d "$sub_done/dir3/dir4" ]
}

@test "delete directories as teacher" {
	run rm "$sub_open/dir"
	[ "$status" != 0 ]
	[ -d "$sub_open/dir" ]

	run rm -r "$sub_open/dir"
	[ "$status" != 0 ]
	[ -d "$sub_open/dir" ]
	[ -f "$sub_open/dir/single_file_work" ]
	[ -f "$sub_open/dir/single_file_work_copy" ]

	run rm "$sub_done/dir"
	[ "$status" != 0 ]
	[ -d "$sub_done/dir" ]

	run rmdir "$sub_done/dir"
	[ "$status" != 0 ]
	[ -d "$sub_done/dir" ]

	# rm -r "$sub_done/dir"
	# ! [ -d "$sub_done/dir" ]

	# mkdir "$sub_done/dir"
	# [ -d "$sub_done/dir" ]
	# rmdir "$sub_done/dir"
	# ! [ -d "$sub_done/dir" ]
}

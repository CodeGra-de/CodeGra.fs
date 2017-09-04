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
		for submission in "$mount_dir/$course/"**/*; do
			grep "^/.*/.*/.*/.*/Stupid[1-4]" <<<"$submission"
		done
	done

	for submission in "$mount_dir/Project Software Engineering/"**/*; do
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
	echo abc >"$sub_done/file1"
	[ "$status" != 0 ]
	rm "$sub_done/file1"
}

@test "read directory as teacher" {
}

@test "make directory as teacher" {
}

@test "delete directory as teacher" {
}

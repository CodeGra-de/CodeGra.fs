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
	for submission in "$mount_dir/Programmeertalen/"**/*; do
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

@test "read directory as student" {
}

@test "make directory as student" {
}

@test "delete directory as student" {
}

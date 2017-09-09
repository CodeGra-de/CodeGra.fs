export CGAPI_BASE_URL=http://localhost:5000/api/v1

mount_dir=
assig_open=
assig_done=
sub_open=
sub_done=
teacher_user="thomas"
teacher_pass="Thomas Schaper"
teacher_jwt=$(http post :5000/api/v1/login username="$teacher_user" password="$teacher_pass" | jq -r .access_token)
student_user="stupid1"
student_pass="Stupid1"
student_jwt=$(http post :5000/api/v1/login username="$student_user" password="$student_pass" | jq -r .access_token)
admin_user="robin"
admin_pass="Robin"
admin_jwt=$(http post :5000/api/v1/login username="$admin_user" password="$admin_pass" | jq -r .access_token)
export CGFS_PID=-1

mount_cgfs()
{
	./cgfs.py --verbose --password "$password" "$username" "$mount_dir" 3>- &
        CGFS_PID="$!"
        sleep 1
	while ! [ -d "$mount_dir/Programmeertalen" ]; do :; done
        sleep 1
}

unmount_cgfs()
{
	fusermount -u "$mount_dir"
        kill "$CGFS_PID"
}

remount_cgfs()
{
	unmount_cgfs
	mount_cgfs
}

setup()
{
	assignments=$(http :5000/api/v1/assignments/ Authorization:Bearer\ $student_jwt)
	assignment_id=$(echo $assignments | jq "map(select(.name == \"Python\")) | .[0].id")
	sub1_id=$(http --form post :5000/api/v1/assignments/$assignment_id/submission Authorization:Bearer\ $student_jwt file@test_data/multiple_dir_archive.zip | jq .id)

	assignment_id=$(echo $assignments | jq "map(select(.name == \"Shell\")) | .[0].id")
	http patch :5000/api/v1/assignments/$assignment_id Authorization:Bearer\ $teacher_jwt state=open deadline=$(date --date=tomorrow +'%Y-%m-%dT%H:%M')
	sub2_id=$(http --form post :5000/api/v1/assignments/$assignment_id/submission Authorization:Bearer\ $student_jwt file@test_data/multiple_dir_archive.zip | jq .id)
	http patch :5000/api/v1/assignments/$assignment_id Authorization:Bearer\ $teacher_jwt state=done deadline=$(date --date=now +'%Y-%m-%dT%H:%M')

	mount_dir=$(mktemp -d)
	mount_cgfs

	assig_open="$mount_dir/Programmeertalen/Python"
	assig_done="$mount_dir/Programmeertalen/Shell"
	sub_open="$assig_open/$(ls -1 "$assig_open" | grep "Stupid1" | tail -n1)"
	sub_done="$assig_done/$(ls -1 "$assig_done" | grep "Stupid1" | tail -n1)"
}

teardown()
{
	unmount_cgfs
	rm -rf "$mount_dir"

	http delete :5000/api/v1/submissions/$sub1_id Authorization:Bearer\ $admin_jwt
	http delete :5000/api/v1/submissions/$sub2_id Authorization:Bearer\ $admin_jwt
}

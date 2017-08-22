#include "cgapi.c"
#include "test.h"
#include <jansson.h>

void test_cgapi_serialize_user()
{
        const char *json = cgapi_serialize_user("test", "test");
        const char *expected = "{\"email\":\"test\",\"password\":\"test\"}";

        EXPECT(json != NULL);
        EXPECT(strcmp(json, expected) == 0);

        free((char *)json);
}

void test_cgapi_deserialize_json(void)
{
        const char *json_array = "[1, 2, 3]";
        const char *json_object = "{\"a\": 1, \"b\": 2, \"c\": 3}";

        json_t *j;

        EXPECT(cgapi_deserialize_json(json_array, &j, cgapi_is_array) == 0);
        EXPECT(json_array_size(j) == 3);
        json_decref(j);
        EXPECT(cgapi_deserialize_json(json_object, &j, cgapi_is_object) == 0);
        EXPECT(json_object_size(j) == 3);
        json_decref(j);
        EXPECT(cgapi_deserialize_json(json_array, &j, cgapi_is_object) == -1);
        EXPECT(j == NULL);
        json_decref(j);
        EXPECT(cgapi_deserialize_json(json_object, &j, cgapi_is_array) == -1);
        EXPECT(j == NULL);
        json_decref(j);
}

void test_cgapi_login()
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        EXPECT(tok != NULL);
#define JWT_HEADER "Authorization: Bearer "
        EXPECT(strncmp(tok->str, JWT_HEADER, strlen(JWT_HEADER)) == 0);
#undef JWT_HEADER

        cgapi_logout(tok);
}

void test_cgapi_get_courses(void)
{
        char *assig_proj_soft[] = {
                "Final deadline", NULL,
        };
        char *assig_besturing[] = {
                "Security assignment", "Shell", NULL,
        };
        char *assig_progtalen[] = {
                "Haskell", "Shell", "Python", "Erlang", "Go", NULL,
        };

        struct {
                char *name;
                char **assig;
        } course_data[] = {
                {
                        "Project Software Engineering", assig_proj_soft,
                },
                {
                        "Besturingssystemen", assig_besturing,
                },
                {
                        "Programmeertalen", assig_progtalen,
                },
        };
        size_t ncourses = sizeof(course_data) / sizeof(*course_data);

        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        json_t *courses;
        int ret = cgapi_get_courses(tok, &courses);

        EXPECT(ret == 0);
        EXPECT(json_is_array(courses));
        EXPECT(json_array_size(courses) == ncourses);

        for (size_t i = 0; i < ncourses; i++) {
                json_t *course = json_array_get(courses, i);
                EXPECT(json_is_object(course));

                json_t *id = json_object_get(course, "id");
                EXPECT(json_is_integer(id));

                json_t *name = json_object_get(course, "name");
                EXPECT(json_is_string(name));

                const char *namestr = json_string_value(name);
                size_t course_idx = ncourses + 1;
                for (size_t j = 0; j < ncourses; j++) {
                        if (strcmp(namestr, course_data[j].name) == 0) {
                                course_idx = j;
                                break;
                        }
                }
                EXPECT(course_idx < ncourses);

                json_t *assignments = json_object_get(course, "assignments");
                EXPECT(json_is_array(assignments));

                for (size_t j = 0; j < json_array_size(assignments); j++) {
                        json_t *assignment = json_array_get(assignments, j);
                        EXPECT(json_is_object(assignment));

                        json_t *id = json_object_get(assignment, "id");
                        EXPECT(json_is_integer(id));

                        json_t *name = json_object_get(assignment, "name");
                        EXPECT(json_is_string(name));

                        const char *namestr = json_string_value(name);
                        char **assig_name = NULL;
                        for (assig_name = course_data[course_idx].assig;
                             *assig_name; assig_name++) {
                                if (strcmp(namestr, *assig_name) == 0) {
                                        break;
                                }
                        }
                        EXPECT(*assig_name != NULL);
                }
        }

        cgapi_logout(tok);
}

void test_cgapi_get_submissions(void)
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        cgapi_logout(tok);
}

void test_cgapi_get_submission_files(void)
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        cgapi_logout(tok);
}

void test_cgapi_get_file_meta(void)
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        cgapi_logout(tok);
}

void test_cgapi_get_file_buf(void)
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        cgapi_logout(tok);
}

void test_cgapi_patch_file_buf(void)
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        cgapi_logout(tok);
}

void test_cgapi_post_file(void)
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        cgapi_logout(tok);
}

void test_cgapi_unlink_file(void)
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        cgapi_logout(tok);
}

int main(void)
{
        test_cgapi_serialize_user();
        test_cgapi_deserialize_json();
        test_cgapi_login();
        // test_cgapi_get_courses();
        // test_cgapi_get_submissions();
        // test_cgapi_get_submission_files();
        // test_cgapi_get_file_meta();
        // test_cgapi_get_file_buf();
        // test_cgapi_patch_file_buf();
        // test_cgapi_post_file();
        // test_cgapi_unlink_file();

        RESULTS();
}

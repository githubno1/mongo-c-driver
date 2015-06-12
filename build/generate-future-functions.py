#!/usr/bin/env python
#
# Copyright 2015 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generate test functions for use with mock_server_t.

Defines functions like future_cursor_next in future-functions.h and
future-functions.c, which defer a libmongoc operation to a background thread
via functions like background_cursor_next. Also defines functions like
future_value_set_bson_ptr and future_value_get_bson_ptr which support the
future / background functions, and functions like future_get_bson_ptr which
wait for a future to resolve, then return its value.

These future functions are used in conjunction with mock_server_t to
conveniently test libmongoc wire protocol operations.

Written for Python 2.6+, requires Jinja 2 for templating.
"""

from collections import namedtuple
from os.path import basename, dirname, join as joinpath, normpath

from jinja2 import Template  # Please "pip install jinja2".


this_dir = dirname(__file__)
template_dir = joinpath(this_dir, 'future_function_templates')
mock_server_dir = normpath(joinpath(this_dir, '../tests/mock_server'))

# Add additional types here. Use typedefs for derived types so they can
# be named with one symbol.
typedef = namedtuple("typedef", ["name", "typedef"])

# These are typedef'ed if necessary in future-value.h, and added to the union
# of possible future_value_t.value types. future_value_t getters and setters
# are generated for all types, as well as future_t getters.
typedef_list = [
    typedef("bool", None),
    typedef("bson_error_ptr", "bson_error_t *"),
    typedef("bson_ptr", "bson_t *"),
    typedef("char_ptr", "char *"),
    typedef("char_ptr_ptr", "char **"),

    typedef("const_char_ptr", "const char *"),
    typedef("const_bson_ptr", "const bson_t *"),
    typedef("const_bson_ptr_ptr", "const bson_t **"),
    typedef("const_mongoc_read_prefs_ptr", "const mongoc_read_prefs_t *"),

    typedef("mongoc_bulk_operation_ptr", "mongoc_bulk_operation_t *"),
    typedef("mongoc_client_ptr", "mongoc_client_t *"),
    typedef("mongoc_cursor_ptr", "mongoc_cursor_t *"),
    typedef("mongoc_database_ptr", "mongoc_database_t *"),
    typedef("mongoc_query_flags_t", None),
    typedef("uint32_t", None),
]

type_list = [T.name for T in typedef_list]

param = namedtuple("param", ["type_name", "name"])
future_function = namedtuple("future_function", ["ret_type", "name", "params"])

# Add additional functions to be tested here. For a name like "cursor_next", we
# generate two functions: future_cursor_next to prepare the future_t and launch
# a background thread, and background_cursor_next to run on the thread and
# resolve the future.
future_functions = [
    future_function("uint32_t",
                    "bulk_operation_execute",
                    [param("mongoc_bulk_operation_ptr", "bulk"),
                     param("bson_ptr", "reply"),
                     param("bson_error_ptr", "error")]),

    future_function("bool",
                    "client_command_simple",
                    [param("mongoc_client_ptr", "client"),
                     param("const_char_ptr", "db_name"),
                     param("const_bson_ptr", "command"),
                     param("const_mongoc_read_prefs_ptr", "read_prefs"),
                     param("bson_ptr", "reply"),
                     param("bson_error_ptr", "error")]),

    future_function("bool",
                    "cursor_next",
                    [param("mongoc_cursor_ptr", "cursor"),
                     param("const_bson_ptr_ptr", "doc")]),

    future_function("char_ptr_ptr",
                    "client_get_database_names",
                    [param("mongoc_client_ptr", "client"),
                     param("bson_error_ptr", "error")]),

    future_function("char_ptr_ptr",
                    "database_get_collection_names",
                    [param("mongoc_database_ptr", "database"),
                     param("bson_error_ptr", "error")]),
]


for fn in future_functions:
    for p in fn.params:
        if p.type_name not in type_list:
            raise Exception('bad type "%s"\n\nin %s' % (p.type_name, fn))


header_comment = """/**************************************************
 *
 * Generated by build/%s.
 *
 * DO NOT EDIT THIS FILE.
 *
 *************************************************/""" % basename(__file__)


files = ["future.h",
         "future.c",
         "future-value.h",
         "future-value.c",
         "future-functions.h",
         "future-functions.c"]


for file_name in files:
    print(file_name)
    template = open(joinpath(template_dir, file_name + '.template')).read()
    with open(joinpath(mock_server_dir, file_name), 'w+') as f:
        f.write(Template(template).render(globals()))

# -*- coding: utf-8 -*-

#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from bayeslite.sqlite3_util import sqlite3_exec_1

bayesdb_schema = """
PRAGMA foreign_keys = ON;
PRAGMA application_id = 1113146434; -- #x42594442, `BYDB'
PRAGMA user_version = 3;

BEGIN;
CREATE TABLE bayesdb_metamodel (
	id		INTEGER NOT NULL UNIQUE PRIMARY KEY CHECK (id >= 0),
	name		TEXT COLLATE NOCASE NOT NULL UNIQUE
);

CREATE TABLE bayesdb_table (
	id		INTEGER NOT NULL UNIQUE PRIMARY KEY CHECK (id >= 0),
	name		TEXT COLLATE NOCASE NOT NULL UNIQUE,
				-- REFERENCES sqlite_master(name)
	metamodel_id	INTEGER NOT NULL REFERENCES bayesdb_metamodel(id),
	metadata	BLOB NOT NULL
);

CREATE TABLE bayesdb_table_column (
	id		INTEGER NOT NULL PRIMARY KEY CHECK (id >= 0),
	table_id	INTEGER NOT NULL REFERENCES bayesdb_table(id),
	name		TEXT COLLATE NOCASE NOT NULL,
	colno		INTEGER NOT NULL,
	UNIQUE (table_id, name),
	UNIQUE (table_id, colno)
);

CREATE TABLE bayesdb_model (
	table_id	INTEGER NOT NULL REFERENCES bayesdb_table(id),
	modelno		INTEGER NOT NULL CHECK (modelno >= 0),
	theta		BLOB NOT NULL,
	PRIMARY KEY (table_id, modelno)
);
COMMIT;
"""

### BayesDB SQLite setup

def bayesdb_install_schema(db):
    application_id = sqlite3_exec_1(db, "PRAGMA application_id")
    user_version = sqlite3_exec_1(db, "PRAGMA user_version")
    if application_id == 0 and user_version == 0:
        # Assume we just created the database.
        #
        # XXX What if we opened some random other sqlite file which
        # did not have an application_id or user_version set?  Hope
        # everyone else sets application_id and user_version too...
        #
        # XXX Idiotic Python sqlite3 module has no way to execute a
        # string with multiple SQL commands that doesn't muck with the
        # application's transactions -- db.executescript("...") will
        # issue a COMMIT first, if there is a transaction pending, so
        # we can't just write
        #
        #   with sqlite3_transaction(db):
        #       db.executescript(bayesdb_schema)
        #
        # Instead, we abuse the use of sqlite database connections as
        # context managers that commit/rollback if there is a
        # transaction active.  Otherwise we make no use of the sqlite3
        # module's automatic transaction handling.
        with db:
            db.executescript(bayesdb_schema)
        assert sqlite3_exec_1(db, "PRAGMA application_id") == 0x42594442
        assert sqlite3_exec_1(db, "PRAGMA user_version") == 3
    elif application_id != 0x42594442:
        raise IOError("Invalid application_id: 0x%08x" % application_id)
    elif user_version != 3:
        raise IOError("Unknown database version: %d" % user_version)
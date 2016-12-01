# ~*~ coding: utf-8 ~*~
"""
tests.orm.conftest
~~~~~~~~~~~~~~~~~~

A simple conftest just for the ORM that creates a fixture for creating a small
sqlite database for testing.
"""

import pytest

SQLITE_DATABASE_NAME = 'test_db.db'

@pytest.fixture
def sqlite_db():
    """Create the `basicmodel` table in the `test_db.db` SQLite database for
    testing.

    All model tests use a single model with a simple schema and drop/create
    that on every run. This fixture does the drop creating.

    The database name is stored in the ``SQLITE_DATABASE_NAME`` constant in this
    module.
    """
    import sqlite3

    # @TODO (test): this should be able to live in a transaction and just
    # rollback at the end; should be faster
    conn = sqlite3.connect(SQLITE_DATABASE_NAME)

    # this is the exact schema PeeWee generates
    create_table_query = """
    CREATE TABLE "basicmodel" (
        "id" INTEGER NOT NULL PRIMARY KEY, "name"
        VARCHAR(32) NOT NULL)
    ;
    """
    conn.execute(create_table_query)
    yield
    conn.execute('DROP TABLE basicmodel')

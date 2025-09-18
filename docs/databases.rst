.. _databases:

=========
Databases
=========

OxenORM supports the following databases via the Rust engine (SQLx):

* SQLite
* PostgreSQL
* MySQL/MariaDB

All database I/O is executed by the Rust extension `oxen_engine`. No Python drivers are required.

.. _db_url:

DB_URL
======

OxenORM supports specifying Database configuration in a URL form. The form is:

:samp:`{DB_TYPE}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}?{PARAM1}=value&{PARAM2}=value`

The supported ``DB_TYPE``:

``sqlite``:
    Typically in the form of :samp:`sqlite://{DB_FILE}`
    So if the ``DB_FILE`` is "/data/db.sqlite3" then the string will be ``sqlite:///data/db.sqlite`` (note the three /'s)
``postgres``:
    Typically in the form of :samp:`postgres://postgres:pass@db.host:5432/somedb`
``mysql``:
    Typically in the form of :samp:`mysql://myuser:mypass@db.host:3306/somedb`

SQLite
======

SQLite is an embedded database that can run on a file or in-memory. Good for local development or testing of code logic.

PostgreSQL
==========

DB URL is typically in the form of :samp:`postgres://postgres:pass@db.host:5432/somedb`, or, if connecting via Unix domain socket :samp:`postgres:///somedb`.

MySQL/MariaDB
=============

DB URL is typically in the form of :samp:`mysql://myuser:mypass@db.host:3306/somedb`

Legacy Python clients
=====================
OxenORM previously documented Python driver usage. As of this release, all DB I/O is routed through Rust.
If you need to debug without Rust, set `OXEN_RUST_BACKEND=0` (queries will be disabled).

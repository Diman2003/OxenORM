.. _query_ir:

=============================
Rust Query IR and SQL Builder
=============================

Overview
========

OxenORM routes query construction to Rust using a compact, JSON-serializable
Query IR (Intermediate Representation). Rust generates dialect-correct SQL with
proper placeholders and quoting, then Oxen executes via the Rust engine.

Key benefits:

- Correct placeholder style per dialect (PostgreSQL, MySQL, SQLite)
- Safe identifier quoting for dotted identifiers (table.column)
- Dialect-aware case-insensitive matches (ILIKE on Postgres, LOWER() emulation elsewhere)
- Support for joins, filters, order by, distinct, limit/offset
- Update/Delete via ``action`` field

IR Schema (v1)
==============

Required:

- ``dialect``: ``postgres`` | ``mysql`` | ``sqlite``
- ``table``: string

Optional:

- ``action``: ``select`` (default) | ``insert`` | ``update`` | ``delete``
- ``select``: list[str]
- ``distinct``: bool
- ``joins``: list of ``{ join_type, table, on: { left, op, right } }``
- ``filters``: list of ``{ field, op, value }`` (ANDed)
- ``groups``: list of OR-groups ``{ kind: "or", filters: [...] }``
- ``order_by``: list of ``{ field, direction }``
- ``limit``: int
- ``offset``: int
- ``set``: object map of column -> value (for update)
- ``rows``: list[object] (for insert-many)

Supported ops: ``eq`` (default), ``ne``, ``lt``, ``lte``, ``gt``, ``gte``,
``like``, ``ilike`` (emulated on MySQL/SQLite), ``contains``, ``icontains``,
``startswith``, ``istartswith``, ``endswith``, ``iendswith``, ``in`` (array values),
``not_in``/``nin`` (array values), ``between`` (2-value array), ``isnull``, ``notnull``

Examples
========

Build-only API (Python):

.. code-block:: python3

    import json
    from oxen_engine import build_sql_json

    ir = {
        "dialect": "postgres",
        "table": "users",
        "select": ["id", "name"],
        "filters": [
            {"field": "age", "op": "gte", "value": 18},
            {"field": "name", "op": "like", "value": "%John%"},
        ],
        "order_by": [{"field": "id", "direction": "desc"}],
        "limit": 10,
        "offset": 5,
    }
    out = build_sql_json(json.dumps(ir))
    sql, params = out["sql"], out["params"]

Joins and OR groups:

.. code-block:: python3

    ir = {
        "dialect": "mysql",
        "table": "orders",
        "select": ["orders.id", "users.name"],
        "joins": [
            {"join_type": "left", "table": "users",
             "on": {"left": "orders.user_id", "op": "=", "right": "users.id"}},
            # Join ON a constant value
            {"join_type": "inner", "table": "regions",
             "on": {"left": "users.region_id", "op": "=", "right_value": 5}},
        ],
        "groups": [
            {"kind": "or", "filters": [
                {"field": "users.email", "op": "ilike", "value": "%@gmail.com"},
                {"field": "users.email", "op": "ilike", "value": "%@hotmail.com"},
            ]},
        ],
    }
    out = build_sql_json(json.dumps(ir))

Updates and Deletes:

.. code-block:: python3

    # UPDATE
    ir = {
        "dialect": "sqlite",
        "table": "users",
        "action": "update",
        "set": {"name": "Alice", "age": 30, "tags": ["pro", "beta"]},
        "filters": [{"field": "id", "op": "eq", "value": 1}],
    }
    out = build_sql_json(json.dumps(ir))

    # DELETE
    ir = {
        "dialect": "postgres",
        "table": "users",
        "action": "delete",
        "filters": [{"field": "id", "op": "eq", "value": 2}],
    }
    out = build_sql_json(json.dumps(ir))

Using IR in OxenORM
====================

OxenORM internally builds IR for QuerySet and update/delete operations and
executes the generated SQL through the Rust engine. You don't need to call
``build_sql_json`` directly unless you want to.

Notes
=====

- ILIKE is emulated on MySQL/SQLite via ``LOWER(col) LIKE LOWER(?)``.
- Postgres placeholders use ``$1..$n``; MySQL/SQLite use ``?``.
- Dotted identifiers (``table.column``) are quoted safely per dialect.
- JSON/arrays:
  - PostgreSQL binds JSON and arrays using native types.
  - MySQL/SQLite store arrays/JSON as JSON text; conversion happens in the Rust binder.



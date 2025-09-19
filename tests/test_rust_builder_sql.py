#!/usr/bin/env python3
import json
import pytest

from oxen_engine import build_sql_json

@pytest.mark.parametrize(
    "dialect,expected_sql",
    [
        (
            "postgres",
            'SELECT "id", "name" FROM "users" WHERE "age" >= $1 AND "name" LIKE $2 ORDER BY "id" DESC LIMIT 10 OFFSET 5',
        ),
        (
            "mysql",
            'SELECT `id`, `name` FROM `users` WHERE `age` >= ? AND `name` LIKE ? ORDER BY `id` DESC LIMIT 10 OFFSET 5',
        ),
        (
            "sqlite",
            'SELECT "id", "name" FROM "users" WHERE "age" >= ? AND "name" LIKE ? ORDER BY "id" DESC LIMIT 10 OFFSET 5',
        ),
    ],
)
def test_basic_select_across_dialects(dialect, expected_sql):
    ir = {
        "dialect": dialect,
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
    assert out["sql"] == expected_sql
    assert out["params"] == [18, "%John%"]

@pytest.mark.parametrize(
    "dialect,expected_sql",
    [
        (
            "postgres",
            'SELECT "orders"."id", "users"."name" FROM "orders" INNER JOIN "users" ON "orders"."user_id" = "users"."id" WHERE "orders"."total" > $1',
        ),
        (
            "mysql",
            'SELECT `orders`.`id`, `users`.`name` FROM `orders` INNER JOIN `users` ON `orders`.`user_id` = `users`.`id` WHERE `orders`.`total` > ?',
        ),
        (
            "sqlite",
            'SELECT "orders"."id", "users"."name" FROM "orders" INNER JOIN "users" ON "orders"."user_id" = "users"."id" WHERE "orders"."total" > ?',
        ),
    ],
)
def test_joins_and_filter(dialect, expected_sql):
    ir = {
        "dialect": dialect,
        "table": "orders",
        "select": ["orders.id", "users.name"],
        "joins": [
            {"join_type": "inner", "table": "users", "on": {"left": "orders.user_id", "op": "=", "right": "users.id"}},
        ],
        "filters": [{"field": "orders.total", "op": "gt", "value": 100}],
    }
    out = build_sql_json(json.dumps(ir))
    assert out["sql"] == expected_sql
    assert out["params"] == [100]

@pytest.mark.parametrize(
    "dialect,expected_sql",
    [
        (
            "postgres",
            'SELECT "id", "email" FROM "users" WHERE ("email" ILIKE $1 OR "email" ILIKE $2)',
        ),
        (
            "mysql",
            'SELECT `id`, `email` FROM `users` WHERE (LOWER(`email`) LIKE LOWER(?) OR LOWER(`email`) LIKE LOWER(?))',
        ),
        (
            "sqlite",
            'SELECT "id", "email" FROM "users" WHERE (LOWER("email") LIKE LOWER(?) OR LOWER("email") LIKE LOWER(?))',
        ),
    ],
)
def test_or_groups_and_ilike(dialect, expected_sql):
    ir = {
        "dialect": dialect,
        "table": "users",
        "select": ["id", "email"],
        "groups": [
            {
                "kind": "or",
                "filters": [
                    {"field": "email", "op": "ilike", "value": "%@gmail.com"},
                    {"field": "email", "op": "ilike", "value": "%@hotmail.com"},
                ],
            }
        ],
    }
    out = build_sql_json(json.dumps(ir))
    assert out["sql"] == expected_sql
    assert out["params"] == ["%@gmail.com", "%@hotmail.com"]


# Additional coverage per dialect

@pytest.mark.parametrize(
    "dialect,op,expected_fragment",
    [
        ("postgres", "eq", '"age" = $1'),
        ("postgres", "ne", '"age" <> $1'),
        ("postgres", "lt", '"age" < $1'),
        ("postgres", "lte", '"age" <= $1'),
        ("postgres", "gt", '"age" > $1'),
        ("postgres", "gte", '"age" >= $1'),
        ("mysql", "eq", '`age` = ?'),
        ("mysql", "ne", '`age` <> ?'),
        ("mysql", "lt", '`age` < ?'),
        ("mysql", "lte", '`age` <= ?'),
        ("mysql", "gt", '`age` > ?'),
        ("mysql", "gte", '`age` >= ?'),
        ("sqlite", "eq", '"age" = ?'),
        ("sqlite", "ne", '"age" <> ?'),
        ("sqlite", "lt", '"age" < ?'),
        ("sqlite", "lte", '"age" <= ?'),
        ("sqlite", "gt", '"age" > ?'),
        ("sqlite", "gte", '"age" >= ?'),
    ],
)
def test_all_ops(dialect, op, expected_fragment):
    ir = {
        "dialect": dialect,
        "table": "users",
        "select": ["id"],
        "filters": [{"field": "age", "op": op, "value": 21}],
    }
    out = build_sql_json(json.dumps(ir))
    assert expected_fragment in out["sql"]
    assert out["params"] == [21]


@pytest.mark.parametrize("dialect", ["postgres", "mysql", "sqlite"])
def test_in_list(dialect):
    out = build_sql_json(
        json.dumps(
            {
                "dialect": dialect,
                "table": "users",
                "select": ["id"],
                "filters": [
                    {"field": "id", "op": "in", "value": [1, 2, 3]},
                ],
            }
        )
    )
    if dialect == "postgres":
        assert '"id" IN ($1, $2, $3' in out["sql"] or '"id" IN ($1, $2, $3 )' in out["sql"]
    elif dialect == "mysql":
        assert "`id` IN (?, ?, ?" in out["sql"]
    else:
        assert '"id" IN (?, ?, ?' in out["sql"]
    assert out["params"] == [1, 2, 3]


@pytest.mark.parametrize("dialect", ["postgres", "mysql", "sqlite"])
def test_distinct_and_multi_order(dialect):
    out = build_sql_json(
        json.dumps(
            {
                "dialect": dialect,
                "table": "users",
                "select": ["id", "name"],
                "distinct": True,
                "order_by": [
                    {"field": "name", "direction": "asc"},
                    {"field": "id", "direction": "desc"},
                ],
            }
        )
    )
    assert out["sql"].startswith("SELECT DISTINCT")
    assert ("ORDER BY" in out["sql"]) and ("," in out["sql"].split("ORDER BY ")[1])


@pytest.mark.parametrize("dialect", ["postgres", "mysql", "sqlite"])
def test_dotted_identifiers_and_join_types(dialect):
    ir = {
        "dialect": dialect,
        "table": "schema.users" if dialect != "sqlite" else "main.users",
        "select": ["users.id", "orders.total"],
        "joins": [
            {"join_type": "left", "table": "orders", "on": {"left": "users.id", "op": "=", "right": "orders.user_id"}},
            {"join_type": "right", "table": "payments", "on": {"left": "users.id", "op": "=", "right": "payments.user_id"}},
        ],
    }
    out = build_sql_json(json.dumps(ir))
    assert "JOIN" in out["sql"]


@pytest.mark.parametrize("dialect", ["postgres", "mysql", "sqlite"])
def test_limit_only_and_offset_only(dialect):
    out = build_sql_json(json.dumps({"dialect": dialect, "table": "users", "select": ["id"], "limit": 7}))
    assert "LIMIT 7" in out["sql"]
    out2 = build_sql_json(json.dumps({"dialect": dialect, "table": "users", "select": ["id"], "offset": 11}))
    assert "OFFSET 11" in out2["sql"]


@pytest.mark.parametrize("dialect", ["postgres", "mysql", "sqlite"])
def test_update_and_delete_building(dialect):
    upd = build_sql_json(
        json.dumps(
            {
                "dialect": dialect,
                "table": "users",
                "action": "update",
                "set": {"name": "Alice", "age": 30},
                "filters": [{"field": "id", "op": "eq", "value": 1}],
            }
        )
    )
    assert upd["sql"].startswith("UPDATE") and " SET " in upd["sql"] and " WHERE " in upd["sql"]
    # First two are SET values (order not guaranteed across languages); third is WHERE id
    assert set(upd["params"][:2]) == set(["Alice", 30])
    assert upd["params"][2] == 1

    dele = build_sql_json(
        json.dumps(
            {
                "dialect": dialect,
                "table": "users",
                "action": "delete",
                "filters": [{"field": "id", "op": "eq", "value": 2}],
            }
        )
    )
    assert dele["sql"].startswith("DELETE FROM") and " WHERE " in dele["sql"]
    assert dele["params"] == [2]

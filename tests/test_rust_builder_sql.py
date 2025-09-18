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

//! OxenORM Rust Backend
//!
//! This crate provides the high-performance Rust backend for OxenORM,
//! handling database operations, connection pooling, and query execution.

use pyo3::prelude::*;
use pyo3::types::{PyList, PyDict, PyBytes, PyString};
use std::collections::HashMap;
use sqlx::{
    PgPool, postgres::{PgPoolOptions, PgConnectOptions}, 
    MySqlPool, mysql::MySqlPoolOptions,
    SqlitePool, sqlite::SqlitePoolOptions,
    Row, query::Query, Postgres, postgres::PgArguments, 
    MySql, mysql::MySqlArguments,
    Sqlite, sqlite::SqliteArguments,
    Error as SqlxError, Column, ValueRef
};
use serde::{Serialize, Deserialize};
use uuid::Uuid;
use std::sync::Arc;
use tokio::runtime::Runtime;
use thiserror::Error;
use pyo3::wrap_pyfunction;
use std::fs;
use std::path::Path;
use std::io::{Read, Write};
use std::time::Instant;
use base64::engine::general_purpose::STANDARD as BASE64_STANDARD;
use base64::Engine as _;
use image::{DynamicImage, GenericImageView};
use image::imageops::{resize, blur, brighten, contrast};
use chrono::{NaiveDate, NaiveDateTime, NaiveTime};
use rust_decimal::Decimal;
use pyo3::types::PyDateTime as PyDT;
use pyo3::types::PyDate as PyD;
use pyo3::types::PyTime as PyT;
use std::str::FromStr;

// ===== Query IR (serde) and SQL builder =====
#[derive(Debug, Deserialize)]
struct QueryIR {
    dialect: String,
    table: String,
    #[serde(default)]
    action: Option<String>, // select (default) | update | delete
    #[serde(default)]
    select: Vec<String>,
    #[serde(default)]
    distinct: bool,
    #[serde(default)]
    joins: Vec<JoinIR>,
    #[serde(default)]
    groups: Vec<GroupIR>,
    #[serde(default)]
    filters: Vec<FilterIR>,
    #[serde(default)]
    order_by: Vec<OrderByIR>,
    #[serde(default)]
    limit: Option<i64>,
    #[serde(default)]
    offset: Option<i64>,
    #[serde(default)]
    set: Option<serde_json::Map<String, serde_json::Value>>, // for update; preserves insertion order
    #[serde(default)]
    rows: Option<Vec<serde_json::Map<String, serde_json::Value>>>, // for insert-many
    #[serde(default)]
    with_sql: Option<String>, // optional CTE prefix without leading WITH
    #[serde(default)]
    returning: Option<Vec<String>>, // optional returning list (Postgres)
}

#[derive(Debug, Deserialize)]
struct FilterIR {
    field: String,
    op: String,
    value: serde_json::Value,
}

#[derive(Debug, Deserialize)]
struct OrderByIR {
    field: String,
    #[serde(default)]
    direction: Option<String>,
}

#[derive(Debug, Deserialize)]
struct JoinIR {
    #[serde(default)]
    join_type: Option<String>, // inner|left|right
    table: String,
    on: JoinOnIR,
}

#[derive(Debug, Deserialize)]
struct JoinOnIR {
    left: String,
    op: String,
    #[serde(default)]
    right: Option<String>,
    #[serde(default)]
    right_value: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
struct GroupIR { #[serde(default)] kind: Option<String>, #[serde(default)] filters: Vec<FilterIR> }

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum DialectKind { Postgres, MySQL, SQLite }

impl DialectKind {
    fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "postgres" | "postgresql" => DialectKind::Postgres,
            "mysql" => DialectKind::MySQL,
            _ => DialectKind::SQLite,
        }
    }

    fn quote_ident(&self, ident: &str) -> String {
        // Support raw expressions, wildcard and dotted paths
        if ident == "*" { return "*".to_string(); }
        if ident.ends_with(".*") {
            let is_mysql = matches!(self, DialectKind::MySQL);
            let (prefix, _) = ident.split_at(ident.len()-2);
            let quoted_prefix = if is_mysql { format!("`{}`", prefix.replace('`', "``")) } else { format!("\"{}\"", prefix.replace('"', "\"")) };
            return format!("{}.{}", quoted_prefix, "*");
        }
        // Support dotted paths: schema.table or table.column
        if ident.contains('(') || ident.contains(')') || ident.contains(' ') {
            // Treat as raw expression
            return ident.to_string();
        }
        let quote_one = |name: &str, is_mysql: bool| -> String {
            if is_mysql { format!("`{}`", name.replace('`', "``")) } else { format!("\"{}\"", name.replace('"', "\"")) }
        };
        let is_mysql = matches!(self, DialectKind::MySQL);
        if ident.contains('.') {
            let parts: Vec<String> = ident.split('.').map(|p| quote_one(p, is_mysql)).collect();
            parts.join(".")
        } else {
            quote_one(ident, is_mysql)
        }
    }
}

fn json_to_paramvalue_value(v: &serde_json::Value) -> ParamValue {
    match v {
        serde_json::Value::Null => ParamValue::Null,
        serde_json::Value::Bool(b) => ParamValue::Bool(*b),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() { ParamValue::I64(i) }
            else if let Some(f) = n.as_f64() { ParamValue::F64(f) }
            else { ParamValue::Str(n.to_string()) }
        }
        serde_json::Value::String(s) => ParamValue::Str(s.clone()),
        serde_json::Value::Array(a) => {
            if a.is_empty() {
                // Empty array - default to JSON to avoid ambiguous type, caller may override
                return ParamValue::Json(serde_json::Value::Array(vec![]));
            }
            let mut all_str = true;
            let mut all_bool = true;
            let mut only_numbers = true;
            let mut has_float = false;
            let mut strs: Vec<String> = Vec::new();
            let mut bools: Vec<bool> = Vec::new();
            let mut i64s: Vec<i64> = Vec::new();
            let mut f64s: Vec<f64> = Vec::new();
            for el in a.iter() {
                match el {
                    serde_json::Value::String(s) => { strs.push(s.clone()); bools.push(false); i64s.push(0); f64s.push(0.0); only_numbers = false; all_bool = false; }
                    serde_json::Value::Bool(b) => { bools.push(*b); all_str = false; only_numbers = false; }
                    serde_json::Value::Number(n) => {
                        all_str = false; all_bool = false;
                        if let Some(i) = n.as_i64() { i64s.push(i); f64s.push(i as f64); }
                        else if let Some(f) = n.as_f64() { f64s.push(f); has_float = true; }
                        else { has_float = true; }
                    }
                    _ => { all_str = false; all_bool = false; only_numbers = false; }
                }
            }
            if all_str { return ParamValue::ArrayStr(strs.into_iter().filter(|s| !s.is_empty() || true).collect()); }
            if all_bool { return ParamValue::ArrayBool(bools); }
            if only_numbers {
                if has_float { return ParamValue::ArrayF64(f64s); }
                else { return ParamValue::ArrayI64(i64s); }
            }
            ParamValue::Json(serde_json::Value::Array(a.clone()))
        }
        serde_json::Value::Object(o) => ParamValue::Json(serde_json::Value::Object(o.clone())),
    }
}

fn build_sql_from_ir(ir: &QueryIR) -> (String, Vec<ParamValue>) {
    let dialect = DialectKind::from_str(&ir.dialect);
    let mut sql = String::new();
    let mut params: Vec<ParamValue> = Vec::new();
    let action = ir.action.as_deref().unwrap_or("select").to_lowercase();

    // Optional CTE prefix
    if let Some(with_sql) = ir.with_sql.as_ref() {
        if !with_sql.trim().is_empty() {
            sql.push_str("WITH ");
            sql.push_str(with_sql);
            sql.push(' ');
        }
    }

    match action.as_str() {
        "insert" => {
            sql.push_str("INSERT INTO ");
            sql.push_str(&dialect.quote_ident(&ir.table));

            // Determine columns and values
            if let Some(rows) = ir.rows.as_ref() {
                // Multiple rows insert
                if rows.is_empty() {
                    // Fallback to DEFAULT VALUES
                    sql.push_str(" DEFAULT VALUES");
                } else {
                    // Use keys from first row as column order
                    let first = &rows[0];
                    let columns: Vec<String> = first.keys().map(|k| dialect.quote_ident(k)).collect();
                    sql.push_str(" (");
                    sql.push_str(&columns.join(", "));
                    sql.push_str(") VALUES ");
                    for (i, row) in rows.iter().enumerate() {
                        if i > 0 { sql.push_str(", "); }
                        sql.push('(');
                        let mut first_val = true;
                        for k in first.keys() {
                            if !first_val { sql.push_str(", "); } else { first_val = false; }
                            sql.push('?');
                            let v = row.get(k).unwrap_or(&serde_json::Value::Null);
                            params.push(json_to_paramvalue_value(v));
                        }
                        sql.push(')');
                    }
                }
            } else if let Some(set_map) = ir.set.as_ref() {
                if set_map.is_empty() {
                    sql.push_str(" DEFAULT VALUES");
                } else {
                    let columns: Vec<String> = set_map.keys().map(|k| dialect.quote_ident(k)).collect();
                    sql.push_str(" (");
                    sql.push_str(&columns.join(", "));
                    sql.push_str(") VALUES (");
                    for (i, k) in set_map.keys().enumerate() {
                        if i > 0 { sql.push_str(", "); }
                        sql.push('?');
                        let v = set_map.get(k).unwrap();
                        params.push(json_to_paramvalue_value(v));
                    }
                    sql.push(')');
                }
            } else {
                // No values provided
                sql.push_str(" DEFAULT VALUES");
            }
        }
        "update" => {
            sql.push_str("UPDATE ");
            sql.push_str(&dialect.quote_ident(&ir.table));
            sql.push_str(" SET ");
            let mut wrote_any = false;
            if let Some(set_map) = ir.set.as_ref() {
                // Iterate in key order to stabilize tests (serde_json::Map preserves insertion order
                for k in set_map.keys() {
                    if wrote_any { sql.push_str(", "); }
                    sql.push_str(&format!("{} = ?", dialect.quote_ident(k)));
                    let v = set_map.get(k).unwrap();
                    params.push(json_to_paramvalue_value(v));
                    wrote_any = true;
                }
            }
            if !wrote_any {
                sql.push_str("1=1");
            }
        }
        "delete" => {
            sql.push_str("DELETE FROM ");
            sql.push_str(&dialect.quote_ident(&ir.table));
        }
        _ => {
            sql.push_str("SELECT ");
            if ir.distinct { sql.push_str("DISTINCT "); }
            if ir.select.is_empty() { sql.push('*'); } else {
                let cols: Vec<String> = ir.select.iter().map(|c| dialect.quote_ident(c)).collect();
                sql.push_str(&cols.join(", "));
            }
            sql.push_str(" FROM ");
            sql.push_str(&dialect.quote_ident(&ir.table));
        }
    }

    // JOINS (basic ON left op right)
    if !ir.joins.is_empty() {
        for j in &ir.joins {
            let jt = j.join_type.as_deref().unwrap_or("inner").to_lowercase();
            let jt_sql = match jt.as_str() { "left" => " LEFT JOIN ", "right" => " RIGHT JOIN ", _ => " INNER JOIN " };
            sql.push_str(jt_sql);
            sql.push_str(&dialect.quote_ident(&j.table));
            sql.push_str(" ON ");
            let op = match j.on.op.to_lowercase().as_str() { "eq" => "=", "<>"|"!=" => "<>", ">" => ">", ">=" => ">=", "<" => "<", "<=" => "<=", _ => "=" };
            let left = dialect.quote_ident(&j.on.left);
            if let Some(right_ident) = &j.on.right {
                sql.push_str(&format!("{} {} {}", left, op, dialect.quote_ident(right_ident)));
            } else if let Some(rv) = &j.on.right_value {
                sql.push_str(&format!("{} {} ?", left, op));
                params.push(json_to_paramvalue_value(rv));
            } else {
                // Fallback: treat as tautology to avoid invalid SQL
                sql.push_str("1=1");
            }
        }
    }

    // WHERE from filters (AND all for v1)
    if !ir.filters.is_empty() {
        let mut first = true;
        // For update/delete/select we add WHERE before filters
        sql.push_str(" WHERE ");
        for f in &ir.filters {
            if !first { sql.push_str(" AND "); } else { first = false; }
            let field = dialect.quote_ident(&f.field);
            let op = f.op.to_lowercase();
            match op.as_str() {
                "in" => {
                    if let serde_json::Value::Array(arr) = &f.value {
                        if arr.is_empty() {
                            sql.push_str("1=0");
                        } else {
                            sql.push_str(&format!("{} IN ({} )", field, {
                                let mut placeholders = String::new();
                                for (i, v) in arr.iter().enumerate() {
                                    if i > 0 { placeholders.push_str(", "); }
                                    placeholders.push('?');
                                    params.push(json_to_paramvalue_value(v));
                                }
                                placeholders
                            }));
                        }
                    } else {
                        // Non-array IN: treat as equality
                        sql.push_str(&format!("{} = ?", field));
                        params.push(json_to_paramvalue_value(&f.value));
                    }
                }
                "like" | "ilike" | "contains" | "icontains" | "startswith" | "istartswith" | "endswith" | "iendswith" => {
                    // Case-insensitive match: Postgres supports ILIKE, others emulate
                    let (use_ilike, value) = if matches!(op.as_str(), "contains"|"icontains"|"startswith"|"istartswith"|"endswith"|"iendswith") {
                        // Build pattern value
                        let s = match &f.value { serde_json::Value::String(s) => s.clone(), _ => f.value.to_string() };
                        let pat = match op.as_str() {
                            "contains"|"icontains" => format!("%{}%", s),
                            "startswith"|"istartswith" => format!("{}%", s),
                            _ => format!("%{}", s),
                        };
                        (op.starts_with('i'), serde_json::Value::String(pat))
                    } else { (op == "ilike", f.value.clone()) };
                    if use_ilike {
                        match dialect {
                            DialectKind::Postgres => sql.push_str(&format!("{} ILIKE ?", field)),
                            _ => sql.push_str(&format!("LOWER({}) LIKE LOWER(?)", field)),
                        }
                    } else {
                        sql.push_str(&format!("{} LIKE ?", field));
                    }
                    params.push(json_to_paramvalue_value(&value));
                }
                "isnull" => { sql.push_str(&format!("{} IS NULL", field)); }
                "notnull" => { sql.push_str(&format!("{} IS NOT NULL", field)); }
                "between" => {
                    if let serde_json::Value::Array(arr) = &f.value {
                        if arr.len() >= 2 {
                            sql.push_str(&format!("{} BETWEEN ? AND ?", field));
                            params.push(json_to_paramvalue_value(&arr[0]));
                            params.push(json_to_paramvalue_value(&arr[1]));
                        } else {
                            sql.push_str(&format!("{} = ?", field));
                            if let Some(v0) = arr.get(0) { params.push(json_to_paramvalue_value(v0)); } else { params.push(ParamValue::Null); }
                        }
                    } else {
                        sql.push_str(&format!("{} = ?", field));
                        params.push(json_to_paramvalue_value(&f.value));
                    }
                }
                "not_in" | "nin" => {
                    if let serde_json::Value::Array(arr) = &f.value {
                        if arr.is_empty() {
                            sql.push_str("1=1"); // NOT IN () -> always true
                        } else {
                            sql.push_str(&format!("{} NOT IN ({} )", field, {
                                let mut placeholders = String::new();
                                for (i, v) in arr.iter().enumerate() {
                                    if i > 0 { placeholders.push_str(", "); }
                                    placeholders.push('?');
                                    params.push(json_to_paramvalue_value(v));
                                }
                                placeholders
                            }));
                        }
                    } else {
                        sql.push_str(&format!("{} <> ?", field));
                        params.push(json_to_paramvalue_value(&f.value));
                    }
                }
                "ne" | "<>" => {
                    sql.push_str(&format!("{} <> ?", field));
                    params.push(json_to_paramvalue_value(&f.value));
                }
                "lt" => { sql.push_str(&format!("{} < ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                "lte" => { sql.push_str(&format!("{} <= ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                "gt" => { sql.push_str(&format!("{} > ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                "gte" => { sql.push_str(&format!("{} >= ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                _ => { // eq
                    sql.push_str(&format!("{} = ?", field));
                    params.push(json_to_paramvalue_value(&f.value));
                }
            }
        }
    }

    // OR groups: (f1 OR f2 ...)
    if !ir.groups.is_empty() {
        for g in &ir.groups {
            let kind = g.kind.as_deref().unwrap_or("or").to_lowercase();
            if g.filters.is_empty() { continue; }
            if kind == "or" {
                if sql.contains(" WHERE ") { sql.push_str(" AND ("); } else { sql.push_str(" WHERE ("); }
                for (i, f) in g.filters.iter().enumerate() {
                    if i > 0 { sql.push_str(" OR "); }
                    let field = dialect.quote_ident(&f.field);
                    let op = f.op.to_lowercase();
                    match op.as_str() {
                        "in" => {
                            if let serde_json::Value::Array(arr) = &f.value {
                                if arr.is_empty() { sql.push_str("1=0"); }
                                else {
                                    sql.push_str(&format!("{} IN ({} )", field, {
                                        let mut placeholders = String::new();
                                        for (j, v) in arr.iter().enumerate() {
                                            if j > 0 { placeholders.push_str(", "); }
                                            placeholders.push('?');
                                            params.push(json_to_paramvalue_value(v));
                                        }
                                        placeholders
                                    }));
                                }
                            } else {
                                sql.push_str(&format!("{} = ?", field));
                                params.push(json_to_paramvalue_value(&f.value));
                            }
                        }
                        "like" | "ilike" | "contains" | "icontains" | "startswith" | "istartswith" | "endswith" | "iendswith" => {
                            let (use_ilike, value) = if matches!(op.as_str(), "contains"|"icontains"|"startswith"|"istartswith"|"endswith"|"iendswith") {
                                let s = match &f.value { serde_json::Value::String(s) => s.clone(), _ => f.value.to_string() };
                                let pat = match op.as_str() {
                                    "contains"|"icontains" => format!("%{}%", s),
                                    "startswith"|"istartswith" => format!("{}%", s),
                                    _ => format!("%{}", s),
                                };
                                (op.starts_with('i'), serde_json::Value::String(pat))
                            } else { (op == "ilike", f.value.clone()) };
                            if use_ilike {
                                match dialect {
                                    DialectKind::Postgres => sql.push_str(&format!("{} ILIKE ?", field)),
                                    _ => sql.push_str(&format!("LOWER({}) LIKE LOWER(?)", field)),
                                }
                            } else { sql.push_str(&format!("{} LIKE ?", field)); }
                            params.push(json_to_paramvalue_value(&value));
                        }
                        "isnull" => { sql.push_str(&format!("{} IS NULL", field)); }
                        "notnull" => { sql.push_str(&format!("{} IS NOT NULL", field)); }
                        "between" => {
                            if let serde_json::Value::Array(arr) = &f.value {
                                if arr.len() >= 2 {
                                    sql.push_str(&format!("{} BETWEEN ? AND ?", field));
                                    params.push(json_to_paramvalue_value(&arr[0]));
                                    params.push(json_to_paramvalue_value(&arr[1]));
                                } else {
                                    sql.push_str(&format!("{} = ?", field));
                                    if let Some(v0) = arr.get(0) { params.push(json_to_paramvalue_value(v0)); } else { params.push(ParamValue::Null); }
                                }
                            } else { sql.push_str(&format!("{} = ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                        }
                        "not_in" | "nin" => {
                            if let serde_json::Value::Array(arr) = &f.value {
                                if arr.is_empty() { sql.push_str("1=1"); }
                                else {
                                    sql.push_str(&format!("{} NOT IN ({} )", field, {
                                        let mut placeholders = String::new();
                                        for (j, v) in arr.iter().enumerate() {
                                            if j > 0 { placeholders.push_str(", "); }
                                            placeholders.push('?');
                                            params.push(json_to_paramvalue_value(v));
                                        }
                                        placeholders
                                    }));
                                }
                            } else { sql.push_str(&format!("{} <> ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                        }
                        "ne" | "<>" => { sql.push_str(&format!("{} <> ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                        "lt" => { sql.push_str(&format!("{} < ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                        "lte" => { sql.push_str(&format!("{} <= ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                        "gt" => { sql.push_str(&format!("{} > ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                        "gte" => { sql.push_str(&format!("{} >= ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                        _ => { sql.push_str(&format!("{} = ?", field)); params.push(json_to_paramvalue_value(&f.value)); }
                    }
                }
                sql.push(')');
            }
        }
    }

    // ORDER BY (only applies to SELECT)
    if action == "select" && !ir.order_by.is_empty() {
        sql.push_str(" ORDER BY ");
        let mut parts: Vec<String> = Vec::new();
        for ob in &ir.order_by {
            let dir = ob.direction.as_deref().unwrap_or("asc");
            parts.push(format!("{} {}", dialect.quote_ident(&ob.field), dir.to_uppercase()));
        }
        sql.push_str(&parts.join(", "));
    }

    // LIMIT/OFFSET
    if action == "select" {
        if let Some(lim) = ir.limit { sql.push_str(&format!(" LIMIT {}", lim)); }
        if let Some(off) = ir.offset { sql.push_str(&format!(" OFFSET {}", off)); }
    }

    // Append RETURNING at end for Postgres when provided and action is insert/update/delete
    if matches!(dialect, DialectKind::Postgres) && (action == "insert" || action == "update" || action == "delete") {
        if let Some(ret) = ir.returning.as_ref() {
            if !ret.is_empty() {
                sql.push_str(" RETURNING ");
                sql.push_str(&ret.iter().map(|c| dialect.quote_ident(c)).collect::<Vec<_>>().join(", "));
            }
        }
    }

    // Postgres placeholder normalization
    if dialect == DialectKind::Postgres {
        let normalized = normalize_placeholders_for_postgres(&sql, params.len());
        return (normalized, params);
    }
    (sql, params)
}

#[pyfunction]
fn build_sql_json(py: Python, ir_json: String) -> PyResult<PyObject> {
    let ir: QueryIR = serde_json::from_str(&ir_json)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid IR: {}", e)))?;
    let (sql, params) = build_sql_from_ir(&ir);
    let py_params = PyList::empty(py);
    for p in params {
        // Convert ParamValue back to JSON-ish and then to PyObject
        let j = match p {
            ParamValue::Null => serde_json::Value::Null,
            ParamValue::Bool(b) => serde_json::Value::Bool(b),
            ParamValue::I64(i) => serde_json::Value::Number(serde_json::Number::from(i)),
            ParamValue::F64(f) => serde_json::Number::from_f64(f).map(serde_json::Value::Number).unwrap_or(serde_json::Value::Null),
            ParamValue::Str(s) => serde_json::Value::String(s),
            ParamValue::Bytes(b) => serde_json::Value::String(BASE64_STANDARD.encode(b)),
            ParamValue::Uuid(u) => serde_json::Value::String(u.to_string()),
            ParamValue::Dec(d) => serde_json::Value::String(d.to_string()),
            ParamValue::Json(v) => v,
            ParamValue::Date(d) => serde_json::Value::String(d.to_string()),
            ParamValue::Time(t) => serde_json::Value::String(t.to_string()),
            ParamValue::DateTime(dt) => serde_json::Value::String(dt.to_string()),
            ParamValue::ArrayStr(v) => serde_json::Value::Array(v.iter().map(|s| serde_json::Value::String(s.clone())).collect()),
            ParamValue::ArrayI64(v) => serde_json::Value::Array(v.iter().map(|x| serde_json::Value::Number((*x).into())).collect()),
            ParamValue::ArrayF64(v) => serde_json::Value::Array(v.iter().filter_map(|x| serde_json::Number::from_f64(*x)).map(serde_json::Value::Number).collect()),
            ParamValue::ArrayBool(v) => serde_json::Value::Array(v.iter().map(|b| serde_json::Value::Bool(*b)).collect()),
        };
        let obj = json_to_py_object(py, j)?;
        py_params.append(obj)?;
    }
    let out = PyDict::new(py);
    out.set_item("sql", sql)?;
    out.set_item("params", py_params)?;
    Ok(out.into())
}

impl DatabasePool {
    fn size(&self) -> usize { match self { DatabasePool::Postgres(p)=>p.size() as usize, DatabasePool::MySQL(p)=>p.size() as usize, DatabasePool::SQLite(p)=>p.size() as usize } }
}

// Execute large insert-many IR in chunks; for Postgres use single transaction
async fn execute_insert_rows_chunked(pool: &DatabasePool, ir: &QueryIR, chunk_size: usize) -> Result<QueryResult, OxenError> {
    let mut total_rows_affected: i64 = 0;
    match pool {
        DatabasePool::Postgres(pg_pool) => {
            let pool_ref: &PgPool = pg_pool.as_ref();
            let mut tx = pool_ref.begin().await.map_err(OxenError::QueryError)?;
            let rows = ir.rows.as_ref().ok_or_else(|| OxenError::ParameterError("rows missing".to_string()))?;
            for chunk in rows.chunks(chunk_size) {
                // Build a chunked IR
                let chunk_ir = QueryIR {
                    dialect: ir.dialect.clone(),
                    table: ir.table.clone(),
                    action: Some("insert".to_string()),
                    select: Vec::new(),
                    distinct: false,
                    joins: Vec::new(),
                    groups: Vec::new(),
                    filters: Vec::new(),
                    order_by: Vec::new(),
                    limit: None,
                    offset: None,
                    set: None,
                    rows: Some(chunk.to_vec()),
                    with_sql: ir.with_sql.clone(),
                    returning: ir.returning.clone(),
                };
                let (sql, params) = build_sql_from_ir(&chunk_ir);
                let sql_to_run = if sql.contains('?') { normalize_placeholders_for_postgres(&sql, params.len()) } else { sql };
                let mut query = sqlx::query(&sql_to_run);
                for param in params.iter() { query = bind_postgres_param(query, param); }
                let result = query.execute(&mut *tx).await.map_err(OxenError::QueryError)?;
                total_rows_affected += result.rows_affected() as i64;
            }
            tx.commit().await.map_err(OxenError::QueryError)?;
            Ok(QueryResult { rows_affected: total_rows_affected, data: Vec::new(), error: None, elapsed_ms: None })
        }
        DatabasePool::MySQL(mysql_pool) => {
            let rows = ir.rows.as_ref().ok_or_else(|| OxenError::ParameterError("rows missing".to_string()))?;
            for chunk in rows.chunks(chunk_size) {
                let chunk_ir = QueryIR {
                    dialect: ir.dialect.clone(),
                    table: ir.table.clone(),
                    action: Some("insert".to_string()),
                    select: Vec::new(),
                    distinct: false,
                    joins: Vec::new(),
                    groups: Vec::new(),
                    filters: Vec::new(),
                    order_by: Vec::new(),
                    limit: None,
                    offset: None,
                    set: None,
                    rows: Some(chunk.to_vec()),
                    with_sql: ir.with_sql.clone(),
                    returning: ir.returning.clone(),
                };
                let (sql, params) = build_sql_from_ir(&chunk_ir);
                let mut query = sqlx::query(&sql);
                for param in params.iter() { query = bind_mysql_param(query, param); }
                let result = query.execute(mysql_pool.as_ref()).await.map_err(OxenError::QueryError)?;
                total_rows_affected += result.rows_affected() as i64;
            }
            Ok(QueryResult { rows_affected: total_rows_affected, data: Vec::new(), error: None, elapsed_ms: None })
        }
        DatabasePool::SQLite(sqlite_pool) => {
            let rows = ir.rows.as_ref().ok_or_else(|| OxenError::ParameterError("rows missing".to_string()))?;
            for chunk in rows.chunks(chunk_size) {
                let chunk_ir = QueryIR {
                    dialect: ir.dialect.clone(),
                    table: ir.table.clone(),
                    action: Some("insert".to_string()),
                    select: Vec::new(),
                    distinct: false,
                    joins: Vec::new(),
                    groups: Vec::new(),
                    filters: Vec::new(),
                    order_by: Vec::new(),
                    limit: None,
                    offset: None,
                    set: None,
                    rows: Some(chunk.to_vec()),
                    with_sql: ir.with_sql.clone(),
                    returning: ir.returning.clone(),
                };
                let (sql, params) = build_sql_from_ir(&chunk_ir);
                let mut query = sqlx::query(&sql);
                for param in params.iter() { query = bind_sqlite_param(query, param); }
                let result = query.execute(sqlite_pool.as_ref()).await.map_err(OxenError::QueryError)?;
                total_rows_affected += result.rows_affected() as i64;
            }
            Ok(QueryResult { rows_affected: total_rows_affected, data: Vec::new(), error: None, elapsed_ms: None })
        }
    }
}

#[derive(Error, Debug)]
pub enum OxenError {
    #[error("Database connection failed: {0}")]
    ConnectionError(#[from] SqlxError),
    #[error("Query execution failed: {0}")]
    QueryError(SqlxError),
    #[error("Transaction error: {0}")]
    TransactionError(String),
    #[error("Invalid parameter: {0}")]
    ParameterError(String),
    #[error("Not connected to database")]
    NotConnected,
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
    #[error("Unsupported database type: {0}")]
    UnsupportedDatabase(String),
}

impl From<OxenError> for PyErr {
    fn from(err: OxenError) -> Self {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(err.to_string())
    }
}

#[derive(Debug, Clone)]
pub enum DatabaseType {
    Postgres,
    MySQL,
    SQLite,
}

impl DatabaseType {
    fn from_url(url: &str) -> Result<Self, OxenError> {
        if url.starts_with("postgresql://") || url.starts_with("postgres://") {
            Ok(DatabaseType::Postgres)
        } else if url.starts_with("mysql://") {
            Ok(DatabaseType::MySQL)
        } else if url.starts_with("sqlite://") || url.starts_with("sqlite:/") || url.starts_with("sqlite::memory:") || url == "sqlite::memory:" || url == "sqlite::memory" || url == "sqlite://:memory:" {
            Ok(DatabaseType::SQLite)
        } else {
            Err(OxenError::UnsupportedDatabase(url.to_string()))
        }
    }
}
fn normalize_sqlite_url(url: &str) -> String {
    if url.starts_with("sqlite:////") {
        // Collapse 4 slashes to 3 for absolute paths
        let rest = &url["sqlite:////".len()..];
        format!("sqlite:///{}", rest)
    } else {
        url.to_string()
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct QueryResult {
    pub rows_affected: i64,
    pub data: Vec<HashMap<String, serde_json::Value>>,
    pub error: Option<String>,
    #[serde(default)]
    pub elapsed_ms: Option<u128>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ConnectionInfo {
    pub status: String,
    pub connection_string: String,
    pub database_type: String,
    pub pool_size: usize,
    pub max_connections: u32,
    pub min_connections: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TransactionInfo {
    pub id: String,
    pub status: String,
    pub created_at: String,
}

// Helper function to convert JsonValue to PyObject
fn json_to_py_object(py: Python, value: serde_json::Value) -> PyResult<PyObject> {
    match value {
        serde_json::Value::Null => Ok(py.None().into_py(py)),
        serde_json::Value::Bool(b) => Ok(b.into_py(py)),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.into_py(py))
            } else if let Some(f) = n.as_f64() {
                Ok(f.into_py(py))
            } else {
                Ok(n.to_string().into_py(py))
            }
        }
        serde_json::Value::String(s) => Ok(s.into_py(py)),
        serde_json::Value::Array(arr) => {
            let py_list = PyList::new(py, Vec::<PyObject>::new());
            for item in arr {
                let py_item = json_to_py_object(py, item)?;
                py_list.append(py_item)?;
            }
            Ok(py_list.into_py(py))
        }
        serde_json::Value::Object(obj) => {
            let py_dict = PyDict::new(py);
            for (k, v) in obj {
                let py_v = json_to_py_object(py, v)?;
                py_dict.set_item(k, py_v)?;
            }
            Ok(py_dict.into_py(py))
        }
    }
}

// Convert Python object to ParamValue (typed parameter)
fn py_to_paramvalue(py: Python, obj: &PyAny) -> PyResult<ParamValue> {
    if obj.is_none() {
        return Ok(ParamValue::Null);
    }
    // Arrays (lists) first to preserve array typing for Postgres
    if let Ok(list) = obj.downcast::<PyList>() {
        // Try to detect homogeneous types
        if list.len() == 0 {
            return Ok(ParamValue::Json(serde_json::Value::Array(vec![])));
        }
        let mut all_str = true;
        let mut all_i64 = true;
        let mut all_f64 = true;
        let mut all_bool = true;
        for v in list.iter() {
            all_str &= v.downcast::<PyString>().is_ok();
            all_i64 &= v.extract::<i64>().is_ok();
            all_f64 &= v.extract::<f64>().is_ok();
            all_bool &= v.extract::<bool>().is_ok();
        }
        if all_str {
            let mut arr = Vec::with_capacity(list.len());
            for v in list.iter() { arr.push(v.downcast::<PyString>()?.to_string_lossy().to_string()); }
            return Ok(ParamValue::ArrayStr(arr));
        }
        if all_i64 {
            let mut arr = Vec::with_capacity(list.len());
            for v in list.iter() { arr.push(v.extract::<i64>()?); }
            return Ok(ParamValue::ArrayI64(arr));
        }
        if all_f64 {
            let mut arr = Vec::with_capacity(list.len());
            for v in list.iter() { arr.push(v.extract::<f64>()?); }
            return Ok(ParamValue::ArrayF64(arr));
        }
        if all_bool {
            let mut arr = Vec::with_capacity(list.len());
            for v in list.iter() { arr.push(v.extract::<bool>()?); }
            return Ok(ParamValue::ArrayBool(arr));
        }
        // Fallback to JSON array
        let mut arr = Vec::new();
        for v in list.iter() { arr.push(py_any_to_json(py, v)?); }
        return Ok(ParamValue::Json(serde_json::Value::Array(arr)));
    }
    if let Ok(b) = obj.extract::<bool>() {
        return Ok(ParamValue::Bool(b));
    }
    if let Ok(i) = obj.extract::<i64>() {
        return Ok(ParamValue::I64(i));
    }
    if let Ok(f) = obj.extract::<f64>() {
        return Ok(ParamValue::F64(f));
    }
    if let Ok(s) = obj.downcast::<PyString>() {
        return Ok(ParamValue::Str(s.to_string_lossy().to_string()));
    }
    if let Ok(bytes) = obj.downcast::<PyBytes>() {
        return Ok(ParamValue::Bytes(bytes.as_bytes().to_vec()));
    }
    // datetime.date
    if let Ok(d) = obj.downcast::<PyD>() {
        let year: i32 = d.getattr("year")?.extract()?;
        let month: u32 = d.getattr("month")?.extract()?;
        let day: u32 = d.getattr("day")?.extract()?;
        if let Some(date) = NaiveDate::from_ymd_opt(year, month, day) {
            return Ok(ParamValue::Date(date));
        }
    }
    // datetime.time
    if let Ok(t) = obj.downcast::<PyT>() {
        let hour: u32 = t.getattr("hour")?.extract()?;
        let minute: u32 = t.getattr("minute")?.extract()?;
        let second: u32 = t.getattr("second")?.extract()?;
        let micro: u32 = t.getattr("microsecond")?.extract()?;
        if let Some(time) = NaiveTime::from_hms_micro_opt(hour, minute, second, micro) {
            return Ok(ParamValue::Time(time));
        }
    }
    // datetime.datetime
    if let Ok(dt) = obj.downcast::<PyDT>() {
        let year: i32 = dt.getattr("year")?.extract()?;
        let month: u32 = dt.getattr("month")?.extract()?;
        let day: u32 = dt.getattr("day")?.extract()?;
        let hour: u32 = dt.getattr("hour")?.extract()?;
        let minute: u32 = dt.getattr("minute")?.extract()?;
        let second: u32 = dt.getattr("second")?.extract()?;
        let micro: u32 = dt.getattr("microsecond")?.extract()?;
        if let (Some(date), Some(time)) = (
            NaiveDate::from_ymd_opt(year, month, day),
            NaiveTime::from_hms_micro_opt(hour, minute, second, micro),
        ) {
            return Ok(ParamValue::DateTime(NaiveDateTime::new(date, time)));
        }
    }
    // uuid.UUID
    if let Ok(uuid_mod) = py.import("uuid") {
        if obj.hasattr("hex")? {
            if let Ok(s) = obj.str() {
                let s = s.to_string_lossy();
                if let Ok(u) = Uuid::parse_str(&s) {
                    return Ok(ParamValue::Uuid(u));
                }
            }
            // Try obj.hex attribute
            if let Ok(hex) = obj.getattr("hex") {
                if let Ok(s) = hex.str() {
                    if let Ok(u) = Uuid::parse_str(&s.to_string_lossy()) {
                        return Ok(ParamValue::Uuid(u));
                    }
                }
            }
        }
        let _ = uuid_mod;
    }
    // decimal.Decimal
    if let Ok(decimal_mod) = py.import("decimal") {
        if let Ok(cls) = decimal_mod.getattr("Decimal") {
            if obj.is_instance(cls)? {
                let s = obj.str()?.to_string_lossy().to_string();
                if let Ok(d) = s.parse::<Decimal>() {
                    return Ok(ParamValue::Dec(d));
                }
            }
        }
        let _ = decimal_mod;
    }
    // JSON-like mapping/list fallback
    if let Ok(dict) = obj.downcast::<PyDict>() {
        let mut m = serde_json::Map::new();
        for (k, v) in dict.iter() {
            let key = k.str()?.to_string_lossy().to_string();
            let val = py_any_to_json(py, v)?;
            m.insert(key, val);
        }
        return Ok(ParamValue::Json(serde_json::Value::Object(m)));
    }
    // default: string repr
    Ok(ParamValue::Str(obj.str()?.to_string_lossy().to_string()))
}

fn py_any_to_json(py: Python, obj: &PyAny) -> PyResult<serde_json::Value> {
    if obj.is_none() { return Ok(serde_json::Value::Null); }
    if let Ok(b) = obj.extract::<bool>() { return Ok(serde_json::Value::Bool(b)); }
    if let Ok(i) = obj.extract::<i64>() { return Ok(serde_json::Value::Number(i.into())); }
    if let Ok(f) = obj.extract::<f64>() {
        return Ok(serde_json::Number::from_f64(f).map(serde_json::Value::Number).unwrap_or(serde_json::Value::Null));
    }
    if let Ok(s) = obj.downcast::<PyString>() { return Ok(serde_json::Value::String(s.to_string_lossy().to_string())); }
    if let Ok(d) = obj.downcast::<PyDict>() {
        let mut m = serde_json::Map::new();
        for (k, v) in d.iter() {
            let key = k.str()?.to_string_lossy().to_string();
            let val = py_any_to_json(py, v)?;
            m.insert(key, val);
        }
        return Ok(serde_json::Value::Object(m));
    }
    if let Ok(l) = obj.downcast::<PyList>() {
        let mut arr = Vec::new();
        for v in l.iter() { arr.push(py_any_to_json(py, v)?); }
        return Ok(serde_json::Value::Array(arr));
    }
    Ok(serde_json::Value::String(obj.str()?.to_string_lossy().to_string()))
}

// Unified database pool enum
pub enum DatabasePool {
    Postgres(Arc<PgPool>),
    MySQL(Arc<MySqlPool>),
    SQLite(Arc<SqlitePool>),
}

impl DatabasePool {
    async fn execute_query(&self, sql: &str, params: &[ParamValue]) -> Result<QueryResult, OxenError> {
        match self {
            DatabasePool::Postgres(pool) => execute_postgres_query_typed(pool, sql, params).await,
            DatabasePool::MySQL(pool) => execute_mysql_query_typed(pool, sql, params).await,
            DatabasePool::SQLite(pool) => execute_sqlite_query_typed(pool, sql, params).await,
        }
    }

    async fn execute_many(&self, sql: &str, params_list: &[Vec<ParamValue>]) -> Result<QueryResult, OxenError> {
        match self {
            DatabasePool::Postgres(pool) => execute_postgres_many_typed(pool, sql, params_list).await,
            DatabasePool::MySQL(pool) => execute_mysql_many_typed(pool, sql, params_list).await,
            DatabasePool::SQLite(pool) => execute_sqlite_many_typed(pool, sql, params_list).await,
        }
    }
}

// ---- Typed parameter representation ----
#[derive(Debug, Clone)]
pub enum ParamValue {
    Null,
    Bool(bool),
    I64(i64),
    F64(f64),
    Str(String),
    Bytes(Vec<u8>),
    Uuid(Uuid),
    Dec(Decimal),
    Json(serde_json::Value),
    Date(NaiveDate),
    Time(NaiveTime),
    DateTime(NaiveDateTime),
    ArrayStr(Vec<String>),
    ArrayI64(Vec<i64>),
    ArrayF64(Vec<f64>),
    ArrayBool(Vec<bool>),
}

// ---- Placeholder normalization for Postgres ----
fn normalize_placeholders_for_postgres(sql: &str, num_params: usize) -> String {
    // Replace unquoted '?' with $1..$n
    let mut out = String::with_capacity(sql.len() + num_params * 2);
    let mut in_single = false;
    let mut in_double = false;
    let mut idx = 1usize;
    let mut chars = sql.chars().peekable();
    while let Some(c) = chars.next() {
        match c {
            '\'' => {
                out.push(c);
                in_single = !in_single && !in_double || (in_single && false);
            }
            '"' => {
                out.push(c);
                in_double = !in_double && !in_single || (in_double && false);
            }
            '?' if !in_single && !in_double => {
                if idx <= num_params {
                    out.push('$');
                    out.push_str(&idx.to_string());
                    idx += 1;
                } else {
                    out.push('?');
                }
            }
            _ => out.push(c),
        }
    }
    out
}

// ---- Typed binders ----
fn bind_postgres_param<'q>(query: Query<'q, Postgres, PgArguments>, param: &'q ParamValue) -> Query<'q, Postgres, PgArguments> {
    match param {
        ParamValue::Null => query.bind::<Option<i32>>(None),
        ParamValue::Bool(v) => query.bind(*v),
        ParamValue::I64(v) => query.bind(*v),
        ParamValue::F64(v) => query.bind(*v),
        ParamValue::Str(s) => query.bind(s),
        ParamValue::Bytes(b) => query.bind(b),
        ParamValue::Uuid(u) => query.bind(*u),
        ParamValue::Dec(d) => query.bind(*d),
        ParamValue::Json(j) => query.bind(sqlx::types::Json(j)),
        ParamValue::Date(d) => query.bind(*d),
        ParamValue::Time(t) => query.bind(*t),
        ParamValue::DateTime(dt) => query.bind(*dt),
        ParamValue::ArrayStr(v) => query.bind(v),
        ParamValue::ArrayI64(v) => query.bind(v),
        ParamValue::ArrayF64(v) => query.bind(v),
        ParamValue::ArrayBool(v) => query.bind(v),
    }
}

fn bind_mysql_param<'q>(query: Query<'q, MySql, MySqlArguments>, param: &'q ParamValue) -> Query<'q, MySql, MySqlArguments> {
    match param {
        ParamValue::Null => query.bind::<Option<i32>>(None),
        ParamValue::Bool(v) => query.bind(*v),
        ParamValue::I64(v) => query.bind(*v),
        ParamValue::F64(v) => query.bind(*v),
        ParamValue::Str(s) => query.bind(s),
        ParamValue::Bytes(b) => query.bind(b),
        ParamValue::Uuid(u) => query.bind(u.to_string()), // MySQL: store as string
        ParamValue::Dec(d) => query.bind(d.to_string()),
        ParamValue::Json(j) => query.bind(serde_json::to_string(j).unwrap_or_default()),
        ParamValue::Date(d) => query.bind(d.to_string()),
        ParamValue::Time(t) => query.bind(t.to_string()),
        ParamValue::DateTime(dt) => query.bind(dt.to_string()),
        ParamValue::ArrayStr(v) => query.bind(serde_json::to_string(v).unwrap_or_default()),
        ParamValue::ArrayI64(v) => query.bind(serde_json::to_string(v).unwrap_or_default()),
        ParamValue::ArrayF64(v) => query.bind(serde_json::to_string(v).unwrap_or_default()),
        ParamValue::ArrayBool(v) => query.bind(serde_json::to_string(v).unwrap_or_default()),
    }
}

fn bind_sqlite_param<'q>(query: Query<'q, Sqlite, SqliteArguments<'q>>, param: &'q ParamValue) -> Query<'q, Sqlite, SqliteArguments<'q>> {
    match param {
        ParamValue::Null => query.bind::<Option<i32>>(None),
        ParamValue::Bool(v) => query.bind(*v as i64), // booleans as integers
        ParamValue::I64(v) => query.bind(*v),
        ParamValue::F64(v) => query.bind(*v),
        ParamValue::Str(s) => query.bind(s),
        ParamValue::Bytes(b) => query.bind(b),
        ParamValue::Uuid(u) => query.bind(u.to_string()),
        ParamValue::Dec(d) => query.bind(d.to_string()),
        ParamValue::Json(j) => query.bind(serde_json::to_string(j).unwrap_or_default()),
        ParamValue::Date(d) => query.bind(d.to_string()),
        ParamValue::Time(t) => query.bind(t.to_string()),
        ParamValue::DateTime(dt) => query.bind(dt.to_string()),
        ParamValue::ArrayStr(v) => query.bind(serde_json::to_string(v).unwrap_or_default()),
        ParamValue::ArrayI64(v) => query.bind(serde_json::to_string(v).unwrap_or_default()),
        ParamValue::ArrayF64(v) => query.bind(serde_json::to_string(v).unwrap_or_default()),
        ParamValue::ArrayBool(v) => query.bind(serde_json::to_string(v).unwrap_or_default()),
    }
}

// Postgres-specific query execution (typed)
async fn execute_postgres_query_typed(pool: &PgPool, sql: &str, params: &[ParamValue]) -> Result<QueryResult, OxenError> {
    let start_time = Instant::now();
    let sql_trimmed = sql.trim().to_lowercase();
    // Normalize placeholders if needed
    let sql_to_run = if sql.contains('?') { normalize_placeholders_for_postgres(sql, params.len()) } else { sql.to_string() };

    if sql_trimmed.starts_with("select") {
        let mut query = sqlx::query(&sql_to_run);
        for param in params.iter() {
            query = bind_postgres_param(query, param);
        }
        
        let rows = query.fetch_all(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        let mut data = Vec::new();
        for row in rows.iter() {
            let mut map = HashMap::new();
            for (i, col) in row.columns().iter().enumerate() {
                let col_name = col.name();
                let value = extract_postgres_value(row, i)?;
                map.insert(col_name.to_string(), value);
            }
            data.push(map);
        }
        
        Ok(QueryResult { rows_affected: data.len() as i64, data, error: None, elapsed_ms: Some(start_time.elapsed().as_millis()) })
    } else {
        let mut query = sqlx::query(&sql_to_run);
        for param in params.iter() {
            query = bind_postgres_param(query, param);
        }
        
        let result = query.execute(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        // If query contains RETURNING, fetch rows instead of only rows_affected
        if sql_trimmed.contains(" returning ") {
            let mut query = sqlx::query(&sql_to_run);
            for param in params.iter() { query = bind_postgres_param(query, param); }
            let rows = query.fetch_all(pool).await.map_err(OxenError::QueryError)?;
            let mut data = Vec::new();
            for row in rows.iter() {
                let mut map = HashMap::new();
                for (i, col) in row.columns().iter().enumerate() {
                    let col_name = col.name();
                    let value = extract_postgres_value(row, i)?;
                    map.insert(col_name.to_string(), value);
                }
                data.push(map);
            }
            Ok(QueryResult { rows_affected: data.len() as i64, data, error: None, elapsed_ms: Some(start_time.elapsed().as_millis()) })
        } else {
            Ok(QueryResult { rows_affected: result.rows_affected() as i64, data: Vec::new(), error: None, elapsed_ms: Some(start_time.elapsed().as_millis()) })
        }
    }
}

// MySQL-specific query execution (typed)
async fn execute_mysql_query_typed(pool: &MySqlPool, sql: &str, params: &[ParamValue]) -> Result<QueryResult, OxenError> {
    let start_time = Instant::now();
    let sql_trimmed = sql.trim().to_lowercase();
    
    if sql_trimmed.starts_with("select") {
        let mut query = sqlx::query(sql);
        for param in params.iter() {
            query = bind_mysql_param(query, param);
        }
        
        let rows = query.fetch_all(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        let mut data = Vec::new();
        for row in rows.iter() {
            let mut map = HashMap::new();
            for (i, col) in row.columns().iter().enumerate() {
                let col_name = col.name();
                let value = extract_mysql_value(row, i)?;
                map.insert(col_name.to_string(), value);
            }
            data.push(map);
        }
        
        Ok(QueryResult { rows_affected: data.len() as i64, data, error: None, elapsed_ms: Some(start_time.elapsed().as_millis()) })
    } else {
        let mut query = sqlx::query(sql);
        for param in params.iter() {
            query = bind_mysql_param(query, param);
        }
        
        let result = query.execute(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        Ok(QueryResult { rows_affected: result.rows_affected() as i64, data: Vec::new(), error: None, elapsed_ms: Some(start_time.elapsed().as_millis()) })
    }
}

// SQLite-specific query execution (typed)
async fn execute_sqlite_query_typed(pool: &SqlitePool, sql: &str, params: &[ParamValue]) -> Result<QueryResult, OxenError> {
    let start_time = Instant::now();
    let sql_trimmed = sql.trim().to_lowercase();
    
    if sql_trimmed.starts_with("select") {
        let mut query = sqlx::query(sql);
        for param in params.iter() {
            query = bind_sqlite_param(query, param);
        }
        
        let rows = query.fetch_all(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        let mut data = Vec::new();
        for row in rows.iter() {
            let mut map = HashMap::new();
            for (i, col) in row.columns().iter().enumerate() {
                let col_name = col.name();
                let value = extract_sqlite_value(row, i)?;
                map.insert(col_name.to_string(), value);
            }
            data.push(map);
        }
        
        Ok(QueryResult { rows_affected: data.len() as i64, data, error: None, elapsed_ms: Some(start_time.elapsed().as_millis()) })
    } else {
        let mut query = sqlx::query(sql);
        for param in params.iter() {
            query = bind_sqlite_param(query, param);
        }
        
        let result = query.execute(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        Ok(QueryResult { rows_affected: result.rows_affected() as i64, data: Vec::new(), error: None, elapsed_ms: Some(start_time.elapsed().as_millis()) })
    }
}

// Value extraction functions
fn extract_postgres_value(row: &sqlx::postgres::PgRow, i: usize) -> Result<serde_json::Value, OxenError> {
    if row.try_get_raw(i).map(|raw| raw.is_null()).unwrap_or(true) {
        return Ok(serde_json::Value::Null);
    }
    
    if let Ok(v) = row.try_get::<String, _>(i) {
        Ok(serde_json::Value::String(v))
    } else if let Ok(v) = row.try_get::<i64, _>(i) {
        Ok(serde_json::Value::Number(v.into()))
    } else if let Ok(v) = row.try_get::<f64, _>(i) {
        Ok(serde_json::Number::from_f64(v).map(|n| serde_json::Value::Number(n)).unwrap_or(serde_json::Value::Null))
    } else if let Ok(v) = row.try_get::<bool, _>(i) {
        Ok(serde_json::Value::Bool(v))
    } else {
        Ok(serde_json::Value::Null)
    }
}

fn extract_mysql_value(row: &sqlx::mysql::MySqlRow, i: usize) -> Result<serde_json::Value, OxenError> {
    if row.try_get_raw(i).map(|raw| raw.is_null()).unwrap_or(true) {
        return Ok(serde_json::Value::Null);
    }
    
    if let Ok(v) = row.try_get::<String, _>(i) {
        Ok(serde_json::Value::String(v))
    } else if let Ok(v) = row.try_get::<i64, _>(i) {
        Ok(serde_json::Value::Number(v.into()))
    } else if let Ok(v) = row.try_get::<f64, _>(i) {
        Ok(serde_json::Number::from_f64(v).map(|n| serde_json::Value::Number(n)).unwrap_or(serde_json::Value::Null))
    } else if let Ok(v) = row.try_get::<bool, _>(i) {
        Ok(serde_json::Value::Bool(v))
    } else {
        Ok(serde_json::Value::Null)
    }
}

fn extract_sqlite_value(row: &sqlx::sqlite::SqliteRow, i: usize) -> Result<serde_json::Value, OxenError> {
    if row.try_get_raw(i).map(|raw| raw.is_null()).unwrap_or(true) {
        return Ok(serde_json::Value::Null);
    }
    
    if let Ok(v) = row.try_get::<String, _>(i) {
        Ok(serde_json::Value::String(v))
    } else if let Ok(v) = row.try_get::<i64, _>(i) {
        Ok(serde_json::Value::Number(v.into()))
    } else if let Ok(v) = row.try_get::<f64, _>(i) {
        Ok(serde_json::Number::from_f64(v).map(|n| serde_json::Value::Number(n)).unwrap_or(serde_json::Value::Null))
    } else if let Ok(v) = row.try_get::<bool, _>(i) {
        Ok(serde_json::Value::Bool(v))
    } else {
        Ok(serde_json::Value::Null)
    }
}

// Execute many functions (typed)
async fn execute_postgres_many_typed(pool: &PgPool, sql: &str, params_list: &[Vec<ParamValue>]) -> Result<QueryResult, OxenError> {
    // Use a single transaction; let sqlx statement cache handle preparation
    let mut tx = pool.begin().await.map_err(OxenError::QueryError)?;
    let mut total_rows_affected = 0i64;

    // Normalize placeholders per row length as needed
    for params in params_list.iter() {
        let sql_to_run = if sql.contains('?') { normalize_placeholders_for_postgres(sql, params.len()) } else { sql.to_string() };
        let mut query = sqlx::query(&sql_to_run);
        for param in params.iter() { query = bind_postgres_param(query, param); }
        let result = query.execute(&mut *tx).await.map_err(OxenError::QueryError)?;
        total_rows_affected += result.rows_affected() as i64;
    }
    tx.commit().await.map_err(OxenError::QueryError)?;

    Ok(QueryResult { rows_affected: total_rows_affected, data: Vec::new(), error: None, elapsed_ms: None })
}

async fn execute_mysql_many_typed(pool: &MySqlPool, sql: &str, params_list: &[Vec<ParamValue>]) -> Result<QueryResult, OxenError> {
    let mut total_rows_affected = 0;
    
    for params in params_list.iter() {
        let mut query = sqlx::query(sql);
        for param in params.iter() {
            query = bind_mysql_param(query, param);
        }
        
        let result = query.execute(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        total_rows_affected += result.rows_affected() as i64;
    }
    
    Ok(QueryResult { rows_affected: total_rows_affected, data: Vec::new(), error: None, elapsed_ms: None })
}

async fn execute_sqlite_many_typed(pool: &SqlitePool, sql: &str, params_list: &[Vec<ParamValue>]) -> Result<QueryResult, OxenError> {
    let mut total_rows_affected = 0;
    
    for params in params_list.iter() {
        let mut query = sqlx::query(sql);
        for param in params.iter() {
            query = bind_sqlite_param(query, param);
        }
        
        let result = query.execute(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        total_rows_affected += result.rows_affected() as i64;
    }
    
    Ok(QueryResult { rows_affected: total_rows_affected, data: Vec::new(), error: None, elapsed_ms: None })
}

#[pyclass]
pub struct OxenEngine {
    connection_string: String,
    database_type: DatabaseType,
    pool: Option<DatabasePool>,
    max_connections: u32,
    min_connections: u32,
    runtime: Arc<Runtime>,
    is_connected: bool,
}

#[pymethods]
impl OxenEngine {
    #[new]
    fn new(connection_string: String) -> PyResult<Self> {
        let database_type = DatabaseType::from_url(&connection_string)?;
        let runtime = Arc::new(Runtime::new().unwrap());
        
        Ok(Self {
            connection_string,
            database_type,
            pool: None,
            max_connections: 10,
            min_connections: 1,
            runtime,
            is_connected: false,
        })
    }

    /// Configure connection pool settings
    fn configure_pool(&mut self, max_connections: Option<u32>, min_connections: Option<u32>) {
        if let Some(max) = max_connections {
            self.max_connections = max;
        }
        if let Some(min) = min_connections {
            self.min_connections = min;
        }
    }

    /// Check if connected to database
    fn is_connected(&self) -> bool {
        self.is_connected
    }

    /// Get connection pool status
    fn get_pool_status(&self, py: Python) -> PyResult<PyObject> {
        if !self.is_connected {
            return Err(OxenError::NotConnected.into());
        }

        let pool = self.pool.as_ref().ok_or(OxenError::NotConnected)?;
        let runtime = self.runtime.clone();
        
        let status = runtime.block_on(async {
            let (size, idle) = match pool {
                DatabasePool::Postgres(p) => (p.size(), p.num_idle()),
                DatabasePool::MySQL(p) => (p.size(), p.num_idle()),
                DatabasePool::SQLite(p) => (p.size(), p.num_idle()),
            };
            
            let used = size as usize - idle;
            
            let status_info = HashMap::from([
                ("pool_size".to_string(), serde_json::Value::Number(size.into())),
                ("idle_connections".to_string(), serde_json::Value::Number(idle.into())),
                ("used_connections".to_string(), serde_json::Value::Number(used.into())),
                ("max_connections".to_string(), serde_json::Value::Number(self.max_connections.into())),
                ("min_connections".to_string(), serde_json::Value::Number(self.min_connections.into())),
            ]);
            
            serde_json::to_value(status_info)
        }).map_err(|e| OxenError::SerializationError(e))?;

        json_to_py_object(py, status)
    }

    fn connect(&mut self, py: Python) -> PyResult<PyObject> {
        let connection_string = self.connection_string.clone();
        let database_type = self.database_type.clone();
        let max_connections = self.max_connections;
        let min_connections = self.min_connections;
        let runtime = self.runtime.clone();
        
        let pool = runtime.block_on(async {
            match database_type {
                DatabaseType::Postgres => {
                    // Enable prepared statement cache for better performance
                    let mut opts = PgConnectOptions::from_str(&connection_string)?;
                    // sqlx default is 100; bump to a higher value for ORM workloads
                    opts = opts.statement_cache_capacity(1024);
                    let pool = PgPoolOptions::new()
                        .max_connections(max_connections)
                        .min_connections(min_connections)
                        .acquire_timeout(std::time::Duration::from_secs(30))
                        .idle_timeout(std::time::Duration::from_secs(300))
                        .max_lifetime(std::time::Duration::from_secs(1800))
                        .connect_with(opts)
                        .await?;
                    Ok(DatabasePool::Postgres(Arc::new(pool)))
                }
                DatabaseType::MySQL => {
                    let pool = MySqlPoolOptions::new()
                        .max_connections(max_connections)
                        .min_connections(min_connections)
                        .acquire_timeout(std::time::Duration::from_secs(30))
                        .idle_timeout(std::time::Duration::from_secs(300))
                        .max_lifetime(std::time::Duration::from_secs(1800))
                        .connect(&connection_string)
                        .await?;
                    Ok(DatabasePool::MySQL(Arc::new(pool)))
                }
                DatabaseType::SQLite => {
                    // Normalize URL and ensure parent directory exists
                    let normalized = normalize_sqlite_url(&connection_string);
                    if let Some(path_part) = normalized.strip_prefix("sqlite:///") {
                        if !path_part.starts_with(":memory:") && !path_part.starts_with("file::memory:") {
                            if let Some(parent) = Path::new(path_part).parent() {
                                let _ = fs::create_dir_all(parent);
                            }
                        }
                    }

                    let opts = sqlx::sqlite::SqliteConnectOptions::from_str(&normalized)
                        .map(|o| o.create_if_missing(true))?;

                    let pool = SqlitePoolOptions::new()
                        .max_connections(max_connections)
                        .acquire_timeout(std::time::Duration::from_secs(30))
                        .idle_timeout(std::time::Duration::from_secs(300))
                        .max_lifetime(std::time::Duration::from_secs(1800))
                        .connect_with(opts)
                        .await?;
                    Ok(DatabasePool::SQLite(Arc::new(pool)))
                }
            }
        }).map_err(|e| OxenError::ConnectionError(e))?;
        
        self.pool = Some(pool);
        self.is_connected = true;
        
        let info = ConnectionInfo {
            status: "connected".to_string(),
            connection_string: connection_string.clone(),
            database_type: format!("{:?}", database_type),
            pool_size: max_connections as usize,
            max_connections,
            min_connections,
        };
        
        let result = serde_json::to_value(info)
            .map_err(|e| OxenError::SerializationError(e))?;
        
        json_to_py_object(py, result)
    }

    fn execute_query(&self, py: Python, sql: String, params: Option<PyObject>) -> PyResult<PyObject> {
        if !self.is_connected {
            return Err(OxenError::NotConnected.into());
        }
        
        let pool = self.pool.as_ref().ok_or(OxenError::NotConnected)?;
        let runtime = self.runtime.clone();

        let params_vec: Vec<ParamValue> = if let Some(py_params) = params {
            let list: &PyList = py_params.extract(py)?;
            let mut vec = Vec::new();
            for item in list.iter() {
                vec.push(py_to_paramvalue(py, item)?);
            }
            vec
        } else {
            Vec::new()
        };

        let result = runtime.block_on(async {
            pool.execute_query(&sql, &params_vec).await
        })?;
        
        let json_result = serde_json::to_value(result)
            .map_err(|e| OxenError::SerializationError(e))?;
        
        json_to_py_object(py, json_result)
    }

    fn execute_ir_json(&self, py: Python, ir_json: String) -> PyResult<PyObject> {
        if !self.is_connected {
            return Err(OxenError::NotConnected.into());
        }

        let pool = self.pool.as_ref().ok_or(OxenError::NotConnected)?;
        let runtime = self.runtime.clone();

        // Parse IR and build SQL + typed params
        let ir: QueryIR = serde_json::from_str(&ir_json)
            .map_err(|e| OxenError::SerializationError(e))?;
        // If this is a large insert-many, use chunked path
        let result = if ir.action.as_deref().unwrap_or("select") == "insert" && ir.rows.as_ref().map(|v| v.len()).unwrap_or(0) > 500 {
            let chunk_size = 500;
            runtime.block_on(async { execute_insert_rows_chunked(pool, &ir, chunk_size).await })?
        } else {
            let (sql, params) = build_sql_from_ir(&ir);
            runtime.block_on(async { pool.execute_query(&sql, &params).await })?
        };

        let json_result = serde_json::to_value(result)
            .map_err(|e| OxenError::SerializationError(e))?;

        json_to_py_object(py, json_result)
    }

    fn execute_many(&self, py: Python, sql: String, params_list: Vec<Vec<PyObject>>) -> PyResult<PyObject> {
        if !self.is_connected {
            return Err(OxenError::NotConnected.into());
        }
        
        let pool = self.pool.as_ref().ok_or(OxenError::NotConnected)?;
        let runtime = self.runtime.clone();
        
        let mut converted_params_list: Vec<Vec<ParamValue>> = Vec::new();
        for py_params in params_list {
            let mut vec: Vec<ParamValue> = Vec::new();
            for item in py_params.iter() {
                vec.push(py_to_paramvalue(py, item.as_ref(py))?);
            }
            converted_params_list.push(vec);
        }
        
        let result = runtime.block_on(async {
            pool.execute_many(&sql, &converted_params_list).await
        })?;
        
        let json_result = serde_json::to_value(result)
            .map_err(|e| OxenError::SerializationError(e))?;
        
        json_to_py_object(py, json_result)
    }

    fn begin_transaction(&self, py: Python) -> PyResult<PyObject> {
        if !self.is_connected {
            return Err(OxenError::NotConnected.into());
        }
        
        // For now, we'll create a transaction info but not store the actual transaction
        // due to lifetime issues with storing sqlx::Transaction across the FFI boundary
        // In a future version, we'll implement a transaction manager
        let transaction_id = Uuid::new_v4().to_string();
        let created_at = chrono::Utc::now().to_rfc3339();
        
        let info = TransactionInfo {
            id: transaction_id.clone(),
            status: "active".to_string(),
            created_at,
        };
        
        let result = serde_json::to_value(info)
            .map_err(|e| OxenError::SerializationError(e))?;
        
        json_to_py_object(py, result)
    }

    fn close(&self, py: Python) -> PyResult<PyObject> {
        if let Some(pool) = &self.pool {
            let runtime = self.runtime.clone();
            runtime.block_on(async {
                match pool {
                    DatabasePool::Postgres(p) => p.close().await,
                    DatabasePool::MySQL(p) => p.close().await,
                    DatabasePool::SQLite(p) => p.close().await,
                }
            });
        }
        
        let info = HashMap::from([
            ("status".to_string(), serde_json::Value::String("closed".to_string())),
            ("was_connected".to_string(), serde_json::Value::Bool(self.is_connected)),
        ]);
        
        let result = serde_json::to_value(info)
            .map_err(|e| OxenError::SerializationError(e))?;
        
        json_to_py_object(py, result)
    }
}

#[pyclass]
pub struct OxenTransaction {
    engine: Py<OxenEngine>,
    transaction_id: String,
    is_active: bool,
}

#[pymethods]
impl OxenTransaction {
    #[new]
    fn new(engine: Py<OxenEngine>, transaction_id: String) -> Self {
        Self { 
            engine, 
            transaction_id, 
            is_active: true 
        }
    }

    fn commit(&mut self, py: Python) -> PyResult<PyObject> {
        let transaction_id = self.transaction_id.clone();
        
        let info = HashMap::from([
            ("transaction_id".to_string(), serde_json::Value::String(transaction_id)),
            ("status".to_string(), serde_json::Value::String("committed".to_string())),
        ]);
        
        let result = serde_json::to_value(info)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        json_to_py_object(py, result)
    }

    fn rollback(&mut self, py: Python) -> PyResult<PyObject> {
        let transaction_id = self.transaction_id.clone();
        
        let info = HashMap::from([
            ("transaction_id".to_string(), serde_json::Value::String(transaction_id)),
            ("status".to_string(), serde_json::Value::String("rolled_back".to_string())),
        ]);
        
        let result = serde_json::to_value(info)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        json_to_py_object(py, result)
    }
}

#[pyfunction]
fn read_file(path: &str) -> PyResult<Vec<u8>> {
    let mut file = fs::File::open(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    let mut contents = Vec::new();
    file.read_to_end(&mut contents)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    Ok(contents)
}

#[pyfunction]
fn write_file(path: &str, data: &[u8]) -> PyResult<()> {
    let mut file = fs::File::create(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    file.write_all(data)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    Ok(())
}

#[pyfunction]
fn file_exists(path: &str) -> PyResult<bool> {
    Ok(Path::new(path).exists())
}

#[pyfunction]
fn delete_file(path: &str) -> PyResult<()> {
    fs::remove_file(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    Ok(())
}

#[pyfunction]
fn get_file_size(path: &str) -> PyResult<u64> {
    let metadata = fs::metadata(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    Ok(metadata.len())
}

#[pyfunction]
fn create_directory(path: &str) -> PyResult<()> {
    fs::create_dir_all(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    Ok(())
}

#[pyfunction]
fn list_directory(path: &str) -> PyResult<Vec<String>> {
    let entries = fs::read_dir(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    let mut files = Vec::new();
    for entry in entries {
        if let Ok(entry) = entry {
            if let Ok(name) = entry.file_name().into_string() {
                files.push(name);
            }
        }
    }
    
    Ok(files)
}

// Image operations
#[pyfunction]
fn load_image(path: &str) -> PyResult<Vec<u8>> {
    let img = image::open(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    let mut buffer = Vec::new();
    img.write_to(&mut std::io::Cursor::new(&mut buffer), image::ImageFormat::Png)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    Ok(buffer)
}

#[pyfunction]
fn save_image(path: &str, data: &PyAny) -> PyResult<()> {
    // Accept both bytes and list[int]
    let bytes: Vec<u8> = if let Ok(pybytes) = data.downcast::<PyBytes>() {
        pybytes.as_bytes().to_vec()
    } else if let Ok(pylist) = data.downcast::<PyList>() {
        let mut v = Vec::with_capacity(pylist.len());
        for item in pylist.iter() {
            let b: u8 = item.extract()?;
            v.push(b);
        }
        v
    } else {
        return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>("Expected bytes or list[int]"));
    };

    let img = image::load_from_memory(&bytes)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    img.save(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    Ok(())
}

#[pyfunction]
fn resize_image(data: &[u8], width: u32, height: u32) -> PyResult<Vec<u8>> {
    let img = image::load_from_memory(data)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    let resized = resize(&img, width, height, image::imageops::FilterType::Lanczos3);
    
    let mut buffer = Vec::new();
    resized.write_to(&mut std::io::Cursor::new(&mut buffer), image::ImageFormat::Png)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    Ok(buffer)
}

#[pyfunction]
fn blur_image(data: &[u8], sigma: f32) -> PyResult<Vec<u8>> {
    let img = image::load_from_memory(data)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    let blurred = blur(&img, sigma);
    
    let mut buffer = Vec::new();
    blurred.write_to(&mut std::io::Cursor::new(&mut buffer), image::ImageFormat::Png)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    Ok(buffer)
}

#[pyfunction]
fn brighten_image(data: &[u8], value: i32) -> PyResult<Vec<u8>> {
    let img = image::load_from_memory(data)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    let brightened = brighten(&img, value);
    
    let mut buffer = Vec::new();
    brightened.write_to(&mut std::io::Cursor::new(&mut buffer), image::ImageFormat::Png)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    Ok(buffer)
}

#[pyfunction]
fn contrast_image(data: &[u8], contrast_value: f32) -> PyResult<Vec<u8>> {
    let img = image::load_from_memory(data)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    let contrasted = contrast(&img, contrast_value);
    
    let mut buffer = Vec::new();
    contrasted.write_to(&mut std::io::Cursor::new(&mut buffer), image::ImageFormat::Png)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    Ok(buffer)
}

#[pyfunction]
fn get_image_info(data: &[u8]) -> PyResult<(u32, u32, String)> {
    let img = image::load_from_memory(data)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    let (width, height) = img.dimensions();
    let format = match img {
        DynamicImage::ImageRgb8(_) => "RGB",
        DynamicImage::ImageRgba8(_) => "RGBA",
        DynamicImage::ImageLuma8(_) => "L",
        DynamicImage::ImageLumaA8(_) => "LA",
        _ => "Unknown",
    };
    
    Ok((width, height, format.to_string()))
}

#[pyfunction]
fn convert_image_format(data: &[u8], format: &str) -> PyResult<Vec<u8>> {
    let img = image::load_from_memory(data)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    let image_format = match format.to_lowercase().as_str() {
        "png" => image::ImageFormat::Png,
        "jpg" | "jpeg" => image::ImageFormat::Jpeg,
        "gif" => image::ImageFormat::Gif,
        "bmp" => image::ImageFormat::Bmp,
        "webp" => image::ImageFormat::WebP,
        _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Unsupported format")),
    };
    
    let mut buffer = Vec::new();
    img.write_to(&mut std::io::Cursor::new(&mut buffer), image_format)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    Ok(buffer)
}

#[pyfunction]
fn create_thumbnail(data: &[u8], max_size: u32) -> PyResult<Vec<u8>> {
    let img = image::load_from_memory(data)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    let (width, height) = img.dimensions();
    let (new_width, new_height) = if width > height {
        (max_size, (height * max_size) / width)
    } else {
        ((width * max_size) / height, max_size)
    };
    
    let thumbnail = resize(&img, new_width, new_height, image::imageops::FilterType::Lanczos3);
    
    let mut buffer = Vec::new();
    thumbnail.write_to(&mut std::io::Cursor::new(&mut buffer), image::ImageFormat::Png)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    
    Ok(buffer)
}

#[pymodule]
fn oxen_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<OxenEngine>()?;
    m.add_class::<OxenTransaction>()?;
    
    // File operations
    m.add_function(wrap_pyfunction!(read_file, m)?)?;
    m.add_function(wrap_pyfunction!(write_file, m)?)?;
    m.add_function(wrap_pyfunction!(file_exists, m)?)?;
    m.add_function(wrap_pyfunction!(delete_file, m)?)?;
    m.add_function(wrap_pyfunction!(get_file_size, m)?)?;
    m.add_function(wrap_pyfunction!(create_directory, m)?)?;
    m.add_function(wrap_pyfunction!(list_directory, m)?)?;
    
    // Image operations
    m.add_function(wrap_pyfunction!(load_image, m)?)?;
    m.add_function(wrap_pyfunction!(save_image, m)?)?;
    m.add_function(wrap_pyfunction!(resize_image, m)?)?;
    m.add_function(wrap_pyfunction!(blur_image, m)?)?;
    m.add_function(wrap_pyfunction!(brighten_image, m)?)?;
    m.add_function(wrap_pyfunction!(contrast_image, m)?)?;
    m.add_function(wrap_pyfunction!(get_image_info, m)?)?;
    m.add_function(wrap_pyfunction!(convert_image_format, m)?)?;
    m.add_function(wrap_pyfunction!(create_thumbnail, m)?)?;
    // Query builder
    m.add_function(wrap_pyfunction!(build_sql_json, m)?)?;
    // Query builder already exposes build_sql_json; execute_ir_json is a method on OxenEngine
    
    Ok(())
} 
//! OxenORM Rust Backend
//!
//! This crate provides the high-performance Rust backend for OxenORM,
//! handling database operations, connection pooling, and query execution.

use pyo3::prelude::*;
use pyo3::types::{PyList, PyDict, PyBytes, PyString};
use std::collections::HashMap;
use sqlx::{
    PgPool, postgres::PgPoolOptions, 
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
use image::{DynamicImage, GenericImageView};
use image::imageops::{resize, blur, brighten, contrast};
use chrono::{NaiveDate, NaiveDateTime, NaiveTime};
use rust_decimal::Decimal;
use pyo3::types::PyDateTime as PyDT;
use pyo3::types::PyDate as PyD;
use pyo3::types::PyTime as PyT;
use std::str::FromStr;

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
        drop(uuid_mod);
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
        drop(decimal_mod);
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
    if let Ok(list) = obj.downcast::<PyList>() {
        let mut arr = Vec::new();
        for v in list.iter() {
            arr.push(py_any_to_json(py, v)?);
        }
        return Ok(ParamValue::Json(serde_json::Value::Array(arr)));
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
fn bind_postgres_param<'q>(mut query: Query<'q, Postgres, PgArguments>, param: &'q ParamValue) -> Query<'q, Postgres, PgArguments> {
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
    }
}

fn bind_mysql_param<'q>(mut query: Query<'q, MySql, MySqlArguments>, param: &'q ParamValue) -> Query<'q, MySql, MySqlArguments> {
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
    }
}

fn bind_sqlite_param<'q>(mut query: Query<'q, Sqlite, SqliteArguments<'q>>, param: &'q ParamValue) -> Query<'q, Sqlite, SqliteArguments<'q>> {
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
    }
}

// Postgres-specific query execution (typed)
async fn execute_postgres_query_typed(pool: &PgPool, sql: &str, params: &[ParamValue]) -> Result<QueryResult, OxenError> {
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
        
        Ok(QueryResult {
            rows_affected: data.len() as i64,
            data,
            error: None,
        })
    } else {
        let mut query = sqlx::query(&sql_to_run);
        for param in params.iter() {
            query = bind_postgres_param(query, param);
        }
        
        let result = query.execute(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        Ok(QueryResult {
            rows_affected: result.rows_affected() as i64,
            data: Vec::new(),
            error: None,
        })
    }
}

// MySQL-specific query execution (typed)
async fn execute_mysql_query_typed(pool: &MySqlPool, sql: &str, params: &[ParamValue]) -> Result<QueryResult, OxenError> {
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
        
        Ok(QueryResult {
            rows_affected: data.len() as i64,
            data,
            error: None,
        })
    } else {
        let mut query = sqlx::query(sql);
        for param in params.iter() {
            query = bind_mysql_param(query, param);
        }
        
        let result = query.execute(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        Ok(QueryResult {
            rows_affected: result.rows_affected() as i64,
            data: Vec::new(),
            error: None,
        })
    }
}

// SQLite-specific query execution (typed)
async fn execute_sqlite_query_typed(pool: &SqlitePool, sql: &str, params: &[ParamValue]) -> Result<QueryResult, OxenError> {
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
        
        Ok(QueryResult {
            rows_affected: data.len() as i64,
            data,
            error: None,
        })
    } else {
        let mut query = sqlx::query(sql);
        for param in params.iter() {
            query = bind_sqlite_param(query, param);
        }
        
        let result = query.execute(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        Ok(QueryResult {
            rows_affected: result.rows_affected() as i64,
            data: Vec::new(),
            error: None,
        })
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
    let mut total_rows_affected = 0;
    
    for params in params_list.iter() {
        let sql_to_run = if sql.contains('?') { normalize_placeholders_for_postgres(sql, params.len()) } else { sql.to_string() };
        let mut query = sqlx::query(&sql_to_run);
        for param in params.iter() {
            query = bind_postgres_param(query, param);
        }
        
        let result = query.execute(pool).await
            .map_err(|e| OxenError::QueryError(e))?;
        
        total_rows_affected += result.rows_affected() as i64;
    }
    
    Ok(QueryResult {
        rows_affected: total_rows_affected,
        data: Vec::new(),
        error: None,
    })
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
    
    Ok(QueryResult {
        rows_affected: total_rows_affected,
        data: Vec::new(),
        error: None,
    })
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
    
    Ok(QueryResult {
        rows_affected: total_rows_affected,
        data: Vec::new(),
        error: None,
    })
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
                    let pool = PgPoolOptions::new()
                        .max_connections(max_connections)
                        .min_connections(min_connections)
                        .acquire_timeout(std::time::Duration::from_secs(30))
                        .idle_timeout(std::time::Duration::from_secs(300))
                        .max_lifetime(std::time::Duration::from_secs(1800))
                        .connect(&connection_string)
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
    
    Ok(())
} 
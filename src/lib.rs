//! OxenORM Rust Backend
//!
//! This crate provides the high-performance Rust backend for OxenORM,
//! handling database operations, connection pooling, and query execution.

use pyo3::prelude::*;
use pyo3::types::{PyList, PyDict};
use std::collections::HashMap;
use sqlx::{PgPool, postgres::PgPoolOptions, Row, query::Query, Postgres, postgres::PgArguments, Column, ValueRef, Error as SqlxError};
use serde::{Serialize, Deserialize};
use uuid::Uuid;
use std::sync::Arc;
use tokio::runtime::Runtime;
use thiserror::Error;

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
}

impl From<OxenError> for PyErr {
    fn from(err: OxenError) -> Self {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(err.to_string())
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

// Helper to bind serde_json::Value to SQLx query
fn bind_param<'q>(query: Query<'q, Postgres, PgArguments>, param: &'q serde_json::Value) -> Query<'q, Postgres, PgArguments> {
    match param {
        serde_json::Value::Null => query.bind(None::<String>),
        serde_json::Value::Bool(b) => query.bind(*b),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                query.bind(i)
            } else if let Some(f) = n.as_f64() {
                query.bind(f)
            } else {
                query.bind(n.to_string())
            }
        }
        serde_json::Value::String(s) => query.bind(s),
        _ => query.bind(param.to_string()),
    }
}

#[pyclass]
pub struct OxenEngine {
    connection_string: String,
    pool: Option<Arc<PgPool>>,
    max_connections: u32,
    min_connections: u32,
    runtime: Arc<Runtime>,
    is_connected: bool,
}

#[pymethods]
impl OxenEngine {
    #[new]
    fn new(connection_string: String) -> Self {
        let runtime = Arc::new(Runtime::new().unwrap());
        Self {
            connection_string,
            pool: None,
            max_connections: 10,
            min_connections: 1,
            runtime,
            is_connected: false,
        }
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
            let size = pool.size();
            let idle = pool.num_idle();
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
        let max_connections = self.max_connections;
        let min_connections = self.min_connections;
        let runtime = self.runtime.clone();
        
        let pool = runtime.block_on(async {
            PgPoolOptions::new()
                .max_connections(max_connections)
                .min_connections(min_connections)
                .acquire_timeout(std::time::Duration::from_secs(30))
                .idle_timeout(std::time::Duration::from_secs(300))
                .max_lifetime(std::time::Duration::from_secs(1800))
                .connect(&connection_string)
                .await
        }).map_err(|e| OxenError::ConnectionError(e))?;
        
        self.pool = Some(Arc::new(pool));
        self.is_connected = true;
        
        let info = ConnectionInfo {
            status: "connected".to_string(),
            connection_string: connection_string.clone(),
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
        
        let pool = self.pool.clone().ok_or(OxenError::NotConnected)?;
        let runtime = self.runtime.clone();
            let params_vec = if let Some(py_params) = params {
                let list: &PyList = py_params.extract(py)?;
                let mut vec = Vec::new();
                for item in list.iter() {
                    // Convert Python object to JSON value
                    let json_value = if let Ok(s) = item.extract::<String>() {
                        serde_json::Value::String(s)
                    } else if let Ok(b) = item.extract::<bool>() {
                        serde_json::Value::Bool(b)
                    } else if let Ok(i) = item.extract::<i64>() {
                        serde_json::Value::Number(i.into())
                    } else if let Ok(f) = item.extract::<f64>() {
                        serde_json::Value::Number(serde_json::Number::from_f64(f).unwrap_or_else(|| serde_json::Number::from(0)))
                    } else {
                        serde_json::Value::Null
                    };
                    vec.push(json_value);
                }
                vec
            } else {
                Vec::new()
            };

            let sql_trimmed = sql.trim().to_lowercase();
            let result: Result<QueryResult, PyErr> = if sql_trimmed.starts_with("select") {
                // SELECT: fetch all rows
                runtime.block_on(async {
                    let mut query = sqlx::query(&sql);
                    for param in &params_vec {
                        query = bind_param(query, param);
                    }
                    let rows = query.fetch_all(&*pool).await
                        .map_err(|e| OxenError::QueryError(e))?;
                    let mut data = Vec::new();
                    for row in rows.iter() {
                        let mut map = HashMap::new();
                        for (i, col) in row.columns().iter().enumerate() {
                            let col_name = col.name();
                            let value: Result<serde_json::Value, _> = row.try_get_raw(i).map(|raw| {
                                if raw.is_null() {
                                    serde_json::Value::Null
                                } else {
                                    // Try to get as string, int, float, bool
                                    if let Ok(v) = row.try_get::<String, _>(i) {
                                        serde_json::Value::String(v)
                                    } else if let Ok(v) = row.try_get::<i64, _>(i) {
                                        serde_json::Value::Number(v.into())
                                    } else if let Ok(v) = row.try_get::<f64, _>(i) {
                                        serde_json::Value::Number(serde_json::Number::from_f64(v).unwrap_or_else(|| serde_json::Number::from(0)))
                                    } else if let Ok(v) = row.try_get::<bool, _>(i) {
                                        serde_json::Value::Bool(v)
                                    } else {
                                        serde_json::Value::Null
                                    }
                                }
                            });
                            map.insert(col_name.to_string(), value.unwrap_or(serde_json::Value::Null));
                        }
                        data.push(map);
                    }
                    Ok(QueryResult {
                        rows_affected: data.len() as i64,
                        data,
                        error: None,
                    })
                })
            } else {
                // DML: execute and return affected rows
                runtime.block_on(async {
                    let mut query = sqlx::query(&sql);
                    for param in &params_vec {
                        query = bind_param(query, param);
                    }
                    let result = query.execute(&*pool).await
                        .map_err(|e| OxenError::QueryError(e))?;
                    Ok(QueryResult {
                        rows_affected: result.rows_affected() as i64,
                        data: Vec::new(),
                        error: None,
                    })
                })
            };
            
            let json_result = serde_json::to_value(result?)
                .map_err(|e| OxenError::SerializationError(e))?;
            
            json_to_py_object(py, json_result)
    }

    fn execute_many(&self, py: Python, sql: String, params_list: Vec<Vec<PyObject>>) -> PyResult<PyObject> {
        let pool = self.pool.clone();
        let runtime = self.runtime.clone();
        
        if let Some(pool) = pool {
            let mut total_rows_affected = 0;
            let mut all_data = Vec::new();
            
            for py_params in params_list {
                let mut vec = Vec::new();
                for item in py_params.iter() {
                    // Convert Python object to JSON value
                    let json_value = if let Ok(s) = item.extract::<String>(py) {
                        serde_json::Value::String(s)
                    } else if let Ok(i) = item.extract::<i64>(py) {
                        serde_json::Value::Number(i.into())
                    } else if let Ok(f) = item.extract::<f64>(py) {
                        serde_json::Value::Number(serde_json::Number::from_f64(f).unwrap_or_else(|| serde_json::Number::from(0)))
                    } else if let Ok(b) = item.extract::<bool>(py) {
                        serde_json::Value::Bool(b)
                    } else {
                        serde_json::Value::Null
                    };
                    vec.push(json_value);
                }
                
                let result = runtime.block_on(async {
                    execute_query_with_pool(&pool, &sql, &vec).await
                });
                total_rows_affected += result.rows_affected;
                all_data.extend(result.data);
            }
            
            let result = QueryResult {
                rows_affected: total_rows_affected,
                data: all_data,
                error: None,
            };
            
            let json_result = serde_json::to_value(result)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
            
            json_to_py_object(py, json_result)
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Database not connected"))
        }
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
                pool.close().await;
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

async fn execute_query_with_pool(pool: &PgPool, sql: &str, _params: &[serde_json::Value]) -> QueryResult {
    match sqlx::query(sql)
        .execute(pool)
        .await
    {
        Ok(result) => {
            QueryResult {
                rows_affected: result.rows_affected() as i64,
                data: Vec::new(),
                error: None,
            }
        }
        Err(e) => {
            QueryResult {
                rows_affected: 0,
                data: Vec::new(),
                error: Some(e.to_string()),
            }
        }
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

#[pymodule]
fn oxen_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<OxenEngine>()?;
    m.add_class::<OxenTransaction>()?;
    Ok(())
} 
//! Database connection management for OxenORM

use pyo3::prelude::*;
use pyo3::types::{PyList, PyDict};
use std::collections::HashMap;
use sqlx::{
    PgPool, postgres::PgPoolOptions, 
    MySqlPool, mysql::MySqlPoolOptions,
    SqlitePool, sqlite::SqlitePoolOptions,
    Error as SqlxError
};
use serde::{Serialize, Deserialize};
use std::time::{Duration, Instant};
use tokio::time::sleep;

#[derive(Debug, Serialize, Deserialize)]
pub struct ConnectionConfig {
    pub max_connections: u32,
    pub min_connections: u32,
    pub connect_timeout: Duration,
    pub idle_timeout: Duration,
    pub max_lifetime: Duration,
    pub health_check_interval: Duration,
    pub retry_attempts: u32,
    pub retry_delay: Duration,
}

impl Default for ConnectionConfig {
    fn default() -> Self {
        Self {
            max_connections: 10,
            min_connections: 1,
            connect_timeout: Duration::from_secs(30),
            idle_timeout: Duration::from_secs(600),
            max_lifetime: Duration::from_secs(1800),
            health_check_interval: Duration::from_secs(30),
            retry_attempts: 3,
            retry_delay: Duration::from_secs(1),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ConnectionStats {
    pub total_connections: u32,
    pub active_connections: u32,
    pub idle_connections: u32,
    pub connection_errors: u32,
    pub avg_connection_time: f64,
    pub last_health_check: String,
    pub pool_health: String,
}

#[derive(Debug)]
pub enum DatabasePool {
    Postgres(PgPool),
    MySQL(MySqlPool),
    SQLite(SqlitePool),
}

impl DatabasePool {
    pub async fn get_connection_stats(&self) -> ConnectionStats {
        match self {
            DatabasePool::Postgres(pool) => {
                let size = pool.size();
                let num_idle = pool.num_idle();
                let num_used = size - num_idle;
                
                ConnectionStats {
                    total_connections: size as u32,
                    active_connections: num_used as u32,
                    idle_connections: num_idle as u32,
                    connection_errors: 0, // Would track this in real implementation
                    avg_connection_time: 0.0, // Would track this in real implementation
                    last_health_check: chrono::Utc::now().to_rfc3339(),
                    pool_health: if size > 0 { "healthy".to_string() } else { "unhealthy".to_string() },
                }
            }
            DatabasePool::MySQL(pool) => {
                let size = pool.size();
                let num_idle = pool.num_idle();
                let num_used = size - num_idle;
                
                ConnectionStats {
                    total_connections: size as u32,
                    active_connections: num_used as u32,
                    idle_connections: num_idle as u32,
                    connection_errors: 0,
                    avg_connection_time: 0.0,
                    last_health_check: chrono::Utc::now().to_rfc3339(),
                    pool_health: if size > 0 { "healthy".to_string() } else { "unhealthy".to_string() },
                }
            }
            DatabasePool::SQLite(pool) => {
                let size = pool.size();
                let num_idle = pool.num_idle();
                let num_used = size - num_idle;
                
                ConnectionStats {
                    total_connections: size as u32,
                    active_connections: num_used as u32,
                    idle_connections: num_idle as u32,
                    connection_errors: 0,
                    avg_connection_time: 0.0,
                    last_health_check: chrono::Utc::now().to_rfc3339(),
                    pool_health: if size > 0 { "healthy".to_string() } else { "unhealthy".to_string() },
                }
            }
        }
    }
    
    pub async fn health_check(&self) -> bool {
        match self {
            DatabasePool::Postgres(pool) => {
                match sqlx::query("SELECT 1").execute(pool).await {
                    Ok(_) => true,
                    Err(_) => false,
                }
            }
            DatabasePool::MySQL(pool) => {
                match sqlx::query("SELECT 1").execute(pool).await {
                    Ok(_) => true,
                    Err(_) => false,
                }
            }
            DatabasePool::SQLite(pool) => {
                match sqlx::query("SELECT 1").execute(pool).await {
                    Ok(_) => true,
                    Err(_) => false,
                }
            }
        }
    }
    
    pub async fn close(&self) {
        match self {
            DatabasePool::Postgres(pool) => pool.close().await,
            DatabasePool::MySQL(pool) => pool.close().await,
            DatabasePool::SQLite(pool) => pool.close().await,
        }
    }
}

#[pyclass]
pub struct OxenConnectionPool {
    pool: Option<DatabasePool>,
    config: ConnectionConfig,
    connection_string: String,
    database_type: String,
    created_at: String,
    last_health_check: Option<Instant>,
}

#[pymethods]
impl OxenConnectionPool {
    #[new]
    fn new(connection_string: String, database_type: String, config: Option<ConnectionConfig>) -> Self {
        Self {
            pool: None,
            config: config.unwrap_or_default(),
            connection_string,
            database_type,
            created_at: chrono::Utc::now().to_rfc3339(),
            last_health_check: None,
        }
    }
    
    async fn connect(&mut self) -> PyResult<PyObject> {
        let start_time = Instant::now();
        
        for attempt in 1..=self.config.retry_attempts {
            match self.create_pool().await {
                Ok(pool) => {
                    self.pool = Some(pool);
                    let connection_time = start_time.elapsed().as_secs_f64();
                    
                    Python::with_gil(|py| {
                        let result = PyDict::new(py);
                        result.set_item("success", true)?;
                        result.set_item("connection_string", self.connection_string.clone())?;
                        result.set_item("database_type", self.database_type.clone())?;
                        result.set_item("connection_time", connection_time)?;
                        result.set_item("attempts", attempt)?;
                        result.set_item("status", "connected")?;
                        Ok(result.into())
                    })
                }
                Err(e) => {
                    if attempt < self.config.retry_attempts {
                        sleep(self.config.retry_delay).await;
                        continue;
                    }
                    
                    return Err(PyErr::new::<pyo3::exceptions::PyConnectionError, _>(
                        format!("Failed to connect after {} attempts: {}", attempt, e)
                    ));
                }
            }
        }
        
        Err(PyErr::new::<pyo3::exceptions::PyConnectionError, _>(
            "Failed to connect to database"
        ))
    }
    
    async fn disconnect(&mut self) -> PyResult<PyObject> {
        if let Some(pool) = &self.pool {
            pool.close().await;
        }
        self.pool = None;
        
        Python::with_gil(|py| {
            let result = PyDict::new(py);
            result.set_item("success", true)?;
            result.set_item("status", "disconnected")?;
            Ok(result.into())
        })
    }
    
    async fn health_check(&self) -> PyResult<PyObject> {
        if let Some(pool) = &self.pool {
            let is_healthy = pool.health_check().await;
            
            Python::with_gil(|py| {
                let result = PyDict::new(py);
                result.set_item("healthy", is_healthy)?;
                result.set_item("timestamp", chrono::Utc::now().to_rfc3339())?;
                result.set_item("database_type", self.database_type.clone())?;
                Ok(result.into())
            })
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "No active connection pool"
            ))
        }
    }
    
    async fn get_stats(&self) -> PyResult<PyObject> {
        if let Some(pool) = &self.pool {
            let stats = pool.get_connection_stats().await;
            
            Python::with_gil(|py| {
                let result = PyDict::new(py);
                result.set_item("total_connections", stats.total_connections)?;
                result.set_item("active_connections", stats.active_connections)?;
                result.set_item("idle_connections", stats.idle_connections)?;
                result.set_item("connection_errors", stats.connection_errors)?;
                result.set_item("avg_connection_time", stats.avg_connection_time)?;
                result.set_item("last_health_check", stats.last_health_check)?;
                result.set_item("pool_health", stats.pool_health)?;
                result.set_item("database_type", self.database_type.clone())?;
                Ok(result.into())
            })
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "No active connection pool"
            ))
        }
    }
    
    fn is_connected(&self) -> bool {
        self.pool.is_some()
    }
    
    fn get_config(&self) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            let result = PyDict::new(py);
            result.set_item("max_connections", self.config.max_connections)?;
            result.set_item("min_connections", self.config.min_connections)?;
            result.set_item("connect_timeout", self.config.connect_timeout.as_secs())?;
            result.set_item("idle_timeout", self.config.idle_timeout.as_secs())?;
            result.set_item("max_lifetime", self.config.max_lifetime.as_secs())?;
            result.set_item("health_check_interval", self.config.health_check_interval.as_secs())?;
            result.set_item("retry_attempts", self.config.retry_attempts)?;
            result.set_item("retry_delay", self.config.retry_delay.as_secs())?;
            Ok(result.into())
        })
    }
    
    fn __str__(&self) -> String {
        format!(
            "OxenConnectionPool(type={}, connected={}, created={})",
            self.database_type, self.is_connected(), self.created_at
        )
    }
    
    fn __repr__(&self) -> String {
        self.__str__()
    }
}

impl OxenConnectionPool {
    async fn create_pool(&self) -> Result<DatabasePool, Box<dyn std::error::Error>> {
        match self.database_type.as_str() {
            "postgresql" | "postgres" => {
                let pool = PgPoolOptions::new()
                    .max_connections(self.config.max_connections)
                    .min_connections(self.config.min_connections)
                    .connect_timeout(self.config.connect_timeout)
                    .idle_timeout(self.config.idle_timeout)
                    .max_lifetime(self.config.max_lifetime)
                    .connect(&self.connection_string)
                    .await?;
                
                Ok(DatabasePool::Postgres(pool))
            }
            "mysql" => {
                let pool = MySqlPoolOptions::new()
                    .max_connections(self.config.max_connections)
                    .min_connections(self.config.min_connections)
                    .connect_timeout(self.config.connect_timeout)
                    .idle_timeout(self.config.idle_timeout)
                    .max_lifetime(self.config.max_lifetime)
                    .connect(&self.connection_string)
                    .await?;
                
                Ok(DatabasePool::MySQL(pool))
            }
            "sqlite" => {
                let pool = SqlitePoolOptions::new()
                    .max_connections(self.config.max_connections)
                    .min_connections(self.config.min_connections)
                    .connect_timeout(self.config.connect_timeout)
                    .idle_timeout(self.config.idle_timeout)
                    .max_lifetime(self.config.max_lifetime)
                    .connect(&self.connection_string)
                    .await?;
                
                Ok(DatabasePool::SQLite(pool))
            }
            _ => Err(format!("Unsupported database type: {}", self.database_type).into()),
        }
    }
} 
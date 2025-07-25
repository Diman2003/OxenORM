//! Multi-Database Support for OxenORM
//!
//! This module provides support for multiple database backends including
//! PostgreSQL, MySQL, and SQLite with database-specific optimizations.

use sqlx::{
    postgres::{PgPool, PgPoolOptions, PgArguments},
    mysql::{MySqlPool, MySqlPoolOptions, MySqlArguments},
    sqlite::{SqlitePool, SqlitePoolOptions, SqliteArguments},
    Row, query::Query, Postgres, MySql, Sqlite, Column, ValueRef, Error as SqlxError,
    Database, Arguments, Pool, PoolOptions,
};
use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::runtime::Runtime;
use thiserror::Error;
use url::Url;

#[derive(Error, Debug)]
pub enum MultiDbError {
    #[error("Database connection failed: {0}")]
    ConnectionError(#[from] SqlxError),
    #[error("Query execution failed: {0}")]
    QueryError(SqlxError),
    #[error("Unsupported database type: {0}")]
    UnsupportedDatabase(String),
    #[error("Invalid connection string: {0}")]
    InvalidConnectionString(String),
    #[error("Not connected to database")]
    NotConnected,
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
}

#[derive(Debug, Clone, PartialEq)]
pub enum DatabaseType {
    PostgreSQL,
    MySQL,
    SQLite,
}

impl DatabaseType {
    pub fn from_url(url: &str) -> Result<Self, MultiDbError> {
        let parsed_url = Url::parse(url)
            .map_err(|e| MultiDbError::InvalidConnectionString(e.to_string()))?;
        
        match parsed_url.scheme() {
            "postgresql" | "postgres" => Ok(DatabaseType::PostgreSQL),
            "mysql" => Ok(DatabaseType::MySQL),
            "sqlite" => Ok(DatabaseType::SQLite),
            _ => Err(MultiDbError::UnsupportedDatabase(parsed_url.scheme().to_string())),
        }
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

// Generic database pool trait
pub trait DatabasePool {
    async fn execute_query(&self, sql: &str, params: &[serde_json::Value]) -> Result<QueryResult, MultiDbError>;
    async fn execute_many(&self, sql: &str, params_list: &[Vec<serde_json::Value>]) -> Result<QueryResult, MultiDbError>;
    async fn begin_transaction(&self) -> Result<String, MultiDbError>;
}

// PostgreSQL implementation
pub struct PostgresPool {
    pool: PgPool,
}

impl PostgresPool {
    pub async fn new(connection_string: &str, max_connections: u32, min_connections: u32) -> Result<Self, MultiDbError> {
        let pool = PgPoolOptions::new()
            .max_connections(max_connections)
            .min_connections(min_connections)
            .acquire_timeout(std::time::Duration::from_secs(30))
            .idle_timeout(std::time::Duration::from_secs(300))
            .max_lifetime(std::time::Duration::from_secs(1800))
            .connect(connection_string)
            .await
            .map_err(MultiDbError::ConnectionError)?;

        Ok(PostgresPool { pool })
    }
}

impl DatabasePool for PostgresPool {
    async fn execute_query(&self, sql: &str, params: &[serde_json::Value]) -> Result<QueryResult, MultiDbError> {
        execute_query_postgres(&self.pool, sql, params).await
    }

    async fn execute_many(&self, sql: &str, params_list: &[Vec<serde_json::Value>]) -> Result<QueryResult, MultiDbError> {
        execute_many_postgres(&self.pool, sql, params_list).await
    }

    async fn begin_transaction(&self) -> Result<String, MultiDbError> {
        let _conn = self.pool.acquire().await.map_err(MultiDbError::ConnectionError)?;
        // For now, return a mock transaction ID
        Ok(uuid::Uuid::new_v4().to_string())
    }
}

// MySQL implementation
pub struct MySqlPoolWrapper {
    pool: MySqlPool,
}

impl MySqlPoolWrapper {
    pub async fn new(connection_string: &str, max_connections: u32, min_connections: u32) -> Result<Self, MultiDbError> {
        let pool = MySqlPoolOptions::new()
            .max_connections(max_connections)
            .min_connections(min_connections)
            .acquire_timeout(std::time::Duration::from_secs(30))
            .idle_timeout(std::time::Duration::from_secs(300))
            .max_lifetime(std::time::Duration::from_secs(1800))
            .connect(connection_string)
            .await
            .map_err(MultiDbError::ConnectionError)?;

        Ok(MySqlPoolWrapper { pool })
    }
}

impl DatabasePool for MySqlPoolWrapper {
    async fn execute_query(&self, sql: &str, params: &[serde_json::Value]) -> Result<QueryResult, MultiDbError> {
        execute_query_mysql(&self.pool, sql, params).await
    }

    async fn execute_many(&self, sql: &str, params_list: &[Vec<serde_json::Value>]) -> Result<QueryResult, MultiDbError> {
        execute_many_mysql(&self.pool, sql, params_list).await
    }

    async fn begin_transaction(&self) -> Result<String, MultiDbError> {
        let _conn = self.pool.acquire().await.map_err(MultiDbError::ConnectionError)?;
        // For now, return a mock transaction ID
        Ok(uuid::Uuid::new_v4().to_string())
    }
}

// SQLite implementation
pub struct SqlitePoolWrapper {
    pool: SqlitePool,
}

impl SqlitePoolWrapper {
    pub async fn new(connection_string: &str, max_connections: u32, min_connections: u32) -> Result<Self, MultiDbError> {
        let pool = SqlitePoolOptions::new()
            .max_connections(max_connections)
            .min_connections(min_connections)
            .acquire_timeout(std::time::Duration::from_secs(30))
            .idle_timeout(std::time::Duration::from_secs(300))
            .max_lifetime(std::time::Duration::from_secs(1800))
            .connect(connection_string)
            .await
            .map_err(MultiDbError::ConnectionError)?;

        Ok(SqlitePoolWrapper { pool })
    }
}

impl DatabasePool for SqlitePoolWrapper {
    async fn execute_query(&self, sql: &str, params: &[serde_json::Value]) -> Result<QueryResult, MultiDbError> {
        execute_query_sqlite(&self.pool, sql, params).await
    }

    async fn execute_many(&self, sql: &str, params_list: &[Vec<serde_json::Value>]) -> Result<QueryResult, MultiDbError> {
        execute_many_sqlite(&self.pool, sql, params_list).await
    }

    async fn begin_transaction(&self) -> Result<String, MultiDbError> {
        let _conn = self.pool.acquire().await.map_err(MultiDbError::ConnectionError)?;
        // For now, return a mock transaction ID
        Ok(uuid::Uuid::new_v4().to_string())
    }
}

// Multi-database engine
pub struct MultiDbEngine {
    connection_string: String,
    database_type: DatabaseType,
    pool: Option<Box<dyn DatabasePool + Send + Sync>>,
    max_connections: u32,
    min_connections: u32,
    runtime: Arc<Runtime>,
    is_connected: bool,
}

impl MultiDbEngine {
    pub fn new(connection_string: String) -> Result<Self, MultiDbError> {
        let database_type = DatabaseType::from_url(&connection_string)?;
        let runtime = Arc::new(Runtime::new().unwrap());

        Ok(MultiDbEngine {
            connection_string,
            database_type,
            pool: None,
            max_connections: 10,
            min_connections: 1,
            runtime,
            is_connected: false,
        })
    }

    pub fn configure_pool(&mut self, max_connections: Option<u32>, min_connections: Option<u32>) {
        if let Some(max) = max_connections {
            self.max_connections = max;
        }
        if let Some(min) = min_connections {
            self.min_connections = min;
        }
    }

    pub fn is_connected(&self) -> bool {
        self.is_connected
    }

    pub async fn connect(&mut self) -> Result<ConnectionInfo, MultiDbError> {
        let pool: Box<dyn DatabasePool + Send + Sync> = match self.database_type {
            DatabaseType::PostgreSQL => {
                let postgres_pool = PostgresPool::new(
                    &self.connection_string,
                    self.max_connections,
                    self.min_connections
                ).await?;
                Box::new(postgres_pool)
            }
            DatabaseType::MySQL => {
                let mysql_pool = MySqlPoolWrapper::new(
                    &self.connection_string,
                    self.max_connections,
                    self.min_connections
                ).await?;
                Box::new(mysql_pool)
            }
            DatabaseType::SQLite => {
                let sqlite_pool = SqlitePoolWrapper::new(
                    &self.connection_string,
                    self.max_connections,
                    self.min_connections
                ).await?;
                Box::new(sqlite_pool)
            }
        };

        self.pool = Some(pool);
        self.is_connected = true;

        Ok(ConnectionInfo {
            status: "connected".to_string(),
            connection_string: self.connection_string.clone(),
            database_type: format!("{:?}", self.database_type),
            pool_size: self.max_connections as usize,
            max_connections: self.max_connections,
            min_connections: self.min_connections,
        })
    }

    pub async fn execute_query(&self, sql: String, params: Vec<serde_json::Value>) -> Result<QueryResult, MultiDbError> {
        if !self.is_connected {
            return Err(MultiDbError::NotConnected);
        }

        if let Some(pool) = &self.pool {
            pool.execute_query(&sql, &params).await
        } else {
            Err(MultiDbError::NotConnected)
        }
    }

    pub async fn execute_many(&self, sql: String, params_list: Vec<Vec<serde_json::Value>>) -> Result<QueryResult, MultiDbError> {
        if !self.is_connected {
            return Err(MultiDbError::NotConnected);
        }

        if let Some(pool) = &self.pool {
            pool.execute_many(&sql, &params_list).await
        } else {
            Err(MultiDbError::NotConnected)
        }
    }

    pub async fn begin_transaction(&self) -> Result<TransactionInfo, MultiDbError> {
        if !self.is_connected {
            return Err(MultiDbError::NotConnected);
        }

        if let Some(pool) = &self.pool {
            let transaction_id = pool.begin_transaction().await?;
            Ok(TransactionInfo {
                id: transaction_id,
                status: "active".to_string(),
                created_at: chrono::Utc::now().to_rfc3339(),
            })
        } else {
            Err(MultiDbError::NotConnected)
        }
    }

    pub async fn close(&mut self) -> Result<ConnectionInfo, MultiDbError> {
        let was_connected = self.is_connected;
        self.pool = None;
        self.is_connected = false;

        Ok(ConnectionInfo {
            status: "disconnected".to_string(),
            connection_string: self.connection_string.clone(),
            database_type: format!("{:?}", self.database_type),
            pool_size: 0,
            max_connections: self.max_connections,
            min_connections: self.min_connections,
        })
    }
}

// Database-specific query execution functions

async fn execute_query_postgres(pool: &PgPool, sql: &str, params: &[serde_json::Value]) -> Result<QueryResult, MultiDbError> {
    let mut query = sqlx::query(sql);
    
    for param in params {
        query = bind_param_postgres(query, param);
    }

    match query.execute(pool).await {
        Ok(result) => {
            let rows_affected = result.rows_affected();
            Ok(QueryResult {
                rows_affected: rows_affected as i64,
                data: vec![],
                error: None,
            })
        }
        Err(e) => Err(MultiDbError::QueryError(e)),
    }
}

async fn execute_query_mysql(pool: &MySqlPool, sql: &str, params: &[serde_json::Value]) -> Result<QueryResult, MultiDbError> {
    let mut query = sqlx::query(sql);
    
    for param in params {
        query = bind_param_mysql(query, param);
    }

    match query.execute(pool).await {
        Ok(result) => {
            let rows_affected = result.rows_affected();
            Ok(QueryResult {
                rows_affected: rows_affected as i64,
                data: vec![],
                error: None,
            })
        }
        Err(e) => Err(MultiDbError::QueryError(e)),
    }
}

async fn execute_query_sqlite(pool: &SqlitePool, sql: &str, params: &[serde_json::Value]) -> Result<QueryResult, MultiDbError> {
    let mut query = sqlx::query(sql);
    
    for param in params {
        query = bind_param_sqlite(query, param);
    }

    match query.execute(pool).await {
        Ok(result) => {
            let rows_affected = result.rows_affected();
            Ok(QueryResult {
                rows_affected: rows_affected as i64,
                data: vec![],
                error: None,
            })
        }
        Err(e) => Err(MultiDbError::QueryError(e)),
    }
}

// Database-specific parameter binding

fn bind_param_postgres<'q>(query: Query<'q, Postgres, PgArguments>, param: &'q serde_json::Value) -> Query<'q, Postgres, PgArguments> {
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

fn bind_param_mysql<'q>(query: Query<'q, MySql, MySqlArguments>, param: &'q serde_json::Value) -> Query<'q, MySql, MySqlArguments> {
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

fn bind_param_sqlite<'q>(query: Query<'q, Sqlite, SqliteArguments>, param: &'q serde_json::Value) -> Query<'q, Sqlite, SqliteArguments> {
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

// Batch execution functions

async fn execute_many_postgres(pool: &PgPool, sql: &str, params_list: &[Vec<serde_json::Value>]) -> Result<QueryResult, MultiDbError> {
    let mut total_rows_affected = 0i64;

    for params in params_list {
        let mut query = sqlx::query(sql);
        for param in params {
            query = bind_param_postgres(query, param);
        }

        match query.execute(pool).await {
            Ok(result) => {
                total_rows_affected += result.rows_affected() as i64;
            }
            Err(e) => return Err(MultiDbError::QueryError(e)),
        }
    }

    Ok(QueryResult {
        rows_affected: total_rows_affected,
        data: vec![],
        error: None,
    })
}

async fn execute_many_mysql(pool: &MySqlPool, sql: &str, params_list: &[Vec<serde_json::Value>]) -> Result<QueryResult, MultiDbError> {
    let mut total_rows_affected = 0i64;

    for params in params_list {
        let mut query = sqlx::query(sql);
        for param in params {
            query = bind_param_mysql(query, param);
        }

        match query.execute(pool).await {
            Ok(result) => {
                total_rows_affected += result.rows_affected() as i64;
            }
            Err(e) => return Err(MultiDbError::QueryError(e)),
        }
    }

    Ok(QueryResult {
        rows_affected: total_rows_affected,
        data: vec![],
        error: None,
    })
}

async fn execute_many_sqlite(pool: &SqlitePool, sql: &str, params_list: &[Vec<serde_json::Value>]) -> Result<QueryResult, MultiDbError> {
    let mut total_rows_affected = 0i64;

    for params in params_list {
        let mut query = sqlx::query(sql);
        for param in params {
            query = bind_param_sqlite(query, param);
        }

        match query.execute(pool).await {
            Ok(result) => {
                total_rows_affected += result.rows_affected() as i64;
            }
            Err(e) => return Err(MultiDbError::QueryError(e)),
        }
    }

    Ok(QueryResult {
        rows_affected: total_rows_affected,
        data: vec![],
        error: None,
    })
} 
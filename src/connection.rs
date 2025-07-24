//! Database connection management for OxenORM

use crate::error::{OxenError, OxenResult};
use std::collections::HashMap;
use url::Url;

/// Supported database types
#[derive(Debug, Clone, PartialEq)]
pub enum DatabaseType {
    PostgreSQL,
    MySQL,
    SQLite,
}

/// Database connection configuration
#[derive(Debug, Clone)]
pub struct ConnectionConfig {
    pub database_type: DatabaseType,
    pub host: String,
    pub port: u16,
    pub username: String,
    pub password: String,
    pub database: String,
    pub ssl_mode: bool,
    pub pool_size: u32,
}

impl ConnectionConfig {
    /// Parse connection string and create configuration
    pub fn from_url(connection_string: &str) -> OxenResult<Self> {
        let url = Url::parse(connection_string)?;
        
        let database_type = match url.scheme() {
            "postgresql" | "postgres" => DatabaseType::PostgreSQL,
            "mysql" => DatabaseType::MySQL,
            "sqlite" => DatabaseType::SQLite,
            _ => return Err(OxenError::Configuration(format!(
                "Unsupported database scheme: {}", url.scheme()
            ))),
        };

        let host = url.host_str()
            .ok_or_else(|| OxenError::Configuration("No host in connection string".to_string()))?
            .to_string();
        
        let port = url.port().unwrap_or_else(|| match database_type {
            DatabaseType::PostgreSQL => 5432,
            DatabaseType::MySQL => 3306,
            DatabaseType::SQLite => 0,
        });

        let username = url.username().to_string();
        let password = url.password().unwrap_or("").to_string();
        
        let database = url.path().trim_start_matches('/').to_string();

        Ok(Self {
            database_type,
            host,
            port,
            username,
            password,
            database,
            ssl_mode: true, // Default to SSL
            pool_size: 10,   // Default pool size
        })
    }
}

/// Database connection enum
pub enum DatabaseConnection {
    PostgreSQL(String),
    MySQL(String),
    SQLite(String),
}

impl DatabaseConnection {
    /// Execute a query and return results
    pub async fn execute_query(
        &mut self,
        sql: &str,
        params: &[serde_json::Value],
    ) -> OxenResult<Vec<HashMap<String, serde_json::Value>>> {
        // TODO: Implement actual database queries
        // For now, return empty results
        Ok(vec![])
    }

    /// Execute a query that doesn't return results
    pub async fn execute_command(&mut self, sql: &str, params: &[serde_json::Value]) -> OxenResult<u64> {
        // TODO: Implement actual database commands
        // For now, return 0 affected rows
        Ok(0)
    }
}

/// Factory function to create appropriate database connection
pub async fn create_connection(config: &ConnectionConfig) -> OxenResult<DatabaseConnection> {
    match config.database_type {
        DatabaseType::PostgreSQL => {
            let connection_string = format!(
                "postgresql://{}:{}@{}:{}/{}",
                config.username, config.password, config.host, config.port, config.database
            );
            Ok(DatabaseConnection::PostgreSQL(connection_string))
        }
        DatabaseType::MySQL => {
            let connection_string = format!(
                "mysql://{}:{}@{}:{}/{}",
                config.username, config.password, config.host, config.port, config.database
            );
            Ok(DatabaseConnection::MySQL(connection_string))
        }
        DatabaseType::SQLite => {
            let connection_string = format!("sqlite:{}", config.database);
            Ok(DatabaseConnection::SQLite(connection_string))
        }
    }
} 
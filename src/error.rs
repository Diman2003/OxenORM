//! Error handling for OxenORM Rust backend

use thiserror::Error;

/// Main error type for OxenORM
#[derive(Error, Debug)]
pub enum OxenError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Connection error: {0}")]
    Connection(String),

    #[error("Configuration error: {0}")]
    Configuration(String),

    #[error("Query error: {0}")]
    Query(String),

    #[error("Transaction error: {0}")]
    Transaction(String),

    #[error("Migration error: {0}")]
    Migration(String),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("Invalid URL: {0}")]
    InvalidUrl(#[from] url::ParseError),

    #[error("Type conversion error: {0}")]
    TypeConversion(String),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Internal error: {0}")]
    Internal(String),
}

impl From<anyhow::Error> for OxenError {
    fn from(err: anyhow::Error) -> Self {
        OxenError::Internal(err.to_string())
    }
}

impl From<std::io::Error> for OxenError {
    fn from(err: std::io::Error) -> Self {
        OxenError::Internal(err.to_string())
    }
}

/// Result type for OxenORM operations
pub type OxenResult<T> = Result<T, OxenError>; 
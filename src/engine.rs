//! Main engine implementation for OxenORM

use crate::connection::{create_connection, ConnectionConfig, DatabaseConnection};
use crate::error::{OxenError, OxenResult};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;

/// Main OxenEngine implementation
pub struct OxenEngineInner {
    connection: Option<DatabaseConnection>,
    connection_string: String,
    config: Option<ConnectionConfig>,
}

impl OxenEngineInner {
    /// Create a new OxenEngine instance
    pub fn new(connection_string: String) -> OxenResult<Self> {
        let config = ConnectionConfig::from_url(&connection_string)?;
        
        Ok(Self {
            connection: None,
            connection_string,
            config: Some(config),
        })
    }

    /// Connect to the database
    pub async fn connect(&mut self) -> OxenResult<()> {
        if self.connection.is_some() {
            return Ok(());
        }

        let config = self.config.as_ref()
            .ok_or_else(|| OxenError::Configuration("No configuration available".to_string()))?;

        let connection = create_connection(config).await?;
        self.connection = Some(connection);
        Ok(())
    }

    /// Disconnect from the database
    pub async fn disconnect(&mut self) -> OxenResult<()> {
        self.connection = None;
        Ok(())
    }

    /// Insert a model into the database
    pub async fn insert_model(
        &mut self,
        table_name: String,
        data: HashMap<String, PyObject>,
        _pk_field: String,
    ) -> OxenResult<Option<HashMap<String, PyObject>>> {
        let _connection = self.get_connection()?;

        // TODO: Implement actual database insertion
        // For now, return None
        Ok(None)
    }

    /// Update a model in the database
    pub async fn update_model(
        &mut self,
        table_name: String,
        pk_value: PyObject,
        data: HashMap<String, PyObject>,
        pk_field: String,
    ) -> OxenResult<bool> {
        let _connection = self.get_connection()?;

        // TODO: Implement actual database update
        // For now, return false
        Ok(false)
    }

    /// Delete a model from the database
    pub async fn delete_model(
        &mut self,
        table_name: String,
        pk_value: PyObject,
        pk_field: String,
    ) -> OxenResult<bool> {
        let _connection = self.get_connection()?;

        // TODO: Implement actual database deletion
        // For now, return false
        Ok(false)
    }

    /// Get a single model from the database
    pub async fn get_model(
        &mut self,
        table_name: String,
        conditions: HashMap<String, PyObject>,
        pk_field: String,
    ) -> OxenResult<Option<HashMap<String, PyObject>>> {
        let _connection = self.get_connection()?;

        // TODO: Implement actual database query
        // For now, return None
        Ok(None)
    }

    /// Query multiple models from the database
    pub async fn query_models(
        &mut self,
        table_name: String,
        conditions: HashMap<String, PyObject>,
        limit: Option<i64>,
        offset: Option<i64>,
        order_by: Vec<String>,
        pk_field: String,
    ) -> OxenResult<Vec<HashMap<String, PyObject>>> {
        let _connection = self.get_connection()?;

        // TODO: Implement actual database query
        // For now, return empty vector
        Ok(vec![])
    }

    /// Count models matching conditions
    pub async fn count_models(
        &mut self,
        table_name: String,
        conditions: HashMap<String, PyObject>,
    ) -> OxenResult<i64> {
        let _connection = self.get_connection()?;

        // TODO: Implement actual database count
        // For now, return 0
        Ok(0)
    }

    /// Bulk insert multiple models
    pub async fn bulk_insert(
        &mut self,
        table_name: String,
        records: Vec<HashMap<String, PyObject>>,
        pk_field: String,
    ) -> OxenResult<Vec<HashMap<String, PyObject>>> {
        if records.is_empty() {
            return Ok(vec![]);
        }

        // TODO: Implement actual bulk insert
        // For now, return empty vector
        Ok(vec![])
    }

    /// Bulk update multiple models
    pub async fn bulk_update(
        &mut self,
        table_name: String,
        records: Vec<HashMap<String, PyObject>>,
        pk_field: String,
    ) -> OxenResult<i64> {
        if records.is_empty() {
            return Ok(0);
        }

        // TODO: Implement actual bulk update
        // For now, return 0
        Ok(0)
    }

    /// Execute raw SQL query
    pub async fn execute_raw_sql(
        &mut self,
        sql: String,
        params: Vec<PyObject>,
    ) -> OxenResult<Vec<HashMap<String, PyObject>>> {
        let _connection = self.get_connection()?;

        // TODO: Implement actual SQL execution
        // For now, return empty vector
        Ok(vec![])
    }

    /// Begin a new transaction
    pub async fn begin_transaction(&mut self) -> OxenResult<()> {
        // TODO: Implement transaction support
        Err(OxenError::Transaction("Transactions not yet implemented".to_string()))
    }

    /// Create a new table
    pub async fn create_table(
        &mut self,
        table_name: String,
        schema: HashMap<String, String>,
    ) -> OxenResult<()> {
        let _connection = self.get_connection()?;

        // TODO: Implement actual table creation
        // For now, return success
        Ok(())
    }

    /// Drop a table
    pub async fn drop_table(&mut self, table_name: String) -> OxenResult<()> {
        let _connection = self.get_connection()?;

        // TODO: Implement actual table dropping
        // For now, return success
        Ok(())
    }

    /// Get the database connection
    fn get_connection(&mut self) -> OxenResult<&mut DatabaseConnection> {
        self.connection.as_mut()
            .ok_or_else(|| OxenError::Connection("Not connected to database".to_string()))
    }

    /// Convert Python object to JSON value
    fn py_object_to_json(&self, py_obj: PyObject) -> OxenResult<serde_json::Value> {
        Python::with_gil(|py| {
            // This is a simplified conversion
            // In a real implementation, you'd need to handle all Python types properly
            if py_obj.is_none(py) {
                Ok(serde_json::Value::Null)
            } else if let Ok(int_val) = py_obj.extract::<i64>(py) {
                Ok(serde_json::Value::Number(int_val.into()))
            } else if let Ok(float_val) = py_obj.extract::<f64>(py) {
                Ok(serde_json::Value::Number(serde_json::Number::from_f64(float_val).unwrap_or_else(|| serde_json::Number::from(0))))
            } else if let Ok(str_val) = py_obj.extract::<String>(py) {
                Ok(serde_json::Value::String(str_val))
            } else if let Ok(bool_val) = py_obj.extract::<bool>(py) {
                Ok(serde_json::Value::Bool(bool_val))
            } else {
                // For complex types, try to convert to string
                let str_repr = match py_obj.as_ref(py).str() {
                    Ok(s) => s.to_string(),
                    Err(_) => "".to_string(),
                };
                Ok(serde_json::Value::String(str_repr))
            }
        })
    }

    /// Convert JSON value to Python object
    fn json_to_py_object(&self, json_value: serde_json::Value) -> OxenResult<PyObject> {
        Python::with_gil(|py| {
            match json_value {
                serde_json::Value::Null => Ok(py.None()),
                serde_json::Value::Bool(b) => Ok(b.to_object(py)),
                serde_json::Value::Number(n) => {
                    if let Some(i) = n.as_i64() {
                        Ok(i.to_object(py))
                    } else if let Some(f) = n.as_f64() {
                        Ok(f.to_object(py))
                    } else {
                        Ok(n.to_string().to_object(py))
                    }
                }
                serde_json::Value::String(s) => Ok(s.to_object(py)),
                serde_json::Value::Array(arr) => {
                    let list = PyList::new(py, Vec::<PyObject>::new());
                    for item in arr {
                        let py_item = self.json_to_py_object(item)?;
                        list.append(py_item).map_err(|e| OxenError::TypeConversion(e.to_string()))?;
                    }
                    Ok(list.to_object(py))
                }
                serde_json::Value::Object(obj) => {
                    let dict = PyDict::new(py);
                    for (key, value) in obj {
                        let py_value = self.json_to_py_object(value)?;
                        dict.set_item(key, py_value).map_err(|e| OxenError::TypeConversion(e.to_string()))?;
                    }
                    Ok(dict.to_object(py))
                }
            }
        })
    }
} 
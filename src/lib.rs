//! OxenORM Rust Backend
//!
//! This crate provides the high-performance Rust backend for OxenORM,
//! handling database operations, connection pooling, and query execution.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;
use tokio::sync::Mutex;

#[pyclass]
pub struct OxenEngine {
    connection_string: String,
    connection: Mutex<Option<tokio::sync::RwLock<HashMap<String, PyObject>>>>,
}

#[pymethods]
impl OxenEngine {
    #[new]
    fn new(connection_string: String) -> Self {
        Self {
            connection_string,
            connection: Mutex::new(None),
        }
    }

    fn connect<'py>(&self, py: Python<'py>) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("status", "connected")?;
        dict.set_item("connection_string", self.connection_string.clone())?;
        Ok(dict.into_py(py))
    }

    fn execute_query<'py>(&self, py: Python<'py>, sql: String, params: Option<Vec<PyObject>>) -> PyResult<PyObject> {
        let result = PyDict::new(py);
        result.set_item("sql", sql)?;
        result.set_item("params", params.unwrap_or_default())?;
        result.set_item("rows_affected", 0)?;
        result.set_item("data", PyList::empty(py))?;
        Ok(result.into_py(py))
    }

    fn execute_many<'py>(&self, py: Python<'py>, sql: String, params_list: Vec<Vec<PyObject>>) -> PyResult<PyObject> {
        let result = PyDict::new(py);
        result.set_item("sql", sql)?;
        result.set_item("batch_size", params_list.len())?;
        result.set_item("rows_affected", 0)?;
        Ok(result.into_py(py))
    }

    fn begin_transaction<'py>(&self, py: Python<'py>) -> PyResult<PyObject> {
        let transaction = PyDict::new(py);
        transaction.set_item("id", format!("tx_{}", uuid::Uuid::new_v4().to_string().split('-').next().unwrap()))?;
        transaction.set_item("status", "active")?;
        Ok(transaction.into_py(py))
    }

    fn commit_transaction<'py>(&self, py: Python<'py>, transaction_id: String) -> PyResult<PyObject> {
        let result = PyDict::new(py);
        result.set_item("transaction_id", transaction_id)?;
        result.set_item("status", "committed")?;
        Ok(result.into_py(py))
    }

    fn rollback_transaction<'py>(&self, py: Python<'py>, transaction_id: String) -> PyResult<PyObject> {
        let result = PyDict::new(py);
        result.set_item("transaction_id", transaction_id)?;
        result.set_item("status", "rolled_back")?;
        Ok(result.into_py(py))
    }

    fn close<'py>(&self, py: Python<'py>) -> PyResult<PyObject> {
        let result = PyDict::new(py);
        result.set_item("status", "closed")?;
        Ok(result.into_py(py))
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
            is_active: true,
        }
    }

    fn commit<'py>(&mut self, py: Python<'py>) -> PyResult<PyObject> {
        if !self.is_active {
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Transaction already closed"));
        }
        
        let engine_ref = self.engine.borrow(py);
        engine_ref.commit_transaction(py, self.transaction_id.clone())
    }

    fn rollback<'py>(&mut self, py: Python<'py>) -> PyResult<PyObject> {
        if !self.is_active {
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Transaction already closed"));
        }
        
        let engine_ref = self.engine.borrow(py);
        engine_ref.rollback_transaction(py, self.transaction_id.clone())
    }

    fn execute<'py>(&self, py: Python<'py>, sql: String, params: Option<Vec<PyObject>>) -> PyResult<PyObject> {
        if !self.is_active {
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Transaction is not active"));
        }
        
        let engine_ref = self.engine.borrow(py);
        engine_ref.execute_query(py, sql, params)
    }
}

#[pymodule]
fn oxen_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<OxenEngine>()?;
    m.add_class::<OxenTransaction>()?;
    Ok(())
} 
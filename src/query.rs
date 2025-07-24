//! Query building and execution for OxenORM

use crate::error::{OxenError, OxenResult};
use serde_json::Value;
use std::collections::HashMap;

/// Query builder for constructing SQL queries
pub struct QueryBuilder {
    table_name: String,
    select_fields: Vec<String>,
    where_conditions: Vec<WhereCondition>,
    order_by: Vec<OrderBy>,
    limit: Option<i64>,
    offset: Option<i64>,
}

/// Where condition for filtering
pub struct WhereCondition {
    field: String,
    operator: String,
    value: Value,
}

/// Order by clause
pub struct OrderBy {
    field: String,
    direction: OrderDirection,
}

/// Order direction
#[derive(Debug, Clone)]
pub enum OrderDirection {
    Asc,
    Desc,
}

impl QueryBuilder {
    /// Create a new query builder
    pub fn new(table_name: String) -> Self {
        Self {
            table_name,
            select_fields: vec!["*".to_string()],
            where_conditions: Vec::new(),
            order_by: Vec::new(),
            limit: None,
            offset: None,
        }
    }

    /// Set the fields to select
    pub fn select(mut self, fields: Vec<String>) -> Self {
        self.select_fields = fields;
        self
    }

    /// Add a where condition
    pub fn where_condition(mut self, field: String, operator: String, value: Value) -> Self {
        self.where_conditions.push(WhereCondition {
            field,
            operator,
            value,
        });
        self
    }

    /// Add an order by clause
    pub fn order_by(mut self, field: String, direction: OrderDirection) -> Self {
        self.order_by.push(OrderBy { field, direction });
        self
    }

    /// Set the limit
    pub fn limit(mut self, limit: i64) -> Self {
        self.limit = Some(limit);
        self
    }

    /// Set the offset
    pub fn offset(mut self, offset: i64) -> Self {
        self.offset = Some(offset);
        self
    }

    /// Build the SELECT query
    pub fn build_select(&self) -> (String, Vec<Value>) {
        let mut sql = format!("SELECT {} FROM {}", self.select_fields.join(", "), self.table_name);
        let mut params = Vec::new();

        // Add WHERE clause
        if !self.where_conditions.is_empty() {
            let where_clauses: Vec<String> = self
                .where_conditions
                .iter()
                .enumerate()
                .map(|(i, condition)| {
                    params.push(condition.value.clone());
                    format!("{} {} ${}", condition.field, condition.operator, i + 1)
                })
                .collect();
            sql.push_str(&format!(" WHERE {}", where_clauses.join(" AND ")));
        }

        // Add ORDER BY clause
        if !self.order_by.is_empty() {
            let order_clauses: Vec<String> = self
                .order_by
                .iter()
                .map(|order| {
                    let direction = match order.direction {
                        OrderDirection::Asc => "ASC",
                        OrderDirection::Desc => "DESC",
                    };
                    format!("{} {}", order.field, direction)
                })
                .collect();
            sql.push_str(&format!(" ORDER BY {}", order_clauses.join(", ")));
        }

        // Add LIMIT clause
        if let Some(limit) = self.limit {
            sql.push_str(&format!(" LIMIT {}", limit));
        }

        // Add OFFSET clause
        if let Some(offset) = self.offset {
            sql.push_str(&format!(" OFFSET {}", offset));
        }

        (sql, params)
    }

    /// Build the COUNT query
    pub fn build_count(&self) -> (String, Vec<Value>) {
        let mut sql = format!("SELECT COUNT(*) as count FROM {}", self.table_name);
        let mut params = Vec::new();

        // Add WHERE clause
        if !self.where_conditions.is_empty() {
            let where_clauses: Vec<String> = self
                .where_conditions
                .iter()
                .enumerate()
                .map(|(i, condition)| {
                    params.push(condition.value.clone());
                    format!("{} {} ${}", condition.field, condition.operator, i + 1)
                })
                .collect();
            sql.push_str(&format!(" WHERE {}", where_clauses.join(" AND ")));
        }

        (sql, params)
    }

    /// Build the INSERT query
    pub fn build_insert(&self, data: &HashMap<String, Value>) -> (String, Vec<Value>) {
        let columns: Vec<&str> = data.keys().map(|s| s.as_str()).collect();
        let placeholders: Vec<String> = (0..columns.len()).map(|i| format!("${}", i + 1)).collect();
        let values: Vec<Value> = data.values().cloned().collect();

        let sql = format!(
            "INSERT INTO {} ({}) VALUES ({}) RETURNING *",
            self.table_name,
            columns.join(", "),
            placeholders.join(", ")
        );

        (sql, values)
    }

    /// Build the UPDATE query
    pub fn build_update(&self, data: &HashMap<String, Value>, pk_field: &str, pk_value: &Value) -> (String, Vec<Value>) {
        let set_clauses: Vec<String> = data
            .keys()
            .enumerate()
            .map(|(i, key)| format!("{} = ${}", key, i + 1))
            .collect();

        let mut values: Vec<Value> = data.values().cloned().collect();
        values.push(pk_value.clone());

        let sql = format!(
            "UPDATE {} SET {} WHERE {} = ${}",
            self.table_name,
            set_clauses.join(", "),
            pk_field,
            values.len()
        );

        (sql, values)
    }

    /// Build the DELETE query
    pub fn build_delete(&self, pk_field: &str, pk_value: &Value) -> (String, Vec<Value>) {
        let sql = format!("DELETE FROM {} WHERE {} = $1", self.table_name, pk_field);
        (sql, vec![pk_value.clone()])
    }
}

/// Query executor trait
pub trait QueryExecutor {
    /// Execute a query and return results
    async fn execute_query(
        &self,
        sql: &str,
        params: &[Value],
    ) -> OxenResult<Vec<HashMap<String, Value>>>;

    /// Execute a command and return affected rows
    async fn execute_command(&self, sql: &str, params: &[Value]) -> OxenResult<u64>;
}

/// Query result processor
pub struct QueryProcessor;

impl QueryProcessor {
    /// Process query results and convert to Python-compatible format
    pub fn process_results(
        results: Vec<HashMap<String, Value>>,
    ) -> OxenResult<Vec<HashMap<String, Value>>> {
        // In a real implementation, this would handle type conversions
        // and other post-processing of query results
        Ok(results)
    }

    /// Extract count from COUNT query result
    pub fn extract_count(results: Vec<HashMap<String, Value>>) -> OxenResult<i64> {
        if results.is_empty() {
            return Ok(0);
        }

        let count_value = results[0]
            .get("count")
            .ok_or_else(|| OxenError::Query("No count result".to_string()))?;

        match count_value {
            Value::Number(n) => n.as_i64().ok_or_else(|| {
                OxenError::TypeConversion("Invalid count value".to_string())
            }),
            _ => Err(OxenError::TypeConversion("Count is not a number".to_string())),
        }
    }
} 
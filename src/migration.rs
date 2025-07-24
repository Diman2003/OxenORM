//! Migration system for OxenORM

use crate::error::{OxenError, OxenResult};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;

/// Migration operation types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MigrationOp {
    CreateTable {
        name: String,
        columns: Vec<ColumnDef>,
        indexes: Vec<IndexDef>,
    },
    DropTable {
        name: String,
    },
    AddColumn {
        table: String,
        column: ColumnDef,
    },
    DropColumn {
        table: String,
        column: String,
    },
    AlterColumn {
        table: String,
        column: String,
        new_type: String,
        nullable: Option<bool>,
        default: Option<String>,
    },
    AddIndex {
        table: String,
        index: IndexDef,
    },
    DropIndex {
        table: String,
        index: String,
    },
    AddForeignKey {
        table: String,
        constraint: ForeignKeyDef,
    },
    DropForeignKey {
        table: String,
        constraint: String,
    },
}

/// Column definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ColumnDef {
    pub name: String,
    pub sql_type: String,
    pub nullable: bool,
    pub primary_key: bool,
    pub unique: bool,
    pub default: Option<String>,
    pub auto_increment: bool,
}

/// Index definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexDef {
    pub name: String,
    pub columns: Vec<String>,
    pub unique: bool,
}

/// Foreign key definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ForeignKeyDef {
    pub name: String,
    pub columns: Vec<String>,
    pub references: String,
    pub referenced_columns: Vec<String>,
    pub on_delete: Option<String>,
    pub on_update: Option<String>,
}

/// Migration definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Migration {
    pub id: String,
    pub name: String,
    pub operations: Vec<MigrationOp>,
    pub dependencies: Vec<String>,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

/// Migration system
pub struct MigrationSystem {
    migrations_dir: String,
    database_type: DatabaseType,
}

/// Database type for migration generation
#[derive(Debug, Clone)]
pub enum DatabaseType {
    PostgreSQL,
    MySQL,
    SQLite,
}

impl MigrationSystem {
    /// Create a new migration system
    pub fn new(migrations_dir: String, database_type: DatabaseType) -> Self {
        Self {
            migrations_dir,
            database_type,
        }
    }

    /// Generate a new migration
    pub fn generate_migration(
        &self,
        name: &str,
        current_schema: &HashMap<String, TableSchema>,
        target_schema: &HashMap<String, TableSchema>,
    ) -> OxenResult<Migration> {
        let operations = self.diff_schemas(current_schema, target_schema)?;
        
        let migration = Migration {
            id: self.generate_migration_id(),
            name: name.to_string(),
            operations,
            dependencies: Vec::new(),
            created_at: chrono::Utc::now(),
        };

        Ok(migration)
    }

    /// Apply a migration to the database
    pub async fn apply_migration(
        &self,
        migration: &Migration,
        connection: &dyn crate::connection::DatabaseConnection,
    ) -> OxenResult<()> {
        for operation in &migration.operations {
            let sql = self.operation_to_sql(operation)?;
            connection.execute_command(&sql, &[]).await?;
        }

        // Record migration as applied
        self.record_migration_applied(migration, connection).await?;
        Ok(())
    }

    /// Rollback a migration
    pub async fn rollback_migration(
        &self,
        migration: &Migration,
        connection: &dyn crate::connection::DatabaseConnection,
    ) -> OxenResult<()> {
        for operation in migration.operations.iter().rev() {
            let sql = self.operation_to_rollback_sql(operation)?;
            connection.execute_command(&sql, &[]).await?;
        }

        // Remove migration record
        self.remove_migration_record(migration, connection).await?;
        Ok(())
    }

    /// Generate SQL for an operation
    fn operation_to_sql(&self, operation: &MigrationOp) -> OxenResult<String> {
        match operation {
            MigrationOp::CreateTable { name, columns, indexes } => {
                self.create_table_sql(name, columns, indexes)
            }
            MigrationOp::DropTable { name } => {
                Ok(format!("DROP TABLE IF EXISTS {}", name))
            }
            MigrationOp::AddColumn { table, column } => {
                self.add_column_sql(table, column)
            }
            MigrationOp::DropColumn { table, column } => {
                Ok(format!("ALTER TABLE {} DROP COLUMN {}", table, column))
            }
            MigrationOp::AlterColumn { table, column, new_type, nullable, default } => {
                self.alter_column_sql(table, column, new_type, nullable, default)
            }
            MigrationOp::AddIndex { table, index } => {
                self.add_index_sql(table, index)
            }
            MigrationOp::DropIndex { table, index } => {
                Ok(format!("DROP INDEX IF EXISTS {}", index))
            }
            MigrationOp::AddForeignKey { table, constraint } => {
                self.add_foreign_key_sql(table, constraint)
            }
            MigrationOp::DropForeignKey { table, constraint } => {
                Ok(format!("ALTER TABLE {} DROP CONSTRAINT {}", table, constraint.name))
            }
        }
    }

    /// Generate rollback SQL for an operation
    fn operation_to_rollback_sql(&self, operation: &MigrationOp) -> OxenResult<String> {
        match operation {
            MigrationOp::CreateTable { name, .. } => {
                Ok(format!("DROP TABLE IF EXISTS {}", name))
            }
            MigrationOp::DropTable { name } => {
                // Note: This is simplified - we'd need the original table definition
                Err(OxenError::Migration("Cannot rollback DROP TABLE without original schema".to_string()))
            }
            MigrationOp::AddColumn { table, column } => {
                Ok(format!("ALTER TABLE {} DROP COLUMN {}", table, column.name))
            }
            MigrationOp::DropColumn { table, column } => {
                // Note: This is simplified - we'd need the original column definition
                Err(OxenError::Migration("Cannot rollback DROP COLUMN without original definition".to_string()))
            }
            MigrationOp::AlterColumn { table, column, .. } => {
                // Note: This is simplified - we'd need the original column definition
                Err(OxenError::Migration("Cannot rollback ALTER COLUMN without original definition".to_string()))
            }
            MigrationOp::AddIndex { table, index } => {
                Ok(format!("DROP INDEX IF EXISTS {}", index.name))
            }
            MigrationOp::DropIndex { table, index } => {
                // Note: This is simplified - we'd need the original index definition
                Err(OxenError::Migration("Cannot rollback DROP INDEX without original definition".to_string()))
            }
            MigrationOp::AddForeignKey { table, constraint } => {
                Ok(format!("ALTER TABLE {} DROP CONSTRAINT {}", table, constraint.name))
            }
            MigrationOp::DropForeignKey { table, constraint } => {
                // Note: This is simplified - we'd need the original constraint definition
                Err(OxenError::Migration("Cannot rollback DROP FOREIGN KEY without original definition".to_string()))
            }
        }
    }

    /// Create table SQL
    fn create_table_sql(
        &self,
        name: &str,
        columns: &[ColumnDef],
        indexes: &[IndexDef],
    ) -> OxenResult<String> {
        let mut sql = format!("CREATE TABLE {} (", name);
        
        let column_defs: Vec<String> = columns
            .iter()
            .map(|col| {
                let mut def = format!("{} {}", col.name, col.sql_type);
                
                if !col.nullable {
                    def.push_str(" NOT NULL");
                }
                
                if col.primary_key {
                    def.push_str(" PRIMARY KEY");
                }
                
                if col.unique {
                    def.push_str(" UNIQUE");
                }
                
                if col.auto_increment {
                    match self.database_type {
                        DatabaseType::PostgreSQL => def.push_str(" GENERATED BY DEFAULT AS IDENTITY"),
                        DatabaseType::MySQL => def.push_str(" AUTO_INCREMENT"),
                        DatabaseType::SQLite => def.push_str(" AUTOINCREMENT"),
                    }
                }
                
                if let Some(default_val) = &col.default {
                    def.push_str(&format!(" DEFAULT {}", default_val));
                }
                
                def
            })
            .collect();
        
        sql.push_str(&column_defs.join(", "));
        sql.push(')');
        
        Ok(sql)
    }

    /// Add column SQL
    fn add_column_sql(&self, table: &str, column: &ColumnDef) -> OxenResult<String> {
        let mut sql = format!("ALTER TABLE {} ADD COLUMN {} {}", table, column.name, column.sql_type);
        
        if !column.nullable {
            sql.push_str(" NOT NULL");
        }
        
        if column.unique {
            sql.push_str(" UNIQUE");
        }
        
        if let Some(default_val) = &column.default {
            sql.push_str(&format!(" DEFAULT {}", default_val));
        }
        
        Ok(sql)
    }

    /// Alter column SQL
    fn alter_column_sql(
        &self,
        table: &str,
        column: &str,
        new_type: &str,
        nullable: &Option<bool>,
        default: &Option<String>,
    ) -> OxenResult<String> {
        match self.database_type {
            DatabaseType::PostgreSQL => {
                let mut sql = format!("ALTER TABLE {} ALTER COLUMN {} TYPE {}", table, column, new_type);
                
                if let Some(nullable_val) = nullable {
                    if *nullable_val {
                        sql.push_str(&format!(", ALTER COLUMN {} DROP NOT NULL", column));
                    } else {
                        sql.push_str(&format!(", ALTER COLUMN {} SET NOT NULL", column));
                    }
                }
                
                if let Some(default_val) = default {
                    sql.push_str(&format!(", ALTER COLUMN {} SET DEFAULT {}", column, default_val));
                }
                
                Ok(sql)
            }
            DatabaseType::MySQL => {
                let mut sql = format!("ALTER TABLE {} MODIFY COLUMN {} {}", table, column, new_type);
                
                if let Some(nullable_val) = nullable {
                    if !*nullable_val {
                        sql.push_str(" NOT NULL");
                    }
                }
                
                if let Some(default_val) = default {
                    sql.push_str(&format!(" DEFAULT {}", default_val));
                }
                
                Ok(sql)
            }
            DatabaseType::SQLite => {
                // SQLite has limited ALTER TABLE support
                Err(OxenError::Migration("SQLite does not support ALTER COLUMN".to_string()))
            }
        }
    }

    /// Add index SQL
    fn add_index_sql(&self, table: &str, index: &IndexDef) -> OxenResult<String> {
        let unique = if index.unique { "UNIQUE " } else { "" };
        let columns = index.columns.join(", ");
        Ok(format!("CREATE {}INDEX {} ON {} ({})", unique, index.name, table, columns))
    }

    /// Add foreign key SQL
    fn add_foreign_key_sql(&self, table: &str, constraint: &ForeignKeyDef) -> OxenResult<String> {
        let columns = constraint.columns.join(", ");
        let referenced_columns = constraint.referenced_columns.join(", ");
        
        let mut sql = format!(
            "ALTER TABLE {} ADD CONSTRAINT {} FOREIGN KEY ({}) REFERENCES {} ({})",
            table, constraint.name, columns, constraint.references, referenced_columns
        );
        
        if let Some(on_delete) = &constraint.on_delete {
            sql.push_str(&format!(" ON DELETE {}", on_delete));
        }
        
        if let Some(on_update) = &constraint.on_update {
            sql.push_str(&format!(" ON UPDATE {}", on_update));
        }
        
        Ok(sql)
    }

    /// Diff schemas to generate migration operations
    fn diff_schemas(
        &self,
        current: &HashMap<String, TableSchema>,
        target: &HashMap<String, TableSchema>,
    ) -> OxenResult<Vec<MigrationOp>> {
        let mut operations = Vec::new();
        
        // Find tables to create
        for (table_name, table_schema) in target {
            if !current.contains_key(table_name) {
                operations.push(MigrationOp::CreateTable {
                    name: table_name.clone(),
                    columns: table_schema.columns.clone(),
                    indexes: table_schema.indexes.clone(),
                });
            }
        }
        
        // Find tables to drop
        for table_name in current.keys() {
            if !target.contains_key(table_name) {
                operations.push(MigrationOp::DropTable {
                    name: table_name.clone(),
                });
            }
        }
        
        // Find columns to add/modify for existing tables
        for (table_name, target_schema) in target {
            if let Some(current_schema) = current.get(table_name) {
                let column_ops = self.diff_table_columns(table_name, current_schema, target_schema)?;
                operations.extend(column_ops);
            }
        }
        
        Ok(operations)
    }

    /// Diff table columns
    fn diff_table_columns(
        &self,
        table_name: &str,
        current: &TableSchema,
        target: &TableSchema,
    ) -> OxenResult<Vec<MigrationOp>> {
        let mut operations = Vec::new();
        
        // Find columns to add
        for column in &target.columns {
            if !current.columns.iter().any(|c| c.name == column.name) {
                operations.push(MigrationOp::AddColumn {
                    table: table_name.to_string(),
                    column: column.clone(),
                });
            }
        }
        
        // Find columns to drop
        for column in &current.columns {
            if !target.columns.iter().any(|c| c.name == column.name) {
                operations.push(MigrationOp::DropColumn {
                    table: table_name.to_string(),
                    column: column.name.clone(),
                });
            }
        }
        
        // Find columns to modify
        for target_column in &target.columns {
            if let Some(current_column) = current.columns.iter().find(|c| c.name == target_column.name) {
                if current_column.sql_type != target_column.sql_type
                    || current_column.nullable != target_column.nullable
                    || current_column.default != target_column.default
                {
                    operations.push(MigrationOp::AlterColumn {
                        table: table_name.to_string(),
                        column: target_column.name.clone(),
                        new_type: target_column.sql_type.clone(),
                        nullable: Some(target_column.nullable),
                        default: target_column.default.clone(),
                    });
                }
            }
        }
        
        Ok(operations)
    }

    /// Generate a unique migration ID
    fn generate_migration_id(&self) -> String {
        use std::time::{SystemTime, UNIX_EPOCH};
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        format!("{:016x}", timestamp)
    }

    /// Record migration as applied
    async fn record_migration_applied(
        &self,
        migration: &Migration,
        connection: &dyn crate::connection::DatabaseConnection,
    ) -> OxenResult<()> {
        let sql = "INSERT INTO oxen_migrations (id, name, applied_at) VALUES ($1, $2, $3)";
        let params = vec![
            serde_json::Value::String(migration.id.clone()),
            serde_json::Value::String(migration.name.clone()),
            serde_json::Value::String(migration.created_at.to_rfc3339()),
        ];
        connection.execute_command(sql, &params).await?;
        Ok(())
    }

    /// Remove migration record
    async fn remove_migration_record(
        &self,
        migration: &Migration,
        connection: &dyn crate::connection::DatabaseConnection,
    ) -> OxenResult<()> {
        let sql = "DELETE FROM oxen_migrations WHERE id = $1";
        let params = vec![serde_json::Value::String(migration.id.clone())];
        connection.execute_command(sql, &params).await?;
        Ok(())
    }
}

/// Table schema definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TableSchema {
    pub name: String,
    pub columns: Vec<ColumnDef>,
    pub indexes: Vec<IndexDef>,
    pub foreign_keys: Vec<ForeignKeyDef>,
} 
#!/usr/bin/env python3
"""
OxenORM Configuration Management

Provides production-ready configuration management with environment-based settings,
validation, and security features.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseType(str, Enum):
    """Database types"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: DatabaseType
    host: str = "localhost"
    port: int = 5432
    database: str = "oxenorm"
    username: str = ""
    password: str = ""
    ssl_mode: str = "prefer"
    max_connections: int = 20
    min_connections: int = 5
    connection_timeout: int = 30
    pool_timeout: int = 30
    max_lifetime: int = 3600
    
    @property
    def connection_string(self) -> str:
        """Generate connection string from config"""
        if self.type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database}"
        elif self.type == DatabaseType.POSTGRESQL:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
        elif self.type == DatabaseType.MYSQL:
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = ""
    allowed_hosts: List[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])
    session_timeout: int = 3600
    password_min_length: int = 8
    require_ssl: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60


@dataclass
class PerformanceConfig:
    """Performance configuration"""
    query_cache_size: int = 1000
    query_cache_ttl: int = 300
    prepared_statement_cache_size: int = 100
    connection_pool_size: int = 20
    max_query_time: float = 30.0
    enable_query_logging: bool = True
    enable_performance_monitoring: bool = True
    slow_query_threshold: float = 1.0


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = False


@dataclass
class MigrationConfig:
    """Migration configuration"""
    migrations_dir: str = "migrations"
    auto_migrate: bool = False
    validate_migrations: bool = True
    backup_before_migrate: bool = True
    max_migration_time: int = 300


@dataclass
class FileConfig:
    """File handling configuration"""
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = field(default_factory=lambda: [".txt", ".pdf", ".jpg", ".png"])
    image_max_width: int = 1920
    image_max_height: int = 1080
    enable_image_processing: bool = True
    storage_backend: str = "local"  # local, s3, gcs


@dataclass
class OxenConfig:
    """Main OxenORM configuration"""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    migration: MigrationConfig = field(default_factory=MigrationConfig)
    file: FileConfig = field(default_factory=FileConfig)
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate()
    
    def _validate(self):
        """Validate configuration settings"""
        if not self.database.connection_string:
            raise ValueError("Database connection string is required")
        
        if self.environment == Environment.PRODUCTION:
            if not self.security.secret_key:
                raise ValueError("Secret key is required in production")
            
            if not self.security.require_ssl and self.database.type != DatabaseType.SQLITE:
                raise ValueError("SSL is required in production for non-SQLite databases")
    
    @classmethod
    def from_env(cls) -> 'OxenConfig':
        """Create configuration from environment variables"""
        config = cls()
        
        # Environment
        config.environment = Environment(os.getenv('OXEN_ENVIRONMENT', 'development'))
        config.debug = os.getenv('OXEN_DEBUG', 'false').lower() == 'true'
        
        # Database
        config.database.type = DatabaseType(os.getenv('OXEN_DB_TYPE', 'sqlite'))
        config.database.host = os.getenv('OXEN_DB_HOST', 'localhost')
        config.database.port = int(os.getenv('OXEN_DB_PORT', '5432'))
        config.database.database = os.getenv('OXEN_DB_NAME', 'oxenorm')
        config.database.username = os.getenv('OXEN_DB_USER', '')
        config.database.password = os.getenv('OXEN_DB_PASS', '')
        config.database.max_connections = int(os.getenv('OXEN_DB_MAX_CONNECTIONS', '20'))
        config.database.min_connections = int(os.getenv('OXEN_DB_MIN_CONNECTIONS', '5'))
        
        # Security
        config.security.secret_key = os.getenv('OXEN_SECRET_KEY', '')
        config.security.allowed_hosts = os.getenv('OXEN_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
        config.security.require_ssl = os.getenv('OXEN_REQUIRE_SSL', 'true').lower() == 'true'
        
        # Performance
        config.performance.query_cache_size = int(os.getenv('OXEN_CACHE_SIZE', '1000'))
        config.performance.enable_performance_monitoring = os.getenv('OXEN_ENABLE_MONITORING', 'true').lower() == 'true'
        
        # Logging
        config.logging.level = os.getenv('OXEN_LOG_LEVEL', 'INFO')
        config.logging.file_path = os.getenv('OXEN_LOG_FILE')
        config.logging.enable_file = bool(config.logging.file_path)
        
        # File handling
        config.file.upload_dir = os.getenv('OXEN_UPLOAD_DIR', 'uploads')
        config.file.max_file_size = int(os.getenv('OXEN_MAX_FILE_SIZE', str(10 * 1024 * 1024)))
        
        return config
    
    @classmethod
    def from_file(cls, file_path: str) -> 'OxenConfig':
        """Create configuration from JSON file"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        config = cls()
        
        # Update configuration from file data
        if 'environment' in data:
            config.environment = Environment(data['environment'])
        
        if 'database' in data:
            db_data = data['database']
            config.database.type = DatabaseType(db_data.get('type', 'sqlite'))
            config.database.host = db_data.get('host', 'localhost')
            config.database.port = db_data.get('port', 5432)
            config.database.database = db_data.get('database', 'oxenorm')
            config.database.username = db_data.get('username', '')
            config.database.password = db_data.get('password', '')
        
        if 'security' in data:
            sec_data = data['security']
            config.security.secret_key = sec_data.get('secret_key', '')
            config.security.allowed_hosts = sec_data.get('allowed_hosts', ['localhost'])
        
        if 'performance' in data:
            perf_data = data['performance']
            config.performance.query_cache_size = perf_data.get('query_cache_size', 1000)
            config.performance.enable_performance_monitoring = perf_data.get('enable_monitoring', True)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'environment': self.environment.value,
            'debug': self.debug,
            'database': {
                'type': self.database.type.value,
                'host': self.database.host,
                'port': self.database.port,
                'database': self.database.database,
                'username': self.database.username,
                'max_connections': self.database.max_connections,
                'min_connections': self.database.min_connections
            },
            'security': {
                'allowed_hosts': self.security.allowed_hosts,
                'require_ssl': self.security.require_ssl,
                'session_timeout': self.security.session_timeout
            },
            'performance': {
                'query_cache_size': self.performance.query_cache_size,
                'enable_performance_monitoring': self.performance.enable_performance_monitoring,
                'slow_query_threshold': self.performance.slow_query_threshold
            },
            'logging': {
                'level': self.logging.level,
                'enable_console': self.logging.enable_console,
                'enable_file': self.logging.enable_file
            },
            'migration': {
                'migrations_dir': self.migration.migrations_dir,
                'auto_migrate': self.migration.auto_migrate,
                'validate_migrations': self.migration.validate_migrations
            },
            'file': {
                'upload_dir': self.file.upload_dir,
                'max_file_size': self.file.max_file_size,
                'allowed_extensions': self.file.allowed_extensions
            }
        }
    
    def save_to_file(self, file_path: str):
        """Save configuration to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def get_connection_string(self) -> str:
        """Get database connection string"""
        return self.database.connection_string
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT


# Global configuration instance
_config: Optional[OxenConfig] = None


def get_config() -> OxenConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = OxenConfig.from_env()
    return _config


def set_config(config: OxenConfig):
    """Set global configuration instance"""
    global _config
    _config = config


def load_config_from_file(file_path: str):
    """Load configuration from file and set as global"""
    config = OxenConfig.from_file(file_path)
    set_config(config)


def create_default_config_file(file_path: str = "oxen_config.json"):
    """Create a default configuration file"""
    config = OxenConfig()
    config.save_to_file(file_path)
    print(f"✅ Default configuration created: {file_path}")


def validate_config(config: OxenConfig) -> List[str]:
    """Validate configuration and return list of issues"""
    issues = []
    
    # Database validation
    if not config.database.database:
        issues.append("Database name is required")
    
    if config.database.type != DatabaseType.SQLITE:
        if not config.database.host:
            issues.append("Database host is required for non-SQLite databases")
        if not config.database.username:
            issues.append("Database username is required for non-SQLite databases")
    
    # Security validation
    if config.is_production():
        if not config.security.secret_key:
            issues.append("Secret key is required in production")
        
        if not config.security.require_ssl and config.database.type != DatabaseType.SQLITE:
            issues.append("SSL is required in production for non-SQLite databases")
    
    # Performance validation
    if config.performance.query_cache_size < 1:
        issues.append("Query cache size must be at least 1")
    
    if config.performance.slow_query_threshold < 0:
        issues.append("Slow query threshold must be non-negative")
    
    return issues


if __name__ == "__main__":
    # Create default configuration file
    create_default_config_file() 
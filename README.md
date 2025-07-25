# 🚀 OxenORM

**High-Performance Python ORM with Rust Backend**

OxenORM is a hybrid ORM that combines the developer-friendly Python interface of Tortoise ORM with a high-performance Rust backend for database operations. This architecture provides the best of both worlds: Python's ease of use and Rust's performance.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Python App    │    │   Tortoise ORM   │    │   Rust Backend  │
│                 │◄──►│   (Interface)    │◄──►│   (Engine)      │
│  - Models       │    │  - QuerySet      │    │  - SQL Engine   │
│  - Queries      │    │  - Fields        │    │  - Transactions │
│  - Migrations   │    │  - Backends      │    │  - Connection   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Components

- **Python Layer**: Tortoise ORM for model definitions and query building
- **Bridge Layer**: Custom backend adapter (`oxen.rust_backend`)
- **Rust Layer**: High-performance database engine (`oxen_engine`)
- **Storage Layer**: In-memory storage with future SQLite/PostgreSQL support

## ✨ Features

- ✅ **Full Tortoise ORM Compatibility**: Use existing Tortoise models and queries
- ✅ **High Performance**: Rust backend for database operations
- ✅ **Async Support**: Native async/await throughout the stack
- ✅ **Transaction Support**: ACID-compliant transactions
- ✅ **Schema Generation**: Automatic table creation and migration
- ✅ **In-Memory Storage**: Fast development and testing
- 🔄 **SQLite Support**: Coming soon
- 🔄 **PostgreSQL Support**: Coming soon
- 🔄 **MySQL Support**: Coming soon

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Rust 1.70+
- Git

## 🛠️ Development Setup

### Automated Setup

For a quick development environment setup, run:

```bash
./scripts/setup_dev.sh
```

This script will:
- Check Python and Rust versions
- Create a virtual environment
- Install all dependencies
- Set up pre-commit hooks
- Build the Rust extension

### Manual Setup

1. **Create virtual environment:**
   ```bash
   python -m venv oxenorm_env
   source oxenorm_env/bin/activate  # On Windows: oxenorm_env\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

4. **Build Rust extension:**
   ```bash
   maturin develop --release
   ```

### Development Commands

```bash
# Run tests
make test

# Run tests without coverage
make test-fast

# Run linting
make lint

# Format code
make format

# Check formatting
make format-check

# Run all checks (format, lint, rust checks, tests)
make all-checks

# Clean build artifacts
make clean

# Show all available commands
make help
```

### Code Quality Tools

- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checking
- **Black**: Code formatting
- **Pre-commit**: Git hooks for code quality
- **Cargo clippy**: Rust linting
- **Cargo fmt**: Rust formatting

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Diman2003/OxenORM.git
   cd OxenORM
   ```

2. **Set up development environment:**
   ```bash
   ./scripts/setup_dev.sh
   ```

3. **Run tests:**
   ```bash
   make test
   ```

## 🔄 CI/CD

OxenORM uses GitHub Actions for continuous integration and deployment:

### CI Pipeline

The CI pipeline runs on every push and pull request:

- **Multi-platform testing**: Ubuntu, macOS, Windows
- **Multi-version testing**: Python 3.9, 3.10, 3.11, 3.12
- **Code quality checks**: Ruff linting, MyPy type checking, Black formatting
- **Rust checks**: Cargo clippy, cargo fmt
- **Test coverage**: pytest with coverage reporting
- **Wheel building**: Automatic wheel builds for releases

### Quality Gates

Before merging, all code must pass:

- ✅ All tests passing
- ✅ No linting errors
- ✅ Type checking passes
- ✅ Code formatting is correct
- ✅ Rust code passes clippy checks

### Pre-commit Hooks

Pre-commit hooks automatically run on every commit:

- Code formatting (Black, Ruff)
- Linting (Ruff)
- Type checking (MyPy)
- Import sorting (isort)
- Basic file checks (trailing whitespace, etc.)

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from tortoise import Tortoise, fields
from tortoise.models import Model
from oxen.tortoise_integration import OxenTortoiseIntegration

# Define your models
class User(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)

class Post(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    content = fields.TextField()
    author = fields.ForeignKeyField('models.User', related_name='posts')
    created_at = fields.DatetimeField(auto_now_add=True)

# Use OxenORM
async def main():
    async with OxenTortoiseIntegration(
        db_url="rust://localhost/test_db",
        modules={"models": ["__main__"]}
    ):
        # Create users
        user1 = await User.create(name="Alice", email="alice@example.com")
        user2 = await User.create(name="Bob", email="bob@example.com")
        
        # Create posts
        post1 = await Post.create(
            title="Hello OxenORM!",
            content="This is my first post with OxenORM",
            author=user1
        )
        
        # Query data
        users = await User.all()
        posts = await Post.filter(author=user1)
        
        print(f"Users: {len(users)}")
        print(f"Posts by Alice: {len(posts)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Configuration

### Database URLs

OxenORM uses the `rust://` scheme to identify the Rust backend:

```python
# In-memory database
db_url = "rust://localhost/memory"

# File-based database (coming soon)
db_url = "rust://localhost/path/to/database.db"

# Remote database (coming soon)
db_url = "rust://user:pass@host:port/database"
```

### Tortoise ORM Integration

The integration is seamless - just use the `rust://` URL scheme:

```python
await Tortoise.init(
    db_url="rust://localhost/test_db",
    modules={"models": ["models"]}
)
```

## 🧪 Testing

### Run Integration Tests

```bash
python test_tortoise_rust_integration.py
```

### Test Coverage

The test suite covers:
- ✅ Database connection and initialization
- ✅ Schema generation and table creation
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Query filtering and relationships
- ✅ Transaction support
- ✅ Error handling

## 🏗️ Development

### Project Structure

```
OxenORM/
├── src/                          # Rust backend source
│   ├── lib.rs                    # Main Rust module
│   ├── connection.rs             # Database connections
│   ├── engine.rs                 # SQL engine
│   └── error.rs                  # Error handling
├── oxen/                         # Python package
│   ├── __init__.py
│   ├── rust_backend.py           # Tortoise backend adapter
│   ├── rust_engine.py            # Python-Rust bridge
│   └── tortoise_integration.py   # Integration utilities
├── tests/                        # Test suite
├── examples/                     # Usage examples
├── docs/                         # Documentation
└── Cargo.toml                    # Rust dependencies
```

### Building from Source

1. **Install Rust dependencies:**
   ```bash
   cargo build
   ```

2. **Build Python extension:**
   ```bash
   maturin develop
   ```

3. **Run tests:**
   ```bash
   python -m pytest tests/
   ```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📊 Performance

### Benchmarks

*Coming soon - we'll add performance benchmarks comparing OxenORM to other Python ORMs*

### Expected Improvements

- **Query Performance**: 2-10x faster than pure Python ORMs
- **Memory Usage**: 30-50% reduction in memory footprint
- **Concurrent Operations**: Better handling of high-concurrency workloads

## 🔮 Roadmap

### Phase 1: Core Features ✅
- [x] Tortoise ORM integration
- [x] In-memory storage
- [x] Basic CRUD operations
- [x] Transaction support
- [x] Schema generation

### Phase 2: Storage Backends 🔄
- [ ] SQLite backend
- [ ] PostgreSQL backend
- [ ] MySQL backend
- [ ] Connection pooling

### Phase 3: Advanced Features 📋
- [ ] Query optimization
- [ ] Indexing support
- [ ] Migration system
- [ ] Bulk operations
- [ ] Relationship optimization

### Phase 4: Production Ready 🚀
- [ ] Performance benchmarks
- [ ] Production deployment guides
- [ ] Monitoring and logging
- [ ] Security hardening

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. **Fork and clone the repository**
2. **Set up development environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   maturin develop
   ```

3. **Run tests:**
   ```bash
   python -m pytest tests/
   ```

4. **Run linting:**
   ```bash
   black oxen/ tests/
   flake8 oxen/ tests/
   ```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Tortoise ORM**: For the excellent Python ORM foundation
- **PyO3**: For Python-Rust interoperability
- **Tokio**: For async runtime support
- **SQLx**: For database driver inspiration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Diman2003/OxenORM/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Diman2003/OxenORM/discussions)
- **Documentation**: [Wiki](https://github.com/Diman2003/OxenORM/wiki)

---

**Made with ❤️ by the OxenORM Team** 
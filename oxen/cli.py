#!/usr/bin/env python3
"""
OxenORM CLI Tool

Provides command-line interface for OxenORM operations, particularly migrations.
"""

import argparse
import asyncio
import sys
import os
from typing import Optional, List
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from oxen.rust_engine import OxenEngine
    from oxen.multi_db_engine import MultiDbEngine, DatabaseSwitcher, DatabaseType
    from oxen.migrations import MigrationEngine, Migration, MigrationStatus
    RUST_AVAILABLE = True
except ImportError as e:
    print(f"❌ Required modules not available: {e}")
    RUST_AVAILABLE = False


class OxenCLI:
    """Main CLI class for OxenORM operations."""

    def __init__(self):
        self.parser = self._create_parser()
        self.engine = None
        self.migration_engine = None

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog='oxen',
            description='OxenORM - Fast, async Python ORM with Rust backend',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  oxen migrate status
  oxen migrate create "Add users table"
  oxen migrate rollback 20231201120000
  oxen migrate run
  oxen migrate history
  oxen db test postgresql://user:pass@localhost/db
  oxen db list
  oxen db switch postgres
            """
        )

        # Global options
        parser.add_argument(
            '--database-url',
            '-d',
            help='Database connection URL (e.g., postgresql://user:pass@localhost/db)',
            default=os.getenv('OXEN_DATABASE_URL')
        )
        parser.add_argument(
            '--migrations-dir',
            '-m',
            help='Directory for migration files (default: migrations)',
            default='migrations'
        )
        parser.add_argument(
            '--verbose',
            '-v',
            action='store_true',
            help='Enable verbose output'
        )

        # Subcommands
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands'
        )

        # Database command
        db_parser = subparsers.add_parser(
            'db',
            help='Manage multiple databases'
        )
        db_subparsers = db_parser.add_subparsers(
            dest='db_command',
            help='Database subcommands'
        )

        # db test
        test_parser = db_subparsers.add_parser(
            'test',
            help='Test database connection'
        )
        test_parser.add_argument(
            'connection_string',
            help='Database connection string to test'
        )

        # db info
        info_parser = db_subparsers.add_parser(
            'info',
            help='Get database information'
        )

        # db switch
        switch_parser = db_subparsers.add_parser(
            'switch',
            help='Switch between databases'
        )
        switch_parser.add_argument(
            'database_name',
            help='Name of the database to switch to'
        )

        # db list
        list_parser = db_subparsers.add_parser(
            'list',
            help='List available databases'
        )

        # Migrate command
        migrate_parser = subparsers.add_parser(
            'migrate',
            help='Manage database migrations'
        )
        migrate_subparsers = migrate_parser.add_subparsers(
            dest='migrate_command',
            help='Migration subcommands'
        )

        # migrate status
        status_parser = migrate_subparsers.add_parser(
            'status',
            help='Show migration status'
        )
        status_parser.add_argument(
            '--format',
            choices=['table', 'json', 'simple'],
            default='table',
            help='Output format (default: table)'
        )

        # migrate create
        create_parser = migrate_subparsers.add_parser(
            'create',
            help='Create a new migration'
        )
        create_parser.add_argument(
            'description',
            help='Migration description'
        )
        create_parser.add_argument(
            '--author',
            help='Migration author'
        )
        create_parser.add_argument(
            '--up-sql',
            help='Up migration SQL (or use --file)'
        )
        create_parser.add_argument(
            '--down-sql',
            help='Down migration SQL (or use --file)'
        )
        create_parser.add_argument(
            '--file',
            help='SQL file containing up and down migrations'
        )

        # migrate run
        run_parser = migrate_subparsers.add_parser(
            'run',
            help='Run pending migrations'
        )
        run_parser.add_argument(
            '--target',
            help='Target migration version (default: run all pending)'
        )
        run_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be run without executing'
        )

        # migrate rollback
        rollback_parser = migrate_subparsers.add_parser(
            'rollback',
            help='Rollback migrations'
        )
        rollback_parser.add_argument(
            'target_version',
            help='Target version to rollback to'
        )
        rollback_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be rolled back without executing'
        )

        # migrate history
        history_parser = migrate_subparsers.add_parser(
            'history',
            help='Show migration history'
        )
        history_parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of recent migrations to show (default: 10)'
        )
        history_parser.add_argument(
            '--format',
            choices=['table', 'json', 'simple'],
            default='table',
            help='Output format (default: table)'
        )

        # migrate validate
        validate_parser = migrate_subparsers.add_parser(
            'validate',
            help='Validate migration files'
        )
        validate_parser.add_argument(
            '--migration',
            help='Specific migration to validate (default: validate all)'
        )

        return parser

    async def _connect(self, database_url: str) -> bool:
        """Connect to the database."""
        if not RUST_AVAILABLE:
            print("❌ Rust engine not available. Please build the Rust extension first.")
            return False

        if not database_url:
            print("❌ Database URL is required. Use --database-url or set OXEN_DATABASE_URL environment variable.")
            return False

        try:
            self.engine = OxenEngine(database_url)
            self.engine.configure_pool(max_connections=5, min_connections=1)
            await self.engine.connect()
            
            self.migration_engine = MigrationEngine(
                self.engine,
                migrations_dir=self.parser.parse_args().migrations_dir
            )
            
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False

    async def _disconnect(self):
        """Disconnect from the database."""
        if self.engine:
            await self.engine.close()

    def _print_table(self, headers: List[str], rows: List[List[str]]):
        """Print data in table format."""
        if not rows:
            print("No data to display.")
            return

        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Print header
        header_str = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        print(header_str)
        print("-" * len(header_str))

        # Print rows
        for row in rows:
            row_str = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
            print(row_str)

    def _print_json(self, data):
        """Print data in JSON format."""
        import json
        print(json.dumps(data, indent=2, default=str))

    def _print_simple(self, data):
        """Print data in simple format."""
        if isinstance(data, list):
            for item in data:
                print(item)
        elif isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}: {value}")

    async def cmd_migrate_status(self, args):
        """Handle 'migrate status' command."""
        print("📊 Migration Status")
        print("=" * 40)

        status = await self.migration_engine.get_migration_status()
        
        if args.format == 'json':
            self._print_json(status)
        elif args.format == 'simple':
            self._print_simple(status)
        else:  # table format
            headers = ["Metric", "Value"]
            rows = [
                ["Applied Migrations", str(status['applied_count'])],
                ["Pending Migrations", str(status['pending_count'])],
                ["Current Version", status['current_version'] or "None"],
                ["Latest Version", status['latest_version'] or "None"]
            ]
            self._print_table(headers, rows)

            if status['applied_migrations']:
                print(f"\n📋 Applied Migrations ({len(status['applied_migrations'])}):")
                for version in status['applied_migrations']:
                    print(f"  ✅ {version}")

            if status['pending_migrations']:
                print(f"\n⏳ Pending Migrations ({len(status['pending_migrations'])}):")
                for version in status['pending_migrations']:
                    print(f"  ⏸️  {version}")

    async def cmd_migrate_create(self, args):
        """Handle 'migrate create' command."""
        print("🆕 Creating New Migration")
        print("=" * 40)

        # Get SQL content
        up_sql = args.up_sql
        down_sql = args.down_sql

        if args.file:
            # Read from file
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"❌ File not found: {args.file}")
                return

            content = file_path.read_text()
            
            # Simple parsing: look for -- UP and -- DOWN markers
            if '-- UP' in content and '-- DOWN' in content:
                parts = content.split('-- UP')
                if len(parts) > 1:
                    up_down_parts = parts[1].split('-- DOWN')
                    if len(up_down_parts) > 1:
                        up_sql = up_down_parts[0].strip()
                        down_sql = up_down_parts[1].strip()
            else:
                # Assume entire content is up migration
                up_sql = content
                down_sql = "-- Rollback SQL here"

        if not up_sql:
            print("❌ Up migration SQL is required. Use --up-sql or --file.")
            return

        if not down_sql:
            down_sql = "-- Rollback SQL here"

        try:
            migration = await self.migration_engine.create_migration(
                description=args.description,
                up_sql=up_sql,
                down_sql=down_sql,
                author=args.author
            )

            print(f"✅ Migration created successfully!")
            print(f"📁 File: {migration.name}")
            print(f"🆔 Version: {migration.version}")
            print(f"📝 Description: {migration.description}")
            if migration.author:
                print(f"👤 Author: {migration.author}")

        except Exception as e:
            print(f"❌ Failed to create migration: {e}")

    async def cmd_migrate_run(self, args):
        """Handle 'migrate run' command."""
        print("▶️  Running Migrations")
        print("=" * 40)

        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
            print()

            plan = await self.migration_engine.create_migration_plan(args.target)
            
            if not plan.migrations_to_run:
                print("✅ No pending migrations to run.")
                return

            print(f"📋 Would run {len(plan.migrations_to_run)} migrations:")
            for migration in plan.migrations_to_run:
                print(f"  ▶️  {migration.version}: {migration.name}")
                if migration.description:
                    print(f"     📝 {migration.description}")

            if not plan.is_valid():
                print(f"\n⚠️  Plan has conflicts:")
                for conflict in plan.conflicts:
                    print(f"  ❌ {conflict}")
        else:
            result = await self.migration_engine.run_migrations(args.target)
            
            if result['success']:
                print(f"✅ Successfully ran {result['migrations_run']} migrations")
                if result['migrations_run'] > 0:
                    print(f"⏱️  Execution time: {result['execution_time_ms']}ms")
            else:
                print(f"❌ Migration failed: {result.get('error', 'Unknown error')}")
                if result.get('errors'):
                    for error in result['errors']:
                        print(f"  ❌ {error}")

    async def cmd_migrate_rollback(self, args):
        """Handle 'migrate rollback' command."""
        print("⏪ Rolling Back Migrations")
        print("=" * 40)

        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
            print()

            plan = await self.migration_engine.create_migration_plan(args.target_version)
            
            if not plan.migrations_to_rollback:
                print("✅ No migrations to rollback.")
                return

            print(f"📋 Would rollback {len(plan.migrations_to_rollback)} migrations:")
            for migration in plan.migrations_to_rollback:
                print(f"  ⏪ {migration.version}: {migration.name}")
                if migration.description:
                    print(f"     📝 {migration.description}")
        else:
            result = await self.migration_engine.rollback_migrations(args.target_version)
            
            if result['success']:
                print(f"✅ Successfully rolled back {result['migrations_rolled_back']} migrations")
                if result['migrations_rolled_back'] > 0:
                    print(f"⏱️  Execution time: {result['execution_time_ms']}ms")
            else:
                print(f"❌ Rollback failed: {result.get('error', 'Unknown error')}")
                if result.get('errors'):
                    for error in result['errors']:
                        print(f"  ❌ {error}")

    async def cmd_migrate_history(self, args):
        """Handle 'migrate history' command."""
        print("📜 Migration History")
        print("=" * 40)

        history = await self.migration_engine.get_migration_history()
        
        # Limit the history
        history = history[-args.limit:] if args.limit > 0 else history

        if not history:
            print("No migration history found.")
            return

        if args.format == 'json':
            self._print_json(history)
        elif args.format == 'simple':
            for entry in history:
                print(f"{entry['version']}: {entry['name']} ({entry['status']})")
        else:  # table format
            headers = ["Version", "Name", "Status", "Executed At", "Duration (ms)"]
            rows = []
            for entry in history:
                rows.append([
                    entry['version'],
                    entry['name'][:30] + "..." if len(entry['name']) > 30 else entry['name'],
                    entry['status'],
                    entry['executed_at'] or "N/A",
                    str(entry['execution_time_ms'] or "N/A")
                ])
            self._print_table(headers, rows)

    async def cmd_migrate_validate(self, args):
        """Handle 'migrate validate' command."""
        print("🔍 Validating Migrations")
        print("=" * 40)

        if args.migration:
            # Validate specific migration
            migration = self.migration_engine.get_migration_by_version(args.migration)
            if not migration:
                print(f"❌ Migration {args.migration} not found.")
                return

            validation = await self.migration_engine.validate_migration(migration)
            self._print_validation_result(migration, validation)
        else:
            # Validate all migrations
            migrations = self.migration_engine.list_migrations()
            
            if not migrations:
                print("No migration files found.")
                return

            all_valid = True
            for filepath in migrations:
                migration = self.migration_engine.generator.load_migration_from_file(filepath)
                validation = await self.migration_engine.validate_migration(migration)
                
                if not validation['valid']:
                    all_valid = False
                
                self._print_validation_result(migration, validation)
                print()

            if all_valid:
                print("✅ All migrations are valid!")
            else:
                print("❌ Some migrations have validation errors.")

    def _print_validation_result(self, migration: Migration, validation: dict):
        """Print validation result for a migration."""
        print(f"📋 Migration: {migration.name} (v{migration.version})")
        
        if validation['valid']:
            print("  ✅ Valid")
        else:
            print("  ❌ Invalid")
            for error in validation['errors']:
                print(f"    ❌ {error}")
        
        if validation['warnings']:
            for warning in validation['warnings']:
                print(f"    ⚠️  {warning}")

    async def cmd_db_test(self, args):
        """Handle 'db test' command."""
        print("🔍 Testing Database Connection")
        print("=" * 40)

        try:
            is_connected = await test_database_connection(args.connection_string)
            if is_connected:
                print(f"✅ Connection successful: {args.connection_string}")
            else:
                print(f"❌ Connection failed: {args.connection_string}")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")

    async def cmd_db_info(self, args):
        """Handle 'db info' command."""
        print("📊 Database Information")
        print("=" * 40)

        if not self.db_switcher.get_current_engine():
            print("❌ No database connected. Use 'oxen db switch <database>' first.")
            return

        try:
            engine = self.db_switcher.get_current_engine()
            info = await engine.get_database_info()
            
            headers = ["Property", "Value"]
            rows = [
                ["Database Type", info.get('database_type', 'Unknown')],
                ["Version", info.get('version', 'Unknown')],
                ["Connection String", info.get('connection_string', 'Unknown')],
            ]
            self._print_table(headers, rows)
        except Exception as e:
            print(f"❌ Failed to get database info: {e}")

    async def cmd_db_switch(self, args):
        """Handle 'db switch' command."""
        print("🔄 Switching Database")
        print("=" * 40)

        try:
            engine = await self.db_switcher.switch_to(args.database_name)
            print(f"✅ Switched to database: {args.database_name}")
            print(f"   Type: {engine.get_database_type().value}")
        except Exception as e:
            print(f"❌ Failed to switch database: {e}")

    async def cmd_db_list(self, args):
        """Handle 'db list' command."""
        print("📋 Available Databases")
        print("=" * 40)

        databases = self.db_switcher.list_databases()
        if not databases:
            print("No databases configured.")
            return

        headers = ["Name", "Type", "Status"]
        rows = []
        for db_name in databases:
            try:
                engine = self.db_switcher.engines[db_name]
                status = "Connected" if engine.is_connected() else "Disconnected"
                rows.append([db_name, engine.get_database_type().value, status])
            except Exception:
                rows.append([db_name, "Unknown", "Error"])

        self._print_table(headers, rows)

    async def run(self, args: Optional[List[str]] = None):
        """Run the CLI with the given arguments."""
        parsed_args = self.parser.parse_args(args)

        if not parsed_args.command:
            self.parser.print_help()
            return

        if parsed_args.command == 'migrate':
            if not parsed_args.migrate_command:
                print("❌ Migration subcommand is required.")
                print("Use 'oxen migrate --help' for available subcommands.")
                return

            # Connect to database for migration commands
            if not await self._connect(parsed_args.database_url):
                return

            try:
                if parsed_args.migrate_command == 'status':
                    await self.cmd_migrate_status(parsed_args)
                elif parsed_args.migrate_command == 'create':
                    await self.cmd_migrate_create(parsed_args)
                elif parsed_args.migrate_command == 'run':
                    await self.cmd_migrate_run(parsed_args)
                elif parsed_args.migrate_command == 'rollback':
                    await self.cmd_migrate_rollback(parsed_args)
                elif parsed_args.migrate_command == 'history':
                    await self.cmd_migrate_history(parsed_args)
                elif parsed_args.migrate_command == 'validate':
                    await self.cmd_migrate_validate(parsed_args)
                else:
                    print(f"❌ Unknown migration command: {parsed_args.migrate_command}")
            finally:
                await self._disconnect()

        elif parsed_args.command == 'db':
            if not parsed_args.db_command:
                print("❌ Database subcommand is required.")
                print("Use 'oxen db --help' for available subcommands.")
                return

            # Initialize database switcher
            self.db_switcher = DatabaseSwitcher()

            try:
                if parsed_args.db_command == 'test':
                    await self.cmd_db_test(parsed_args)
                elif parsed_args.db_command == 'info':
                    await self.cmd_db_info(parsed_args)
                elif parsed_args.db_command == 'switch':
                    await self.cmd_db_switch(parsed_args)
                elif parsed_args.db_command == 'list':
                    await self.cmd_db_list(parsed_args)
                else:
                    print(f"❌ Unknown database command: {parsed_args.db_command}")
            finally:
                await self.db_switcher.close_all()


def main():
    """Main entry point for the CLI."""
    cli = OxenCLI()
    
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ CLI error: {e}")
        if '--verbose' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main() 
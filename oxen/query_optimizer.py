#!/usr/bin/env python3
"""
Query Optimization System for OxenORM

This module provides query plan analysis, performance monitoring,
and optimization suggestions for database queries.
"""

import time
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class QueryType(Enum):
    """Types of database queries."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"


class OptimizationLevel(Enum):
    """Levels of query optimization."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QueryPlan:
    """Query execution plan information."""
    sql: str
    query_type: QueryType
    execution_time: float
    rows_affected: int
    timestamp: datetime
    database_type: str
    plan_details: Dict[str, Any] = field(default_factory=dict)
    optimization_suggestions: List[str] = field(default_factory=list)
    performance_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'sql': self.sql,
            'query_type': self.query_type.value,
            'execution_time': self.execution_time,
            'rows_affected': self.rows_affected,
            'timestamp': self.timestamp.isoformat(),
            'database_type': self.database_type,
            'plan_details': self.plan_details,
            'optimization_suggestions': self.optimization_suggestions,
            'performance_score': self.performance_score
        }


@dataclass
class IndexRecommendation:
    """Index recommendation for query optimization."""
    table_name: str
    column_name: str
    index_type: str
    reason: str
    estimated_improvement: float
    priority: OptimizationLevel


class QueryAnalyzer:
    """Analyzes SQL queries for optimization opportunities."""
    
    def __init__(self):
        self.patterns = {
            'full_table_scan': r'\bFROM\s+(\w+)\s+(?!WHERE|JOIN|LIMIT)',
            'missing_index': r'\bWHERE\s+(\w+)\s*[=<>!]',
            'inefficient_join': r'\bJOIN\s+(\w+)\s+ON\s+(\w+\.\w+)\s*=\s*(\w+\.\w+)',
            'select_star': r'\bSELECT\s+\*\b',
            'no_limit': r'\bSELECT\b(?!.*\bLIMIT\b)',
            'inefficient_order': r'\bORDER BY\s+(\w+)\b(?!.*\bINDEX\b)',
            'subquery_in_where': r'\bWHERE\s+.*\bSELECT\b',
            'like_without_index': r'\bLIKE\s+[\'"]%[^\'"]*[\'"]',
        }
    
    def analyze_query(self, sql: str, execution_time: float, rows_affected: int) -> QueryPlan:
        """Analyze a SQL query for optimization opportunities."""
        query_type = self._detect_query_type(sql)
        plan_details = self._extract_plan_details(sql)
        suggestions = self._generate_suggestions(sql, execution_time, rows_affected)
        performance_score = self._calculate_performance_score(sql, execution_time, rows_affected)
        
        return QueryPlan(
            sql=sql,
            query_type=query_type,
            execution_time=execution_time,
            rows_affected=rows_affected,
            timestamp=datetime.now(),
            database_type="sqlite",  # For now, hardcoded
            plan_details=plan_details,
            optimization_suggestions=suggestions,
            performance_score=performance_score
        )
    
    def _detect_query_type(self, sql: str) -> QueryType:
        """Detect the type of SQL query."""
        sql_upper = sql.upper().strip()
        if sql_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif sql_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif sql_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif sql_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif sql_upper.startswith('CREATE'):
            return QueryType.CREATE
        elif sql_upper.startswith('DROP'):
            return QueryType.DROP
        elif sql_upper.startswith('ALTER'):
            return QueryType.ALTER
        else:
            return QueryType.SELECT  # Default
    
    def _extract_plan_details(self, sql: str) -> Dict[str, Any]:
        """Extract execution plan details from SQL."""
        details = {
            'tables_involved': self._extract_tables(sql),
            'joins': self._extract_joins(sql),
            'where_conditions': self._extract_where_conditions(sql),
            'order_by': self._extract_order_by(sql),
            'group_by': self._extract_group_by(sql),
            'has_limit': 'LIMIT' in sql.upper(),
            'has_offset': 'OFFSET' in sql.upper(),
        }
        return details
    
    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL."""
        # Simple regex to extract table names
        tables = re.findall(r'\bFROM\s+(\w+)', sql, re.IGNORECASE)
        tables.extend(re.findall(r'\bJOIN\s+(\w+)', sql, re.IGNORECASE))
        return list(set(tables))
    
    def _extract_joins(self, sql: str) -> List[Dict[str, str]]:
        """Extract JOIN clauses from SQL."""
        joins = []
        join_pattern = r'\bJOIN\s+(\w+)\s+ON\s+([^,\s]+)\s*=\s*([^,\s]+)'
        for match in re.finditer(join_pattern, sql, re.IGNORECASE):
            joins.append({
                'table': match.group(1),
                'left_column': match.group(2),
                'right_column': match.group(3)
            })
        return joins
    
    def _extract_where_conditions(self, sql: str) -> List[str]:
        """Extract WHERE conditions from SQL."""
        where_match = re.search(r'\bWHERE\s+(.*?)(?:\bGROUP BY\b|\bORDER BY\b|\bLIMIT\b|$)', sql, re.IGNORECASE | re.DOTALL)
        if where_match:
            conditions = where_match.group(1).strip()
            return [cond.strip() for cond in conditions.split('AND')]
        return []
    
    def _extract_order_by(self, sql: str) -> List[str]:
        """Extract ORDER BY clauses from SQL."""
        order_match = re.search(r'\bORDER BY\s+(.*?)(?:\bLIMIT\b|$)', sql, re.IGNORECASE)
        if order_match:
            return [col.strip() for col in order_match.group(1).split(',')]
        return []
    
    def _extract_group_by(self, sql: str) -> List[str]:
        """Extract GROUP BY clauses from SQL."""
        group_match = re.search(r'\bGROUP BY\s+(.*?)(?:\bORDER BY\b|\bLIMIT\b|$)', sql, re.IGNORECASE)
        if group_match:
            return [col.strip() for col in group_match.group(1).split(',')]
        return []
    
    def _generate_suggestions(self, sql: str, execution_time: float, rows_affected: int) -> List[str]:
        """Generate optimization suggestions based on query analysis."""
        suggestions = []
        
        # Check for common optimization opportunities
        if re.search(self.patterns['select_star'], sql, re.IGNORECASE):
            suggestions.append("Consider selecting specific columns instead of using SELECT *")
        
        if re.search(self.patterns['no_limit'], sql, re.IGNORECASE) and QueryType.SELECT == self._detect_query_type(sql):
            suggestions.append("Consider adding LIMIT clause to prevent large result sets")
        
        if re.search(self.patterns['like_without_index'], sql, re.IGNORECASE):
            suggestions.append("LIKE queries with leading wildcards cannot use indexes effectively")
        
        if re.search(self.patterns['subquery_in_where'], sql, re.IGNORECASE):
            suggestions.append("Consider using JOIN instead of subquery in WHERE clause")
        
        if execution_time > 1.0:  # More than 1 second
            suggestions.append("Query execution time is high - consider adding indexes")
        
        if rows_affected > 1000:
            suggestions.append("Large number of rows affected - consider batching operations")
        
        # Check for missing indexes
        where_conditions = self._extract_where_conditions(sql)
        for condition in where_conditions:
            if re.search(r'\b(\w+)\s*[=<>!]', condition):
                suggestions.append(f"Consider adding index on column used in WHERE clause")
        
        return suggestions
    
    def _calculate_performance_score(self, sql: str, execution_time: float, rows_affected: int) -> float:
        """Calculate a performance score (0-100, higher is better)."""
        score = 100.0
        
        # Penalize for execution time
        if execution_time > 1.0:
            score -= min(30, execution_time * 10)
        
        # Penalize for large result sets
        if rows_affected > 1000:
            score -= min(20, rows_affected / 100)
        
        # Penalize for inefficient patterns
        if re.search(self.patterns['select_star'], sql, re.IGNORECASE):
            score -= 10
        
        if re.search(self.patterns['like_without_index'], sql, re.IGNORECASE):
            score -= 15
        
        if re.search(self.patterns['subquery_in_where'], sql, re.IGNORECASE):
            score -= 20
        
        return max(0, score)


class IndexAnalyzer:
    """Analyzes database schema for index recommendations."""
    
    def __init__(self):
        self.recommendations = []
    
    def analyze_schema(self, tables_info: Dict[str, Any]) -> List[IndexRecommendation]:
        """Analyze database schema for index recommendations."""
        recommendations = []
        
        for table_name, table_info in tables_info.items():
            # Analyze foreign key columns
            for column in table_info.get('columns', []):
                if column.get('is_foreign_key'):
                    recommendations.append(IndexRecommendation(
                        table_name=table_name,
                        column_name=column['name'],
                        index_type='INDEX',
                        reason='Foreign key column for join performance',
                        estimated_improvement=0.8,
                        priority=OptimizationLevel.HIGH
                    ))
                
                # Analyze WHERE clause columns
                if column.get('used_in_where'):
                    recommendations.append(IndexRecommendation(
                        table_name=table_name,
                        column_name=column['name'],
                        index_type='INDEX',
                        reason='Frequently used in WHERE clauses',
                        estimated_improvement=0.6,
                        priority=OptimizationLevel.MEDIUM
                    ))
                
                # Analyze ORDER BY columns
                if column.get('used_in_order_by'):
                    recommendations.append(IndexRecommendation(
                        table_name=table_name,
                        column_name=column['name'],
                        index_type='INDEX',
                        reason='Used in ORDER BY clauses',
                        estimated_improvement=0.5,
                        priority=OptimizationLevel.MEDIUM
                    ))
        
        return recommendations


class QueryOptimizer:
    """Main query optimization system."""
    
    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self.index_analyzer = IndexAnalyzer()
        self.query_history: List[QueryPlan] = []
        self.performance_thresholds = {
            'slow_query_threshold': 1.0,  # seconds
            'large_result_threshold': 1000,  # rows
            'critical_performance_score': 50.0
        }
    
    def optimize_query(self, sql: str, execution_time: float, rows_affected: int) -> QueryPlan:
        """Analyze and optimize a query."""
        plan = self.analyzer.analyze_query(sql, execution_time, rows_affected)
        self.query_history.append(plan)
        
        # Check if query needs immediate attention
        if execution_time > self.performance_thresholds['slow_query_threshold']:
            plan.optimization_suggestions.append("CRITICAL: Query execution time exceeds threshold")
        
        if rows_affected > self.performance_thresholds['large_result_threshold']:
            plan.optimization_suggestions.append("WARNING: Large number of rows affected")
        
        if plan.performance_score < self.performance_thresholds['critical_performance_score']:
            plan.optimization_suggestions.append("CRITICAL: Low performance score detected")
        
        return plan
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics."""
        if not self.query_history:
            return {}
        
        total_queries = len(self.query_history)
        avg_execution_time = sum(p.execution_time for p in self.query_history) / total_queries
        avg_performance_score = sum(p.performance_score for p in self.query_history) / total_queries
        
        slow_queries = [p for p in self.query_history if p.execution_time > self.performance_thresholds['slow_query_threshold']]
        critical_queries = [p for p in self.query_history if p.performance_score < self.performance_thresholds['critical_performance_score']]
        
        return {
            'total_queries': total_queries,
            'avg_execution_time': avg_execution_time,
            'avg_performance_score': avg_performance_score,
            'slow_queries_count': len(slow_queries),
            'critical_queries_count': len(critical_queries),
            'optimization_suggestions_count': sum(len(p.optimization_suggestions) for p in self.query_history)
        }
    
    def get_slow_queries(self, threshold: Optional[float] = None) -> List[QueryPlan]:
        """Get queries that exceed the performance threshold."""
        threshold = threshold or self.performance_thresholds['slow_query_threshold']
        return [p for p in self.query_history if p.execution_time > threshold]
    
    def get_critical_queries(self) -> List[QueryPlan]:
        """Get queries with critical performance issues."""
        return [p for p in self.query_history if p.performance_score < self.performance_thresholds['critical_performance_score']]
    
    def generate_index_recommendations(self, schema_info: Dict[str, Any]) -> List[IndexRecommendation]:
        """Generate index recommendations based on query history and schema."""
        return self.index_analyzer.analyze_schema(schema_info)
    
    def export_performance_report(self, filename: str) -> None:
        """Export performance report to JSON file."""
        report = {
            'performance_stats': self.get_performance_stats(),
            'slow_queries': [p.to_dict() for p in self.get_slow_queries()],
            'critical_queries': [p.to_dict() for p in self.get_critical_queries()],
            'all_queries': [p.to_dict() for p in self.query_history]
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
    
    def clear_history(self) -> None:
        """Clear query history."""
        self.query_history.clear()


# Global optimizer instance
_global_optimizer = QueryOptimizer()


def get_optimizer() -> QueryOptimizer:
    """Get the global query optimizer instance."""
    return _global_optimizer


def optimize_query(sql: str, execution_time: float, rows_affected: int) -> QueryPlan:
    """Optimize a query using the global optimizer."""
    return _global_optimizer.optimize_query(sql, execution_time, rows_affected)


def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics."""
    return _global_optimizer.get_performance_stats()


def export_performance_report(filename: str) -> None:
    """Export performance report."""
    _global_optimizer.export_performance_report(filename) 
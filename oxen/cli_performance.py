#!/usr/bin/env python3
"""
OxenORM Performance CLI

Command-line interface for running performance tests, monitoring, and generating reports.
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import List, Optional
import time

from .monitoring import PerformanceMonitor, get_performance_monitor, enable_performance_monitoring
from benchmarks.performance_test import PerformanceBenchmark


class PerformanceCLI:
    """CLI for OxenORM performance testing and monitoring."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="OxenORM Performance Testing and Monitoring CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Run full benchmark suite
  python -m oxen.cli_performance benchmark --full
  
  # Run quick benchmark with custom record counts
  python -m oxen.cli_performance benchmark --records 100 1000 5000
  
  # Start monitoring
  python -m oxen.cli_performance monitor --start
  
  # Generate performance report
  python -m oxen.cli_performance report --output report.json
  
  # Export metrics
  python -m oxen.cli_performance export --format json
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Benchmark command
        benchmark_parser = subparsers.add_parser('benchmark', help='Run performance benchmarks')
        benchmark_parser.add_argument('--full', action='store_true', help='Run full benchmark suite')
        benchmark_parser.add_argument('--records', type=int, nargs='+', default=[100, 1000, 10000],
                                    help='Record counts for benchmarking')
        benchmark_parser.add_argument('--output', type=str, help='Output file for results')
        benchmark_parser.add_argument('--database', type=str, default='sqlite:///benchmark.db',
                                    help='Database URL for benchmarking')
        
        # Monitor command
        monitor_parser = subparsers.add_parser('monitor', help='Performance monitoring')
        monitor_parser.add_argument('--start', action='store_true', help='Start monitoring')
        monitor_parser.add_argument('--stop', action='store_true', help='Stop monitoring')
        monitor_parser.add_argument('--status', action='store_true', help='Show monitoring status')
        monitor_parser.add_argument('--interval', type=float, default=5.0,
                                  help='Monitoring interval in seconds')
        
        # Report command
        report_parser = subparsers.add_parser('report', help='Generate performance reports')
        report_parser.add_argument('--output', type=str, help='Output file for report')
        report_parser.add_argument('--format', choices=['json', 'html', 'text'], default='json',
                                 help='Report format')
        report_parser.add_argument('--time-window', type=int, default=3600,
                                 help='Time window in seconds for analysis')
        
        # Export command
        export_parser = subparsers.add_parser('export', help='Export performance metrics')
        export_parser.add_argument('--output', type=str, help='Output file')
        export_parser.add_argument('--format', choices=['json', 'csv'], default='json',
                                 help='Export format')
        export_parser.add_argument('--time-window', type=int, default=3600,
                                 help='Time window in seconds')
        
        # Analyze command
        analyze_parser = subparsers.add_parser('analyze', help='Analyze performance data')
        analyze_parser.add_argument('--input', type=str, required=True, help='Input file to analyze')
        analyze_parser.add_argument('--output', type=str, help='Output file for analysis')
        analyze_parser.add_argument('--threshold', type=float, default=1000,
                                  help='Slow query threshold in milliseconds')
        
        return parser
    
    async def run_benchmark(self, args):
        """Run performance benchmarks."""
        print("🚀 Starting OxenORM Performance Benchmarks")
        print("=" * 60)
        
        # Determine record counts
        if args.full:
            record_counts = [100, 1000, 10000, 50000, 100000]
            print("📊 Running full benchmark suite...")
        else:
            record_counts = args.records
            print(f"📊 Running benchmarks with {len(record_counts)} record count(s)...")
        
        # Create benchmark instance
        benchmark = PerformanceBenchmark(args.database)
        
        try:
            # Run benchmarks
            start_time = time.time()
            suite = await benchmark.run_benchmarks(record_counts)
            end_time = time.time()
            
            # Print results
            print(f"\n⏱️  Benchmark completed in {end_time - start_time:.2f} seconds")
            benchmark.print_summary(suite)
            
            # Save results
            if args.output:
                filename = benchmark.save_results(suite, args.output)
            else:
                filename = benchmark.save_results(suite)
            
            print(f"\n💾 Results saved to: {filename}")
            
            # Performance insights
            self._print_performance_insights(suite)
            
        except Exception as e:
            print(f"❌ Benchmark failed: {e}")
            sys.exit(1)
        finally:
            await benchmark.cleanup_database()
    
    async def run_monitor(self, args):
        """Handle monitoring commands."""
        monitor = get_performance_monitor()
        
        if args.start:
            print("🔍 Starting performance monitoring...")
            enable_performance_monitoring()
            print("✅ Monitoring started")
            
            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(args.interval)
                    stats = monitor.get_query_statistics()
                    print(f"📊 Active queries: {stats.get('total_queries', 0)}, "
                          f"Avg duration: {stats.get('avg_duration', 0):.2f}ms")
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
        
        elif args.stop:
            print("🛑 Stopping performance monitoring...")
            from .monitoring import disable_performance_monitoring
            disable_performance_monitoring()
            print("✅ Monitoring stopped")
        
        elif args.status:
            stats = monitor.get_query_statistics()
            print("📊 Monitoring Status:")
            print(f"  Total queries: {stats.get('total_queries', 0)}")
            print(f"  Average duration: {stats.get('avg_duration', 0):.2f}ms")
            print(f"  Success rate: {stats.get('success_rate', 0):.1%}")
            print(f"  Queries per second: {stats.get('queries_per_second', 0):.1f}")
    
    async def run_report(self, args):
        """Generate performance reports."""
        print("📋 Generating Performance Report")
        print("=" * 60)
        
        monitor = get_performance_monitor()
        
        # Generate report
        report = monitor.get_performance_report()
        
        if args.format == 'json':
            output = json.dumps(report, indent=2)
        elif args.format == 'text':
            output = self._format_text_report(report)
        elif args.format == 'html':
            output = self._format_html_report(report)
        
        # Save or print
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"💾 Report saved to: {args.output}")
        else:
            print(output)
    
    async def run_export(self, args):
        """Export performance metrics."""
        print("📤 Exporting Performance Metrics")
        print("=" * 60)
        
        monitor = get_performance_monitor()
        
        if args.format == 'json':
            filename = monitor.export_metrics(args.output)
        elif args.format == 'csv':
            filename = self._export_csv_metrics(monitor, args.output)
        
        print(f"💾 Metrics exported to: {filename}")
    
    async def run_analyze(self, args):
        """Analyze performance data."""
        print("🔍 Analyzing Performance Data")
        print("=" * 60)
        
        # Load input file
        try:
            with open(args.input, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load input file: {e}")
            sys.exit(1)
        
        # Analyze data
        analysis = self._analyze_performance_data(data, args.threshold)
        
        # Save or print results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"💾 Analysis saved to: {args.output}")
        else:
            print(json.dumps(analysis, indent=2))
    
    def _print_performance_insights(self, suite):
        """Print performance insights from benchmark results."""
        print("\n💡 Performance Insights:")
        print("-" * 40)
        
        if not suite.summary.get('performance_ranking'):
            print("No performance data available")
            return
        
        # Get fastest framework
        fastest = suite.summary['performance_ranking'][0]
        print(f"🏆 Fastest framework: {fastest[0]} ({fastest[1]:.2f}ms avg)")
        
        # Compare with others
        for framework, duration in suite.summary['performance_ranking'][1:]:
            speedup = duration / fastest[1]
            print(f"  {framework}: {speedup:.1f}x slower")
        
        # Recommendations
        print("\n📝 Recommendations:")
        if fastest[0] != "OxenORM":
            print("  • Consider using OxenORM for better performance")
        else:
            print("  • OxenORM shows excellent performance!")
        
        # Check for issues
        for framework, stats in suite.summary['framework_stats'].items():
            if stats['success_rate'] < 0.95:
                print(f"  • {framework} has low success rate ({stats['success_rate']:.1%})")
    
    def _format_text_report(self, report: dict) -> str:
        """Format report as text."""
        lines = []
        lines.append("OxenORM Performance Report")
        lines.append("=" * 50)
        lines.append(f"Generated: {report.get('timestamp', 'Unknown')}")
        lines.append("")
        
        # Query performance
        query_perf = report.get('query_performance', {})
        lines.append("Query Performance:")
        lines.append(f"  Total queries: {query_perf.get('total_queries', 0)}")
        lines.append(f"  Average duration: {query_perf.get('avg_duration_ms', 0):.2f}ms")
        lines.append(f"  Success rate: {query_perf.get('success_rate', 0):.1%}")
        lines.append(f"  Queries per second: {query_perf.get('queries_per_second', 0):.1f}")
        lines.append("")
        
        # System performance
        sys_perf = report.get('system_performance', {})
        if sys_perf:
            lines.append("System Performance:")
            lines.append(f"  CPU usage: {sys_perf.get('avg_cpu_percent', 0):.1f}%")
            lines.append(f"  Memory usage: {sys_perf.get('avg_memory_percent', 0):.1f}%")
            lines.append("")
        
        # Alerts
        alerts = report.get('alerts', [])
        if alerts:
            lines.append("Active Alerts:")
            for alert in alerts:
                if alert.get('triggered'):
                    lines.append(f"  ⚠️  {alert.get('name')}: {alert.get('message')}")
            lines.append("")
        
        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            lines.append("Recommendations:")
            for rec in recommendations:
                lines.append(f"  • {rec}")
        
        return "\n".join(lines)
    
    def _format_html_report(self, report: dict) -> str:
        """Format report as HTML."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>OxenORM Performance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f9f9f9; border-radius: 3px; }
        .alert { color: #d32f2f; }
        .success { color: #388e3c; }
    </style>
</head>
<body>
    <div class="header">
        <h1>OxenORM Performance Report</h1>
        <p>Generated: {timestamp}</p>
    </div>
        """.format(timestamp=report.get('timestamp', 'Unknown'))
        
        # Add sections
        query_perf = report.get('query_performance', {})
        html += f"""
    <div class="section">
        <h2>Query Performance</h2>
        <div class="metric">Total Queries: {query_perf.get('total_queries', 0)}</div>
        <div class="metric">Avg Duration: {query_perf.get('avg_duration_ms', 0):.2f}ms</div>
        <div class="metric">Success Rate: {query_perf.get('success_rate', 0):.1%}</div>
        <div class="metric">Queries/sec: {query_perf.get('queries_per_second', 0):.1f}</div>
    </div>
        """
        
        # Add recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            html += """
    <div class="section">
        <h2>Recommendations</h2>
        <ul>
        """
            for rec in recommendations:
                html += f"<li>{rec}</li>"
            html += "</ul></div>"
        
        html += "</body></html>"
        return html
    
    def _export_csv_metrics(self, monitor, output_file: str) -> str:
        """Export metrics as CSV."""
        if not output_file:
            output_file = f"metrics_{int(time.time())}.csv"
        
        # Get query metrics
        query_stats = monitor.get_query_statistics()
        
        # Create CSV content
        csv_lines = [
            "metric,value",
            f"total_queries,{query_stats.get('total_queries', 0)}",
            f"avg_duration_ms,{query_stats.get('avg_duration', 0):.2f}",
            f"success_rate,{query_stats.get('success_rate', 0):.3f}",
            f"queries_per_second,{query_stats.get('queries_per_second', 0):.2f}"
        ]
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(csv_lines))
        
        return output_file
    
    def _analyze_performance_data(self, data: dict, threshold: float) -> dict:
        """Analyze performance data."""
        analysis = {
            'summary': {},
            'slow_queries': [],
            'recommendations': []
        }
        
        # Analyze query metrics
        query_metrics = data.get('query_metrics', [])
        if query_metrics:
            durations = [m.get('duration_ms', 0) for m in query_metrics]
            analysis['summary'] = {
                'total_queries': len(query_metrics),
                'avg_duration': sum(durations) / len(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'min_duration': min(durations) if durations else 0,
                'slow_queries_count': len([d for d in durations if d > threshold])
            }
            
            # Find slow queries
            slow_queries = [m for m in query_metrics if m.get('duration_ms', 0) > threshold]
            analysis['slow_queries'] = slow_queries[:10]  # Top 10 slowest
        
        # Generate recommendations
        summary = analysis['summary']
        if summary.get('avg_duration', 0) > threshold:
            analysis['recommendations'].append("Average query duration is high - consider optimization")
        
        if summary.get('slow_queries_count', 0) > 0:
            analysis['recommendations'].append(f"Found {summary['slow_queries_count']} slow queries")
        
        return analysis
    
    def run(self, args=None):
        """Run the CLI."""
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return
        
        # Run appropriate command
        if parsed_args.command == 'benchmark':
            asyncio.run(self.run_benchmark(parsed_args))
        elif parsed_args.command == 'monitor':
            asyncio.run(self.run_monitor(parsed_args))
        elif parsed_args.command == 'report':
            asyncio.run(self.run_report(parsed_args))
        elif parsed_args.command == 'export':
            asyncio.run(self.run_export(parsed_args))
        elif parsed_args.command == 'analyze':
            asyncio.run(self.run_analyze(parsed_args))


def main():
    """Main entry point."""
    cli = PerformanceCLI()
    cli.run()


if __name__ == "__main__":
    main() 
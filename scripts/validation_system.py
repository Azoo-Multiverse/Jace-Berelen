import os
import sys
import json
import pytest
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import coverage

class RequirementTracer:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
    
    def extract_requirements(self, task_id: str) -> List[Dict[str, Any]]:
        """Extract requirements from task file"""
        task_file = self._find_task_file(task_id)
        if not task_file:
            return []
        
        content = task_file.read_text()
        requirements = []
        
        # Extract requirements section
        req_match = re.search(r'## Requirements\s+(.+?)(?=##|\Z)', content, re.DOTALL)
        if req_match:
            req_text = req_match.group(1)
            req_lines = [line.strip() for line in req_text.split('\n') if line.strip().startswith('-')]
            requirements = [{'id': f'REQ{i+1}', 'text': line[1:].strip(), 'satisfied': False} 
                           for i, line in enumerate(req_lines)]
        
        return requirements
    
    def trace_requirements(self, task_id: str, implementation_text: str) -> List[Dict[str, Any]]:
        """Check if implementation satisfies requirements"""
        requirements = self.extract_requirements(task_id)
        
        for req in requirements:
            # Basic keyword matching - this would be more sophisticated in real implementation
            keywords = self._extract_keywords(req['text'])
            req['satisfied'] = all(k.lower() in implementation_text.lower() for k in keywords if len(k) > 3)
            
            # Reason for satisfaction/non-satisfaction
            if req['satisfied']:
                req['reason'] = "Keywords found in implementation"
            else:
                req['reason'] = "Some keywords missing from implementation"
                
            # Evidence - code snippets that satisfy the requirement
            if req['satisfied']:
                req['evidence'] = self._find_evidence(implementation_text, keywords)
        
        return requirements
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from requirement text"""
        # Remove common words and keep only significant terms
        common_words = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'at', 'from', 'by', 'for', 'with', 'about', 'to'}
        words = text.lower().split()
        return [w for w in words if w not in common_words and len(w) > 2]
    
    def _find_evidence(self, implementation_text: str, keywords: List[str]) -> List[str]:
        """Find code snippets that provide evidence for requirement satisfaction"""
        lines = implementation_text.split('\n')
        evidence = []
        
        for i, line in enumerate(lines):
            if any(k.lower() in line.lower() for k in keywords if len(k) > 3):
                # Get context (line before and after)
                start = max(0, i-1)
                end = min(len(lines), i+2)
                context = '\n'.join(lines[start:end])
                evidence.append(context)
        
        # Limit to 3 pieces of evidence
        return evidence[:3]
    
    def _find_task_file(self, task_id: str) -> Optional[Path]:
        """Find task file in various locations"""
        locations = [
            self.task_dir / "TASKS" / "TODO",
            self.task_dir / "TASKS" / "DONE" / task_id,
            self.task_dir / "TASKS" / "IN_PROGRESS"
        ]
        
        for loc in locations:
            if loc.exists():
                for file in loc.glob(f"{task_id}*.md"):
                    return file
        
        return None

class CoverageAnalyzer:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.cov = coverage.Coverage()
    
    def analyze_coverage(self, task_id: str) -> Dict[str, Any]:
        """Analyze code coverage for a specific task"""
        # Find implementation files
        src_dir = self.task_dir / "src"
        implementation_files = list(src_dir.glob(f"*{task_id}*.py"))
        
        if not implementation_files:
            return {
                'percentage': 0,
                'lines_covered': 0,
                'lines_missed': 0,
                'files_analyzed': [],
                'error': "No implementation files found"
            }
        
        # Find test files
        test_dir = self.task_dir / "tests"
        test_files = list(test_dir.glob(f"*{task_id}*.py"))
        
        if not test_files:
            return {
                'percentage': 0,
                'lines_covered': 0,
                'lines_missed': 0,
                'files_analyzed': [str(f.relative_to(self.task_dir)) for f in implementation_files],
                'error': "No test files found"
            }
        
        # Run coverage
        self.cov = coverage.Coverage(source=[str(f) for f in implementation_files])
        self.cov.start()
        
        # Run the tests
        pytest.main([str(f) for f in test_files])
        
        self.cov.stop()
        self.cov.save()
        
        # Get coverage data
        data = self.cov.get_data()
        total_statements = 0
        total_covered = 0
        
        file_coverage = {}
        for file_path in implementation_files:
            file_str = str(file_path)
            if file_str in data.measured_files():
                analysis = self.cov.analysis2(file_str)
                statements = len(analysis[1])
                missing = len(analysis[2])
                covered = statements - missing
                
                total_statements += statements
                total_covered += covered
                
                file_coverage[str(file_path.relative_to(self.task_dir))] = {
                    'statements': statements,
                    'covered': covered,
                    'percentage': 100 * covered / statements if statements > 0 else 0
                }
        
        # Calculate overall coverage
        percentage = 100 * total_covered / total_statements if total_statements > 0 else 0
        
        return {
            'percentage': percentage,
            'lines_covered': total_covered,
            'lines_missed': total_statements - total_covered,
            'files_analyzed': file_coverage,
            'timestamp': datetime.now().isoformat()
        }

class TestValidator:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
    
    def run_tests(self, task_id: str) -> Dict[str, Any]:
        """Run tests for a specific task and capture results"""
        # Find test files
        test_dir = self.task_dir / "tests"
        test_files = list(test_dir.glob(f"*{task_id}*.py"))
        
        if not test_files:
            return {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'error': 0,
                'skipped': 0,
                'details': [],
                'error_message': "No test files found"
            }
        
        # Run pytest with JSON output
        temp_result_file = self.task_dir / "temp_test_results.json"
        
        cmd = [
            sys.executable, 
            "-m", "pytest", 
            "--json-report", 
            f"--json-report-file={temp_result_file}",
            *[str(f) for f in test_files]
        ]
        
        try:
            subprocess.run(cmd, check=False, capture_output=True)
            
            # Read results
            if temp_result_file.exists():
                with open(temp_result_file, 'r') as f:
                    report = json.load(f)
                
                # Clean up
                temp_result_file.unlink()
                
                # Extract key information
                summary = report.get('summary', {})
                test_details = []
                
                for test_id, test_data in report.get('tests', {}).items():
                    test_details.append({
                        'id': test_id,
                        'name': test_data.get('name', ''),
                        'outcome': test_data.get('outcome', ''),
                        'message': test_data.get('call', {}).get('longrepr', '')
                    })
                
                return {
                    'total': summary.get('total', 0),
                    'passed': summary.get('passed', 0),
                    'failed': summary.get('failed', 0),
                    'error': summary.get('error', 0),
                    'skipped': summary.get('skipped', 0),
                    'details': test_details,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'error': 0,
                    'skipped': 0,
                    'details': [],
                    'error_message': "Failed to generate test report"
                }
                
        except Exception as e:
            return {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'error': 0,
                'skipped': 0,
                'details': [],
                'error_message': str(e)
            }

class ValidationRunner:
    def __init__(self, task_dir: Path = None):
        self.task_dir = task_dir or Path(os.getcwd())
        self.todo_dir = self.task_dir / "TASKS" / "TODO"
        self.done_dir = self.task_dir / "TASKS" / "DONE"
        self.in_progress_dir = self.task_dir / "TASKS" / "IN_PROGRESS"
        
        self.test_validator = TestValidator(self.task_dir)
        self.coverage_analyzer = CoverageAnalyzer(self.task_dir)
        self.requirement_tracer = RequirementTracer(self.task_dir)
    
    def run_validation(self, task_id: str) -> Dict[str, Any]:
        """Run full validation for a task"""
        # Find implementation files
        src_dir = self.task_dir / "src"
        implementation_files = list(src_dir.glob(f"*{task_id}*.py"))
        
        if not implementation_files:
            return {
                'task_id': task_id,
                'validation_status': 'failed',
                'error': "No implementation files found",
                'timestamp': datetime.now().isoformat()
            }
        
        # Read implementation code
        implementation_text = ""
        for file in implementation_files:
            implementation_text += file.read_text() + "\n\n"
        
        # Run tests
        test_results = self.test_validator.run_tests(task_id)
        
        # Analyze coverage
        coverage_results = self.coverage_analyzer.analyze_coverage(task_id)
        
        # Trace requirements
        requirement_results = self.requirement_tracer.trace_requirements(task_id, implementation_text)
        
        # Determine overall validation status
        validation_status = 'passed'
        validation_issues = []
        
        # Check for test failures
        if test_results.get('failed', 0) > 0 or test_results.get('error', 0) > 0:
            validation_status = 'failed'
            validation_issues.append(f"Tests failed: {test_results.get('failed', 0)} failed, {test_results.get('error', 0)} errors")
        
        # Check for low coverage
        if coverage_results.get('percentage', 0) < 70:
            validation_status = 'warning' if validation_status == 'passed' else validation_status
            validation_issues.append(f"Low coverage: {coverage_results.get('percentage', 0):.1f}%")
        
        # Check for unmet requirements
        unmet_reqs = [req for req in requirement_results if not req.get('satisfied', False)]
        if unmet_reqs:
            validation_status = 'failed'
            validation_issues.append(f"Unmet requirements: {len(unmet_reqs)} requirements not satisfied")
        
        # Generate report
        validation_report = {
            'task_id': task_id,
            'validation_status': validation_status,
            'issues': validation_issues,
            'test_results': test_results,
            'coverage': coverage_results,
            'requirements': requirement_results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save report
        self._save_validation_report(task_id, validation_report)
        
        return validation_report
    
    def _save_validation_report(self, task_id: str, report: Dict[str, Any]) -> Path:
        """Save validation report to file"""
        # Ensure directory exists
        validation_dir = self.task_dir / "TASKS" / "VALIDATION"
        validation_dir.mkdir(exist_ok=True, parents=True)
        
        # Create report file
        report_file = validation_dir / f"{task_id}_validation.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Also create a markdown summary
        summary_file = validation_dir / f"{task_id}_validation.md"
        
        # Format markdown summary
        summary = f"""# Validation Report: {task_id}

## Status: {report['validation_status'].upper()}

Generated: {report['timestamp']}

## Issues
"""
        if report['issues']:
            for issue in report['issues']:
                summary += f"- {issue}\n"
        else:
            summary += "- No issues found\n"
        
        summary += f"""
## Test Results
- Total: {report['test_results']['total']}
- Passed: {report['test_results']['passed']}
- Failed: {report['test_results']['failed']}
- Errors: {report['test_results']['error']}
- Skipped: {report['test_results']['skipped']}

## Coverage
- Overall: {report['coverage']['percentage']:.1f}%
- Lines Covered: {report['coverage']['lines_covered']}
- Lines Missed: {report['coverage']['lines_missed']}

## Requirements
"""
        for req in report['requirements']:
            status = "✓" if req['satisfied'] else "✗"
            summary += f"- [{status}] {req['text']}\n"
            if not req['satisfied']:
                summary += f"  - Reason: {req.get('reason', 'Not specified')}\n"
        
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        return report_file

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validation system for task outputs")
    parser.add_argument("--task", required=True, help="Task ID to validate")
    parser.add_argument("--dir", help="Root directory for tasks", default=os.getcwd())
    
    args = parser.parse_args()
    
    validator = ValidationRunner(Path(args.dir))
    result = validator.run_validation(args.task)
    
    print(f"Validation result: {result['validation_status']}")
    if result['issues']:
        print("Issues found:")
        for issue in result['issues']:
            print(f"- {issue}")
    else:
        print("No issues found!")
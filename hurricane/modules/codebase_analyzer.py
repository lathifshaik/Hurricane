"""
Codebase analysis and optimization module for Hurricane AI Agent.
Automatically analyzes code quality, suggests improvements, and identifies optimization opportunities.
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

from .language_support import MultiLanguageSupport
from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


@dataclass
class CodeIssue:
    """Represents a code quality issue or optimization opportunity."""
    file_path: str
    line_number: int
    issue_type: str  # error_handling, performance, duplication, style, security
    severity: str    # low, medium, high, critical
    description: str
    suggestion: str
    code_snippet: str = ""
    auto_fixable: bool = False


@dataclass
class CodeMetrics:
    """Code quality metrics for a file or project."""
    lines_of_code: int
    complexity_score: int
    duplication_percentage: float
    test_coverage: float
    maintainability_index: float
    technical_debt_hours: float


class CodebaseAnalyzer:
    """Advanced codebase analysis and optimization engine."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config, project_root: Path):
        self.ollama_client = ollama_client
        self.config = config
        self.project_root = Path(project_root)
        self.language_support = MultiLanguageSupport()
        
        # Analysis patterns for different issue types
        self.error_patterns = {
            'bare_except': r'except\s*:',
            'generic_exception': r'except\s+Exception\s*:',
            'no_error_handling': r'(open\(|requests\.|json\.)',
            'silent_failure': r'pass\s*#.*error'
        }
        
        self.performance_patterns = {
            'sync_in_async': r'def\s+\w+.*:\s*.*(?:requests\.|time\.sleep|open\()',
            'inefficient_loop': r'for.*in.*:\s*.*\.append\(',
            'string_concatenation': r'\+\=.*str\(',
            'repeated_computation': r'for.*:\s*.*\.\w+\(\).*\.\w+\(\)'
        }
        
        self.style_patterns = {
            'long_line': r'.{120,}',
            'deep_nesting': r'(\s{16,})',
            'magic_numbers': r'\b\d{2,}\b',
            'inconsistent_naming': r'[a-z]+[A-Z]|[A-Z]+[a-z]'
        }
    
    async def analyze_project(self, include_ai_suggestions: bool = True) -> Dict[str, Any]:
        """Perform comprehensive project analysis."""
        console.print("[bold blue]🔍 Starting comprehensive codebase analysis...[/bold blue]")
        
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "files_analyzed": 0,
            "issues_found": [],
            "metrics": {},
            "suggestions": [],
            "optimization_opportunities": []
        }
        
        # Find all code files
        code_files = []
        for ext in self.language_support.extension_map.keys():
            code_files.extend(self.project_root.rglob(f"*{ext}"))
        
        # Filter out ignored files
        code_files = [f for f in code_files if not self._should_ignore(f)]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing files...", total=len(code_files))
            
            for file_path in code_files:
                try:
                    file_analysis = await self._analyze_file(file_path)
                    analysis_results["issues_found"].extend(file_analysis["issues"])
                    analysis_results["files_analyzed"] += 1
                    
                    progress.update(task, advance=1)
                except Exception as e:
                    console.print(f"[yellow]⚠️ Could not analyze {file_path}: {e}[/yellow]")
        
        # Calculate overall metrics
        analysis_results["metrics"] = self._calculate_project_metrics(analysis_results["issues_found"])
        
        # Generate AI-powered suggestions if requested
        if include_ai_suggestions and analysis_results["issues_found"]:
            console.print("[blue]🤖 Generating AI-powered optimization suggestions...[/blue]")
            analysis_results["suggestions"] = await self._generate_ai_suggestions(analysis_results)
        
        # Identify optimization opportunities
        analysis_results["optimization_opportunities"] = self._identify_optimizations(analysis_results["issues_found"])
        
        return analysis_results
    
    async def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single file for issues and metrics."""
        try:
            content = file_path.read_text(encoding='utf-8')
            language = self.language_support.detect_language(file_path)
            
            issues = []
            lines = content.split('\n')
            
            # Check for error handling issues
            issues.extend(self._check_error_handling(content, file_path, lines))
            
            # Check for performance issues
            issues.extend(self._check_performance_issues(content, file_path, lines))
            
            # Check for style issues
            issues.extend(self._check_style_issues(content, file_path, lines))
            
            # Check for security issues
            issues.extend(self._check_security_issues(content, file_path, lines))
            
            # Language-specific analysis
            if language == "python":
                issues.extend(self._analyze_python_specific(content, file_path))
            
            return {
                "file_path": str(file_path),
                "language": language,
                "issues": issues,
                "lines_of_code": len([l for l in lines if l.strip()]),
                "complexity": self._calculate_complexity(content)
            }
            
        except Exception as e:
            return {"file_path": str(file_path), "issues": [], "error": str(e)}
    
    def _check_error_handling(self, content: str, file_path: Path, lines: List[str]) -> List[CodeIssue]:
        """Check for error handling issues."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Bare except clauses
            if re.search(self.error_patterns['bare_except'], line):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="error_handling",
                    severity="high",
                    description="Bare except clause catches all exceptions",
                    suggestion="Use specific exception types or 'except Exception as e:'",
                    code_snippet=line.strip(),
                    auto_fixable=True
                ))
            
            # Generic exception handling
            if re.search(self.error_patterns['generic_exception'], line):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="error_handling",
                    severity="medium",
                    description="Generic exception handling",
                    suggestion="Use more specific exception types when possible",
                    code_snippet=line.strip()
                ))
        
        return issues
    
    def _check_performance_issues(self, content: str, file_path: Path, lines: List[str]) -> List[CodeIssue]:
        """Check for performance issues."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # String concatenation in loops
            if '+=' in line and any(loop in lines[max(0, i-5):i] for loop in ['for ', 'while ']):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="performance",
                    severity="medium",
                    description="String concatenation in loop",
                    suggestion="Use list.append() and ''.join() for better performance",
                    code_snippet=line.strip(),
                    auto_fixable=True
                ))
            
            # Inefficient list operations
            if re.search(r'for.*in.*:\s*.*\.append\(.*\.pop\(', line):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="performance",
                    severity="high",
                    description="Inefficient list operations",
                    suggestion="Consider using collections.deque for frequent pop(0) operations",
                    code_snippet=line.strip()
                ))
        
        return issues
    
    def _check_style_issues(self, content: str, file_path: Path, lines: List[str]) -> List[CodeIssue]:
        """Check for style and maintainability issues."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Long lines
            if len(line) > 120:
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="style",
                    severity="low",
                    description=f"Line too long ({len(line)} characters)",
                    suggestion="Break long lines for better readability",
                    code_snippet=line[:50] + "..." if len(line) > 50 else line
                ))
            
            # Deep nesting
            indent_level = len(line) - len(line.lstrip())
            if indent_level > 16:
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="style",
                    severity="medium",
                    description=f"Deep nesting (indent level {indent_level//4})",
                    suggestion="Consider extracting nested logic into separate functions",
                    code_snippet=line.strip()
                ))
        
        return issues
    
    def _check_security_issues(self, content: str, file_path: Path, lines: List[str]) -> List[CodeIssue]:
        """Check for potential security issues."""
        issues = []
        
        security_patterns = {
            'hardcoded_password': r'(password|pwd|pass)\s*=\s*["\'][^"\']+["\']',
            'sql_injection': r'(execute|query).*%.*\+',
            'unsafe_eval': r'\beval\s*\(',
            'shell_injection': r'(os\.system|subprocess\.call).*\+',
        }
        
        for i, line in enumerate(lines, 1):
            for pattern_name, pattern in security_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="security",
                        severity="critical" if pattern_name in ['sql_injection', 'shell_injection'] else "high",
                        description=f"Potential {pattern_name.replace('_', ' ')} vulnerability",
                        suggestion=self._get_security_suggestion(pattern_name),
                        code_snippet=line.strip()
                    ))
        
        return issues
    
    def _analyze_python_specific(self, content: str, file_path: Path) -> List[CodeIssue]:
        """Python-specific analysis using AST."""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Check for missing docstrings
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_type="style",
                            severity="low",
                            description=f"Missing docstring for {node.name}",
                            suggestion="Add a descriptive docstring",
                            code_snippet=f"def {node.name}:" if isinstance(node, ast.FunctionDef) else f"class {node.name}:"
                        ))
                
                # Check for unused variables
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    # This is a simplified check - a full implementation would need scope analysis
                    pass
        
        except SyntaxError:
            issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=1,
                issue_type="error_handling",
                severity="critical",
                description="Syntax error in Python file",
                suggestion="Fix syntax errors before analysis",
                code_snippet="Syntax error"
            ))
        
        return issues
    
    def _calculate_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'and', 'or']
        
        for keyword in decision_keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', content))
        
        return complexity
    
    def _calculate_project_metrics(self, issues: List[CodeIssue]) -> Dict[str, Any]:
        """Calculate overall project metrics."""
        total_issues = len(issues)
        critical_issues = len([i for i in issues if i.severity == "critical"])
        high_issues = len([i for i in issues if i.severity == "high"])
        medium_issues = len([i for i in issues if i.severity == "medium"])
        low_issues = len([i for i in issues if i.severity == "low"])
        
        # Calculate technical debt (rough estimation)
        debt_hours = (critical_issues * 4) + (high_issues * 2) + (medium_issues * 1) + (low_issues * 0.5)
        
        # Calculate quality score (0-100)
        quality_score = max(0, 100 - (critical_issues * 20) - (high_issues * 10) - (medium_issues * 5) - (low_issues * 2))
        
        return {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "medium_issues": medium_issues,
            "low_issues": low_issues,
            "technical_debt_hours": debt_hours,
            "quality_score": quality_score,
            "auto_fixable_issues": len([i for i in issues if i.auto_fixable])
        }
    
    async def _generate_ai_suggestions(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate AI-powered optimization suggestions."""
        try:
            # Prepare summary for AI
            metrics = analysis_results["metrics"]
            top_issues = sorted(analysis_results["issues_found"], 
                              key=lambda x: {"critical": 4, "high": 3, "medium": 2, "low": 1}[x.severity], 
                              reverse=True)[:10]
            
            prompt = f"""Analyze this codebase quality report and provide 5 specific, actionable optimization suggestions:

Project Metrics:
- Total Issues: {metrics['total_issues']}
- Critical Issues: {metrics['critical_issues']}
- Quality Score: {metrics['quality_score']}/100
- Technical Debt: {metrics['technical_debt_hours']} hours

Top Issues:
"""
            
            for issue in top_issues:
                prompt += f"- {issue.severity.upper()}: {issue.description} in {Path(issue.file_path).name}\n"
            
            prompt += "\nProvide 5 specific suggestions to improve code quality, performance, and maintainability."
            
            response = await self.ollama_client.generate_response(
                prompt,
                system_prompt="You are a senior software architect and code quality expert. Provide specific, actionable suggestions."
            )
            
            # Parse suggestions from response
            suggestions = []
            for line in response.split('\n'):
                if line.strip() and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    suggestions.append(line.strip().lstrip('-•0123456789. '))
            
            return suggestions[:5]
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not generate AI suggestions: {e}[/yellow]")
            return []
    
    def _identify_optimizations(self, issues: List[CodeIssue]) -> List[Dict[str, Any]]:
        """Identify specific optimization opportunities."""
        optimizations = []
        
        # Group issues by type
        issue_groups = {}
        for issue in issues:
            if issue.issue_type not in issue_groups:
                issue_groups[issue.issue_type] = []
            issue_groups[issue.issue_type].append(issue)
        
        # Generate optimization recommendations
        for issue_type, type_issues in issue_groups.items():
            if len(type_issues) >= 3:  # If we have multiple instances
                optimizations.append({
                    "type": issue_type,
                    "count": len(type_issues),
                    "priority": "high" if issue_type in ["security", "performance"] else "medium",
                    "description": f"Multiple {issue_type} issues detected",
                    "recommendation": self._get_optimization_recommendation(issue_type),
                    "files_affected": list(set(issue.file_path for issue in type_issues))
                })
        
        return optimizations
    
    def _get_security_suggestion(self, pattern_name: str) -> str:
        """Get security-specific suggestions."""
        suggestions = {
            'hardcoded_password': "Use environment variables or secure configuration files",
            'sql_injection': "Use parameterized queries or ORM methods",
            'unsafe_eval': "Avoid eval() - use ast.literal_eval() or safer alternatives",
            'shell_injection': "Use subprocess with shell=False and validate inputs"
        }
        return suggestions.get(pattern_name, "Review for security implications")
    
    def _get_optimization_recommendation(self, issue_type: str) -> str:
        """Get optimization recommendations by issue type."""
        recommendations = {
            "error_handling": "Implement consistent error handling patterns across the codebase",
            "performance": "Profile and optimize hot paths, consider async operations",
            "style": "Set up automated code formatting (black, prettier) and linting",
            "security": "Conduct security review and implement secure coding practices"
        }
        return recommendations.get(issue_type, "Review and refactor affected code")
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored during analysis."""
        ignore_patterns = {
            '__pycache__', '.git', '.svn', 'node_modules', '.vscode', 
            '.idea', 'venv', 'env', '.env', 'dist', 'build', '.DS_Store',
            '.pytest_cache', '.coverage', 'htmlcov'
        }
        
        return any(pattern in str(file_path) for pattern in ignore_patterns)
    
    async def show_analysis_results(self, analysis_results: Dict[str, Any]) -> None:
        """Display analysis results in a beautiful format."""
        metrics = analysis_results["metrics"]
        
        # Quality Score Panel
        quality_color = "green" if metrics["quality_score"] >= 80 else "yellow" if metrics["quality_score"] >= 60 else "red"
        console.print(Panel(
            f"[bold {quality_color}]Quality Score: {metrics['quality_score']}/100[/bold {quality_color}]\n"
            f"Technical Debt: {metrics['technical_debt_hours']:.1f} hours\n"
            f"Auto-fixable Issues: {metrics['auto_fixable_issues']}",
            title="📊 Codebase Health",
            border_style=quality_color
        ))
        
        # Issues Summary Table
        table = Table(title="🔍 Issues Summary")
        table.add_column("Severity", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Impact", style="italic")
        
        table.add_row("Critical", str(metrics["critical_issues"]), "🚨 Immediate attention required")
        table.add_row("High", str(metrics["high_issues"]), "⚠️ Should be fixed soon")
        table.add_row("Medium", str(metrics["medium_issues"]), "💡 Consider fixing")
        table.add_row("Low", str(metrics["low_issues"]), "📝 Nice to have")
        
        console.print(table)
        
        # Top Issues
        if analysis_results["issues_found"]:
            console.print("\n[bold red]🔥 Top Critical Issues:[/bold red]")
            critical_issues = [i for i in analysis_results["issues_found"] if i.severity == "critical"][:5]
            
            for i, issue in enumerate(critical_issues, 1):
                console.print(f"{i}. [red]{issue.description}[/red]")
                console.print(f"   📁 {Path(issue.file_path).name}:{issue.line_number}")
                console.print(f"   💡 {issue.suggestion}\n")
        
        # AI Suggestions
        if analysis_results["suggestions"]:
            console.print("[bold blue]🤖 AI-Powered Optimization Suggestions:[/bold blue]")
            for i, suggestion in enumerate(analysis_results["suggestions"], 1):
                console.print(f"{i}. {suggestion}")
        
        # Optimization Opportunities
        if analysis_results["optimization_opportunities"]:
            console.print("\n[bold green]🚀 Optimization Opportunities:[/bold green]")
            for opt in analysis_results["optimization_opportunities"]:
                console.print(f"• {opt['description']} ({opt['count']} instances)")
                console.print(f"  💡 {opt['recommendation']}")
    
    async def auto_fix_issues(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically fix issues that can be safely auto-fixed."""
        console.print("[bold blue]🔧 Auto-fixing issues...[/bold blue]")
        
        auto_fixable = [i for i in analysis_results["issues_found"] if i.auto_fixable]
        fixed_count = 0
        
        for issue in auto_fixable:
            try:
                if await self._apply_auto_fix(issue):
                    fixed_count += 1
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not auto-fix {issue.description}: {e}[/yellow]")
        
        console.print(f"[green]✅ Auto-fixed {fixed_count} issues[/green]")
        
        return {"fixed_count": fixed_count, "total_fixable": len(auto_fixable)}
    
    async def _apply_auto_fix(self, issue: CodeIssue) -> bool:
        """Apply an automatic fix for a specific issue."""
        file_path = Path(issue.file_path)
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            if issue.issue_type == "error_handling" and "bare except" in issue.description:
                # Fix bare except clauses
                line_idx = issue.line_number - 1
                if line_idx < len(lines):
                    lines[line_idx] = lines[line_idx].replace('except:', 'except Exception as e:')
                    
                    file_path.write_text('\n'.join(lines), encoding='utf-8')
                    return True
            
            # Add more auto-fix patterns here
            
        except Exception:
            return False
        
        return False

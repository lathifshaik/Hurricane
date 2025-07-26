"""
Tool integration and environment interaction module for Hurricane AI Agent.
Provides integration with Git, package managers, testing frameworks, and deployment tools.
"""

import asyncio
import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import shutil

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""
    tool_name: str
    command: str
    success: bool
    output: str
    error: str
    execution_time: float
    timestamp: str


class ToolIntegration:
    """External tool integration and environment interaction engine."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config, project_root: Path):
        self.ollama_client = ollama_client
        self.config = config
        self.project_root = Path(project_root)
        
        # Tool availability cache
        self.available_tools = {}
        self.tool_configs = {}
        
        # Initialize tool availability
        asyncio.create_task(self._check_tool_availability())
    
    async def _check_tool_availability(self):
        """Check which tools are available in the system."""
        tools_to_check = {
            'git': 'git --version',
            'python': 'python --version',
            'pip': 'pip --version',
            'npm': 'npm --version',
            'node': 'node --version',
            'docker': 'docker --version',
            'pytest': 'pytest --version',
            'black': 'black --version',
            'flake8': 'flake8 --version',
            'mypy': 'mypy --version',
            'poetry': 'poetry --version',
            'pipenv': 'pipenv --version'
        }
        
        for tool, check_cmd in tools_to_check.items():
            try:
                result = await self._run_command(check_cmd, timeout=5)
                self.available_tools[tool] = result.success
                if result.success:
                    console.print(f"[green]✅ {tool} available[/green]")
            except Exception:
                self.available_tools[tool] = False
    
    async def _run_command(self, command: str, cwd: Optional[Path] = None, 
                          timeout: int = 30, capture_output: bool = True) -> ToolResult:
        """Run a system command and return the result."""
        start_time = datetime.now()
        cwd = cwd or self.project_root
        
        try:
            if capture_output:
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=cwd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                
                output = stdout.decode('utf-8') if stdout else ""
                error = stderr.decode('utf-8') if stderr else ""
                success = process.returncode == 0
            else:
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=cwd
                )
                
                returncode = await asyncio.wait_for(
                    process.wait(), timeout=timeout
                )
                
                output = ""
                error = ""
                success = returncode == 0
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ToolResult(
                tool_name=command.split()[0],
                command=command,
                success=success,
                output=output,
                error=error,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )
            
        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=command.split()[0],
                command=command,
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                execution_time=timeout,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            return ToolResult(
                tool_name=command.split()[0],
                command=command,
                success=False,
                output="",
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now().isoformat()
            )
    
    # Git Integration
    async def git_status(self) -> Dict[str, Any]:
        """Get Git repository status."""
        if not self.available_tools.get('git', False):
            return {"error": "Git not available"}
        
        result = await self._run_command("git status --porcelain")
        if not result.success:
            return {"error": result.error}
        
        # Parse git status output
        status = {
            "modified": [],
            "added": [],
            "deleted": [],
            "untracked": [],
            "staged": []
        }
        
        for line in result.output.strip().split('\n'):
            if not line:
                continue
            
            status_code = line[:2]
            filename = line[3:]
            
            if status_code == '??':
                status["untracked"].append(filename)
            elif status_code[0] == 'M':
                status["staged"].append(filename)
            elif status_code[1] == 'M':
                status["modified"].append(filename)
            elif status_code[0] == 'A':
                status["added"].append(filename)
            elif status_code[0] == 'D':
                status["deleted"].append(filename)
        
        return status
    
    async def git_commit(self, message: str, files: Optional[List[str]] = None) -> ToolResult:
        """Commit changes to Git."""
        if not self.available_tools.get('git', False):
            return ToolResult("git", "commit", False, "", "Git not available", 0, datetime.now().isoformat())
        
        # Add files if specified
        if files:
            for file in files:
                add_result = await self._run_command(f"git add {file}")
                if not add_result.success:
                    return add_result
        else:
            # Add all modified files
            add_result = await self._run_command("git add -A")
            if not add_result.success:
                return add_result
        
        # Commit
        commit_result = await self._run_command(f'git commit -m "{message}"')
        return commit_result
    
    async def git_create_branch(self, branch_name: str) -> ToolResult:
        """Create and switch to a new Git branch."""
        if not self.available_tools.get('git', False):
            return ToolResult("git", "branch", False, "", "Git not available", 0, datetime.now().isoformat())
        
        return await self._run_command(f"git checkout -b {branch_name}")
    
    async def git_push(self, branch: str = "main") -> ToolResult:
        """Push changes to remote repository."""
        if not self.available_tools.get('git', False):
            return ToolResult("git", "push", False, "", "Git not available", 0, datetime.now().isoformat())
        
        return await self._run_command(f"git push origin {branch}")
    
    # Package Management
    async def install_package(self, package: str, package_manager: str = "auto") -> ToolResult:
        """Install a package using the appropriate package manager."""
        if package_manager == "auto":
            # Auto-detect package manager
            if (self.project_root / "requirements.txt").exists() and self.available_tools.get('pip'):
                package_manager = "pip"
            elif (self.project_root / "package.json").exists() and self.available_tools.get('npm'):
                package_manager = "npm"
            elif (self.project_root / "pyproject.toml").exists() and self.available_tools.get('poetry'):
                package_manager = "poetry"
            elif (self.project_root / "Pipfile").exists() and self.available_tools.get('pipenv'):
                package_manager = "pipenv"
            else:
                package_manager = "pip"  # Default fallback
        
        commands = {
            "pip": f"pip install {package}",
            "npm": f"npm install {package}",
            "poetry": f"poetry add {package}",
            "pipenv": f"pipenv install {package}"
        }
        
        if package_manager not in commands:
            return ToolResult("package", "install", False, "", f"Unknown package manager: {package_manager}", 0, datetime.now().isoformat())
        
        if not self.available_tools.get(package_manager, False):
            return ToolResult("package", "install", False, "", f"{package_manager} not available", 0, datetime.now().isoformat())
        
        console.print(f"[blue]📦 Installing {package} using {package_manager}...[/blue]")
        result = await self._run_command(commands[package_manager])
        
        if result.success:
            console.print(f"[green]✅ Successfully installed {package}[/green]")
        else:
            console.print(f"[red]❌ Failed to install {package}: {result.error}[/red]")
        
        return result
    
    async def update_requirements(self) -> ToolResult:
        """Update requirements.txt file."""
        if not self.available_tools.get('pip', False):
            return ToolResult("pip", "freeze", False, "", "pip not available", 0, datetime.now().isoformat())
        
        result = await self._run_command("pip freeze")
        if result.success:
            requirements_file = self.project_root / "requirements.txt"
            try:
                with open(requirements_file, 'w') as f:
                    f.write(result.output)
                console.print(f"[green]✅ Updated {requirements_file}[/green]")
            except Exception as e:
                return ToolResult("pip", "freeze", False, "", str(e), result.execution_time, result.timestamp)
        
        return result
    
    # Testing Integration
    async def run_tests(self, test_path: Optional[str] = None, test_framework: str = "auto") -> ToolResult:
        """Run tests using the appropriate testing framework."""
        if test_framework == "auto":
            # Auto-detect testing framework
            if (self.project_root / "pytest.ini").exists() or self.available_tools.get('pytest'):
                test_framework = "pytest"
            elif (self.project_root / "setup.cfg").exists():
                test_framework = "unittest"
            else:
                test_framework = "pytest"  # Default
        
        commands = {
            "pytest": f"pytest {test_path or ''}",
            "unittest": f"python -m unittest {test_path or 'discover'}",
            "nose": f"nosetests {test_path or ''}"
        }
        
        if test_framework not in commands:
            return ToolResult("test", "run", False, "", f"Unknown test framework: {test_framework}", 0, datetime.now().isoformat())
        
        console.print(f"[blue]🧪 Running tests with {test_framework}...[/blue]")
        result = await self._run_command(commands[test_framework])
        
        if result.success:
            console.print(f"[green]✅ Tests passed[/green]")
        else:
            console.print(f"[red]❌ Tests failed[/red]")
        
        return result
    
    async def run_coverage(self) -> ToolResult:
        """Run test coverage analysis."""
        if not self.available_tools.get('pytest', False):
            return ToolResult("coverage", "run", False, "", "pytest not available", 0, datetime.now().isoformat())
        
        console.print("[blue]📊 Running coverage analysis...[/blue]")
        result = await self._run_command("pytest --cov=. --cov-report=html")
        
        if result.success:
            console.print("[green]✅ Coverage analysis complete[/green]")
            console.print("[dim]Coverage report generated in htmlcov/[/dim]")
        
        return result
    
    # Code Quality Tools
    async def format_code(self, files: Optional[List[str]] = None) -> ToolResult:
        """Format code using Black or similar formatter."""
        if not self.available_tools.get('black', False):
            return ToolResult("black", "format", False, "", "black not available", 0, datetime.now().isoformat())
        
        file_args = " ".join(files) if files else "."
        console.print("[blue]🎨 Formatting code with Black...[/blue]")
        result = await self._run_command(f"black {file_args}")
        
        if result.success:
            console.print("[green]✅ Code formatted successfully[/green]")
        
        return result
    
    async def lint_code(self, files: Optional[List[str]] = None) -> ToolResult:
        """Lint code using flake8 or similar linter."""
        if not self.available_tools.get('flake8', False):
            return ToolResult("flake8", "lint", False, "", "flake8 not available", 0, datetime.now().isoformat())
        
        file_args = " ".join(files) if files else "."
        console.print("[blue]🔍 Linting code with flake8...[/blue]")
        result = await self._run_command(f"flake8 {file_args}")
        
        if result.success:
            console.print("[green]✅ No linting issues found[/green]")
        else:
            console.print("[yellow]⚠️ Linting issues found[/yellow]")
        
        return result
    
    async def type_check(self, files: Optional[List[str]] = None) -> ToolResult:
        """Run type checking with mypy."""
        if not self.available_tools.get('mypy', False):
            return ToolResult("mypy", "check", False, "", "mypy not available", 0, datetime.now().isoformat())
        
        file_args = " ".join(files) if files else "."
        console.print("[blue]🔍 Type checking with mypy...[/blue]")
        result = await self._run_command(f"mypy {file_args}")
        
        if result.success:
            console.print("[green]✅ No type errors found[/green]")
        else:
            console.print("[yellow]⚠️ Type errors found[/yellow]")
        
        return result
    
    # Code Execution
    async def execute_python_file(self, file_path: str, args: Optional[List[str]] = None) -> ToolResult:
        """Execute a Python file."""
        if not self.available_tools.get('python', False):
            return ToolResult("python", "execute", False, "", "python not available", 0, datetime.now().isoformat())
        
        args_str = " ".join(args) if args else ""
        command = f"python {file_path} {args_str}".strip()
        
        console.print(f"[blue]🐍 Executing: {command}[/blue]")
        result = await self._run_command(command)
        
        if result.success:
            console.print("[green]✅ Execution completed successfully[/green]")
            if result.output:
                console.print(f"[dim]Output:\n{result.output}[/dim]")
        else:
            console.print(f"[red]❌ Execution failed: {result.error}[/red]")
        
        return result
    
    async def execute_script(self, script_content: str, language: str = "python") -> ToolResult:
        """Execute a script from content."""
        if language == "python" and not self.available_tools.get('python', False):
            return ToolResult("python", "execute", False, "", "python not available", 0, datetime.now().isoformat())
        
        # Create temporary file
        temp_dir = self.project_root / ".hurricane" / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        extensions = {"python": ".py", "javascript": ".js", "bash": ".sh"}
        extension = extensions.get(language, ".txt")
        
        temp_file = temp_dir / f"temp_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}"
        
        try:
            with open(temp_file, 'w') as f:
                f.write(script_content)
            
            if language == "python":
                result = await self.execute_python_file(str(temp_file))
            elif language == "bash":
                result = await self._run_command(f"bash {temp_file}")
            else:
                result = ToolResult("script", "execute", False, "", f"Unsupported language: {language}", 0, datetime.now().isoformat())
            
            # Clean up
            temp_file.unlink(missing_ok=True)
            
            return result
            
        except Exception as e:
            return ToolResult("script", "execute", False, "", str(e), 0, datetime.now().isoformat())
    
    # Environment Management
    async def create_virtual_environment(self, env_name: str = "venv") -> ToolResult:
        """Create a Python virtual environment."""
        if not self.available_tools.get('python', False):
            return ToolResult("python", "venv", False, "", "python not available", 0, datetime.now().isoformat())
        
        env_path = self.project_root / env_name
        if env_path.exists():
            return ToolResult("python", "venv", False, "", f"Virtual environment {env_name} already exists", 0, datetime.now().isoformat())
        
        console.print(f"[blue]🐍 Creating virtual environment: {env_name}[/blue]")
        result = await self._run_command(f"python -m venv {env_name}")
        
        if result.success:
            console.print(f"[green]✅ Virtual environment created: {env_name}[/green]")
            console.print(f"[dim]Activate with: source {env_name}/bin/activate[/dim]")
        
        return result
    
    # Docker Integration
    async def build_docker_image(self, tag: str, dockerfile: str = "Dockerfile") -> ToolResult:
        """Build a Docker image."""
        if not self.available_tools.get('docker', False):
            return ToolResult("docker", "build", False, "", "docker not available", 0, datetime.now().isoformat())
        
        console.print(f"[blue]🐳 Building Docker image: {tag}[/blue]")
        result = await self._run_command(f"docker build -t {tag} -f {dockerfile} .")
        
        if result.success:
            console.print(f"[green]✅ Docker image built: {tag}[/green]")
        
        return result
    
    async def run_docker_container(self, image: str, args: Optional[List[str]] = None) -> ToolResult:
        """Run a Docker container."""
        if not self.available_tools.get('docker', False):
            return ToolResult("docker", "run", False, "", "docker not available", 0, datetime.now().isoformat())
        
        args_str = " ".join(args) if args else ""
        command = f"docker run {args_str} {image}".strip()
        
        console.print(f"[blue]🐳 Running Docker container: {image}[/blue]")
        result = await self._run_command(command)
        
        return result
    
    # Utility Methods
    def get_available_tools(self) -> Dict[str, bool]:
        """Get list of available tools."""
        return self.available_tools.copy()
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a specific tool is available."""
        return self.available_tools.get(tool_name, False)
    
    async def suggest_tools_for_task(self, task_description: str) -> List[str]:
        """Suggest appropriate tools for a given task."""
        task_lower = task_description.lower()
        suggestions = []
        
        # Git-related tasks
        if any(word in task_lower for word in ['commit', 'push', 'branch', 'merge', 'git']):
            if self.is_tool_available('git'):
                suggestions.append('git')
        
        # Testing tasks
        if any(word in task_lower for word in ['test', 'testing', 'coverage', 'unittest']):
            if self.is_tool_available('pytest'):
                suggestions.append('pytest')
        
        # Code quality tasks
        if any(word in task_lower for word in ['format', 'lint', 'style', 'quality']):
            if self.is_tool_available('black'):
                suggestions.append('black')
            if self.is_tool_available('flake8'):
                suggestions.append('flake8')
        
        # Package management
        if any(word in task_lower for word in ['install', 'package', 'dependency']):
            if self.is_tool_available('pip'):
                suggestions.append('pip')
            if self.is_tool_available('npm'):
                suggestions.append('npm')
        
        # Docker tasks
        if any(word in task_lower for word in ['docker', 'container', 'image']):
            if self.is_tool_available('docker'):
                suggestions.append('docker')
        
        return suggestions
    
    def show_tool_status(self):
        """Display tool availability status."""
        console.print(Panel.fit(
            "[bold blue]🔧 Tool Integration Status[/bold blue]",
            border_style="blue"
        ))
        
        # Available tools table
        tools_table = Table(title="Available Tools")
        tools_table.add_column("Tool", style="cyan")
        tools_table.add_column("Status", style="bold")
        tools_table.add_column("Purpose", style="dim")
        
        tool_purposes = {
            'git': 'Version control',
            'python': 'Python execution',
            'pip': 'Python package management',
            'npm': 'Node.js package management',
            'docker': 'Containerization',
            'pytest': 'Python testing',
            'black': 'Code formatting',
            'flake8': 'Code linting',
            'mypy': 'Type checking',
            'poetry': 'Python dependency management'
        }
        
        for tool, available in self.available_tools.items():
            status = "[green]✅ Available[/green]" if available else "[red]❌ Not Available[/red]"
            purpose = tool_purposes.get(tool, "Unknown")
            tools_table.add_row(tool, status, purpose)
        
        console.print(tools_table)

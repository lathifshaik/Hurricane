"""
Project planning and context management module for Hurricane AI Agent.
Maintains persistent project plans, tracks context, and manages editing progress.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


@dataclass
class Task:
    """Represents a project task."""
    id: str
    title: str
    description: str
    status: str  # todo, in_progress, done, blocked
    priority: str  # low, medium, high, critical
    created_at: str
    updated_at: str
    assigned_files: List[str] = None
    dependencies: List[str] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.assigned_files is None:
            self.assigned_files = []
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []


@dataclass
class ProjectContext:
    """Represents the current project context."""
    project_name: str
    project_root: str
    current_goal: str
    active_tasks: List[str]
    completed_tasks: List[str]
    blocked_tasks: List[str]
    current_files: List[str]  # Files currently being worked on
    recent_edits: List[Dict[str, Any]]  # Recent file edits with timestamps
    tech_stack: List[str]
    project_type: str
    last_updated: str
    session_start: str
    total_sessions: int = 0
    total_hours: float = 0.0


@dataclass
class FileEditProgress:
    """Tracks progress on file editing."""
    file_path: str
    status: str  # planning, editing, reviewing, complete
    last_edited: str
    changes_made: List[str]
    todo_items: List[str]
    estimated_completion: float  # 0.0 to 1.0
    context_notes: str = ""


class ProjectPlanner:
    """Intelligent project planning and context management."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config, project_root: Path):
        self.ollama_client = ollama_client
        self.config = config
        self.project_root = Path(project_root)
        
        # Project files
        self.hurricane_dir = self.project_root / ".hurricane"
        self.hurricane_dir.mkdir(exist_ok=True)
        
        self.plan_file = self.project_root / "plan.md"
        self.context_file = self.hurricane_dir / "context.json"
        self.tasks_file = self.hurricane_dir / "tasks.json"
        self.progress_file = self.hurricane_dir / "file_progress.json"
        
        # Load existing data
        self.project_context = self._load_context()
        self.tasks = self._load_tasks()
        self.file_progress = self._load_file_progress()
        
        # Update session info
        self._update_session_info()
    
    def _load_context(self) -> ProjectContext:
        """Load project context from file."""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r') as f:
                    data = json.load(f)
                return ProjectContext(**data)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load context: {e}[/yellow]")
        
        # Create default context
        return ProjectContext(
            project_name=self.project_root.name,
            project_root=str(self.project_root),
            current_goal="Project setup and initial development",
            active_tasks=[],
            completed_tasks=[],
            blocked_tasks=[],
            current_files=[],
            recent_edits=[],
            tech_stack=[],
            project_type="unknown",
            last_updated=datetime.now().isoformat(),
            session_start=datetime.now().isoformat()
        )
    
    def _load_tasks(self) -> Dict[str, Task]:
        """Load tasks from file."""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                return {task_id: Task(**task_data) for task_id, task_data in data.items()}
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load tasks: {e}[/yellow]")
        
        return {}
    
    def _load_file_progress(self) -> Dict[str, FileEditProgress]:
        """Load file editing progress."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                return {file_path: FileEditProgress(**progress_data) 
                       for file_path, progress_data in data.items()}
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load file progress: {e}[/yellow]")
        
        return {}
    
    def _update_session_info(self):
        """Update session information."""
        now = datetime.now().isoformat()
        self.project_context.session_start = now
        self.project_context.last_updated = now
        self.project_context.total_sessions += 1
        self._save_context()
    
    def _save_context(self):
        """Save project context to file."""
        try:
            with open(self.context_file, 'w') as f:
                json.dump(asdict(self.project_context), f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Could not save context: {e}[/red]")
    
    def _save_tasks(self):
        """Save tasks to file."""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump({task_id: asdict(task) for task_id, task in self.tasks.items()}, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Could not save tasks: {e}[/red]")
    
    def _save_file_progress(self):
        """Save file progress to file."""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump({file_path: asdict(progress) 
                          for file_path, progress in self.file_progress.items()}, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Could not save file progress: {e}[/red]")
    
    async def initialize_project_plan(self, user_goal: str = None) -> bool:
        """Initialize or update the project plan."""
        console.print("[bold blue]📋 Initializing project plan...[/bold blue]")
        
        # Detect project type and tech stack
        await self._detect_project_info()
        
        # Get or update project goal
        if user_goal:
            self.project_context.current_goal = user_goal
        elif not self.project_context.current_goal or self.project_context.current_goal == "Project setup and initial development":
            goal = await self._generate_project_goal()
            self.project_context.current_goal = goal
        
        # Generate initial plan if it doesn't exist
        if not self.plan_file.exists():
            await self._generate_initial_plan()
        else:
            await self._update_existing_plan()
        
        self._save_context()
        console.print("[green]✅ Project plan initialized![/green]")
        return True
    
    async def _detect_project_info(self):
        """Detect project type and technology stack."""
        console.print("[blue]🔍 Analyzing project structure...[/blue]")
        
        # Check for common project files
        tech_indicators = {
            'python': ['requirements.txt', 'setup.py', 'pyproject.toml', '*.py'],
            'javascript': ['package.json', 'node_modules', '*.js', '*.jsx'],
            'typescript': ['tsconfig.json', '*.ts', '*.tsx'],
            'react': ['package.json', 'src/App.js', 'src/App.tsx', 'public/index.html'],
            'vue': ['vue.config.js', '*.vue', 'package.json'],
            'angular': ['angular.json', '*.component.ts'],
            'go': ['go.mod', '*.go'],
            'rust': ['Cargo.toml', '*.rs'],
            'java': ['pom.xml', 'build.gradle', '*.java'],
            'docker': ['Dockerfile', 'docker-compose.yml'],
            'web': ['index.html', '*.css', '*.html']
        }
        
        detected_tech = []
        project_type = "general"
        
        for tech, indicators in tech_indicators.items():
            for indicator in indicators:
                if indicator.startswith('*.'):
                    # Check for file extensions
                    ext = indicator[1:]
                    if list(self.project_root.rglob(f"*{ext}")):
                        detected_tech.append(tech)
                        break
                else:
                    # Check for specific files
                    if (self.project_root / indicator).exists():
                        detected_tech.append(tech)
                        if tech in ['react', 'vue', 'angular']:
                            project_type = "web_app"
                        elif tech in ['python', 'go', 'rust', 'java']:
                            project_type = "backend"
                        break
        
        self.project_context.tech_stack = list(set(detected_tech))
        self.project_context.project_type = project_type
        
        console.print(f"[green]📊 Detected: {', '.join(detected_tech)} ({project_type})[/green]")
    
    async def _generate_project_goal(self) -> str:
        """Generate a project goal using AI."""
        try:
            # Analyze project structure for context
            file_list = []
            for file_path in self.project_root.rglob("*"):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    file_list.append(str(file_path.relative_to(self.project_root)))
            
            prompt = f"""Analyze this project structure and suggest a clear, specific project goal:

Project: {self.project_context.project_name}
Type: {self.project_context.project_type}
Tech Stack: {', '.join(self.project_context.tech_stack)}

Key Files:
{chr(10).join(file_list[:20])}  # Show first 20 files

Generate a concise, actionable project goal (1-2 sentences) that describes what this project aims to accomplish."""
            
            goal = await self.ollama_client.generate_response(
                prompt,
                system_prompt="You are a project manager. Generate clear, specific project goals based on codebase analysis."
            )
            
            return goal.strip()
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not generate goal: {e}[/yellow]")
            return f"Develop and maintain the {self.project_context.project_name} project"
    
    async def _generate_initial_plan(self):
        """Generate initial project plan."""
        console.print("[blue]📝 Generating project plan...[/blue]")
        
        try:
            # Generate plan content using AI
            prompt = f"""Create a comprehensive project plan for:

Project: {self.project_context.project_name}
Goal: {self.project_context.current_goal}
Type: {self.project_context.project_type}
Tech Stack: {', '.join(self.project_context.tech_stack)}

Generate a detailed plan in Markdown format with:
1. Project Overview
2. Goals and Objectives
3. Technical Requirements
4. Development Phases
5. Task Breakdown
6. Timeline Estimates
7. Success Criteria

Make it specific to this project type and technology stack."""
            
            plan_content = await self.ollama_client.generate_response(
                prompt,
                system_prompt="You are a senior project manager. Create detailed, actionable project plans."
            )
            
            # Add metadata header
            header = f"""# {self.project_context.project_name} - Project Plan

**Generated by Hurricane AI Agent**  
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Project Type:** {self.project_context.project_type}  
**Tech Stack:** {', '.join(self.project_context.tech_stack)}  

---

"""
            
            # Save plan file
            with open(self.plan_file, 'w') as f:
                f.write(header + plan_content)
            
            # Extract tasks from the plan
            await self._extract_tasks_from_plan(plan_content)
            
            console.print(f"[green]✅ Project plan created: {self.plan_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ Could not generate plan: {e}[/red]")
            # Create a basic plan
            self._create_basic_plan()
    
    async def _update_existing_plan(self):
        """Update existing project plan with current context."""
        console.print("[blue]🔄 Updating project plan...[/blue]")
        
        try:
            # Read existing plan
            current_plan = self.plan_file.read_text()
            
            # Generate update using AI
            prompt = f"""Update this project plan based on current progress:

Current Plan:
{current_plan[:2000]}  # First 2000 chars

Current Context:
- Goal: {self.project_context.current_goal}
- Active Tasks: {len(self.project_context.active_tasks)}
- Completed Tasks: {len(self.project_context.completed_tasks)}
- Files in Progress: {', '.join(self.project_context.current_files[:5])}
- Recent Session: {self.project_context.total_sessions} sessions

Add a "Progress Update" section at the end with current status and next steps."""
            
            update_content = await self.ollama_client.generate_response(
                prompt,
                system_prompt="You are a project manager updating project plans based on current progress."
            )
            
            # Append update to plan
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_section = f"\n\n---\n\n## Progress Update - {timestamp}\n\n{update_content}\n"
            
            with open(self.plan_file, 'a') as f:
                f.write(update_section)
            
            console.print("[green]✅ Project plan updated![/green]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not update plan: {e}[/yellow]")
    
    def _create_basic_plan(self):
        """Create a basic project plan as fallback."""
        basic_plan = f"""# {self.project_context.project_name} - Project Plan

## Overview
{self.project_context.current_goal}

## Tech Stack
{', '.join(self.project_context.tech_stack)}

## Tasks
- [ ] Project setup and configuration
- [ ] Core functionality implementation
- [ ] Testing and quality assurance
- [ ] Documentation
- [ ] Deployment preparation

## Notes
This is a basic plan. Use Hurricane's AI features to generate a more detailed plan.

---
*Generated by Hurricane AI Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(self.plan_file, 'w') as f:
            f.write(basic_plan)
    
    async def _extract_tasks_from_plan(self, plan_content: str):
        """Extract tasks from plan content using AI."""
        try:
            prompt = f"""Extract actionable tasks from this project plan:

{plan_content[:1500]}

Return a JSON list of tasks with this format:
[
  {{
    "title": "Task title",
    "description": "Detailed description",
    "priority": "high|medium|low",
    "estimated_hours": 2.0
  }}
]

Focus on concrete, actionable tasks."""
            
            response = await self.ollama_client.generate_response(
                prompt,
                system_prompt="Extract tasks from project plans. Return valid JSON only."
            )
            
            # Try to parse JSON response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                tasks_data = json.loads(json_match.group())
                
                for i, task_data in enumerate(tasks_data[:10]):  # Limit to 10 tasks
                    task_id = f"task_{i+1:03d}"
                    task = Task(
                        id=task_id,
                        title=task_data.get('title', f'Task {i+1}'),
                        description=task_data.get('description', ''),
                        status='todo',
                        priority=task_data.get('priority', 'medium'),
                        created_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat(),
                        estimated_hours=task_data.get('estimated_hours', 1.0)
                    )
                    self.tasks[task_id] = task
                    self.project_context.active_tasks.append(task_id)
                
                self._save_tasks()
                console.print(f"[green]✅ Extracted {len(tasks_data)} tasks from plan[/green]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not extract tasks: {e}[/yellow]")
    
    def track_file_edit(self, file_path: str, changes: List[str], status: str = "editing"):
        """Track file editing progress."""
        file_path = str(Path(file_path).relative_to(self.project_root))
        
        if file_path not in self.file_progress:
            self.file_progress[file_path] = FileEditProgress(
                file_path=file_path,
                status=status,
                last_edited=datetime.now().isoformat(),
                changes_made=[],
                todo_items=[],
                estimated_completion=0.0
            )
        
        progress = self.file_progress[file_path]
        progress.last_edited = datetime.now().isoformat()
        progress.status = status
        progress.changes_made.extend(changes)
        
        # Update project context
        if file_path not in self.project_context.current_files:
            self.project_context.current_files.append(file_path)
        
        # Add to recent edits
        edit_record = {
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
            "changes": changes,
            "status": status
        }
        self.project_context.recent_edits.append(edit_record)
        
        # Keep only last 20 edits
        self.project_context.recent_edits = self.project_context.recent_edits[-20:]
        
        self._save_file_progress()
        self._save_context()
    
    def get_context_for_file(self, file_path: str) -> Dict[str, Any]:
        """Get context information for a specific file."""
        file_path = str(Path(file_path).relative_to(self.project_root))
        
        context = {
            "project_goal": self.project_context.current_goal,
            "project_type": self.project_context.project_type,
            "tech_stack": self.project_context.tech_stack,
            "active_tasks": [self.tasks[task_id] for task_id in self.project_context.active_tasks if task_id in self.tasks],
            "file_progress": self.file_progress.get(file_path),
            "related_files": self._get_related_files(file_path),
            "recent_changes": [edit for edit in self.project_context.recent_edits if edit["file"] == file_path]
        }
        
        return context
    
    def _get_related_files(self, file_path: str) -> List[str]:
        """Get files related to the current file."""
        # Simple heuristic: files in same directory or with similar names
        file_path_obj = Path(file_path)
        related = []
        
        # Files in same directory
        if file_path_obj.parent != Path('.'):
            for other_file in self.project_context.current_files:
                if Path(other_file).parent == file_path_obj.parent and other_file != file_path:
                    related.append(other_file)
        
        # Files with similar names (same stem)
        stem = file_path_obj.stem
        for other_file in self.project_context.current_files:
            if Path(other_file).stem == stem and other_file != file_path:
                related.append(other_file)
        
        return related[:5]  # Limit to 5 related files
    
    async def suggest_next_steps(self) -> List[str]:
        """Suggest next steps based on current context."""
        try:
            # Prepare context for AI
            active_tasks = [self.tasks[task_id] for task_id in self.project_context.active_tasks if task_id in self.tasks]
            
            prompt = f"""Based on the current project context, suggest 3-5 specific next steps:

Project: {self.project_context.project_name}
Goal: {self.project_context.current_goal}
Type: {self.project_context.project_type}

Active Tasks:
{chr(10).join([f"- {task.title}: {task.description}" for task in active_tasks[:5]])}

Files in Progress:
{chr(10).join([f"- {file}: {self.file_progress[file].status}" for file in self.project_context.current_files[:5] if file in self.file_progress])}

Recent Activity:
{chr(10).join([f"- {edit['file']}: {', '.join(edit['changes'][:2])}" for edit in self.project_context.recent_edits[-3:]])}

Suggest specific, actionable next steps to move the project forward."""
            
            response = await self.ollama_client.generate_response(
                prompt,
                system_prompt="You are a project manager. Suggest specific, actionable next steps based on current project context."
            )
            
            # Parse suggestions
            suggestions = []
            for line in response.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    suggestions.append(line.lstrip('-•0123456789. '))
            
            return suggestions[:5]
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not generate suggestions: {e}[/yellow]")
            return ["Continue working on active tasks", "Review and test recent changes", "Update documentation"]
    
    def show_project_status(self):
        """Display current project status."""
        console.print(Panel.fit(
            f"[bold blue]{self.project_context.project_name}[/bold blue]\n"
            f"[dim]{self.project_context.current_goal}[/dim]",
            title="🎯 Current Project",
            border_style="blue"
        ))
        
        # Tasks summary
        total_tasks = len(self.tasks)
        active_tasks = len(self.project_context.active_tasks)
        completed_tasks = len(self.project_context.completed_tasks)
        
        tasks_table = Table(title="📋 Tasks Overview")
        tasks_table.add_column("Status", style="bold")
        tasks_table.add_column("Count", justify="right")
        tasks_table.add_column("Percentage", justify="right")
        
        if total_tasks > 0:
            tasks_table.add_row("Active", str(active_tasks), f"{(active_tasks/total_tasks)*100:.1f}%")
            tasks_table.add_row("Completed", str(completed_tasks), f"{(completed_tasks/total_tasks)*100:.1f}%")
            tasks_table.add_row("Total", str(total_tasks), "100%")
        else:
            tasks_table.add_row("No tasks", "0", "0%")
        
        console.print(tasks_table)
        
        # Files in progress
        if self.project_context.current_files:
            console.print("\n[bold green]📁 Files in Progress:[/bold green]")
            for file_path in self.project_context.current_files[:10]:
                if file_path in self.file_progress:
                    progress = self.file_progress[file_path]
                    status_color = {
                        "planning": "yellow",
                        "editing": "blue",
                        "reviewing": "cyan",
                        "complete": "green"
                    }.get(progress.status, "white")
                    
                    completion = int(progress.estimated_completion * 100)
                    console.print(f"  • [{status_color}]{file_path}[/{status_color}] - {progress.status} ({completion}%)")
        
        # Recent activity
        if self.project_context.recent_edits:
            console.print("\n[bold cyan]⚡ Recent Activity:[/bold cyan]")
            for edit in self.project_context.recent_edits[-5:]:
                timestamp = datetime.fromisoformat(edit["timestamp"]).strftime("%H:%M")
                changes_summary = ", ".join(edit["changes"][:2])
                if len(edit["changes"]) > 2:
                    changes_summary += "..."
                console.print(f"  • [dim]{timestamp}[/dim] {edit['file']}: {changes_summary}")
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        ignore_patterns = {
            '__pycache__', '.git', '.svn', 'node_modules', '.vscode', 
            '.idea', 'venv', 'env', '.env', 'dist', 'build', '.DS_Store',
            '.pytest_cache', '.coverage', 'htmlcov', '.hurricane'
        }
        
        return any(pattern in str(file_path) for pattern in ignore_patterns)
    
    def update_project_goal(self, new_goal: str):
        """Update the project goal."""
        self.project_context.current_goal = new_goal
        self.project_context.last_updated = datetime.now().isoformat()
        self._save_context()
        console.print(f"[green]✅ Updated project goal: {new_goal}[/green]")
    
    def complete_task(self, task_id: str):
        """Mark a task as completed."""
        if task_id in self.tasks:
            self.tasks[task_id].status = "done"
            self.tasks[task_id].updated_at = datetime.now().isoformat()
            
            if task_id in self.project_context.active_tasks:
                self.project_context.active_tasks.remove(task_id)
            if task_id not in self.project_context.completed_tasks:
                self.project_context.completed_tasks.append(task_id)
            
            self._save_tasks()
            self._save_context()
            
            console.print(f"[green]✅ Task completed: {self.tasks[task_id].title}[/green]")
            return True
        
        return False

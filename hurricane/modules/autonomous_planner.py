"""
Autonomous task planning and goal-oriented behavior module for Hurricane AI Agent.
Enables the agent to break down high-level goals, make autonomous decisions, and persist objectives.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class AutonomousTask:
    """Represents an autonomous task with decision-making context."""
    id: str
    title: str
    description: str
    goal_context: str
    priority: TaskPriority
    status: TaskStatus
    created_at: str
    updated_at: str
    estimated_duration: int  # minutes
    dependencies: List[str]
    required_tools: List[str]
    success_criteria: List[str]
    autonomous_actions: List[str]  # Actions the agent can take without human approval
    human_approval_required: bool
    progress_percentage: float
    metadata: Dict[str, Any]

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class Goal:
    """Represents a high-level goal that can be decomposed into tasks."""
    id: str
    title: str
    description: str
    target_outcome: str
    priority: TaskPriority
    deadline: Optional[str]
    created_at: str
    status: str  # active, paused, completed, abandoned
    progress_percentage: float
    subtasks: List[str]  # Task IDs
    success_metrics: List[str]
    context: Dict[str, Any]


class AutonomousPlanner:
    """Autonomous task planning and goal-oriented behavior engine."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config, project_root: Path):
        self.ollama_client = ollama_client
        self.config = config
        self.project_root = Path(project_root)
        
        # Storage files
        self.hurricane_dir = self.project_root / ".hurricane"
        self.hurricane_dir.mkdir(exist_ok=True)
        
        self.goals_file = self.hurricane_dir / "goals.json"
        self.tasks_file = self.hurricane_dir / "autonomous_tasks.json"
        self.decisions_file = self.hurricane_dir / "decisions.json"
        self.learning_file = self.hurricane_dir / "learning_patterns.json"
        
        # Load existing data
        self.goals = self._load_goals()
        self.tasks = self._load_tasks()
        self.decisions = self._load_decisions()
        self.learning_patterns = self._load_learning_patterns()
        
        # Planning context
        self.current_session_goals = []
        self.proactive_suggestions = []
        
    def _load_goals(self) -> Dict[str, Goal]:
        """Load goals from storage."""
        if self.goals_file.exists():
            try:
                with open(self.goals_file, 'r') as f:
                    data = json.load(f)
                return {g_id: Goal(**g_data) for g_id, g_data in data.items()}
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load goals: {e}[/yellow]")
        return {}
    
    def _load_tasks(self) -> Dict[str, AutonomousTask]:
        """Load autonomous tasks from storage."""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                tasks = {}
                for t_id, t_data in data.items():
                    # Convert enum strings back to enums
                    t_data['priority'] = TaskPriority(t_data['priority'])
                    t_data['status'] = TaskStatus(t_data['status'])
                    tasks[t_id] = AutonomousTask(**t_data)
                return tasks
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load tasks: {e}[/yellow]")
        return {}
    
    def _load_decisions(self) -> List[Dict[str, Any]]:
        """Load decision history."""
        if self.decisions_file.exists():
            try:
                with open(self.decisions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load decisions: {e}[/yellow]")
        return []
    
    def _load_learning_patterns(self) -> Dict[str, Any]:
        """Load learning patterns and user preferences."""
        if self.learning_file.exists():
            try:
                with open(self.learning_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load learning patterns: {e}[/yellow]")
        return {
            "user_preferences": {},
            "successful_patterns": [],
            "failed_patterns": [],
            "context_patterns": {}
        }
    
    def _save_goals(self):
        """Save goals to storage."""
        try:
            data = {g_id: asdict(goal) for g_id, goal in self.goals.items()}
            with open(self.goals_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving goals: {e}[/red]")
    
    def _save_tasks(self):
        """Save tasks to storage."""
        try:
            data = {}
            for t_id, task in self.tasks.items():
                task_data = asdict(task)
                # Convert enums to strings for JSON serialization
                task_data['priority'] = task.priority.value
                task_data['status'] = task.status.value
                data[t_id] = task_data
            
            with open(self.tasks_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving tasks: {e}[/red]")
    
    def _save_decisions(self):
        """Save decision history."""
        try:
            with open(self.decisions_file, 'w') as f:
                json.dump(self.decisions, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving decisions: {e}[/red]")
    
    def _save_learning_patterns(self):
        """Save learning patterns."""
        try:
            with open(self.learning_file, 'w') as f:
                json.dump(self.learning_patterns, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving learning patterns: {e}[/red]")
    
    async def set_goal(self, title: str, description: str, target_outcome: str, 
                      priority: TaskPriority = TaskPriority.MEDIUM, 
                      deadline: Optional[str] = None) -> str:
        """Set a new high-level goal and begin autonomous planning."""
        goal_id = str(uuid.uuid4())
        
        goal = Goal(
            id=goal_id,
            title=title,
            description=description,
            target_outcome=target_outcome,
            priority=priority,
            deadline=deadline,
            created_at=datetime.now().isoformat(),
            status="active",
            progress_percentage=0.0,
            subtasks=[],
            success_metrics=[],
            context={}
        )
        
        self.goals[goal_id] = goal
        self.current_session_goals.append(goal_id)
        
        console.print(f"[bold green]🎯 New goal set: {title}[/bold green]")
        
        # Autonomous task decomposition
        await self._decompose_goal_into_tasks(goal)
        
        # Generate initial proactive suggestions
        await self._generate_proactive_suggestions(goal_id)
        
        self._save_goals()
        return goal_id
    
    async def _decompose_goal_into_tasks(self, goal: Goal):
        """Autonomously break down a goal into actionable tasks."""
        console.print("[blue]🧠 Analyzing goal and creating autonomous task plan...[/blue]")
        
        system_prompt = """You are Hurricane's autonomous planning engine. Break down the given goal into specific, actionable tasks.

For each task, consider:
1. What specific action needs to be taken
2. What tools/resources are required
3. Dependencies between tasks
4. Whether the task can be done autonomously or needs human approval
5. Success criteria for the task

Return a JSON array of tasks with this structure:
{
  "title": "Task title",
  "description": "Detailed description",
  "priority": "high|medium|low|critical",
  "estimated_duration": 30,
  "dependencies": ["task_id_1"],
  "required_tools": ["git", "ollama", "file_system"],
  "success_criteria": ["Criteria 1", "Criteria 2"],
  "autonomous_actions": ["Action 1", "Action 2"],
  "human_approval_required": false
}"""
        
        prompt = f"""
Goal: {goal.title}
Description: {goal.description}
Target Outcome: {goal.target_outcome}

Project Context:
- Project Root: {self.project_root}
- Current Goals: {len(self.current_session_goals)} active
- Available Tools: git, ollama, file_system, code_analysis, documentation

Please create a comprehensive task breakdown for this goal.
"""
        
        try:
            response = await self.ollama_client.generate_response(
                system_prompt, prompt, model=self.config.ollama.model
            )
            
            # Parse the response and create tasks
            tasks_data = json.loads(response.strip())
            
            for task_data in tasks_data:
                task = AutonomousTask(
                    id=str(uuid.uuid4()),
                    title=task_data["title"],
                    description=task_data["description"],
                    goal_context=goal.id,
                    priority=TaskPriority(task_data.get("priority", "medium")),
                    status=TaskStatus.PLANNED,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat(),
                    estimated_duration=task_data.get("estimated_duration", 30),
                    dependencies=task_data.get("dependencies", []),
                    required_tools=task_data.get("required_tools", []),
                    success_criteria=task_data.get("success_criteria", []),
                    autonomous_actions=task_data.get("autonomous_actions", []),
                    human_approval_required=task_data.get("human_approval_required", False),
                    progress_percentage=0.0,
                    metadata={"auto_generated": True}
                )
                
                self.tasks[task.id] = task
                goal.subtasks.append(task.id)
            
            console.print(f"[green]✅ Created {len(tasks_data)} autonomous tasks for goal[/green]")
            self._save_tasks()
            self._save_goals()
            
        except Exception as e:
            console.print(f"[red]❌ Error decomposing goal: {e}[/red]")
            # Create a basic fallback task
            fallback_task = AutonomousTask(
                id=str(uuid.uuid4()),
                title=f"Work on: {goal.title}",
                description=goal.description,
                goal_context=goal.id,
                priority=goal.priority,
                status=TaskStatus.PLANNED,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                estimated_duration=60,
                dependencies=[],
                required_tools=["ollama"],
                success_criteria=[goal.target_outcome],
                autonomous_actions=["Analyze requirements", "Generate initial plan"],
                human_approval_required=True,
                progress_percentage=0.0,
                metadata={"fallback": True}
            )
            
            self.tasks[fallback_task.id] = fallback_task
            goal.subtasks.append(fallback_task.id)
            self._save_tasks()
            self._save_goals()
    
    async def _generate_proactive_suggestions(self, goal_id: str):
        """Generate proactive suggestions for the next steps."""
        goal = self.goals[goal_id]
        active_tasks = [task for task in self.tasks.values() 
                       if task.goal_context == goal_id and task.status == TaskStatus.PLANNED]
        
        if not active_tasks:
            return
        
        # Find the highest priority task that can be started
        next_task = min(active_tasks, key=lambda t: (
            t.priority.value != "critical",
            t.priority.value != "high", 
            len(t.dependencies)
        ))
        
        suggestion = {
            "type": "next_task",
            "task_id": next_task.id,
            "title": next_task.title,
            "description": next_task.description,
            "autonomous": not next_task.human_approval_required,
            "estimated_duration": next_task.estimated_duration,
            "timestamp": datetime.now().isoformat()
        }
        
        self.proactive_suggestions.append(suggestion)
        
        console.print(f"[cyan]💡 Proactive suggestion: {next_task.title}[/cyan]")
        
        if not next_task.human_approval_required:
            console.print("[yellow]🤖 This task can be executed autonomously. Would you like me to proceed?[/yellow]")
    
    async def execute_autonomous_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a task autonomously if it doesn't require human approval."""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
        
        task = self.tasks[task_id]
        
        if task.human_approval_required:
            return {"error": "Task requires human approval"}
        
        if task.status != TaskStatus.PLANNED:
            return {"error": f"Task is not in planned state: {task.status.value}"}
        
        console.print(f"[blue]🤖 Executing autonomous task: {task.title}[/blue]")
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now().isoformat()
        
        # Record decision
        decision = {
            "timestamp": datetime.now().isoformat(),
            "type": "autonomous_execution",
            "task_id": task_id,
            "task_title": task.title,
            "reasoning": "Task marked as autonomous and meets execution criteria",
            "context": {
                "goal_id": task.goal_context,
                "required_tools": task.required_tools,
                "estimated_duration": task.estimated_duration
            }
        }
        self.decisions.append(decision)
        
        try:
            # Execute autonomous actions
            results = []
            for action in task.autonomous_actions:
                result = await self._execute_autonomous_action(action, task)
                results.append(result)
            
            # Update progress
            task.progress_percentage = 100.0
            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.now().isoformat()
            
            # Update goal progress
            await self._update_goal_progress(task.goal_context)
            
            console.print(f"[green]✅ Autonomous task completed: {task.title}[/green]")
            
            # Generate next suggestions
            await self._generate_proactive_suggestions(task.goal_context)
            
            self._save_tasks()
            self._save_decisions()
            
            return {
                "success": True,
                "task_id": task_id,
                "results": results,
                "completion_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            task.status = TaskStatus.BLOCKED
            task.metadata["error"] = str(e)
            task.updated_at = datetime.now().isoformat()
            
            console.print(f"[red]❌ Error executing autonomous task: {e}[/red]")
            
            self._save_tasks()
            return {"error": str(e), "task_id": task_id}
    
    async def _execute_autonomous_action(self, action: str, task: AutonomousTask) -> Dict[str, Any]:
        """Execute a specific autonomous action."""
        # This is where specific autonomous actions would be implemented
        # For now, we'll simulate the execution
        
        console.print(f"[dim]  Executing: {action}[/dim]")
        
        # Simulate some processing time
        await asyncio.sleep(0.5)
        
        return {
            "action": action,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "details": f"Simulated execution of: {action}"
        }
    
    async def _update_goal_progress(self, goal_id: str):
        """Update goal progress based on completed tasks."""
        if goal_id not in self.goals:
            return
        
        goal = self.goals[goal_id]
        if not goal.subtasks:
            return
        
        completed_tasks = sum(1 for task_id in goal.subtasks 
                            if task_id in self.tasks and 
                            self.tasks[task_id].status == TaskStatus.COMPLETED)
        
        total_tasks = len(goal.subtasks)
        goal.progress_percentage = (completed_tasks / total_tasks) * 100
        
        if goal.progress_percentage == 100:
            goal.status = "completed"
            console.print(f"[bold green]🎉 Goal completed: {goal.title}[/bold green]")
        
        self._save_goals()
    
    def get_proactive_suggestions(self) -> List[Dict[str, Any]]:
        """Get current proactive suggestions."""
        return self.proactive_suggestions
    
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals."""
        return [goal for goal in self.goals.values() if goal.status == "active"]
    
    def get_next_autonomous_task(self) -> Optional[AutonomousTask]:
        """Get the next task that can be executed autonomously."""
        autonomous_tasks = [
            task for task in self.tasks.values()
            if (task.status == TaskStatus.PLANNED and 
                not task.human_approval_required and
                len(task.dependencies) == 0)
        ]
        
        if not autonomous_tasks:
            return None
        
        # Return highest priority task
        return min(autonomous_tasks, key=lambda t: (
            t.priority.value != "critical",
            t.priority.value != "high",
            t.created_at
        ))
    
    def show_autonomous_status(self):
        """Display current autonomous planning status."""
        console.print(Panel.fit(
            "[bold blue]🤖 Autonomous Planning Status[/bold blue]",
            border_style="blue"
        ))
        
        # Active goals
        active_goals = self.get_active_goals()
        if active_goals:
            goals_table = Table(title="🎯 Active Goals")
            goals_table.add_column("Goal", style="cyan")
            goals_table.add_column("Progress", style="green")
            goals_table.add_column("Tasks", style="yellow")
            
            for goal in active_goals[:5]:  # Show top 5
                task_count = len(goal.subtasks)
                goals_table.add_row(
                    goal.title[:40] + "..." if len(goal.title) > 40 else goal.title,
                    f"{goal.progress_percentage:.1f}%",
                    str(task_count)
                )
            
            console.print(goals_table)
        
        # Next autonomous task
        next_task = self.get_next_autonomous_task()
        if next_task:
            console.print(f"\n[bold yellow]🚀 Next Autonomous Task:[/bold yellow]")
            console.print(f"[cyan]{next_task.title}[/cyan]")
            console.print(f"[dim]{next_task.description}[/dim]")
            console.print(f"[green]Estimated duration: {next_task.estimated_duration} minutes[/green]")
        
        # Proactive suggestions
        if self.proactive_suggestions:
            console.print(f"\n[bold magenta]💡 Proactive Suggestions ({len(self.proactive_suggestions)}):[/bold magenta]")
            for suggestion in self.proactive_suggestions[-3:]:  # Show last 3
                console.print(f"• {suggestion['title']}")

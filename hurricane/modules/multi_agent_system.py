"""
Multi-agent collaborative system for Hurricane AI Agent.
Coordinates specialized agents for different tasks and manages workflow orchestration.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


class AgentRole(Enum):
    COORDINATOR = "coordinator"
    CODER = "coder"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    REVIEWER = "reviewer"
    DEPLOYER = "deployer"
    MONITOR = "monitor"


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class AgentTask:
    """Represents a task assigned to an agent."""
    id: str
    title: str
    description: str
    assigned_agent: AgentRole
    status: TaskStatus
    priority: int  # 1-5, 5 being highest
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    dependencies: List[str] = None
    outputs: Dict[str, Any] = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.outputs is None:
            self.outputs = {}
        if self.context is None:
            self.context = {}


@dataclass
class Agent:
    """Represents a specialized agent."""
    role: AgentRole
    name: str
    description: str
    capabilities: List[str]
    current_task: Optional[str] = None
    task_history: List[str] = None
    performance_metrics: Dict[str, float] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.task_history is None:
            self.task_history = []
        if self.performance_metrics is None:
            self.performance_metrics = {
                "tasks_completed": 0,
                "success_rate": 1.0,
                "avg_completion_time": 0.0
            }


class MultiAgentSystem:
    """Multi-agent collaborative system for Hurricane."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config, project_root: Path):
        self.ollama_client = ollama_client
        self.config = config
        self.project_root = Path(project_root)
        
        # Storage
        self.hurricane_dir = self.project_root / ".hurricane"
        self.hurricane_dir.mkdir(exist_ok=True)
        
        self.agents_file = self.hurricane_dir / "agents.json"
        self.tasks_file = self.hurricane_dir / "agent_tasks.json"
        self.workflows_file = self.hurricane_dir / "workflows.json"
        
        # Initialize agents and tasks
        self.agents = self._initialize_agents()
        self.tasks = self._load_tasks()
        self.workflows = self._load_workflows()
        
        # Coordination state
        self.active_workflows = {}
        self.task_queue = []
        self.coordination_running = False
    
    def _initialize_agents(self) -> Dict[AgentRole, Agent]:
        """Initialize specialized agents."""
        agents = {
            AgentRole.COORDINATOR: Agent(
                role=AgentRole.COORDINATOR,
                name="Hurricane Coordinator",
                description="Orchestrates tasks and coordinates between agents",
                capabilities=[
                    "task_planning", "workflow_orchestration", "resource_allocation",
                    "conflict_resolution", "progress_monitoring"
                ]
            ),
            AgentRole.CODER: Agent(
                role=AgentRole.CODER,
                name="Hurricane Coder",
                description="Specialized in code generation, debugging, and refactoring",
                capabilities=[
                    "code_generation", "debugging", "refactoring", "optimization",
                    "architecture_design", "code_review"
                ]
            ),
            AgentRole.TESTER: Agent(
                role=AgentRole.TESTER,
                name="Hurricane Tester",
                description="Handles testing, quality assurance, and validation",
                capabilities=[
                    "test_generation", "test_execution", "coverage_analysis",
                    "performance_testing", "integration_testing", "bug_detection"
                ]
            ),
            AgentRole.DOCUMENTER: Agent(
                role=AgentRole.DOCUMENTER,
                name="Hurricane Documenter",
                description="Creates and maintains documentation",
                capabilities=[
                    "documentation_generation", "api_documentation", "readme_creation",
                    "code_commenting", "tutorial_writing", "changelog_maintenance"
                ]
            ),
            AgentRole.REVIEWER: Agent(
                role=AgentRole.REVIEWER,
                name="Hurricane Reviewer",
                description="Reviews code quality, architecture, and best practices",
                capabilities=[
                    "code_review", "architecture_review", "security_audit",
                    "performance_analysis", "best_practices_enforcement", "quality_gates"
                ]
            ),
            AgentRole.DEPLOYER: Agent(
                role=AgentRole.DEPLOYER,
                name="Hurricane Deployer",
                description="Handles deployment, CI/CD, and infrastructure",
                capabilities=[
                    "deployment_automation", "ci_cd_setup", "infrastructure_management",
                    "environment_configuration", "monitoring_setup", "rollback_management"
                ]
            ),
            AgentRole.MONITOR: Agent(
                role=AgentRole.MONITOR,
                name="Hurricane Monitor",
                description="Monitors system health, performance, and issues",
                capabilities=[
                    "system_monitoring", "performance_tracking", "error_detection",
                    "alert_management", "health_checks", "metrics_collection"
                ]
            )
        }
        
        # Load existing agent data if available
        if self.agents_file.exists():
            try:
                with open(self.agents_file, 'r') as f:
                    saved_data = json.load(f)
                
                for role_str, agent_data in saved_data.items():
                    role = AgentRole(role_str)
                    if role in agents:
                        # Update performance metrics and history
                        agents[role].task_history = agent_data.get("task_history", [])
                        agents[role].performance_metrics = agent_data.get("performance_metrics", agents[role].performance_metrics)
                        agents[role].is_active = agent_data.get("is_active", True)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load agent data: {e}[/yellow]")
        
        return agents
    
    def _load_tasks(self) -> Dict[str, AgentTask]:
        """Load agent tasks from storage."""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                
                tasks = {}
                for task_id, task_data in data.items():
                    # Convert enum strings back to enums
                    task_data['assigned_agent'] = AgentRole(task_data['assigned_agent'])
                    task_data['status'] = TaskStatus(task_data['status'])
                    tasks[task_id] = AgentTask(**task_data)
                
                return tasks
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load agent tasks: {e}[/yellow]")
        
        return {}
    
    def _load_workflows(self) -> Dict[str, Any]:
        """Load workflow definitions."""
        if self.workflows_file.exists():
            try:
                with open(self.workflows_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load workflows: {e}[/yellow]")
        
        return {}
    
    def _save_agents(self):
        """Save agent data to storage."""
        try:
            data = {}
            for role, agent in self.agents.items():
                data[role.value] = asdict(agent)
                # Convert enum to string for JSON serialization
                data[role.value]['role'] = role.value
            
            with open(self.agents_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving agents: {e}[/red]")
    
    def _save_tasks(self):
        """Save tasks to storage."""
        try:
            data = {}
            for task_id, task in self.tasks.items():
                task_data = asdict(task)
                # Convert enums to strings for JSON serialization
                task_data['assigned_agent'] = task.assigned_agent.value
                task_data['status'] = task.status.value
                data[task_id] = task_data
            
            with open(self.tasks_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving tasks: {e}[/red]")
    
    def _save_workflows(self):
        """Save workflows to storage."""
        try:
            with open(self.workflows_file, 'w') as f:
                json.dump(self.workflows, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving workflows: {e}[/red]")
    
    async def create_task(self, title: str, description: str, agent_role: AgentRole,
                         priority: int = 3, dependencies: List[str] = None,
                         context: Dict[str, Any] = None) -> str:
        """Create a new task for an agent."""
        task_id = str(uuid.uuid4())
        
        task = AgentTask(
            id=task_id,
            title=title,
            description=description,
            assigned_agent=agent_role,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=datetime.now().isoformat(),
            dependencies=dependencies or [],
            context=context or {}
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        
        console.print(f"[blue]📋 Created task for {agent_role.value}: {title}[/blue]")
        
        self._save_tasks()
        return task_id
    
    async def assign_task(self, task_id: str) -> bool:
        """Assign a task to its designated agent."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        agent = self.agents[task.assigned_agent]
        
        # Check if agent is available
        if agent.current_task is not None:
            console.print(f"[yellow]⚠️ Agent {agent.name} is busy with task {agent.current_task}[/yellow]")
            return False
        
        # Check dependencies
        for dep_id in task.dependencies:
            if dep_id in self.tasks and self.tasks[dep_id].status != TaskStatus.COMPLETED:
                console.print(f"[yellow]⚠️ Task {task_id} waiting for dependency {dep_id}[/yellow]")
                return False
        
        # Assign task
        task.status = TaskStatus.ASSIGNED
        task.started_at = datetime.now().isoformat()
        agent.current_task = task_id
        
        console.print(f"[green]✅ Assigned task '{task.title}' to {agent.name}[/green]")
        
        # Start task execution
        asyncio.create_task(self._execute_task(task_id))
        
        self._save_tasks()
        self._save_agents()
        return True
    
    async def _execute_task(self, task_id: str):
        """Execute a task using the appropriate agent."""
        task = self.tasks[task_id]
        agent = self.agents[task.assigned_agent]
        
        try:
            task.status = TaskStatus.IN_PROGRESS
            console.print(f"[blue]🚀 {agent.name} starting task: {task.title}[/blue]")
            
            # Execute based on agent role
            result = await self._execute_agent_task(agent, task)
            
            if result.get("success", False):
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                task.outputs = result.get("outputs", {})
                
                # Update agent metrics
                agent.performance_metrics["tasks_completed"] += 1
                agent.task_history.append(task_id)
                
                console.print(f"[green]✅ {agent.name} completed task: {task.title}[/green]")
            else:
                task.status = TaskStatus.FAILED
                console.print(f"[red]❌ {agent.name} failed task: {task.title}[/red]")
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            console.print(f"[red]❌ Error executing task {task_id}: {e}[/red]")
        
        finally:
            # Release agent
            agent.current_task = None
            
            # Remove from queue if present
            if task_id in self.task_queue:
                self.task_queue.remove(task_id)
            
            self._save_tasks()
            self._save_agents()
    
    async def _execute_agent_task(self, agent: Agent, task: AgentTask) -> Dict[str, Any]:
        """Execute a task based on the agent's role."""
        try:
            if agent.role == AgentRole.CODER:
                return await self._execute_coder_task(task)
            elif agent.role == AgentRole.TESTER:
                return await self._execute_tester_task(task)
            elif agent.role == AgentRole.DOCUMENTER:
                return await self._execute_documenter_task(task)
            elif agent.role == AgentRole.REVIEWER:
                return await self._execute_reviewer_task(task)
            elif agent.role == AgentRole.DEPLOYER:
                return await self._execute_deployer_task(task)
            elif agent.role == AgentRole.MONITOR:
                return await self._execute_monitor_task(task)
            elif agent.role == AgentRole.COORDINATOR:
                return await self._execute_coordinator_task(task)
            else:
                return {"success": False, "error": f"Unknown agent role: {agent.role}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_coder_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a coding task."""
        # Simulate coding task execution
        await asyncio.sleep(2)  # Simulate work
        
        system_prompt = """You are Hurricane's coding specialist. You excel at:
- Writing clean, efficient code
- Debugging complex issues
- Refactoring for better maintainability
- Following best practices

Provide a detailed response for the given coding task."""
        
        try:
            response = await self.ollama_client.generate_response(
                system_prompt, 
                f"Task: {task.title}\nDescription: {task.description}",
                model=self.config.ollama.model
            )
            
            return {
                "success": True,
                "outputs": {
                    "code_response": response,
                    "task_type": "coding",
                    "completion_time": datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_tester_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a testing task."""
        await asyncio.sleep(1.5)
        
        system_prompt = """You are Hurricane's testing specialist. You excel at:
- Creating comprehensive test suites
- Identifying edge cases
- Performance testing
- Quality assurance

Provide a detailed testing strategy for the given task."""
        
        try:
            response = await self.ollama_client.generate_response(
                system_prompt,
                f"Task: {task.title}\nDescription: {task.description}",
                model=self.config.ollama.model
            )
            
            return {
                "success": True,
                "outputs": {
                    "test_strategy": response,
                    "task_type": "testing",
                    "completion_time": datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_documenter_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a documentation task."""
        await asyncio.sleep(1)
        
        system_prompt = """You are Hurricane's documentation specialist. You excel at:
- Creating clear, comprehensive documentation
- Writing user-friendly guides
- API documentation
- Code comments and docstrings

Provide detailed documentation for the given task."""
        
        try:
            response = await self.ollama_client.generate_response(
                system_prompt,
                f"Task: {task.title}\nDescription: {task.description}",
                model=self.config.ollama.model
            )
            
            return {
                "success": True,
                "outputs": {
                    "documentation": response,
                    "task_type": "documentation",
                    "completion_time": datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_reviewer_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a review task."""
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "outputs": {
                "review_result": f"Reviewed: {task.title}",
                "task_type": "review",
                "completion_time": datetime.now().isoformat()
            }
        }
    
    async def _execute_deployer_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a deployment task."""
        await asyncio.sleep(2)
        
        return {
            "success": True,
            "outputs": {
                "deployment_result": f"Deployed: {task.title}",
                "task_type": "deployment",
                "completion_time": datetime.now().isoformat()
            }
        }
    
    async def _execute_monitor_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a monitoring task."""
        await asyncio.sleep(0.5)
        
        return {
            "success": True,
            "outputs": {
                "monitoring_result": f"Monitored: {task.title}",
                "task_type": "monitoring",
                "completion_time": datetime.now().isoformat()
            }
        }
    
    async def _execute_coordinator_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a coordination task."""
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "outputs": {
                "coordination_result": f"Coordinated: {task.title}",
                "task_type": "coordination",
                "completion_time": datetime.now().isoformat()
            }
        }
    
    async def create_workflow(self, name: str, description: str, 
                            workflow_steps: List[Dict[str, Any]]) -> str:
        """Create a new workflow."""
        workflow_id = str(uuid.uuid4())
        
        workflow = {
            "id": workflow_id,
            "name": name,
            "description": description,
            "steps": workflow_steps,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.workflows[workflow_id] = workflow
        self._save_workflows()
        
        console.print(f"[blue]🔄 Created workflow: {name}[/blue]")
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a predefined workflow."""
        if workflow_id not in self.workflows:
            return {"success": False, "error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        console.print(f"[blue]🔄 Executing workflow: {workflow['name']}[/blue]")
        
        task_ids = []
        
        try:
            for step in workflow["steps"]:
                task_id = await self.create_task(
                    title=step["title"],
                    description=step["description"],
                    agent_role=AgentRole(step["agent"]),
                    priority=step.get("priority", 3),
                    dependencies=step.get("dependencies", []),
                    context=step.get("context", {})
                )
                task_ids.append(task_id)
            
            # Start task coordination
            await self._coordinate_workflow_tasks(task_ids)
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "task_ids": task_ids
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _coordinate_workflow_tasks(self, task_ids: List[str]):
        """Coordinate execution of workflow tasks."""
        while task_ids:
            # Find tasks that can be executed (no pending dependencies)
            ready_tasks = []
            
            for task_id in task_ids:
                task = self.tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    # Check if all dependencies are completed
                    deps_ready = all(
                        dep_id in self.tasks and self.tasks[dep_id].status == TaskStatus.COMPLETED
                        for dep_id in task.dependencies
                    )
                    
                    if deps_ready:
                        ready_tasks.append(task_id)
            
            # Assign ready tasks
            for task_id in ready_tasks:
                await self.assign_task(task_id)
                task_ids.remove(task_id)
            
            # Wait a bit before checking again
            await asyncio.sleep(1)
            
            # Check if any tasks failed
            failed_tasks = [
                task_id for task_id in list(task_ids)
                if task_id in self.tasks and self.tasks[task_id].status == TaskStatus.FAILED
            ]
            
            if failed_tasks:
                console.print(f"[red]❌ Workflow failed due to task failures: {failed_tasks}[/red]")
                break
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        status = {}
        
        for role, agent in self.agents.items():
            status[role.value] = {
                "name": agent.name,
                "is_active": agent.is_active,
                "current_task": agent.current_task,
                "tasks_completed": agent.performance_metrics["tasks_completed"],
                "success_rate": agent.performance_metrics["success_rate"]
            }
        
        return status
    
    def get_task_queue_status(self) -> List[Dict[str, Any]]:
        """Get status of task queue."""
        queue_status = []
        
        for task_id in self.task_queue:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                queue_status.append({
                    "id": task_id,
                    "title": task.title,
                    "agent": task.assigned_agent.value,
                    "status": task.status.value,
                    "priority": task.priority
                })
        
        return queue_status
    
    def show_multi_agent_status(self):
        """Display multi-agent system status."""
        console.print(Panel.fit(
            "[bold blue]🤖 Multi-Agent System Status[/bold blue]",
            border_style="blue"
        ))
        
        # Agents table
        agents_table = Table(title="🤖 Agents")
        agents_table.add_column("Agent", style="cyan")
        agents_table.add_column("Status", style="bold")
        agents_table.add_column("Current Task", style="yellow")
        agents_table.add_column("Completed", style="green")
        
        for role, agent in self.agents.items():
            status = "🟢 Active" if agent.is_active else "🔴 Inactive"
            current = agent.current_task[:20] + "..." if agent.current_task and len(agent.current_task) > 20 else (agent.current_task or "None")
            completed = str(agent.performance_metrics["tasks_completed"])
            
            agents_table.add_row(agent.name, status, current, completed)
        
        console.print(agents_table)
        
        # Task queue
        if self.task_queue:
            queue_table = Table(title="📋 Task Queue")
            queue_table.add_column("Task", style="cyan")
            queue_table.add_column("Agent", style="yellow")
            queue_table.add_column("Status", style="bold")
            queue_table.add_column("Priority", style="red")
            
            for task_id in self.task_queue[:10]:  # Show first 10
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    queue_table.add_row(
                        task.title[:30] + "..." if len(task.title) > 30 else task.title,
                        task.assigned_agent.value,
                        task.status.value,
                        str(task.priority)
                    )
            
            console.print(queue_table)
        
        # Recent completions
        recent_completed = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.COMPLETED
        ]
        recent_completed.sort(key=lambda t: t.completed_at or "", reverse=True)
        
        if recent_completed:
            console.print(f"\n[bold green]✅ Recent Completions ({len(recent_completed[:5])}):[/bold green]")
            for task in recent_completed[:5]:
                agent_name = self.agents[task.assigned_agent].name
                console.print(f"[dim]• {task.title} - {agent_name}[/dim]")

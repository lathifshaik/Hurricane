"""
Main Hurricane AI Agent class with enhanced agentic capabilities.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from .config import Config
from .ollama_client import OllamaClient
from ..modules.code_assistant import CodeAssistant
from ..modules.documentation import DocumentationGenerator
from ..modules.file_manager import FileManager
from ..modules.project_indexer import ProjectIndexer
from ..modules.git_assistant import GitAssistant
from ..modules.web_search import WebSearchAssistant
from ..modules.language_support import MultiLanguageSupport
from ..modules.codebase_analyzer import CodebaseAnalyzer
from ..modules.model_selector import ModelSelector
from ..modules.project_planner import ProjectPlanner
from ..modules.app_generator import AppGenerator

# New agentic modules
from ..modules.autonomous_planner import AutonomousPlanner, TaskPriority
from ..modules.enhanced_memory import EnhancedMemory
from ..modules.tool_integration import ToolIntegration
from ..modules.reactive_monitor import ReactiveMonitor
from ..modules.multi_agent_system import MultiAgentSystem, AgentRole

console = Console()


class HurricaneAgent:
    """Main Hurricane AI Agent class."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize Hurricane Agent with enhanced agentic capabilities."""
        self.config = Config.load_config(config_path)
        self.ollama_client = OllamaClient(self.config)
        
        # Set project root to current working directory
        self.project_root = Path.cwd()
        
        # Initialize core modules
        self.code_assistant = CodeAssistant(self.ollama_client, self.config)
        self.documentation_generator = DocumentationGenerator(self.ollama_client, self.config)
        self.file_manager = FileManager(self.config)
        self.project_indexer = ProjectIndexer(self.project_root)
        self.git_assistant = GitAssistant(self.ollama_client, self.config, self.project_root)
        self.web_search = WebSearchAssistant(self.ollama_client, self.config)
        self.language_support = MultiLanguageSupport()
        self.codebase_analyzer = CodebaseAnalyzer(self.ollama_client, self.config, self.project_root)
        self.model_selector = ModelSelector(self.ollama_client, self.config)
        self.project_planner = ProjectPlanner(self.ollama_client, self.config, self.project_root)
        self.app_generator = AppGenerator(self.ollama_client, self.config, self.project_root)
        
        # Initialize new agentic modules
        self.autonomous_planner = AutonomousPlanner(self.ollama_client, self.config, self.project_root)
        self.enhanced_memory = EnhancedMemory(self.ollama_client, self.config, self.project_root)
        self.tool_integration = ToolIntegration(self.ollama_client, self.config, self.project_root)
        self.reactive_monitor = ReactiveMonitor(self.ollama_client, self.config, self.project_root)
        self.multi_agent_system = MultiAgentSystem(self.ollama_client, self.config, self.project_root)
        
        self._initialized = False
        self._agentic_mode = False
    
    async def initialize(self) -> bool:
        """Initialize the agent and check dependencies."""
        if self._initialized:
            return True
        
        console.print(Panel.fit(
            Text("🌪️ Hurricane AI Agent", style="bold blue"),
            title="Initializing",
            border_style="blue"
        ))
        
        # Check if Ollama is running
        try:
            models = self.ollama_client.list_models()
            if not models:
                console.print("[yellow]No models found. You may need to pull a model first.[/yellow]")
                console.print("Try: [bold]ollama pull codellama[/bold]")
            else:
                console.print(f"[green]✅ Found {len(models)} available models[/green]")
        except Exception as e:
            console.print(f"[red]❌ Cannot connect to Ollama: {e}[/red]")
            console.print("Make sure Ollama is running: [bold]ollama serve[/bold]")
            return False
        
        # Check if default model is available
        if not self.ollama_client.check_model_availability(self.config.ollama.model):
            console.print(f"[yellow]Model '{self.config.ollama.model}' not found.[/yellow]")
            console.print(f"Pulling model: [bold]{self.config.ollama.model}[/bold]")
            if not self.ollama_client.pull_model(self.config.ollama.model):
                return False
        
        self._initialized = True
        console.print("[green]✅ Hurricane initialized successfully![/green]")
        return True
    
    async def generate_code(
        self, 
        description: str, 
        language: str = "python",
        context: Optional[str] = None,
        save_to_file: Optional[Path] = None
    ) -> str:
        """Generate code using the code assistant."""
        if not await self.initialize():
            raise RuntimeError("Failed to initialize Hurricane")
        
        console.print(f"[blue]🔧 Generating {language} code...[/blue]")
        
        code = await self.code_assistant.generate_code(description, language, context)
        
        if save_to_file and self.config.preferences.auto_save:
            await self.file_manager.save_file(save_to_file, code)
            console.print(f"[green]💾 Code saved to {save_to_file}[/green]")
        
        return code
    
    async def debug_code(
        self, 
        code: str, 
        error: Optional[str] = None,
        file_path: Optional[Path] = None
    ) -> str:
        """Debug code and provide fixes."""
        if not await self.initialize():
            raise RuntimeError("Failed to initialize Hurricane")
        
        console.print("[blue]🐛 Debugging code...[/blue]")
        
        if file_path and file_path.exists():
            code = await self.file_manager.read_file(file_path)
        
        debug_result = await self.code_assistant.debug_code(code, error)
        
        return debug_result
    
    async def refactor_code(
        self, 
        code: str, 
        style: str = "clean",
        file_path: Optional[Path] = None
    ) -> str:
        """Refactor code according to specified style."""
        if not await self.initialize():
            raise RuntimeError("Failed to initialize Hurricane")
        
        console.print(f"[blue]♻️ Refactoring code with '{style}' style...[/blue]")
        
        if file_path and file_path.exists():
            code = await self.file_manager.read_file(file_path)
        
        refactored_code = await self.code_assistant.refactor_code(code, style)
        
        return refactored_code
    
    async def generate_documentation(
        self, 
        target: str,
        doc_type: str = "readme",
        format_type: str = "markdown",
        save_to_file: Optional[Path] = None
    ) -> str:
        """Generate documentation."""
        if not await self.initialize():
            raise RuntimeError("Failed to initialize Hurricane")
        
        console.print(f"[blue]📝 Generating {doc_type} documentation...[/blue]")
        
        # If target is a file path, read the file
        if Path(target).exists():
            target = await self.file_manager.read_file(Path(target))
        
        documentation = await self.documentation_generator.generate_documentation(
            target, doc_type, format_type
        )
        
        if save_to_file and self.config.preferences.auto_save:
            await self.file_manager.save_file(save_to_file, documentation)
            console.print(f"[green]💾 Documentation saved to {save_to_file}[/green]")
        
        return documentation
    
    async def create_project_structure(
        self, 
        project_type: str,
        project_name: str,
        base_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Create a project structure."""
        if not await self.initialize():
            raise RuntimeError("Failed to initialize Hurricane")
        
        console.print(f"[blue]🏗️ Creating {project_type} project structure...[/blue]")
        
        result = await self.file_manager.create_project_structure(
            project_type, project_name, base_path
        )
        
        console.print(f"[green]✅ Project '{project_name}' created successfully![/green]")
        
        return result
    
    async def organize_files(self, directory: Path, strategy: str = "by_type") -> Dict[str, Any]:
        """Organize files in a directory."""
        if not await self.initialize():
            raise RuntimeError("Failed to initialize Hurricane")
        
        console.print(f"[blue]🗂️ Organizing files using '{strategy}' strategy...[/blue]")
        
        result = await self.file_manager.organize_files(directory, strategy)
        
        console.print("[green]✅ Files organized successfully![/green]")
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get Hurricane status information."""
        return {
            "initialized": self._initialized,
            "config": {
                "ollama_host": self.config.ollama.host,
                "model": self.config.ollama.model,
                "code_style": self.config.preferences.code_style,
                "documentation_format": self.config.preferences.documentation_format,
            },
            "available_models": self.ollama_client.list_models() if self._initialized else [],
        }
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration."""
        self.config.update_config(updates)
        self.config.save_config()
        console.print("[green]✅ Configuration updated![/green]")
    
    # New agentic methods
    async def enable_agentic_mode(self) -> bool:
        """Enable autonomous agentic behavior."""
        if not await self.initialize():
            return False
        
        console.print("[bold blue]🤖 Enabling Agentic Mode...[/bold blue]")
        
        # Start reactive monitoring
        self.reactive_monitor.start_monitoring()
        
        # Initialize multi-agent system
        console.print("[blue]🤖 Multi-agent system ready[/blue]")
        
        self._agentic_mode = True
        console.print("[bold green]✅ Hurricane is now operating in full agentic mode![/bold green]")
        console.print("[dim]The agent will now autonomously monitor, plan, and execute tasks.[/dim]")
        
        return True
    
    async def disable_agentic_mode(self):
        """Disable autonomous agentic behavior."""
        console.print("[blue]🛑 Disabling Agentic Mode...[/blue]")
        
        # Stop reactive monitoring
        self.reactive_monitor.stop_monitoring()
        
        self._agentic_mode = False
        console.print("[green]✅ Agentic mode disabled[/green]")
    
    async def set_autonomous_goal(self, goal_description: str, priority: str = "medium") -> str:
        """Set a high-level goal for autonomous pursuit."""
        if not self._agentic_mode:
            console.print("[yellow]⚠️ Agentic mode not enabled. Use 'enable_agentic_mode()' first.[/yellow]")
            return ""
        
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL
        }
        
        goal_id = await self.autonomous_planner.set_goal(
            title=f"Autonomous Goal: {goal_description[:50]}...",
            description=goal_description,
            target_outcome="Goal successfully achieved with measurable results",
            priority=priority_map.get(priority, TaskPriority.MEDIUM)
        )
        
        # Record the interaction in memory
        await self.enhanced_memory.record_interaction(
            user_input=f"Set autonomous goal: {goal_description}",
            agent_response=f"Goal set with ID: {goal_id}",
            context={"goal_id": goal_id, "priority": priority}
        )
        
        return goal_id
    
    async def process_with_memory(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Process user input with enhanced memory and context awareness."""
        # Retrieve relevant context from memory
        relevant_context = self.enhanced_memory.retrieve_relevant_context(user_input)
        
        # Get user preferences
        user_preferences = self.enhanced_memory.get_user_preferences()
        
        # Enhanced context for AI processing
        enhanced_context = {
            "user_input": user_input,
            "relevant_history": relevant_context,
            "user_preferences": user_preferences,
            "project_root": str(self.project_root),
            "agentic_mode": self._agentic_mode
        }
        
        if context:
            enhanced_context.update(context)
        
        # Process with AI
        system_prompt = f"""You are Hurricane, an advanced agentic AI coding assistant. You have access to:
        
- Conversation history and context
- User preferences and patterns: {user_preferences}
- Project context and structure
- Autonomous planning capabilities
- Multi-agent coordination
- Tool integration
- Reactive monitoring

Use this context to provide intelligent, personalized responses. If in agentic mode, consider autonomous actions."""
        
        response = await self.ollama_client.generate_response(
            system_prompt, 
            f"Context: {enhanced_context}\n\nUser: {user_input}",
            model=self.config.ollama.model
        )
        
        # Record interaction in memory
        await self.enhanced_memory.record_interaction(
            user_input=user_input,
            agent_response=response,
            context=enhanced_context
        )
        
        return response
    
    async def execute_autonomous_task(self) -> Dict[str, Any]:
        """Execute the next available autonomous task."""
        if not self._agentic_mode:
            return {"error": "Agentic mode not enabled"}
        
        # Get next autonomous task
        next_task = self.autonomous_planner.get_next_autonomous_task()
        
        if not next_task:
            return {"message": "No autonomous tasks available"}
        
        # Execute the task
        result = await self.autonomous_planner.execute_autonomous_task(next_task.id)
        
        return result
    
    async def run_tool_command(self, tool_name: str, command_args: Dict[str, Any]) -> Dict[str, Any]:
        """Run a tool command through the tool integration system."""
        if not self.tool_integration.is_tool_available(tool_name):
            return {"error": f"Tool {tool_name} not available"}
        
        # Map tool commands to methods
        tool_methods = {
            "git_status": self.tool_integration.git_status,
            "git_commit": lambda: self.tool_integration.git_commit(command_args.get("message", "Auto commit")),
            "run_tests": self.tool_integration.run_tests,
            "format_code": self.tool_integration.format_code,
            "lint_code": self.tool_integration.lint_code,
            "install_package": lambda: self.tool_integration.install_package(command_args.get("package")),
            "execute_python": lambda: self.tool_integration.execute_python_file(command_args.get("file_path"))
        }
        
        if tool_name in tool_methods:
            try:
                result = await tool_methods[tool_name]()
                return {"success": True, "result": result}
            except Exception as e:
                return {"error": str(e)}
        else:
            return {"error": f"Unknown tool command: {tool_name}"}
    
    async def create_multi_agent_workflow(self, workflow_name: str, workflow_description: str, 
                                        tasks: List[Dict[str, Any]]) -> str:
        """Create a multi-agent workflow."""
        workflow_id = await self.multi_agent_system.create_workflow(
            name=workflow_name,
            description=workflow_description,
            workflow_steps=tasks
        )
        
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a multi-agent workflow."""
        return await self.multi_agent_system.execute_workflow(workflow_id)
    
    def get_agentic_status(self) -> Dict[str, Any]:
        """Get comprehensive agentic system status."""
        return {
            "agentic_mode": self._agentic_mode,
            "initialized": self._initialized,
            "autonomous_goals": len(self.autonomous_planner.get_active_goals()),
            "proactive_suggestions": len(self.autonomous_planner.get_proactive_suggestions()),
            "memory_interactions": len(self.enhanced_memory.conversation_history),
            "available_tools": sum(1 for available in self.tool_integration.get_available_tools().values() if available),
            "monitoring_active": self.reactive_monitor.is_monitoring,
            "unacknowledged_notifications": len(self.reactive_monitor.get_unacknowledged_notifications()),
            "active_agents": sum(1 for agent in self.multi_agent_system.agents.values() if agent.is_active),
            "queued_tasks": len(self.multi_agent_system.task_queue)
        }
    
    def show_agentic_dashboard(self):
        """Display comprehensive agentic system dashboard."""
        console.print(Panel.fit(
            "[bold blue]🌪️ Hurricane Agentic AI Agent Dashboard[/bold blue]",
            title="🤖 Agentic Mode",
            border_style="blue"
        ))
        
        # Main status
        status = self.get_agentic_status()
        
        main_table = Table(title="📊 System Status")
        main_table.add_column("Component", style="cyan")
        main_table.add_column("Status", style="bold")
        main_table.add_column("Details", style="dim")
        
        main_table.add_row(
            "Agentic Mode", 
            "🟢 Active" if status["agentic_mode"] else "🔴 Inactive",
            "Autonomous behavior enabled" if status["agentic_mode"] else "Manual mode"
        )
        main_table.add_row(
            "Autonomous Goals", 
            str(status["autonomous_goals"]),
            "Active high-level objectives"
        )
        main_table.add_row(
            "Memory System", 
            f"{status['memory_interactions']} interactions",
            "Conversation history and learning"
        )
        main_table.add_row(
            "Tool Integration", 
            f"{status['available_tools']} tools",
            "External tool availability"
        )
        main_table.add_row(
            "Reactive Monitor", 
            "🟢 Active" if status["monitoring_active"] else "🔴 Inactive",
            f"{status['unacknowledged_notifications']} notifications"
        )
        main_table.add_row(
            "Multi-Agent System", 
            f"{status['active_agents']} agents",
            f"{status['queued_tasks']} queued tasks"
        )
        
        console.print(main_table)
        
        # Show individual system statuses
        if status["agentic_mode"]:
            console.print("\n[bold cyan]📋 Detailed Status:[/bold cyan]")
            
            # Autonomous planner status
            self.autonomous_planner.show_autonomous_status()
            
            # Memory status
            self.enhanced_memory.show_memory_status()
            
            # Tool status
            self.tool_integration.show_tool_status()
            
            # Monitoring status
            self.reactive_monitor.show_monitoring_status()
            
            # Multi-agent status
            self.multi_agent_system.show_multi_agent_status()

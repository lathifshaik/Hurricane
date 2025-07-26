"""
Main Hurricane AI Agent class.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

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

console = Console()


class HurricaneAgent:
    """Main Hurricane AI Agent class."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize Hurricane Agent."""
        self.config = Config.load_config(config_path)
        self.ollama_client = OllamaClient(self.config)
        
        # Set project root to current working directory
        self.project_root = Path.cwd()
        
        # Initialize modules
        self.code_assistant = CodeAssistant(self.ollama_client, self.config)
        self.documentation_generator = DocumentationGenerator(self.ollama_client, self.config)
        self.file_manager = FileManager(self.config)
        self.project_indexer = ProjectIndexer(self.project_root)
        self.git_assistant = GitAssistant(self.ollama_client, self.config, self.project_root)
        self.web_search = WebSearchAssistant(self.ollama_client, self.config)
        self.language_support = MultiLanguageSupport()
        self.codebase_analyzer = CodebaseAnalyzer(self.ollama_client, self.config, self.project_root)
        self.model_selector = ModelSelector(self.ollama_client, self.config)
        
        self._initialized = False
    
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

"""
Enhanced model selector with dropdown UI for Hurricane AI Agent.
Provides beautiful interactive model selection, installation, and management.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.tree import Tree
from rich.align import Align
from rich.columns import Columns
from rich.text import Text

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


@dataclass
class ModelInfo:
    """Information about an AI model."""
    name: str
    display_name: str
    description: str
    size: str
    use_cases: List[str]
    performance_rating: float
    recommended: bool = False
    installed: bool = False
    download_url: str = ""


class ModelSelector:
    """Enhanced model selector with beautiful dropdown UI."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config):
        self.ollama_client = ollama_client
        self.config = config
        
        # Curated list of recommended models with detailed information
        self.recommended_models = [
            ModelInfo(
                name="qwen2.5-coder:7b",
                display_name="🚀 Qwen2.5-Coder 7B",
                description="Excellent for coding tasks, fast and efficient. Great all-around coding model.",
                size="4.2GB",
                use_cases=["Code generation", "Debugging", "Refactoring", "Code completion"],
                performance_rating=4.8,
                recommended=True
            ),
            ModelInfo(
                name="deepseek-coder:6.7b",
                display_name="💎 DeepSeek Coder 6.7B",
                description="Specialized for code generation and understanding. Excellent for complex coding tasks.",
                size="3.8GB",
                use_cases=["Code generation", "Documentation", "Code review", "Architecture design"],
                performance_rating=4.7,
                recommended=True
            ),
            ModelInfo(
                name="codellama:7b",
                display_name="🦙 CodeLlama 7B",
                description="Meta's coding model, great all-rounder for various programming tasks.",
                size="3.8GB",
                use_cases=["Code completion", "Debugging", "Explanations", "General coding"],
                performance_rating=4.5
            ),
            ModelInfo(
                name="codegemma:7b",
                display_name="💎 CodeGemma 7B",
                description="Google's coding model with excellent performance for complex tasks.",
                size="5.0GB",
                use_cases=["Complex coding tasks", "Architecture design", "Code optimization"],
                performance_rating=4.6
            ),
            ModelInfo(
                name="mistral:7b",
                display_name="⚡ Mistral 7B",
                description="Fast and versatile, good for general programming and documentation tasks.",
                size="4.1GB",
                use_cases=["General coding", "Documentation", "Quick fixes", "Explanations"],
                performance_rating=4.3
            ),
            ModelInfo(
                name="llama3.1:8b",
                display_name="🦙 Llama 3.1 8B",
                description="Latest Llama model with improved reasoning and coding capabilities.",
                size="4.7GB",
                use_cases=["Advanced reasoning", "Code generation", "Problem solving"],
                performance_rating=4.4
            ),
            ModelInfo(
                name="phi3:mini",
                display_name="🔬 Phi-3 Mini",
                description="Microsoft's compact model, great for quick tasks and resource-constrained environments.",
                size="2.3GB",
                use_cases=["Quick coding tasks", "Code completion", "Lightweight operations"],
                performance_rating=4.0
            ),
            ModelInfo(
                name="starcoder2:7b",
                display_name="⭐ StarCoder2 7B",
                description="Specialized code generation model with support for many programming languages.",
                size="4.0GB",
                use_cases=["Multi-language coding", "Code translation", "API generation"],
                performance_rating=4.2
            )
        ]
    
    async def show_interactive_selector(self) -> Optional[str]:
        """Show beautiful interactive model selector with dropdown-style UI."""
        console.print(Panel.fit(
            "[bold blue]🤖 AI Model Selection[/bold blue]\n"
            "Choose the perfect AI model for your coding needs",
            border_style="blue"
        ))
        
        # Check which models are already installed
        installed_models = self.ollama_client.list_models()
        for model in self.recommended_models:
            model.installed = any(model.name in installed for installed in installed_models)
        
        # Show current model
        current_model = self.config.ollama.model
        console.print(f"[dim]Current model: [bold]{current_model}[/bold][/dim]\n")
        
        while True:
            # Display model selection menu
            selected_model = await self._show_model_menu()
            
            if selected_model is None:
                return None
            
            if selected_model == "refresh":
                # Refresh installed models list
                installed_models = self.ollama_client.list_models()
                for model in self.recommended_models:
                    model.installed = any(model.name in installed for installed in installed_models)
                continue
            
            if selected_model == "custom":
                return await self._handle_custom_model()
            
            # Handle selected model
            model_info = next((m for m in self.recommended_models if m.name == selected_model), None)
            if model_info:
                return await self._handle_model_selection(model_info)
    
    async def _show_model_menu(self) -> Optional[str]:
        """Show the main model selection menu."""
        # Create beautiful model display
        self._display_model_grid()
        
        # Create choices list
        choices = []
        choice_map = {}
        
        for i, model in enumerate(self.recommended_models, 1):
            choice_key = str(i)
            choices.append(choice_key)
            choice_map[choice_key] = model.name
            
            status = "✅ Installed" if model.installed else "📥 Available"
            recommended = " ⭐" if model.recommended else ""
            console.print(f"  [bold cyan]{i}.[/bold cyan] {model.display_name}{recommended} - {status}")
        
        # Add special options
        choices.extend(["r", "c", "q"])
        console.print(f"\n  [bold yellow]r.[/bold yellow] 🔄 Refresh installed models")
        console.print(f"  [bold yellow]c.[/bold yellow] 🛠️ Enter custom model name")
        console.print(f"  [bold yellow]q.[/bold yellow] ❌ Quit")
        
        # Get user choice
        choice = Prompt.ask(
            "\n[bold green]Select a model[/bold green]",
            choices=choices,
            default="1"
        )
        
        if choice == "q":
            return None
        elif choice == "r":
            return "refresh"
        elif choice == "c":
            return "custom"
        else:
            return choice_map.get(choice)
    
    def _display_model_grid(self) -> None:
        """Display models in a beautiful grid layout."""
        # Group models by category
        recommended = [m for m in self.recommended_models if m.recommended]
        others = [m for m in self.recommended_models if not m.recommended]
        
        if recommended:
            console.print("[bold green]⭐ Recommended Models:[/bold green]")
            self._display_model_table(recommended)
        
        if others:
            console.print("\n[bold blue]📦 Other Available Models:[/bold blue]")
            self._display_model_table(others)
    
    def _display_model_table(self, models: List[ModelInfo]) -> None:
        """Display models in a table format."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Model", style="cyan", width=25)
        table.add_column("Description", style="white", width=40)
        table.add_column("Size", style="yellow", width=8)
        table.add_column("Use Cases", style="green", width=25)
        table.add_column("Status", style="bold", width=12)
        
        for model in models:
            status = "[green]✅ Installed[/green]" if model.installed else "[blue]📥 Available[/blue]"
            use_cases = ", ".join(model.use_cases[:2])  # Show first 2 use cases
            if len(model.use_cases) > 2:
                use_cases += "..."
            
            table.add_row(
                model.display_name,
                model.description,
                model.size,
                use_cases,
                status
            )
        
        console.print(table)
    
    async def _handle_custom_model(self) -> Optional[str]:
        """Handle custom model input."""
        console.print("\n[bold blue]🛠️ Custom Model Setup[/bold blue]")
        
        model_name = Prompt.ask("Enter model name (e.g., 'llama2:13b', 'mistral:latest')")
        
        if not model_name:
            return None
        
        # Check if model exists in Ollama registry
        console.print(f"[blue]🔍 Checking if model '{model_name}' exists...[/blue]")
        
        if Confirm.ask(f"Download and install '{model_name}'?"):
            success = await self._download_model(model_name)
            if success:
                return model_name
        
        return None
    
    async def _handle_model_selection(self, model_info: ModelInfo) -> Optional[str]:
        """Handle selection of a specific model."""
        console.print(f"\n[bold blue]📋 Model Details: {model_info.display_name}[/bold blue]")
        
        # Show detailed information
        details_panel = Panel(
            f"[bold]Description:[/bold] {model_info.description}\n\n"
            f"[bold]Size:[/bold] {model_info.size}\n"
            f"[bold]Performance Rating:[/bold] {model_info.performance_rating}/5.0 ⭐\n\n"
            f"[bold]Best for:[/bold]\n" + "\n".join(f"  • {use_case}" for use_case in model_info.use_cases),
            title=f"📊 {model_info.display_name}",
            border_style="cyan"
        )
        console.print(details_panel)
        
        if model_info.installed:
            if Confirm.ask(f"Use '{model_info.name}' as your default model?"):
                self._update_config_model(model_info.name)
                return model_info.name
        else:
            console.print(f"\n[yellow]📥 Model '{model_info.name}' is not installed[/yellow]")
            if Confirm.ask(f"Download and install '{model_info.name}' ({model_info.size})?"):
                success = await self._download_model(model_info.name)
                if success:
                    self._update_config_model(model_info.name)
                    return model_info.name
        
        return None
    
    async def _download_model(self, model_name: str) -> bool:
        """Download and install a model with progress tracking."""
        console.print(f"[bold blue]📥 Downloading {model_name}...[/bold blue]")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                
                download_task = progress.add_task(f"Downloading {model_name}...", total=100)
                
                # Use Ollama client to pull the model
                success = self.ollama_client.pull_model(model_name)
                
                if success:
                    progress.update(download_task, completed=100)
                    console.print(f"[green]✅ Successfully downloaded {model_name}![/green]")
                    
                    # Show success message with tips
                    self._show_success_message(model_name)
                    return True
                else:
                    console.print(f"[red]❌ Failed to download {model_name}[/red]")
                    return False
                    
        except Exception as e:
            console.print(f"[red]❌ Error downloading model: {e}[/red]")
            return False
    
    def _update_config_model(self, model_name: str) -> None:
        """Update the configuration with the new default model."""
        self.config.ollama.model = model_name
        self.config.save_config()
        console.print(f"[green]✅ Updated default model to '{model_name}'[/green]")
    
    def _show_success_message(self, model_name: str) -> None:
        """Show success message with helpful tips."""
        tips = [
            f"🎉 {model_name} is now ready to use!",
            "💡 You can start coding with Hurricane immediately",
            "🚀 Try: 'Generate a Python function to sort a list'",
            "🔧 Use 'hurricane status' to see your current setup"
        ]
        
        success_panel = Panel(
            "\n".join(tips),
            title="🎊 Installation Complete!",
            border_style="green"
        )
        console.print(success_panel)
    
    async def show_installed_models(self) -> None:
        """Show all installed models with management options."""
        console.print("[bold blue]📦 Installed Models[/bold blue]")
        
        installed_models = self.ollama_client.list_models()
        
        if not installed_models:
            console.print("[yellow]No models installed yet.[/yellow]")
            if Confirm.ask("Would you like to install a recommended model?"):
                await self.show_interactive_selector()
            return
        
        # Create table of installed models
        table = Table(title="Installed AI Models")
        table.add_column("Model", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Actions", style="yellow")
        
        current_model = self.config.ollama.model
        
        for model in installed_models:
            status = "✅ Current" if model == current_model else "📦 Available"
            actions = "Set as default, Remove" if model != current_model else "Remove"
            table.add_row(model, status, actions)
        
        console.print(table)
        
        # Model management options
        if len(installed_models) > 1:
            console.print("\n[bold green]Model Management:[/bold green]")
            console.print("1. Switch default model")
            console.print("2. Remove unused models")
            console.print("3. Install new model")
            console.print("4. Back to main menu")
            
            choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"], default="4")
            
            if choice == "1":
                await self._switch_default_model(installed_models)
            elif choice == "2":
                await self._remove_models(installed_models)
            elif choice == "3":
                await self.show_interactive_selector()
    
    async def _switch_default_model(self, installed_models: List[str]) -> None:
        """Switch the default model."""
        console.print("\n[bold blue]🔄 Switch Default Model[/bold blue]")
        
        choices = {str(i): model for i, model in enumerate(installed_models, 1)}
        
        for i, model in enumerate(installed_models, 1):
            current = " (current)" if model == self.config.ollama.model else ""
            console.print(f"  {i}. {model}{current}")
        
        choice = Prompt.ask("Select new default model", choices=list(choices.keys()))
        new_model = choices[choice]
        
        if new_model != self.config.ollama.model:
            self._update_config_model(new_model)
        else:
            console.print("[yellow]That's already your default model![/yellow]")
    
    async def _remove_models(self, installed_models: List[str]) -> None:
        """Remove unused models."""
        console.print("\n[bold red]🗑️ Remove Models[/bold red]")
        console.print("[yellow]⚠️ This will permanently delete the selected models[/yellow]")
        
        removable_models = [m for m in installed_models if m != self.config.ollama.model]
        
        if not removable_models:
            console.print("[yellow]No models available for removal (can't remove current default)[/yellow]")
            return
        
        for i, model in enumerate(removable_models, 1):
            console.print(f"  {i}. {model}")
        
        if Confirm.ask("Remove unused models?"):
            # This would integrate with Ollama's remove functionality
            console.print("[blue]Model removal feature coming soon![/blue]")
    
    def get_model_recommendations(self, use_case: str) -> List[ModelInfo]:
        """Get model recommendations based on use case."""
        use_case_lower = use_case.lower()
        
        recommendations = []
        for model in self.recommended_models:
            if any(use_case_lower in uc.lower() for uc in model.use_cases):
                recommendations.append(model)
        
        # Sort by performance rating
        recommendations.sort(key=lambda x: x.performance_rating, reverse=True)
        
        return recommendations[:3]  # Top 3 recommendations

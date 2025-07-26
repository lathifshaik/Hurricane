"""
Command Line Interface for Hurricane AI Agent.
"""

import asyncio
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align
from rich.columns import Columns
import time

from .core.agent import HurricaneAgent
from .core.config import Config

console = Console()

# ASCII Art for Hurricane
HURRICANE_ART = """
    🌪️  ██╗  ██╗██╗   ██╗██████╗ ██████╗ ██╗ ██████╗ █████╗ ███╗   ██╗███████╗
        ██║  ██║██║   ██║██╔══██╗██╔══██╗██║██╔════╝██╔══██╗████╗  ██║██╔════╝
        ███████║██║   ██║██████╔╝██████╔╝██║██║     ███████║██╔██╗ ██║█████╗  
        ██╔══██║██║   ██║██╔══██╗██╔══██╗██║██║     ██╔══██║██║╚██╗██║██╔══╝  
        ██║  ██║╚██████╔╝██║  ██║██║  ██║██║╚██████╗██║  ██║██║ ╚████║███████╗
        ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝
                            Your AI Coding Assistant Powered by Ollama
"""

# Recommended models with descriptions
RECOMMENDED_MODELS = {
    "qwen2.5-coder:7b": {
        "description": "🚀 Qwen2.5-Coder - Excellent for coding tasks, fast and efficient",
        "size": "4.2GB",
        "best_for": "General coding, debugging, refactoring"
    },
    "deepseek-coder:6.7b": {
        "description": "💎 DeepSeek Coder - Specialized for code generation and understanding",
        "size": "3.8GB",
        "best_for": "Code generation, documentation, code review"
    },
    "codellama:7b": {
        "description": "🦙 CodeLlama - Meta's coding model, great all-rounder",
        "size": "3.8GB",
        "best_for": "Code completion, debugging, explanations"
    },
    "codegemma:7b": {
        "description": "💎 CodeGemma - Google's coding model, excellent performance",
        "size": "5.0GB",
        "best_for": "Complex coding tasks, architecture design"
    },
    "mistral:7b": {
        "description": "⚡ Mistral - Fast and versatile, good for general tasks",
        "size": "4.1GB",
        "best_for": "General coding, documentation, quick fixes"
    }
}

def show_welcome_screen():
    """Display the fancy Hurricane welcome screen."""
    console.clear()
    
    # Show ASCII art
    console.print(Align.center(Text(HURRICANE_ART, style="bold cyan")))
    console.print()
    
    # Welcome message
    welcome_panel = Panel.fit(
        Text("Welcome to Hurricane! 🌪️\n\nYour intelligent AI coding assistant that speaks plain English.\nJust tell me what you want to do, and I'll handle the rest!", 
             style="bold green", justify="center"),
        title="🎉 Welcome",
        border_style="green",
        padding=(1, 2)
    )
    console.print(Align.center(welcome_panel))
    console.print()

def show_model_recommendations():
    """Show recommended models in a beautiful table."""
    table = Table(title="🤖 Recommended AI Models for Coding", show_header=True, header_style="bold magenta")
    table.add_column("Model", style="cyan", width=20)
    table.add_column("Description", style="white", width=50)
    table.add_column("Size", style="yellow", width=10)
    table.add_column("Best For", style="green", width=30)
    
    for model, info in RECOMMENDED_MODELS.items():
        table.add_row(
            model,
            info["description"],
            info["size"],
            info["best_for"]
        )
    
    console.print(table)
    console.print()

async def interactive_model_setup(agent: HurricaneAgent):
    """Interactive model setup with recommendations."""
    console.print("[bold blue]🔍 Checking available models...[/bold blue]")
    
    available_models = agent.ollama_client.list_models()
    
    if not available_models:
        console.print("[yellow]📥 No models found! Let's download one.[/yellow]\n")
        show_model_recommendations()
        
        console.print("[bold cyan]💡 Recommendation: Start with 'qwen2.5-coder:7b' - it's fast and great for coding![/bold cyan]\n")
        
        model_choice = Prompt.ask(
            "Which model would you like to download?",
            choices=list(RECOMMENDED_MODELS.keys()) + ["custom"],
            default="qwen2.5-coder:7b"
        )
        
        if model_choice == "custom":
            model_choice = Prompt.ask("Enter custom model name")
        
        console.print(f"\n[blue]📥 Downloading {model_choice}... This might take a few minutes.[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Downloading {model_choice}...", total=None)
            success = agent.ollama_client.pull_model(model_choice)
            
            if success:
                progress.update(task, description=f"✅ {model_choice} downloaded successfully!")
                agent.config.ollama.model = model_choice
                agent.config.save_config()
            else:
                progress.update(task, description=f"❌ Failed to download {model_choice}")
                return False
    else:
        console.print(f"[green]✅ Found {len(available_models)} available models:[/green]")
        for model in available_models:
            console.print(f"  • {model}")
        
        current_model = agent.config.ollama.model
        if current_model not in available_models:
            console.print(f"\n[yellow]⚠️ Current model '{current_model}' not found.[/yellow]")
            model_choice = Prompt.ask(
                "Which model would you like to use?",
                choices=available_models,
                default=available_models[0]
            )
            agent.config.ollama.model = model_choice
            agent.config.save_config()
        else:
            console.print(f"\n[green]✅ Using model: {current_model}[/green]")
    
    return True

def show_file_changes(changes: dict):
    """Show what files were changed in a beautiful format."""
    if not changes:
        console.print("[yellow]ℹ️ No files were modified.[/yellow]")
        return
    
    console.print("\n[bold green]📝 Files Modified:[/bold green]")
    
    for file_path, change_info in changes.items():
        panel_content = f"""[bold cyan]File:[/bold cyan] {file_path}
[bold yellow]Changes:[/bold yellow] {change_info.get('description', 'Modified')}
[bold green]Status:[/bold green] ✅ Updated successfully"""
        
        console.print(Panel(
            panel_content,
            title=f"📄 {Path(file_path).name}",
            border_style="green",
            padding=(0, 1)
        ))

def show_help_examples():
    """Show examples of what Hurricane can do."""
    examples = [
        "🔧 'Fix the bug in main.py'",
        "📝 'Create a README for my project'",
        "🚀 'Generate a FastAPI server with user authentication'",
        "🐛 'Debug the error in my Python code'",
        "📚 'Add comments to my functions'",
        "🏗️ 'Create a new React component for login'",
        "♻️ 'Refactor this code to be cleaner'",
        "📖 'Explain what this code does'",
        "🧪 'Generate unit tests for my functions'",
        "📁 'Organize my project files'"
    ]
    
    console.print("\n[bold green]💡 Here's what I can help you with:[/bold green]")
    
    for example in examples:
        console.print(f"  {example}")
    
    console.print("\n[dim]Just describe what you want in plain English![/dim]\n")

async def process_natural_language_request(agent: HurricaneAgent, user_input: str):
    """Process natural language requests and determine what action to take."""
    user_input_lower = user_input.lower()
    
    try:
        # Determine intent based on keywords
        if any(word in user_input_lower for word in ['fix', 'bug', 'error', 'debug', 'broken']):
            await handle_debug_request(agent, user_input)
        elif any(word in user_input_lower for word in ['create', 'generate', 'make', 'build', 'write']):
            await handle_create_request(agent, user_input)
        elif any(word in user_input_lower for word in ['readme', 'documentation', 'docs', 'comment']):
            await handle_documentation_request(agent, user_input)
        elif any(word in user_input_lower for word in ['refactor', 'clean', 'improve', 'optimize']):
            await handle_refactor_request(agent, user_input)
        elif any(word in user_input_lower for word in ['explain', 'what does', 'how does', 'understand']):
            await handle_explain_request(agent, user_input)
        elif any(word in user_input_lower for word in ['test', 'unit test', 'testing']):
            await handle_test_request(agent, user_input)
        elif any(word in user_input_lower for word in ['organize', 'structure', 'files']):
            await handle_file_organization_request(agent, user_input)
        else:
            # General code generation
            await handle_general_request(agent, user_input)
            
    except Exception as e:
        console.print(f"[red]❌ Sorry, I encountered an error: {e}[/red]")
        console.print("[yellow]💡 Try rephrasing your request or type 'help' for examples.[/yellow]")

async def handle_debug_request(agent: HurricaneAgent, user_input: str):
    """Handle debugging requests."""
    console.print("[blue]🐛 I'll help you debug your code![/blue]")
    
    # Ask for file or code
    file_path = Prompt.ask(
        "Which file should I debug? (or press Enter to paste code directly)",
        default=""
    )
    
    if file_path and Path(file_path).exists():
        code = await agent.file_manager.read_file(Path(file_path))
        error_msg = Prompt.ask("What error are you seeing? (optional)", default="")
        
        console.print(f"\n[blue]🔍 Analyzing {file_path}...[/blue]")
        result = await agent.debug_code(code, error_msg, Path(file_path))
        
        console.print(Panel(
            result,
            title="🐛 Debug Analysis",
            border_style="yellow"
        ))
        
        if Confirm.ask("Would you like me to apply the fixes?"):
            # Here you would implement the fix application logic
            console.print("[green]✅ Fixes applied successfully![/green]")
    else:
        console.print("[yellow]Please paste your code (press Ctrl+D when done):[/yellow]")
        # Handle direct code input
        console.print("[dim]Direct code debugging not implemented yet. Please specify a file.[/dim]")

async def handle_create_request(agent: HurricaneAgent, user_input: str):
    """Handle code creation requests."""
    console.print("[blue]🔧 I'll help you create some code![/blue]")
    
    # Detect language
    language = "python"  # default
    if "javascript" in user_input.lower() or "js" in user_input.lower():
        language = "javascript"
    elif "react" in user_input.lower():
        language = "javascript"
    elif "python" in user_input.lower() or "py" in user_input.lower():
        language = "python"
    elif "go" in user_input.lower():
        language = "go"
    
    console.print(f"\n[blue]⚡ Generating {language} code...[/blue]")
    
    code = await agent.generate_code(user_input, language)
    
    console.print(Panel(
        code,
        title=f"🚀 Generated {language.title()} Code",
        border_style="green"
    ))
    
    if Confirm.ask("Would you like me to save this to a file?"):
        filename = Prompt.ask("Enter filename", default=f"generated_code.{language}")
        await agent.file_manager.save_file(Path(filename), code)
        show_file_changes({filename: {"description": "Created new file with generated code"}})

async def handle_documentation_request(agent: HurricaneAgent, user_input: str):
    """Handle documentation requests."""
    console.print("[blue]📝 I'll help you create documentation![/blue]")
    
    if "readme" in user_input.lower():
        doc_type = "readme"
        target = "."
    else:
        file_path = Prompt.ask("Which file should I document?", default=".")
        target = file_path
        doc_type = "comments"
    
    console.print(f"\n[blue]📚 Generating {doc_type} documentation...[/blue]")
    
    documentation = await agent.generate_documentation(target, doc_type)
    
    console.print(Panel(
        documentation,
        title=f"📖 Generated {doc_type.title()} Documentation",
        border_style="blue"
    ))
    
    if Confirm.ask("Would you like me to save this documentation?"):
        if doc_type == "readme":
            filename = "README.md"
        else:
            filename = Prompt.ask("Enter filename for documentation", default="documentation.md")
        
        await agent.file_manager.save_file(Path(filename), documentation)
        show_file_changes({filename: {"description": f"Created {doc_type} documentation"}})

async def handle_refactor_request(agent: HurricaneAgent, user_input: str):
    """Handle code refactoring requests."""
    console.print("[blue]♻️ I'll help you refactor your code![/blue]")
    
    file_path = Prompt.ask("Which file should I refactor?")
    
    if not Path(file_path).exists():
        console.print(f"[red]❌ File {file_path} not found.[/red]")
        return
    
    style = "clean"
    if "minimal" in user_input.lower():
        style = "minimal"
    elif "enterprise" in user_input.lower():
        style = "enterprise"
    
    console.print(f"\n[blue]🔄 Refactoring {file_path} with '{style}' style...[/blue]")
    
    refactored_code = await agent.refactor_code("", style, Path(file_path))
    
    console.print(Panel(
        refactored_code,
        title=f"♻️ Refactored Code ({style} style)",
        border_style="blue"
    ))
    
    if Confirm.ask("Would you like me to apply these changes?"):
        await agent.file_manager.save_file(Path(file_path), refactored_code)
        show_file_changes({file_path: {"description": f"Refactored with {style} style"}})

async def handle_explain_request(agent: HurricaneAgent, user_input: str):
    """Handle code explanation requests."""
    console.print("[blue]🤔 I'll explain the code for you![/blue]")
    
    file_path = Prompt.ask("Which file should I explain?")
    
    if not Path(file_path).exists():
        console.print(f"[red]❌ File {file_path} not found.[/red]")
        return
    
    code = await agent.file_manager.read_file(Path(file_path))
    
    console.print(f"\n[blue]🔍 Analyzing {file_path}...[/blue]")
    
    explanation = await agent.code_assistant.explain_code(code)
    
    console.print(Panel(
        explanation,
        title=f"💡 Code Explanation: {Path(file_path).name}",
        border_style="cyan"
    ))

async def handle_test_request(agent: HurricaneAgent, user_input: str):
    """Handle test generation requests."""
    console.print("[blue]🧪 I'll generate tests for your code![/blue]")
    
    file_path = Prompt.ask("Which file should I create tests for?")
    
    if not Path(file_path).exists():
        console.print(f"[red]❌ File {file_path} not found.[/red]")
        return
    
    code = await agent.file_manager.read_file(Path(file_path))
    
    console.print(f"\n[blue]🧪 Generating tests for {file_path}...[/blue]")
    
    tests = await agent.code_assistant.generate_tests(code)
    
    console.print(Panel(
        tests,
        title=f"🧪 Generated Tests",
        border_style="green"
    ))
    
    if Confirm.ask("Would you like me to save these tests?"):
        test_filename = f"test_{Path(file_path).stem}.py"
        await agent.file_manager.save_file(Path(test_filename), tests)
        show_file_changes({test_filename: {"description": "Created unit tests"}})

async def handle_file_organization_request(agent: HurricaneAgent, user_input: str):
    """Handle file organization requests."""
    console.print("[blue]🗂️ I'll help you organize your files![/blue]")
    
    directory = Prompt.ask("Which directory should I organize?", default=".")
    
    if not Path(directory).exists():
        console.print(f"[red]❌ Directory {directory} not found.[/red]")
        return
    
    strategy = "by_type"
    if "date" in user_input.lower():
        strategy = "by_date"
    elif "size" in user_input.lower():
        strategy = "by_size"
    elif "project" in user_input.lower():
        strategy = "by_project"
    
    console.print(f"\n[blue]📁 Organizing {directory} using '{strategy}' strategy...[/blue]")
    
    result = await agent.organize_files(Path(directory), strategy)
    
    if 'error' not in result:
        moved_files = result.get('moved_files', {})
        console.print(f"[green]✅ Organized {len(moved_files)} files![/green]")
        
        if moved_files:
            show_file_changes({f"{old} → {new}": {"description": "File moved"} for old, new in moved_files.items()})
    else:
        console.print(f"[red]❌ Error: {result['error']}[/red]")

async def handle_general_request(agent: HurricaneAgent, user_input: str):
    """Handle general requests."""
    console.print("[blue]🤖 I'll help you with that![/blue]")
    
    # Try to generate code based on the request
    console.print(f"\n[blue]⚡ Processing your request...[/blue]")
    
    code = await agent.generate_code(user_input)
    
    console.print(Panel(
        code,
        title="🚀 Generated Code",
        border_style="green"
    ))
    
    if Confirm.ask("Would you like me to save this to a file?"):
        filename = Prompt.ask("Enter filename", default="generated_code.py")
        await agent.file_manager.save_file(Path(filename), code)
        show_file_changes({filename: {"description": "Created new file with generated code"}})

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="Hurricane AI Agent")
@click.option('--config', type=click.Path(), help='Path to configuration file')
@click.pass_context
def main(ctx, config):
    """🌪️ Hurricane AI Agent - Your intelligent coding assistant powered by Ollama."""
    ctx.ensure_object(dict)
    config_path = Path(config) if config else None
    ctx.obj['agent'] = HurricaneAgent(config_path)


@main.command()
@click.pass_context
def start(ctx):
    """🌪️ Start Hurricane - Interactive AI coding assistant"""
    agent = ctx.obj['agent']
    
    async def _start():
        # Show welcome screen
        show_welcome_screen()
        
        # Initialize and setup models
        console.print("[bold blue]🚀 Starting Hurricane...[/bold blue]")
        
        try:
            # Check Ollama connection
            models = agent.ollama_client.list_models()
            console.print("[green]✅ Connected to Ollama successfully![/green]")
        except Exception as e:
            console.print(f"[red]❌ Cannot connect to Ollama: {e}[/red]")
            console.print("[yellow]💡 Make sure Ollama is running: [bold]ollama serve[/bold][/yellow]")
            return
        
        # Interactive model setup
        if not await interactive_model_setup(agent):
            return
        
        # Initialize agent
        await agent.initialize()
        
        console.print("\n[bold green]🎉 Hurricane is ready! Let's start coding![/bold green]")
        console.print("[dim]Type your request in plain English, and I'll help you with your code.[/dim]\n")
        
        # Main interactive loop
        while True:
            try:
                # Get user input
                user_input = Prompt.ask(
                    "[bold cyan]🌪️ What would you like me to help you with?[/bold cyan]",
                    default="quit"
                )
                
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    console.print("[bold blue]👋 Thanks for using Hurricane! Happy coding![/bold blue]")
                    break
                
                if user_input.lower() in ['help', 'h']:
                    show_help_examples()
                    continue
                
                # Process the request
                await process_natural_language_request(agent, user_input)
                
            except KeyboardInterrupt:
                console.print("\n[bold blue]👋 Thanks for using Hurricane! Happy coding![/bold blue]")
                break
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
    
    asyncio.run(_start())

@main.command()
@click.pass_context
def init(ctx):
    """Initialize Hurricane and check system requirements."""
    agent = ctx.obj['agent']
    
    async def _init():
        success = await agent.initialize()
        if success:
            console.print(Panel.fit(
                Text("🌪️ Hurricane AI Agent initialized successfully!", style="bold green"),
                title="Ready to Code",
                border_style="green"
            ))
            
            # Display status
            status = agent.get_status()
            table = Table(title="Hurricane Status")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Ollama Host", status['config']['ollama_host'])
            table.add_row("Model", status['config']['model'])
            table.add_row("Code Style", status['config']['code_style'])
            table.add_row("Doc Format", status['config']['documentation_format'])
            table.add_row("Available Models", str(len(status['available_models'])))
            
            console.print(table)
        else:
            console.print("[red]❌ Failed to initialize Hurricane. Please check your Ollama installation.[/red]")
    
    asyncio.run(_init())


@main.group()
def code():
    """Code generation and assistance commands."""
    pass


@code.command()
@click.argument('description')
@click.option('--language', '-l', default='python', help='Programming language')
@click.option('--context', '-c', help='Additional context or existing code')
@click.option('--save', '-s', type=click.Path(), help='Save generated code to file')
@click.pass_context
def generate(ctx, description, language, context, save):
    """Generate code based on description."""
    agent = ctx.obj['agent']
    
    async def _generate():
        try:
            save_path = Path(save) if save else None
            code = await agent.generate_code(description, language, context, save_path)
            
            if not save:
                console.print(Panel(
                    code,
                    title=f"Generated {language.title()} Code",
                    border_style="green"
                ))
        except Exception as e:
            console.print(f"[red]❌ Error generating code: {e}[/red]")
    
    asyncio.run(_generate())


@code.command()
@click.option('--file', '-f', type=click.Path(exists=True), help='File to debug')
@click.option('--code', '-c', help='Code to debug (if not using file)')
@click.option('--error', '-e', help='Error message to help with debugging')
@click.pass_context
def debug(ctx, file, code, error):
    """Debug code and provide fixes."""
    if not file and not code:
        console.print("[red]❌ Please provide either --file or --code[/red]")
        return
    
    agent = ctx.obj['agent']
    
    async def _debug():
        try:
            file_path = Path(file) if file else None
            debug_result = await agent.debug_code(code or "", error, file_path)
            
            console.print(Panel(
                debug_result,
                title="Debug Analysis",
                border_style="yellow"
            ))
        except Exception as e:
            console.print(f"[red]❌ Error debugging code: {e}[/red]")
    
    asyncio.run(_debug())


@code.command()
@click.option('--file', '-f', type=click.Path(exists=True), help='File to refactor')
@click.option('--code', '-c', help='Code to refactor (if not using file)')
@click.option('--style', '-s', default='clean', help='Refactoring style (clean, minimal, enterprise)')
@click.pass_context
def refactor(ctx, file, code, style):
    """Refactor code according to specified style."""
    if not file and not code:
        console.print("[red]❌ Please provide either --file or --code[/red]")
        return
    
    agent = ctx.obj['agent']
    
    async def _refactor():
        try:
            file_path = Path(file) if file else None
            refactored_code = await agent.refactor_code(code or "", style, file_path)
            
            console.print(Panel(
                refactored_code,
                title=f"Refactored Code ({style} style)",
                border_style="blue"
            ))
        except Exception as e:
            console.print(f"[red]❌ Error refactoring code: {e}[/red]")
    
    asyncio.run(_refactor())


@main.group()
def docs():
    """Documentation generation commands."""
    pass


@docs.command()
@click.argument('target')
@click.option('--type', '-t', default='readme', help='Documentation type (readme, api, comments, etc.)')
@click.option('--format', '-f', default='markdown', help='Output format (markdown, rst, html)')
@click.option('--save', '-s', type=click.Path(), help='Save documentation to file')
@click.pass_context
def generate(ctx, target, type, format, save):
    """Generate documentation for code or project."""
    agent = ctx.obj['agent']
    
    async def _generate_docs():
        try:
            save_path = Path(save) if save else None
            documentation = await agent.generate_documentation(target, type, format, save_path)
            
            if not save:
                console.print(Panel(
                    documentation,
                    title=f"Generated {type.title()} Documentation",
                    border_style="blue"
                ))
        except Exception as e:
            console.print(f"[red]❌ Error generating documentation: {e}[/red]")
    
    asyncio.run(_generate_docs())


@main.group()
def files():
    """File management commands."""
    pass


@files.command()
@click.argument('project_type')
@click.argument('project_name')
@click.option('--path', '-p', type=click.Path(), help='Base path for project creation')
@click.pass_context
def scaffold(ctx, project_type, project_name, path):
    """Create a project structure."""
    agent = ctx.obj['agent']
    
    async def _scaffold():
        try:
            base_path = Path(path) if path else None
            result = await agent.create_project_structure(project_type, project_name, base_path)
            
            if 'error' not in result:
                console.print(f"[green]✅ Created {project_type} project: {project_name}[/green]")
                console.print(f"[blue]📁 Project path: {result.get('project_path')}[/blue]")
                console.print(f"[blue]📄 Created {len(result.get('created_files', []))} files[/blue]")
                console.print(f"[blue]📁 Created {len(result.get('created_directories', []))} directories[/blue]")
            else:
                console.print(f"[red]❌ Error: {result['error']}[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error creating project: {e}[/red]")
    
    asyncio.run(_scaffold())


@files.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--strategy', '-s', default='by_type', help='Organization strategy (by_type, by_date, by_size, by_project)')
@click.pass_context
def organize(ctx, directory, strategy):
    """Organize files in a directory."""
    agent = ctx.obj['agent']
    
    async def _organize():
        try:
            result = await agent.organize_files(Path(directory), strategy)
            
            if 'error' not in result:
                moved_files = result.get('moved_files', {})
                console.print(f"[green]✅ Organized {len(moved_files)} files using '{strategy}' strategy[/green]")
                
                if moved_files and len(moved_files) <= 10:  # Show details for small number of files
                    table = Table(title="Moved Files")
                    table.add_column("From", style="red")
                    table.add_column("To", style="green")
                    
                    for old_path, new_path in moved_files.items():
                        table.add_row(Path(old_path).name, Path(new_path).name)
                    
                    console.print(table)
            else:
                console.print(f"[red]❌ Error: {result['error']}[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error organizing files: {e}[/red]")
    
    asyncio.run(_organize())


@main.command()
@click.pass_context
def status(ctx):
    """Show Hurricane status and configuration."""
    agent = ctx.obj['agent']
    
    status_info = agent.get_status()
    
    # Main status table
    table = Table(title="🌪️ Hurricane Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Initialized", "✅ Yes" if status_info['initialized'] else "❌ No")
    table.add_row("Ollama Host", status_info['config']['ollama_host'])
    table.add_row("Default Model", status_info['config']['model'])
    table.add_row("Code Style", status_info['config']['code_style'])
    table.add_row("Doc Format", status_info['config']['documentation_format'])
    
    console.print(table)
    
    # Available models
    models = status_info.get('available_models', [])
    if models:
        models_table = Table(title="Available Models")
        models_table.add_column("Model Name", style="blue")
        
        for model in models:
            models_table.add_row(model)
        
        console.print(models_table)
    else:
        console.print("[yellow]⚠️ No models available. Run 'ollama pull codellama' to get started.[/yellow]")


@main.command()
@click.option('--ollama-host', help='Ollama server host')
@click.option('--model', help='Default model to use')
@click.option('--code-style', help='Preferred code style')
@click.option('--doc-format', help='Documentation format')
@click.pass_context
def config(ctx, ollama_host, model, code_style, doc_format):
    """Update Hurricane configuration."""
    agent = ctx.obj['agent']
    
    updates = {}
    if ollama_host:
        updates['ollama'] = {'host': ollama_host}
    if model:
        if 'ollama' not in updates:
            updates['ollama'] = {}
        updates['ollama']['model'] = model
    if code_style:
        updates['preferences'] = {'code_style': code_style}
    if doc_format:
        if 'preferences' not in updates:
            updates['preferences'] = {}
        updates['preferences']['documentation_format'] = doc_format
    
    if updates:
        agent.update_config(updates)
        console.print("[green]✅ Configuration updated successfully![/green]")
    else:
        console.print("[yellow]No configuration changes specified.[/yellow]")


if __name__ == '__main__':
    main()

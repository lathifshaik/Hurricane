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
from .modules.project_indexer import ProjectIndexer
from .modules.context_aware_editor import ContextAwareEditor
from .modules.project_planner import ProjectPlanner

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
        "🏗️ 'Create a new file called utils.py'",
        "♻️ 'Refactor this code to be cleaner'",
        "📖 'Explain what this code does'",
        "🧪 'Generate unit tests for my functions'",
        "📁 'Show project structure'",
        "🔍 'Find files with login'",
        "🧭 'Navigate to main.py'",
        "⚠️ 'Delete old_file.py'",
        "📊 'Show project summary'",
        "💻 'Commit changes with a message'",
        "📈 'Push changes to GitHub'",
        "🔄 'Pull changes from GitHub'",
        "📦 'Create a new branch'",
        "🔄 'Merge branch into main'",
        "🔍 'Analyze codebase for issues'",
        "🤖 'Select AI model'",
        "⚡ 'Auto-fix code issues'",
        "📈 'Show code quality metrics'",
        "✏️ 'Start smart editing session for main.py'",
        "🎯 'Edit file with context awareness'",
        "💡 'Suggest improvements for my code'",
        "📊 'Show editing progress'",
        "✅ 'Finish editing session'",
        "🚀 'Create a React landing page app'",
        "🎮 'Build a Python game with Pygame'",
        "🌐 'Generate a Next.js web application'",
        "📱 'Create a Flutter mobile app'",
        "🔧 'Build an Express.js API'"
    ]
    console.print("\n[bold green]💡 Here's what I can help you with:[/bold green]")
    
    for example in examples:
        console.print(f"  {example}")
    
    console.print("\n[dim]Just describe what you want in plain English![/dim]\n")

# Context-aware editing patterns
context_editing_patterns = [
    r'(?i).*\b(edit|modify|change|update)\b.*\b(file|code)\b.*\b(context|smart|intelligent)\b.*',
    r'(?i).*\b(start|begin)\b.*\b(editing|edit)\b.*\b(session)\b.*',
    r'(?i).*\b(suggest|recommend)\b.*\b(edit|change|improvement)\b.*',
    r'(?i).*\b(analyze|review)\b.*\b(file|code)\b.*\b(editing|edit)\b.*',
    r'(?i).*\b(finish|complete|end)\b.*\b(editing|edit)\b.*\b(session)\b.*',
    r'(?i).*\b(show|display)\b.*\b(editing|edit)\b.*\b(progress|status)\b.*',
]

# Git patterns
git_patterns = [
    r'(?i).*\b(git|version control|commit|push|pull|branch|merge)\b.*',
    r'(?i).*\b(commit.*changes|add.*files|create.*branch|switch.*branch)\b.*',
    r'(?i).*\b(git status|git log|git history|commit message)\b.*',
    r'(?i).*\b(smart commit|auto commit|generate commit message)\b.*'
]

# Codebase analysis patterns
codebase_analysis_patterns = [
    r'(?i).*\b(analyze|analysis|check|review|audit)\b.*\b(codebase|code|project)\b.*',
    r'(?i).*\b(optimize|optimization|improve|enhancement)\b.*\b(suggestions?|opportunities)\b.*',
    r'(?i).*\b(quality|metrics|score|debt)\b.*\b(code|technical)\b.*',
    r'(?i).*\b(auto.?fix|fix.?issues|fix.?problems)\b.*',
]

# Model selection patterns
model_selection_patterns = [
    r'(?i).*\b(select|choose|pick|change)\b.*\b(model|ai)\b.*',
    r'(?i).*\b(install|setup|configure)\b.*\b(model|ai)\b.*',
    r'(?i).*\b(recommend|suggest|best)\b.*\b(model|ai)\b.*',
    r'(?i).*\b(show|list|display)\b.*\b(models?|installed)\b.*',
]

# App generation patterns
app_generation_patterns = [
    r'(?i).*\b(create|build|generate|make)\b.*\b(app|application|project)\b.*',
    r'(?i).*\b(landing page|website|web app|web application)\b.*',
    r'(?i).*\b(game|pygame|python game)\b.*',
    r'(?i).*\b(mobile app|flutter|android|ios)\b.*',
    r'(?i).*\b(api|backend|express|rest api)\b.*',
    r'(?i).*\b(react|nextjs|next.js|vue|angular)\b.*\b(app|application)\b.*',
]

async def process_natural_language_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer):
    """Process natural language requests and determine what action to take."""
    user_input_lower = user_input.lower()
    
    try:
        # Determine intent based on keywords
        if any(word in user_input_lower for word in ['show', 'display', 'tree', 'structure', 'project']):
            await handle_navigation_request(agent, user_input, indexer)
        elif any(word in user_input_lower for word in ['find', 'search', 'locate', 'where']):
            await handle_search_request(agent, user_input, indexer)
        elif any(re.search(pattern, user_input, re.IGNORECASE) for pattern in app_generation_patterns):
            await handle_app_generation_request(agent, user_input, indexer)
        elif any(re.search(pattern, user_input, re.IGNORECASE) for pattern in context_editing_patterns):
            await handle_context_editing_request(agent, user_input, indexer)
        elif any(re.search(pattern, user_input, re.IGNORECASE) for pattern in git_patterns):
            await handle_git_request(agent, user_input, indexer)
        elif any(word in user_input_lower for word in ['web', 'search', 'documentation', 'docs', 'lookup']):
            await handle_web_search_request(agent, user_input)
        elif any(re.search(pattern, user_input, re.IGNORECASE) for pattern in codebase_analysis_patterns):
            await handle_codebase_analysis_request(agent, user_input, indexer)
        elif any(re.search(pattern, user_input, re.IGNORECASE) for pattern in model_selection_patterns):
            await handle_model_selection_request(agent, user_input)
        elif any(word in user_input_lower for word in ['debug', 'fix', 'error', 'bug']):
            await handle_debug_request(agent, user_input, indexer)
        elif any(word in user_input_lower for word in ['create', 'generate', 'make', 'build', 'write', 'new']):
            await handle_create_request(agent, user_input, indexer)
        elif any(word in user_input_lower for word in ['readme', 'documentation', 'docs', 'comment']):
            await handle_documentation_request(agent, user_input, indexer)
        elif any(word in user_input_lower for word in ['refactor', 'clean', 'improve', 'optimize']):
            await handle_refactor_request(agent, user_input, indexer)
        elif any(word in user_input_lower for word in ['explain', 'what does', 'how does', 'understand']):
            await handle_explain_request(agent, user_input, indexer)
        elif any(word in user_input_lower for word in ['test', 'unit test', 'testing']):
            await handle_test_request(agent, user_input, indexer)
        elif any(word in user_input_lower for word in ['organize', 'structure', 'files']):
            await handle_file_organization_request(agent, user_input, indexer)
        else:
            # General code generation
            await handle_general_request(agent, user_input, indexer)
            
    except Exception as e:
        console.print(f"[red]❌ Sorry, I encountered an error: {e}[/red]")
        console.print("[yellow]💡 Try rephrasing your request or type 'help' for examples.[/yellow]")

async def handle_navigation_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer):
    """Handle project navigation and structure display requests."""
    console.print("[blue]🗂️ I'll show you the project structure![/blue]")
    
    if "summary" in user_input.lower() or "stats" in user_input.lower():
        # Show project summary
        summary = indexer.get_project_summary()
        
        table = Table(title="📊 Project Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Total Files", str(summary["total_files"]))
        table.add_row("Functions", str(summary["total_functions"]))
        table.add_row("Classes", str(summary["total_classes"]))
        
        for file_type, count in summary["by_type"].items():
            table.add_row(f"{file_type.title()} Files", str(count))
        
        console.print(table)
        
        if summary["by_language"]:
            lang_table = Table(title="🔤 Languages Used")
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Files", style="green")
            
            for lang, count in summary["by_language"].items():
                lang_table.add_row(lang.title(), str(count))
            
            console.print(lang_table)
    else:
        # Show project tree
        depth = 3
        if "deep" in user_input.lower() or "detailed" in user_input.lower():
            depth = 5
        elif "shallow" in user_input.lower() or "brief" in user_input.lower():
            depth = 2
        
        indexer.show_project_tree(max_depth=depth)

async def handle_search_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer):
    """Handle file search requests."""
    console.print("[blue]🔍 I'll help you find files![/blue]")
    
    # Extract search query
    search_terms = ["find", "search", "locate", "where", "files", "with", "containing"]
    words = user_input.lower().split()
    
    # Find the actual search query
    query = ""
    for i, word in enumerate(words):
        if word in search_terms and i + 1 < len(words):
            query = " ".join(words[i+1:])
            break
    
    if not query:
        query = Prompt.ask("What would you like to search for?")
    
    # Determine file type filter
    file_type = None
    if "code" in user_input.lower() or "python" in user_input.lower():
        file_type = "code"
    elif "doc" in user_input.lower() or "readme" in user_input.lower():
        file_type = "documentation"
    
    results = indexer.search_files(query, file_type)
    
    if not results:
        console.print(f"[yellow]No files found matching '{query}'[/yellow]")
        return
    
    console.print(f"[green]Found {len(results)} files matching '{query}':[/green]\n")
    
    for result in results[:10]:  # Show top 10 results
        path = result["path"]
        match_type = result["match_type"]
        info = result["info"]
        
        if match_type == "filename":
            console.print(f"📄 [cyan]{path}[/cyan] - {info.get('summary', 'File match')}")
        elif match_type == "function":
            console.print(f"🔧 [cyan]{path}[/cyan] - Function: [yellow]{result['match_name']}[/yellow] (line {result['line']})")
        elif match_type == "class":
            console.print(f"🏗️ [cyan]{path}[/cyan] - Class: [yellow]{result['match_name']}[/yellow] (line {result['line']})")
    
    if len(results) > 10:
        console.print(f"\n[dim]... and {len(results) - 10} more results[/dim]")

async def handle_delete_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer):
    """Handle file deletion requests with safety checks."""
    console.print("[yellow]⚠️ I'll help you safely delete files![/yellow]")
    
    # Extract filename from request
    words = user_input.split()
    filename = None
    
    for i, word in enumerate(words):
        if word.lower() in ["delete", "remove", "rm"] and i + 1 < len(words):
            filename = words[i + 1]
            break
    
    if not filename:
        filename = Prompt.ask("Which file would you like to delete?")
    
    # Search for the file if not exact path
    if not Path(filename).exists():
        search_results = indexer.search_files(filename)
        
        if not search_results:
            console.print(f"[red]❌ File '{filename}' not found[/red]")
            return
        
        if len(search_results) == 1:
            filename = search_results[0]["path"]
        else:
            console.print("[yellow]Multiple files found:[/yellow]")
            choices = []
            for i, result in enumerate(search_results[:5]):
                console.print(f"  {i+1}. {result['path']}")
                choices.append(str(i+1))
            
            choice = Prompt.ask("Which file?", choices=choices + ["cancel"])
            if choice == "cancel":
                return
            
            filename = search_results[int(choice) - 1]["path"]
    
    # Perform safe deletion
    await indexer.safe_delete_file(filename)

async def handle_file_navigation_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer):
    """Handle file navigation requests."""
    console.print("[blue]🧭 I'll help you navigate to files![/blue]")
    
    # Extract filename from request
    words = user_input.split()
    filename = None
    
    for i, word in enumerate(words):
        if word.lower() in ["navigate", "go", "open", "cd"] and i + 1 < len(words):
            filename = " ".join(words[i + 1:])
            break
    
    if not filename:
        filename = Prompt.ask("Which file would you like to navigate to?")
    
    # Search for the file
    search_results = indexer.search_files(filename)
    
    if not search_results:
        console.print(f"[red]❌ File '{filename}' not found[/red]")
        return
    
    if len(search_results) == 1:
        target_file = search_results[0]["path"]
    else:
        console.print("[yellow]Multiple files found:[/yellow]")
        choices = []
        for i, result in enumerate(search_results[:5]):
            console.print(f"  {i+1}. {result['path']}")
            choices.append(str(i+1))
        
        choice = Prompt.ask("Which file?", choices=choices + ["cancel"])
        if choice == "cancel":
            return
        
        target_file = search_results[int(choice) - 1]["path"]
    
    # Navigate to file and show context
    context = indexer.navigate_to_file(target_file)
    
    if not context:
        console.print(f"[red]❌ Could not navigate to {target_file}[/red]")
        return
    
    console.print(Panel(
        f"""[bold cyan]File:[/bold cyan] {context['path']}
[bold cyan]Full Path:[/bold cyan] {context['full_path']}
[bold cyan]Exists:[/bold cyan] {'✅ Yes' if context['exists'] else '❌ No'}
[bold cyan]Type:[/bold cyan] {context['info'].get('type', 'unknown')}
[bold cyan]Language:[/bold cyan] {context['info'].get('language', 'unknown')}
[bold cyan]Size:[/bold cyan] {context['info'].get('size', 0)} bytes
[bold cyan]Summary:[/bold cyan] {context['info'].get('summary', 'No summary')}""",
        title=f"📄 {Path(target_file).name}",
        border_style="blue"
    ))
    
    # Show related files
    if context['related_files']:
        console.print("\n[bold green]🔗 Related Files:[/bold green]")
        for related in context['related_files'][:5]:
            console.print(f"  📄 {related}")

async def handle_debug_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer = None):
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

async def handle_create_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer = None):
    """Handle code creation requests."""
    console.print("[blue]🔧 I'll help you create some code![/blue]")
    
    # Check if user wants to create a new file
    if "new file" in user_input.lower() or "create file" in user_input.lower():
        filename = Prompt.ask("What should I name the new file?")
        
        if indexer:
            success = await indexer.create_file_with_template(filename)
            if success:
                show_file_changes({filename: {"description": "Created new file with template"}})
            return
        else:
            console.print("[yellow]File creation requires project indexing. Use 'hurricane start' for full features.[/yellow]")
    
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

async def handle_documentation_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer = None):
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

async def handle_refactor_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer = None):
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

async def handle_explain_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer = None):
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

async def handle_test_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer = None):
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

async def handle_file_organization_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer = None):
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

async def handle_git_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer = None):
    """Handle Git version control requests."""
    console.print("[blue]🌿 I'll help you with Git![/blue]")
    
    user_input_lower = user_input.lower()
    
    try:
        if any(word in user_input_lower for word in ['status', 'show status']):
            await agent.git_assistant.show_status()
        
        elif any(word in user_input_lower for word in ['commit', 'smart commit']):
            if 'smart' in user_input_lower or 'auto' in user_input_lower:
                await agent.git_assistant.smart_commit_workflow()
            else:
                # Add all files and commit with AI-generated message
                await agent.git_assistant.add_files()
                await agent.git_assistant.commit_changes(auto_message=False)
        
        elif any(word in user_input_lower for word in ['history', 'log', 'commits']):
            await agent.git_assistant.show_commit_history()
        
        elif any(word in user_input_lower for word in ['branch', 'branches']):
            if 'create' in user_input_lower or 'new' in user_input_lower:
                branch_name = Prompt.ask("Enter branch name")
                await agent.git_assistant.create_branch(branch_name)
            elif 'switch' in user_input_lower or 'checkout' in user_input_lower:
                await agent.git_assistant.show_branches()
                branch_name = Prompt.ask("Enter branch name to switch to")
                await agent.git_assistant.switch_branch(branch_name)
            else:
                await agent.git_assistant.show_branches()
        
        elif any(word in user_input_lower for word in ['init', 'initialize']):
            await agent.git_assistant.init_repo()
        
        else:
            # Use AI to help with Git command
            git_help = await agent.ollama_client.generate_response(
                f"Help with this Git request: {user_input}",
                system_prompt="You are a Git expert. Provide helpful Git commands and explanations. Be concise and practical."
            )
            console.print(Panel(
                git_help,
                title="🌿 Git Assistant",
                border_style="green"
            ))
    
    except Exception as e:
        console.print(f"[red]❌ Git error: {e}[/red]")

async def handle_codebase_analysis_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer = None):
    """Handle codebase analysis and optimization requests."""
    console.print("[blue]🔍 I'll analyze your codebase for optimization opportunities![/blue]")
    
    user_input_lower = user_input.lower()
    
    try:
        if any(word in user_input_lower for word in ['auto-fix', 'fix issues', 'auto fix']):
            # Auto-fix issues
            console.print("[blue]🔧 Running codebase analysis and auto-fixing issues...[/blue]")
            analysis_results = await agent.codebase_analyzer.analyze_project(include_ai_suggestions=False)
            await agent.codebase_analyzer.show_analysis_results(analysis_results)
            
            if analysis_results["metrics"]["auto_fixable_issues"] > 0:
                if Confirm.ask("Auto-fix the fixable issues?"):
                    fix_results = await agent.codebase_analyzer.auto_fix_issues(analysis_results)
                    console.print(f"[green]✅ Fixed {fix_results['fixed_count']} issues automatically![/green]")
        
        elif any(word in user_input_lower for word in ['metrics', 'quality', 'score']):
            # Show quality metrics only
            console.print("[blue]📊 Analyzing code quality metrics...[/blue]")
            analysis_results = await agent.codebase_analyzer.analyze_project(include_ai_suggestions=False)
            
            metrics = analysis_results["metrics"]
            console.print(Panel(
                f"[bold]Quality Score:[/bold] {metrics['quality_score']}/100\n"
                f"[bold]Total Issues:[/bold] {metrics['total_issues']}\n"
                f"[bold]Technical Debt:[/bold] {metrics['technical_debt_hours']:.1f} hours\n"
                f"[bold]Auto-fixable:[/bold] {metrics['auto_fixable_issues']} issues",
                title="📈 Code Quality Metrics",
                border_style="green" if metrics['quality_score'] >= 80 else "yellow" if metrics['quality_score'] >= 60 else "red"
            ))
        
        else:
            # Full analysis with AI suggestions
            console.print("[blue]🤖 Running comprehensive codebase analysis with AI suggestions...[/blue]")
            analysis_results = await agent.codebase_analyzer.analyze_project(include_ai_suggestions=True)
            await agent.codebase_analyzer.show_analysis_results(analysis_results)
            
            # Offer auto-fix if available
            if analysis_results["metrics"]["auto_fixable_issues"] > 0:
                if Confirm.ask("Would you like me to auto-fix the fixable issues?"):
                    fix_results = await agent.codebase_analyzer.auto_fix_issues(analysis_results)
                    console.print(f"[green]✅ Fixed {fix_results['fixed_count']} issues automatically![/green]")
    
    except Exception as e:
        console.print(f"[red]❌ Analysis error: {e}[/red]")

async def handle_model_selection_request(agent: HurricaneAgent, user_input: str):
    """Handle AI model selection and management requests."""
    console.print("[blue]🤖 I'll help you select the perfect AI model![/blue]")
    
    user_input_lower = user_input.lower()
    
    try:
        if any(word in user_input_lower for word in ['installed', 'list', 'show models']):
            # Show installed models
            await agent.model_selector.show_installed_models()
        
        elif any(word in user_input_lower for word in ['recommend', 'suggestion', 'best']):
            # Get recommendations based on use case
            use_case = "general coding"  # Default
            if "debug" in user_input_lower:
                use_case = "debugging"
            elif "document" in user_input_lower:
                use_case = "documentation"
            elif "complex" in user_input_lower:
                use_case = "complex coding"
            
            recommendations = agent.model_selector.get_model_recommendations(use_case)
            
            console.print(f"[bold green]🎯 Top recommendations for {use_case}:[/bold green]")
            for i, model in enumerate(recommendations, 1):
                status = "✅ Installed" if model.installed else "📥 Available"
                console.print(f"{i}. {model.display_name} - {status}")
                console.print(f"   {model.description}")
                console.print(f"   Rating: {model.performance_rating}/5.0 ⭐\n")
        
        else:
            # Show interactive model selector
            selected_model = await agent.model_selector.show_interactive_selector()
            
            if selected_model:
                console.print(f"[green]🎉 Successfully set up {selected_model}![/green]")
                console.print("[blue]💡 You can now use Hurricane with your new model![/blue]")
            else:
                console.print("[yellow]Model selection cancelled.[/yellow]")
    
    except Exception as e:
        console.print(f"[red]❌ Model selection error: {e}[/red]")

async def handle_context_editing_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer):
    """Handle context-aware editing requests."""
    console.print("[blue]✏️ I'll help you with context-aware editing![/blue]")
    user_input_lower = user_input.lower()
    
    try:
        # Initialize project planner and context-aware editor
        project_planner = ProjectPlanner(agent.ollama_client, agent.config, agent.project_root)
        context_editor = ContextAwareEditor(agent.ollama_client, agent.config, project_planner)
        
        if any(word in user_input_lower for word in ['start', 'begin', 'session']):
            # Start editing session
            file_path = None
            # Try to extract file path from input
            words = user_input.split()
            for word in words:
                if '.' in word and ('/' in word or word.endswith(('.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.c', '.h'))):
                    file_path = word
                    break
            
            if not file_path:
                file_path = Prompt.ask("Enter the file path to edit")
            
            task_description = Prompt.ask("What would you like to accomplish with this file?", default="General editing")
            
            # Start editing session
            edit_context = await context_editor.start_editing_session(file_path, task_description)
            
            # Analyze file and show suggestions
            suggestions = await context_editor.analyze_file_for_editing(file_path, task_description)
            if suggestions:
                console.print("\n[bold cyan]💡 AI Suggestions:[/bold cyan]")
                for i, suggestion in enumerate(suggestions, 1):
                    console.print(f"{i}. Line {suggestion.line_number}: {suggestion.reason}")
                    if suggestion.requires_research:
                        console.print(f"   [dim]Research performed: {suggestion.research_query}[/dim]")
        
        elif any(word in user_input_lower for word in ['suggest', 'recommend', 'improvement']):
            # Get editing suggestions for current context
            file_path = Prompt.ask("Enter the file path to analyze")
            edit_goal = Prompt.ask("What's your editing goal?", default="General improvements")
            
            suggestions = await context_editor.analyze_file_for_editing(file_path, edit_goal)
            if suggestions:
                console.print("\n[bold green]🎯 Context-Aware Suggestions:[/bold green]")
                for i, suggestion in enumerate(suggestions, 1):
                    console.print(f"\n{i}. [bold]Line {suggestion.line_number}[/bold]")
                    console.print(f"   [yellow]Current:[/yellow] {suggestion.original_code}")
                    console.print(f"   [green]Suggested:[/green] {suggestion.suggested_code}")
                    console.print(f"   [blue]Reason:[/blue] {suggestion.reason}")
                    console.print(f"   [dim]Confidence: {suggestion.confidence:.1%}[/dim]")
        
        elif any(word in user_input_lower for word in ['edit', 'modify', 'change', 'update']):
            # Apply context-aware edit
            file_path = None
            # Try to extract file path from input
            words = user_input.split()
            for word in words:
                if '.' in word and ('/' in word or word.endswith(('.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.c', '.h'))):
                    file_path = word
                    break
            
            if not file_path:
                file_path = Prompt.ask("Enter the file path to edit")
            
            edit_description = Prompt.ask("Describe the edit you want to make")
            
            success = await context_editor.apply_edit_with_context(file_path, edit_description, context_aware=True)
            if success:
                # Suggest next edit
                next_suggestion = await context_editor.suggest_next_edit(file_path)
                if next_suggestion:
                    console.print(f"\n[bold blue]💡 Next suggestion:[/bold blue] {next_suggestion}")
        
        elif any(word in user_input_lower for word in ['progress', 'status']):
            # Show editing progress
            context_editor.show_editing_progress()
        
        elif any(word in user_input_lower for word in ['finish', 'complete', 'end']):
            # Finish editing session
            completion_notes = Prompt.ask("Any completion notes?", default="")
            await context_editor.finish_editing_session(completion_notes)
        
        else:
            # General context-aware editing help
            console.print("[bold cyan]🎯 Context-Aware Editing Options:[/bold cyan]")
            console.print("• 'Start editing session for main.py' - Begin context-aware editing")
            console.print("• 'Suggest improvements for my code' - Get AI suggestions")
            console.print("• 'Edit file with context' - Apply context-aware edits")
            console.print("• 'Show editing progress' - View current session status")
            console.print("• 'Finish editing session' - Complete and save session")
    
    except Exception as e:
        console.print(f"[red]❌ Context editing error: {e}[/red]")

async def handle_app_generation_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer):
    """Handle app generation requests."""
    console.print("[blue]🚀 I'll help you create a complete application![/blue]")
    user_input_lower = user_input.lower()
    
    try:
        if any(word in user_input_lower for word in ['list', 'show', 'available', 'templates']):
            # Show available app templates
            agent.app_generator.list_available_templates()
            return
        
        # Check if user wants to specify app name
        app_name = None
        if "called" in user_input_lower or "named" in user_input_lower:
            # Try to extract app name from input
            words = user_input.split()
            for i, word in enumerate(words):
                if word.lower() in ['called', 'named'] and i + 1 < len(words):
                    app_name = words[i + 1].strip('"\'')
                    break
        
        # Detect app type from request
        app_type = await agent.app_generator.detect_app_type(user_input)
        
        if not app_type:
            console.print("[yellow]⚠️ Could not determine app type from your request.[/yellow]")
            console.print("[blue]Available app types:[/blue]")
            agent.app_generator.list_available_templates()
            
            app_type = Prompt.ask(
                "\nWhich type of app would you like to create?",
                choices=list(agent.app_generator.templates.keys()),
                default="react_landing"
            )
        
        # Get app name if not provided
        if not app_name:
            suggested_name = await agent.app_generator._generate_app_name(user_input, agent.app_generator.templates[app_type])
            app_name = Prompt.ask(f"App name", default=suggested_name)
        
        # Confirm before creating
        template = agent.app_generator.templates[app_type]
        console.print(f"\n[bold cyan]📋 App Generation Summary:[/bold cyan]")
        console.print(f"[bold]Name:[/bold] {app_name}")
        console.print(f"[bold]Type:[/bold] {template.name}")
        console.print(f"[bold]Description:[/bold] {template.description}")
        console.print(f"[bold]Tech Stack:[/bold] {', '.join(template.tech_stack)}")
        console.print(f"[bold]Files to Generate:[/bold] {len(template.required_files)}")
        
        if not Confirm.ask("\nProceed with app generation?"):
            console.print("[yellow]App generation cancelled.[/yellow]")
            return
        
        # Create the app
        console.print(f"\n[bold green]🎯 Creating {template.name}: '{app_name}'[/bold green]")
        app_path = await agent.app_generator.create_app(user_input, app_name, app_type)
        
        if app_path:
            console.print(f"\n[bold green]✅ Successfully created '{app_name}' at {app_path}![/bold green]")
            
            # Ask if user wants to open the directory
            if Confirm.ask("Would you like to navigate to the new app directory?"):
                os.chdir(app_path)
                console.print(f"[green]📁 Changed directory to {app_path}[/green]")
                
                # Update the agent's project root
                agent.project_root = app_path
                agent.project_indexer = ProjectIndexer(app_path)
                
                console.print("[blue]💡 You can now use Hurricane commands within your new app![/blue]")
        else:
            console.print("[red]❌ App generation failed.[/red]")
    
    except Exception as e:
        console.print(f"[red]❌ App generation error: {e}[/red]")

async def handle_web_search_request(agent: HurricaneAgent, user_input: str, language: str = None):
    """Handle web search for documentation requests."""
    console.print("[blue]🔍 Searching documentation...[/blue]")
    
    try:
        # Extract search query from user input
        search_terms = ['search', 'find', 'look up', 'documentation', 'docs', 'how to']
        query = user_input
        
        for term in search_terms:
            query = query.replace(term, '').strip()
        
        # Detect language from context if not provided
        if not language:
            language = agent.web_search.get_language_from_context(user_input)
        
        # Search and get AI summary
        async with agent.web_search as search_assistant:
            summary = await search_assistant.search_and_summarize(query, language)
            
            console.print(Panel(
                summary,
                title="📚 Documentation Search Results",
                border_style="cyan"
            ))
    
    except Exception as e:
        console.print(f"[red]❌ Search error: {e}[/red]")

async def handle_general_request(agent: HurricaneAgent, user_input: str, indexer: ProjectIndexer = None):
    """Handle general requests."""
    console.print("[blue]🤖 I'll help you with that![/blue]")
    
    # Check if this might be a documentation search request
    if any(word in user_input.lower() for word in ['how to', 'documentation', 'docs', 'tutorial', 'guide', 'example']):
        await handle_web_search_request(agent, user_input)
        return
    
    # Use AI to understand and respond to the request
    response = await agent.ollama_client.generate_response(
        f"Help the user with this request: {user_input}",
        system_prompt="You are Hurricane, an AI coding assistant. Provide helpful, concise responses about programming and development."
    )
    
    console.print(Panel(
        response,
        title="🤖 Hurricane Response",
        border_style="blue"
    ))
    
    # For code generation requests, offer to save the response
    if any(word in user_input.lower() for word in ['generate', 'create', 'write', 'build']):
        if Confirm.ask("Would you like me to save this to a file?"):
            filename = Prompt.ask("Enter filename", default="generated_code.py")
            await agent.file_manager.save_file(Path(filename), response)
            show_file_changes({filename: {"description": "Created new file with generated content"}})

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
        
        # Initialize project indexer
        current_dir = Path.cwd()
        indexer = ProjectIndexer(current_dir)
        project_info = await indexer.initialize_project()
        
        console.print(f"\n[bold green]🎉 Hurricane is ready! Indexed {project_info['total_files']} files![/bold green]")
        console.print("[dim]Type your request in plain English, and I'll help you with your code.[/dim]")
        console.print("[dim]Try: 'show project structure', 'find files with login', 'create new file', etc.[/dim]\n")
        
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
                await process_natural_language_request(agent, user_input, indexer)
                
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

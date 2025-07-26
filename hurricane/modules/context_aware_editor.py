"""
Context-aware file editor for Hurricane AI Agent.
Provides intelligent file editing with project context, progress tracking, and web search integration.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import Config
from ..core.ollama_client import OllamaClient
from .project_planner import ProjectPlanner, FileEditProgress
from .web_search import WebSearchAssistant

console = Console()


@dataclass
class EditSuggestion:
    """Represents an AI-generated edit suggestion."""
    line_number: int
    original_code: str
    suggested_code: str
    reason: str
    confidence: float
    requires_research: bool = False
    research_query: str = ""


@dataclass
class EditContext:
    """Context information for file editing."""
    file_path: str
    project_goal: str
    current_task: str
    related_files: List[str]
    recent_changes: List[str]
    tech_stack: List[str]
    edit_history: List[Dict[str, Any]]
    todo_items: List[str]


class ContextAwareEditor:
    """Intelligent file editor with project context and web search integration."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config, project_planner: ProjectPlanner):
        self.ollama_client = ollama_client
        self.config = config
        self.project_planner = project_planner
        self.web_search = WebSearchAssistant(ollama_client, config)
        
        # Edit session tracking
        self.current_session = {
            "file_path": None,
            "start_time": None,
            "changes_made": [],
            "research_performed": [],
            "context_used": {}
        }
    
    async def start_editing_session(self, file_path: str, task_description: str = None) -> EditContext:
        """Start a context-aware editing session."""
        file_path = str(Path(file_path).resolve())
        console.print(f"[bold blue]📝 Starting context-aware editing session for {Path(file_path).name}[/bold blue]")
        
        # Initialize session
        self.current_session = {
            "file_path": file_path,
            "start_time": datetime.now().isoformat(),
            "changes_made": [],
            "research_performed": [],
            "context_used": {}
        }
        
        # Get project context
        context = self.project_planner.get_context_for_file(file_path)
        
        # Create edit context
        edit_context = EditContext(
            file_path=file_path,
            project_goal=context["project_goal"],
            current_task=task_description or "File editing",
            related_files=context["related_files"],
            recent_changes=context["recent_changes"],
            tech_stack=context["tech_stack"],
            edit_history=[],
            todo_items=[]
        )
        
        # Show context information
        await self._show_editing_context(edit_context)
        
        # Track editing start
        self.project_planner.track_file_edit(
            file_path, 
            [f"Started editing session: {task_description or 'General editing'}"], 
            "editing"
        )
        
        return edit_context
    
    async def _show_editing_context(self, context: EditContext):
        """Display editing context to the user."""
        context_info = f"""[bold]Project Goal:[/bold] {context.project_goal}
[bold]Current Task:[/bold] {context.current_task}
[bold]Tech Stack:[/bold] {', '.join(context.tech_stack)}"""
        
        if context.related_files:
            context_info += f"\n[bold]Related Files:[/bold] {', '.join(context.related_files[:3])}"
        
        if context.recent_changes:
            recent = [change["changes"][0] if change["changes"] else "No details" 
                     for change in context.recent_changes[-2:]]
            context_info += f"\n[bold]Recent Changes:[/bold] {', '.join(recent)}"
        
        console.print(Panel(
            context_info,
            title="🎯 Editing Context",
            border_style="cyan"
        ))
    
    async def analyze_file_for_editing(self, file_path: str, edit_goal: str = None) -> List[EditSuggestion]:
        """Analyze file and suggest context-aware edits."""
        console.print("[blue]🔍 Analyzing file with project context...[/blue]")
        
        try:
            # Read file content
            file_content = Path(file_path).read_text(encoding='utf-8')
            
            # Get project context
            context = self.project_planner.get_context_for_file(file_path)
            
            # Prepare analysis prompt
            prompt = f"""Analyze this file and suggest improvements based on project context:

File: {Path(file_path).name}
Project Goal: {context['project_goal']}
Tech Stack: {', '.join(context['tech_stack'])}
Edit Goal: {edit_goal or 'General improvements'}

File Content:
{file_content[:2000]}  # First 2000 characters

Suggest 3-5 specific improvements with:
1. Line numbers (approximate)
2. Current code snippet
3. Improved code
4. Reason for change
5. Whether web research would help (true/false)
6. Research query if needed

Focus on improvements that align with the project goal and current task."""
            
            response = await self.ollama_client.generate_response(
                prompt,
                system_prompt="You are a senior developer providing context-aware code improvements. Be specific and practical."
            )
            
            # Parse suggestions (simplified - in production would use structured output)
            suggestions = await self._parse_edit_suggestions(response, file_content)
            
            # Perform web research for suggestions that need it
            for suggestion in suggestions:
                if suggestion.requires_research and suggestion.research_query:
                    await self._research_for_suggestion(suggestion, context['tech_stack'])
            
            return suggestions
            
        except Exception as e:
            console.print(f"[red]❌ Error analyzing file: {e}[/red]")
            return []
    
    async def _parse_edit_suggestions(self, ai_response: str, file_content: str) -> List[EditSuggestion]:
        """Parse AI response into structured edit suggestions."""
        suggestions = []
        lines = file_content.split('\n')
        
        # Simple parsing - in production would use more sophisticated parsing
        suggestion_blocks = ai_response.split('\n\n')
        
        for i, block in enumerate(suggestion_blocks[:5]):  # Limit to 5 suggestions
            if any(keyword in block.lower() for keyword in ['line', 'improve', 'change', 'add', 'fix']):
                # Extract line number (simple heuristic)
                line_num = 1
                for word in block.split():
                    if word.isdigit() and int(word) <= len(lines):
                        line_num = int(word)
                        break
                
                # Create suggestion
                suggestion = EditSuggestion(
                    line_number=line_num,
                    original_code=lines[line_num-1] if line_num <= len(lines) else "",
                    suggested_code="# AI suggested improvement",
                    reason=block[:100] + "..." if len(block) > 100 else block,
                    confidence=0.8,
                    requires_research="research" in block.lower() or "documentation" in block.lower(),
                    research_query=self._extract_research_query(block)
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _extract_research_query(self, text: str) -> str:
        """Extract research query from suggestion text."""
        # Simple extraction - look for patterns
        if "best practice" in text.lower():
            return "best practices"
        elif "documentation" in text.lower():
            return "documentation"
        elif "example" in text.lower():
            return "code examples"
        else:
            return "implementation guide"
    
    async def _research_for_suggestion(self, suggestion: EditSuggestion, tech_stack: List[str]):
        """Perform web research to enhance a suggestion."""
        try:
            # Determine primary language for research
            primary_lang = tech_stack[0] if tech_stack else "general"
            
            # Construct research query
            query = f"{suggestion.research_query} {primary_lang}"
            
            console.print(f"[blue]🔍 Researching: {query}[/blue]")
            
            # Perform web search
            async with self.web_search as search_assistant:
                research_results = await search_assistant.search_and_summarize(query, primary_lang)
                
                # Enhance suggestion with research
                if research_results and len(research_results) > 50:
                    suggestion.reason += f"\n\n📚 Research findings: {research_results[:200]}..."
                    suggestion.confidence = min(0.95, suggestion.confidence + 0.1)
                    
                    # Track research
                    self.current_session["research_performed"].append({
                        "query": query,
                        "results_summary": research_results[:100],
                        "timestamp": datetime.now().isoformat()
                    })
        
        except Exception as e:
            console.print(f"[yellow]⚠️ Research failed for suggestion: {e}[/yellow]")
    
    async def apply_edit_with_context(self, file_path: str, edit_description: str, 
                                    line_number: int = None, context_aware: bool = True) -> bool:
        """Apply an edit with full project context awareness."""
        console.print(f"[blue]✏️ Applying context-aware edit to {Path(file_path).name}[/blue]")
        
        try:
            # Read current file
            file_content = Path(file_path).read_text(encoding='utf-8')
            lines = file_content.split('\n')
            
            if context_aware:
                # Get project context
                context = self.project_planner.get_context_for_file(file_path)
                
                # Generate context-aware edit
                prompt = f"""Apply this edit with full project context:

File: {Path(file_path).name}
Project Goal: {context['project_goal']}
Tech Stack: {', '.join(context['tech_stack'])}
Edit Request: {edit_description}

Current file content:
{file_content}

Apply the requested edit while maintaining:
1. Consistency with project goals
2. Coding standards for {context['tech_stack']}
3. Integration with related files: {', '.join(context['related_files'][:3])}

Return the complete modified file content."""
                
                # Check if we need research
                if any(keyword in edit_description.lower() for keyword in ['best practice', 'documentation', 'example', 'how to']):
                    research_query = f"{edit_description} {context['tech_stack'][0] if context['tech_stack'] else ''}"
                    console.print(f"[blue]🔍 Researching best practices: {research_query}[/blue]")
                    
                    async with self.web_search as search_assistant:
                        research = await search_assistant.search_and_summarize(research_query, context['tech_stack'][0] if context['tech_stack'] else None)
                        if research:
                            prompt += f"\n\nResearch findings:\n{research[:500]}"
                
                # Generate the edit
                modified_content = await self.ollama_client.generate_response(
                    prompt,
                    system_prompt="You are an expert developer. Apply edits while maintaining code quality and project consistency. Return only the complete file content."
                )
                
                # Clean up the response (remove any markdown formatting)
                if "```" in modified_content:
                    # Extract code from markdown blocks
                    import re
                    code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', modified_content, re.DOTALL)
                    if code_blocks:
                        modified_content = code_blocks[0]
            
            else:
                # Simple edit without full context
                modified_content = await self._apply_simple_edit(file_content, edit_description, line_number)
            
            # Show diff preview
            await self._show_edit_preview(file_content, modified_content, Path(file_path).name)
            
            # Confirm and apply
            if Confirm.ask("Apply this edit?"):
                # Backup original
                backup_path = Path(file_path).with_suffix(Path(file_path).suffix + '.backup')
                Path(file_path).write_text(file_content, encoding='utf-8')  # Write to backup
                backup_path.write_text(file_content, encoding='utf-8')
                
                # Apply edit
                Path(file_path).write_text(modified_content, encoding='utf-8')
                
                # Track the edit
                self.project_planner.track_file_edit(
                    file_path,
                    [edit_description],
                    "editing"
                )
                
                # Update session
                self.current_session["changes_made"].append({
                    "description": edit_description,
                    "timestamp": datetime.now().isoformat(),
                    "line_number": line_number
                })
                
                console.print(f"[green]✅ Edit applied successfully! Backup saved to {backup_path.name}[/green]")
                return True
            else:
                console.print("[yellow]Edit cancelled[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Error applying edit: {e}[/red]")
            return False
    
    async def _apply_simple_edit(self, content: str, edit_description: str, line_number: int = None) -> str:
        """Apply a simple edit without full context."""
        prompt = f"""Apply this edit to the code:

Edit: {edit_description}
Line: {line_number or 'Not specified'}

Code:
{content}

Return the modified code."""
        
        return await self.ollama_client.generate_response(
            prompt,
            system_prompt="Apply the requested code edit. Return only the modified code."
        )
    
    async def _show_edit_preview(self, original: str, modified: str, filename: str):
        """Show a preview of the changes."""
        console.print(f"\n[bold yellow]📋 Edit Preview for {filename}:[/bold yellow]")
        
        # Simple diff display (in production would use proper diff library)
        original_lines = original.split('\n')
        modified_lines = modified.split('\n')
        
        # Show first few differences
        differences = 0
        for i, (orig, mod) in enumerate(zip(original_lines, modified_lines)):
            if orig != mod and differences < 5:
                console.print(f"[red]- Line {i+1}: {orig}[/red]")
                console.print(f"[green]+ Line {i+1}: {mod}[/green]")
                differences += 1
        
        if len(modified_lines) != len(original_lines):
            console.print(f"[blue]Lines changed: {len(original_lines)} → {len(modified_lines)}[/blue]")
    
    async def suggest_next_edit(self, file_path: str) -> Optional[str]:
        """Suggest the next logical edit based on context."""
        try:
            # Get current context
            context = self.project_planner.get_context_for_file(file_path)
            
            # Get file content
            file_content = Path(file_path).read_text(encoding='utf-8')
            
            prompt = f"""Based on the current state and project context, suggest the next logical edit:

File: {Path(file_path).name}
Project Goal: {context['project_goal']}
Recent Changes: {', '.join([change['changes'][0] for change in context['recent_changes'][-2:] if change['changes']])}

Current file content (first 1000 chars):
{file_content[:1000]}

What should be the next logical edit to move towards the project goal?
Provide a specific, actionable suggestion."""
            
            suggestion = await self.ollama_client.generate_response(
                prompt,
                system_prompt="Suggest the next logical edit based on project context and current file state."
            )
            
            return suggestion.strip()
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not suggest next edit: {e}[/yellow]")
            return None
    
    def show_editing_progress(self):
        """Show current editing session progress."""
        if not self.current_session["file_path"]:
            console.print("[yellow]No active editing session[/yellow]")
            return
        
        file_name = Path(self.current_session["file_path"]).name
        start_time = datetime.fromisoformat(self.current_session["start_time"])
        duration = datetime.now() - start_time
        
        console.print(Panel(
            f"[bold]File:[/bold] {file_name}\n"
            f"[bold]Duration:[/bold] {duration.total_seconds()/60:.1f} minutes\n"
            f"[bold]Changes Made:[/bold] {len(self.current_session['changes_made'])}\n"
            f"[bold]Research Performed:[/bold] {len(self.current_session['research_performed'])}",
            title="📊 Editing Session Progress",
            border_style="green"
        ))
        
        # Show recent changes
        if self.current_session["changes_made"]:
            console.print("\n[bold cyan]Recent Changes:[/bold cyan]")
            for change in self.current_session["changes_made"][-5:]:
                timestamp = datetime.fromisoformat(change["timestamp"]).strftime("%H:%M")
                console.print(f"  • [dim]{timestamp}[/dim] {change['description']}")
        
        # Show research performed
        if self.current_session["research_performed"]:
            console.print("\n[bold blue]Research Performed:[/bold blue]")
            for research in self.current_session["research_performed"][-3:]:
                console.print(f"  • {research['query']}: {research['results_summary'][:50]}...")
    
    async def finish_editing_session(self, completion_notes: str = None):
        """Finish the current editing session."""
        if not self.current_session["file_path"]:
            console.print("[yellow]No active editing session to finish[/yellow]")
            return
        
        file_path = self.current_session["file_path"]
        
        # Calculate session summary
        start_time = datetime.fromisoformat(self.current_session["start_time"])
        duration = datetime.now() - start_time
        changes_count = len(self.current_session["changes_made"])
        research_count = len(self.current_session["research_performed"])
        
        # Update project planner
        session_summary = f"Completed editing session: {changes_count} changes, {research_count} research queries, {duration.total_seconds()/60:.1f} minutes"
        if completion_notes:
            session_summary += f". Notes: {completion_notes}"
        
        self.project_planner.track_file_edit(
            file_path,
            [session_summary],
            "complete"
        )
        
        # Show session summary
        console.print(Panel(
            f"[bold green]Session completed![/bold green]\n\n"
            f"[bold]File:[/bold] {Path(file_path).name}\n"
            f"[bold]Duration:[/bold] {duration.total_seconds()/60:.1f} minutes\n"
            f"[bold]Changes:[/bold] {changes_count}\n"
            f"[bold]Research:[/bold] {research_count}\n"
            f"[bold]Notes:[/bold] {completion_notes or 'None'}",
            title="🎉 Editing Session Complete",
            border_style="green"
        ))
        
        # Reset session
        self.current_session = {
            "file_path": None,
            "start_time": None,
            "changes_made": [],
            "research_performed": [],
            "context_used": {}
        }
    
    async def get_editing_suggestions_for_task(self, task_description: str) -> List[str]:
        """Get file editing suggestions for a specific task."""
        try:
            # Get project context
            context = self.project_planner.project_context
            
            prompt = f"""Suggest specific files to edit for this task:

Task: {task_description}
Project: {context.project_name}
Goal: {context.current_goal}
Tech Stack: {', '.join(context.tech_stack)}
Current Files: {', '.join(context.current_files[:10])}

Suggest 3-5 specific files that should be edited to complete this task, with brief reasons."""
            
            response = await self.ollama_client.generate_response(
                prompt,
                system_prompt="Suggest specific files to edit based on the task and project context."
            )
            
            # Parse suggestions
            suggestions = []
            for line in response.split('\n'):
                if line.strip() and ('.' in line or '/' in line):  # Likely a file path
                    suggestions.append(line.strip())
            
            return suggestions[:5]
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not generate editing suggestions: {e}[/yellow]")
            return []

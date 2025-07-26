"""
Enhanced context awareness and memory system for Hurricane AI Agent.
Provides conversation memory, code understanding, and pattern learning capabilities.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import re

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


@dataclass
class ConversationMemory:
    """Represents a conversation memory entry."""
    id: str
    timestamp: str
    user_input: str
    agent_response: str
    context: Dict[str, Any]
    intent: str
    entities: List[str]
    sentiment: str
    importance_score: float
    tags: List[str]


@dataclass
class CodeContext:
    """Represents semantic understanding of code."""
    file_path: str
    function_name: str
    class_name: Optional[str]
    purpose: str
    dependencies: List[str]
    complexity_score: int
    last_modified: str
    usage_patterns: List[str]
    relationships: Dict[str, List[str]]


@dataclass
class UserPattern:
    """Represents learned user behavior patterns."""
    pattern_id: str
    pattern_type: str  # coding_style, workflow, preference
    description: str
    frequency: int
    confidence_score: float
    examples: List[str]
    context_conditions: List[str]
    last_observed: str


class EnhancedMemory:
    """Enhanced memory system with conversation history and code understanding."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config, project_root: Path):
        self.ollama_client = ollama_client
        self.config = config
        self.project_root = Path(project_root)
        
        # Memory storage
        self.hurricane_dir = self.project_root / ".hurricane"
        self.hurricane_dir.mkdir(exist_ok=True)
        
        self.conversation_file = self.hurricane_dir / "conversation_memory.json"
        self.code_context_file = self.hurricane_dir / "code_context.json"
        self.user_patterns_file = self.hurricane_dir / "user_patterns.json"
        self.semantic_index_file = self.hurricane_dir / "semantic_index.json"
        
        # Load existing memories
        self.conversation_history = self._load_conversation_history()
        self.code_contexts = self._load_code_contexts()
        self.user_patterns = self._load_user_patterns()
        self.semantic_index = self._load_semantic_index()
        
        # Working memory for current session
        self.current_session = {
            "start_time": datetime.now().isoformat(),
            "interactions": [],
            "active_context": {},
            "temporary_patterns": []
        }
    
    def _load_conversation_history(self) -> List[ConversationMemory]:
        """Load conversation history from storage."""
        if self.conversation_file.exists():
            try:
                with open(self.conversation_file, 'r') as f:
                    data = json.load(f)
                return [ConversationMemory(**item) for item in data]
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load conversation history: {e}[/yellow]")
        return []
    
    def _load_code_contexts(self) -> Dict[str, CodeContext]:
        """Load code context understanding."""
        if self.code_context_file.exists():
            try:
                with open(self.code_context_file, 'r') as f:
                    data = json.load(f)
                return {path: CodeContext(**context) for path, context in data.items()}
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load code contexts: {e}[/yellow]")
        return {}
    
    def _load_user_patterns(self) -> Dict[str, UserPattern]:
        """Load learned user patterns."""
        if self.user_patterns_file.exists():
            try:
                with open(self.user_patterns_file, 'r') as f:
                    data = json.load(f)
                return {pid: UserPattern(**pattern) for pid, pattern in data.items()}
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load user patterns: {e}[/yellow]")
        return {}
    
    def _load_semantic_index(self) -> Dict[str, Any]:
        """Load semantic index for fast retrieval."""
        if self.semantic_index_file.exists():
            try:
                with open(self.semantic_index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load semantic index: {e}[/yellow]")
        return {
            "keywords": defaultdict(list),
            "concepts": defaultdict(list),
            "file_relationships": defaultdict(list),
            "function_calls": defaultdict(list)
        }
    
    def _save_conversation_history(self):
        """Save conversation history to storage."""
        try:
            data = [asdict(memory) for memory in self.conversation_history]
            with open(self.conversation_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving conversation history: {e}[/red]")
    
    def _save_code_contexts(self):
        """Save code contexts to storage."""
        try:
            data = {path: asdict(context) for path, context in self.code_contexts.items()}
            with open(self.code_context_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving code contexts: {e}[/red]")
    
    def _save_user_patterns(self):
        """Save user patterns to storage."""
        try:
            data = {pid: asdict(pattern) for pid, pattern in self.user_patterns.items()}
            with open(self.user_patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving user patterns: {e}[/red]")
    
    def _save_semantic_index(self):
        """Save semantic index to storage."""
        try:
            data = {
                "keywords": dict(self.semantic_index["keywords"]),
                "concepts": dict(self.semantic_index["concepts"]),
                "file_relationships": dict(self.semantic_index["file_relationships"]),
                "function_calls": dict(self.semantic_index["function_calls"])
            }
            with open(self.semantic_index_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving semantic index: {e}[/red]")
    
    async def record_interaction(self, user_input: str, agent_response: str, 
                               context: Dict[str, Any] = None) -> str:
        """Record a user-agent interaction with context analysis."""
        interaction_id = hashlib.md5(
            f"{user_input}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Analyze the interaction
        intent = await self._analyze_intent(user_input)
        entities = await self._extract_entities(user_input)
        sentiment = await self._analyze_sentiment(user_input)
        importance = self._calculate_importance(user_input, agent_response, context or {})
        tags = self._generate_tags(user_input, intent, entities)
        
        memory = ConversationMemory(
            id=interaction_id,
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            agent_response=agent_response,
            context=context or {},
            intent=intent,
            entities=entities,
            sentiment=sentiment,
            importance_score=importance,
            tags=tags
        )
        
        self.conversation_history.append(memory)
        self.current_session["interactions"].append(interaction_id)
        
        # Update patterns based on this interaction
        await self._update_user_patterns(memory)
        
        # Maintain memory size (keep last 1000 interactions)
        if len(self.conversation_history) > 1000:
            self.conversation_history = self.conversation_history[-1000:]
        
        self._save_conversation_history()
        return interaction_id
    
    async def _analyze_intent(self, user_input: str) -> str:
        """Analyze user intent from input."""
        intent_patterns = {
            "code_generation": [r"create", r"generate", r"write", r"build"],
            "debugging": [r"debug", r"fix", r"error", r"bug", r"issue"],
            "explanation": [r"explain", r"what", r"how", r"why", r"understand"],
            "refactoring": [r"refactor", r"improve", r"optimize", r"clean"],
            "documentation": [r"document", r"readme", r"docs", r"comment"],
            "testing": [r"test", r"unit test", r"integration", r"coverage"],
            "navigation": [r"find", r"search", r"locate", r"show", r"list"],
            "planning": [r"plan", r"roadmap", r"strategy", r"approach"]
        }
        
        user_lower = user_input.lower()
        for intent, patterns in intent_patterns.items():
            if any(re.search(pattern, user_lower) for pattern in patterns):
                return intent
        
        return "general"
    
    async def _extract_entities(self, user_input: str) -> List[str]:
        """Extract entities (file names, function names, etc.) from input."""
        entities = []
        
        # Extract file paths
        file_patterns = [
            r'[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z]{1,4}',
            r'[a-zA-Z_][a-zA-Z0-9_/]*\.py',
            r'[a-zA-Z_][a-zA-Z0-9_/]*\.js',
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, user_input)
            entities.extend(matches)
        
        return list(set(entities))
    
    async def _analyze_sentiment(self, user_input: str) -> str:
        """Analyze sentiment of user input."""
        positive_words = ['good', 'great', 'excellent', 'perfect', 'awesome']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'frustrated']
        
        user_lower = user_input.lower()
        positive_count = sum(1 for word in positive_words if word in user_lower)
        negative_count = sum(1 for word in negative_words if word in user_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_importance(self, user_input: str, agent_response: str, context: Dict[str, Any]) -> float:
        """Calculate importance score for the interaction."""
        score = 0.5
        
        if len(user_input) > 100:
            score += 0.1
        if context.get('file_path'):
            score += 0.2
        if context.get('error'):
            score += 0.3
        if context.get('goal_id'):
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_tags(self, user_input: str, intent: str, entities: List[str]) -> List[str]:
        """Generate tags for the interaction."""
        tags = [intent]
        
        for entity in entities[:5]:
            if '.' in entity:
                tags.append(f"file:{entity}")
            elif entity[0].isupper():
                tags.append(f"class:{entity}")
            else:
                tags.append(f"function:{entity}")
        
        return list(set(tags))
    
    async def _update_user_patterns(self, memory: ConversationMemory):
        """Update user patterns based on new interaction."""
        # Simple pattern detection for workflow
        if len(self.current_session["interactions"]) >= 3:
            recent_intents = [
                self._get_memory_by_id(iid).intent 
                for iid in self.current_session["interactions"][-3:]
                if self._get_memory_by_id(iid)
            ]
            
            if len(set(recent_intents)) == len(recent_intents):
                pattern_id = f"workflow_{hashlib.md5(''.join(recent_intents).encode()).hexdigest()[:8]}"
                
                if pattern_id in self.user_patterns:
                    self.user_patterns[pattern_id].frequency += 1
                    self.user_patterns[pattern_id].last_observed = datetime.now().isoformat()
                else:
                    self.user_patterns[pattern_id] = UserPattern(
                        pattern_id=pattern_id,
                        pattern_type="workflow",
                        description=f"User workflow: {' -> '.join(recent_intents)}",
                        frequency=1,
                        confidence_score=0.3,
                        examples=[memory.user_input],
                        context_conditions=[f"intent_sequence:{','.join(recent_intents)}"],
                        last_observed=datetime.now().isoformat()
                    )
        
        self._save_user_patterns()
    
    def _get_memory_by_id(self, memory_id: str) -> Optional[ConversationMemory]:
        """Get memory by ID."""
        for memory in self.conversation_history:
            if memory.id == memory_id:
                return memory
        return None
    
    def retrieve_relevant_context(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context based on query."""
        relevant_contexts = []
        
        query_lower = query.lower()
        for memory in reversed(self.conversation_history[-50:]):
            relevance_score = 0
            
            if any(term in memory.user_input.lower() for term in query_lower.split()):
                relevance_score += 0.5
            
            if any(term in ' '.join(memory.tags).lower() for term in query_lower.split()):
                relevance_score += 0.3
            
            time_diff = datetime.now() - datetime.fromisoformat(memory.timestamp)
            if time_diff.days < 1:
                relevance_score += 0.2
            
            if relevance_score > 0.3:
                relevant_contexts.append({
                    "type": "conversation",
                    "content": memory.user_input,
                    "response": memory.agent_response,
                    "timestamp": memory.timestamp,
                    "relevance": relevance_score,
                    "tags": memory.tags
                })
        
        relevant_contexts.sort(key=lambda x: x["relevance"], reverse=True)
        return relevant_contexts[:limit]
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get learned user preferences and patterns."""
        preferences = {
            "coding_style": {},
            "workflow_patterns": [],
            "frequent_intents": {},
            "preferred_tools": []
        }
        
        # Analyze workflow patterns
        workflow_patterns = [p for p in self.user_patterns.values() if p.pattern_type == "workflow"]
        for pattern in workflow_patterns:
            if pattern.frequency > 2:
                preferences["workflow_patterns"].append({
                    "description": pattern.description,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence_score
                })
        
        # Analyze frequent intents
        intent_counts = defaultdict(int)
        for memory in self.conversation_history[-100:]:
            intent_counts[memory.intent] += 1
        
        preferences["frequent_intents"] = dict(intent_counts)
        
        return preferences
    
    def show_memory_status(self):
        """Display memory system status."""
        console.print(Panel.fit(
            "[bold blue]🧠 Enhanced Memory Status[/bold blue]",
            border_style="blue"
        ))
        
        stats_table = Table(title="📊 Memory Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green")
        
        stats_table.add_row("Conversation History", str(len(self.conversation_history)))
        stats_table.add_row("Code Contexts", str(len(self.code_contexts)))
        stats_table.add_row("User Patterns", str(len(self.user_patterns)))
        stats_table.add_row("Current Session", str(len(self.current_session["interactions"])))
        
        console.print(stats_table)

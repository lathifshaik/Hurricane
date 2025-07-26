"""
Ollama client for Hurricane AI Agent.
"""

import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, List
import ollama
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config

console = Console()


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = ollama.Client(host=config.ollama.host)
    
    async def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """Generate a response from Ollama."""
        model = model or self.config.ollama.model
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            if stream:
                return await self._stream_response(model, messages)
            else:
                response = self.client.chat(
                    model=model,
                    messages=messages,
                    options={
                        "temperature": self.config.ollama.temperature,
                        "num_predict": self.config.ollama.max_tokens,
                    }
                )
                return response['message']['content']
        except Exception as e:
            console.print(f"[red]Error generating response: {e}[/red]")
            raise
    
    async def _stream_response(self, model: str, messages: List[Dict]) -> str:
        """Stream response from Ollama with progress indicator."""
        full_response = ""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating response...", total=None)
            
            try:
                stream = self.client.chat(
                    model=model,
                    messages=messages,
                    stream=True,
                    options={
                        "temperature": self.config.ollama.temperature,
                        "num_predict": self.config.ollama.max_tokens,
                    }
                )
                
                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        full_response += content
                        progress.update(task, description=f"Generated {len(full_response)} characters...")
                
                progress.update(task, description="✅ Response generated!")
                
            except Exception as e:
                progress.update(task, description=f"❌ Error: {e}")
                raise
        
        return full_response
    
    def list_models(self) -> List[str]:
        """List available models."""
        try:
            models = self.client.list()
            return [model['name'] for model in models['models']]
        except Exception as e:
            console.print(f"[red]Error listing models: {e}[/red]")
            return []
    
    def check_model_availability(self, model: str) -> bool:
        """Check if a model is available."""
        available_models = self.list_models()
        return model in available_models
    
    def pull_model(self, model: str) -> bool:
        """Pull a model if not available."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Pulling model {model}...", total=None)
                
                self.client.pull(model)
                progress.update(task, description=f"✅ Model {model} pulled successfully!")
                return True
                
        except Exception as e:
            console.print(f"[red]Error pulling model {model}: {e}[/red]")
            return False
    
    async def generate_code(
        self, 
        description: str, 
        language: str = "python",
        context: Optional[str] = None
    ) -> str:
        """Generate code based on description."""
        system_prompt = f"""You are Hurricane, an expert {language} developer. 
Generate clean, well-documented, and production-ready code.
Follow best practices and include appropriate error handling.
Only return the code, no explanations unless specifically requested."""
        
        prompt = f"Generate {language} code for: {description}"
        if context:
            prompt += f"\n\nContext: {context}"
        
        return await self.generate_response(prompt, system_prompt=system_prompt)
    
    async def generate_documentation(
        self, 
        code: str, 
        doc_type: str = "readme",
        format_type: str = "markdown"
    ) -> str:
        """Generate documentation for code."""
        system_prompt = f"""You are Hurricane, a technical documentation expert.
Generate comprehensive, clear, and well-structured {format_type} documentation.
Focus on usability and include examples where appropriate."""
        
        prompt = f"Generate {doc_type} documentation in {format_type} format for this code:\n\n{code}"
        
        return await self.generate_response(prompt, system_prompt=system_prompt)
    
    async def debug_code(self, code: str, error: Optional[str] = None) -> str:
        """Debug code and provide fixes."""
        system_prompt = """You are Hurricane, an expert debugger.
Analyze the code, identify issues, and provide clear fixes.
Explain what was wrong and how to prevent similar issues."""
        
        prompt = f"Debug this code:\n\n{code}"
        if error:
            prompt += f"\n\nError message: {error}"
        
        return await self.generate_response(prompt, system_prompt=system_prompt)

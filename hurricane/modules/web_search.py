"""
Web search module for Hurricane AI Agent.
Enables AI to search for documentation and code examples.
"""

import aiohttp
import asyncio
import json
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


class WebSearchAssistant:
    """AI-powered web search for documentation and code examples."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config):
        self.ollama_client = ollama_client
        self.config = config
        self.session = None
        
        # Popular documentation sites for different languages/frameworks
        self.doc_sites = {
            "python": [
                "docs.python.org",
                "pypi.org",
                "realpython.com",
                "stackoverflow.com"
            ],
            "javascript": [
                "developer.mozilla.org",
                "nodejs.org",
                "npmjs.com",
                "stackoverflow.com"
            ],
            "typescript": [
                "typescriptlang.org",
                "developer.mozilla.org",
                "stackoverflow.com"
            ],
            "react": [
                "react.dev",
                "reactjs.org",
                "developer.mozilla.org",
                "stackoverflow.com"
            ],
            "vue": [
                "vuejs.org",
                "nuxtjs.org",
                "stackoverflow.com"
            ],
            "go": [
                "golang.org",
                "pkg.go.dev",
                "gobyexample.com",
                "stackoverflow.com"
            ],
            "rust": [
                "doc.rust-lang.org",
                "crates.io",
                "rust-lang.github.io",
                "stackoverflow.com"
            ],
            "java": [
                "docs.oracle.com",
                "spring.io",
                "maven.apache.org",
                "stackoverflow.com"
            ],
            "cpp": [
                "cppreference.com",
                "isocpp.org",
                "stackoverflow.com"
            ],
            "csharp": [
                "docs.microsoft.com",
                "dotnet.microsoft.com",
                "stackoverflow.com"
            ],
            "php": [
                "php.net",
                "laravel.com",
                "symfony.com",
                "stackoverflow.com"
            ],
            "ruby": [
                "ruby-doc.org",
                "rubyonrails.org",
                "rubygems.org",
                "stackoverflow.com"
            ]
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Hurricane AI Agent - Documentation Search Bot'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def search_documentation(self, query: str, language: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for documentation and code examples."""
        console.print(f"[blue]🔍 Searching documentation for: {query}[/blue]")
        
        try:
            # Determine search sites based on language
            search_sites = []
            if language and language.lower() in self.doc_sites:
                search_sites = self.doc_sites[language.lower()]
            else:
                # Use general programming sites
                search_sites = ["stackoverflow.com", "github.com", "developer.mozilla.org"]
            
            # Create search queries for different sites
            search_results = []
            
            for site in search_sites[:3]:  # Limit to 3 sites to avoid rate limiting
                site_results = await self._search_site(query, site, limit=2)
                search_results.extend(site_results)
                
                if len(search_results) >= limit:
                    break
            
            # Filter and rank results
            filtered_results = await self._filter_and_rank_results(search_results, query, language)
            
            return filtered_results[:limit]
            
        except Exception as e:
            console.print(f"[red]❌ Error searching documentation: {e}[/red]")
            return []
    
    async def _search_site(self, query: str, site: str, limit: int = 2) -> List[Dict[str, Any]]:
        """Search a specific site using DuckDuckGo."""
        try:
            # Use DuckDuckGo for site-specific search
            search_query = f"site:{site} {query}"
            encoded_query = quote_plus(search_query)
            
            # DuckDuckGo instant answer API (limited but free)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    
                    # Parse DuckDuckGo results
                    if 'RelatedTopics' in data:
                        for topic in data['RelatedTopics'][:limit]:
                            if isinstance(topic, dict) and 'FirstURL' in topic:
                                results.append({
                                    'title': topic.get('Text', '').split(' - ')[0],
                                    'url': topic['FirstURL'],
                                    'snippet': topic.get('Text', ''),
                                    'site': site
                                })
                    
                    return results
            
            return []
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not search {site}: {e}[/yellow]")
            return []
    
    async def _filter_and_rank_results(self, results: List[Dict], query: str, language: str = None) -> List[Dict]:
        """Filter and rank search results by relevance."""
        if not results:
            return []
        
        try:
            # Score results based on relevance
            scored_results = []
            
            for result in results:
                score = 0
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                url = result.get('url', '').lower()
                
                # Score based on query terms
                query_terms = query.lower().split()
                for term in query_terms:
                    if term in title:
                        score += 3
                    if term in snippet:
                        score += 2
                    if term in url:
                        score += 1
                
                # Boost official documentation sites
                if any(official in url for official in ['docs.', 'doc.', 'documentation']):
                    score += 5
                
                # Boost language-specific sites
                if language and language.lower() in url:
                    score += 3
                
                # Penalize very short snippets
                if len(snippet) < 50:
                    score -= 2
                
                result['relevance_score'] = score
                scored_results.append(result)
            
            # Sort by score and return
            scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return scored_results
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Error ranking results: {e}[/yellow]")
            return results
    
    async def get_page_content(self, url: str, max_length: int = 2000) -> str:
        """Fetch and extract main content from a webpage."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Parse HTML and extract main content
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "header", "footer"]):
                        script.decompose()
                    
                    # Try to find main content areas
                    content_selectors = [
                        'main', 'article', '.content', '#content', 
                        '.documentation', '.docs', '.post-content'
                    ]
                    
                    content = ""
                    for selector in content_selectors:
                        elements = soup.select(selector)
                        if elements:
                            content = elements[0].get_text(strip=True)
                            break
                    
                    # Fallback to body content
                    if not content:
                        body = soup.find('body')
                        if body:
                            content = body.get_text(strip=True)
                    
                    # Clean and truncate content
                    content = ' '.join(content.split())  # Normalize whitespace
                    if len(content) > max_length:
                        content = content[:max_length] + "..."
                    
                    return content
                
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not fetch content from {url}: {e}[/yellow]")
        
        return ""
    
    async def search_and_summarize(self, query: str, language: str = None) -> str:
        """Search for documentation and provide an AI summary."""
        console.print(f"[blue]🤖 Searching and summarizing documentation for: {query}[/blue]")
        
        try:
            # Search for relevant documentation
            search_results = await self.search_documentation(query, language, limit=3)
            
            if not search_results:
                return "No relevant documentation found."
            
            # Fetch content from top results
            content_pieces = []
            for result in search_results[:2]:  # Limit to top 2 to avoid token limits
                content = await self.get_page_content(result['url'])
                if content:
                    content_pieces.append({
                        'title': result['title'],
                        'url': result['url'],
                        'content': content[:1000]  # Limit content length
                    })
            
            if not content_pieces:
                return "Could not fetch documentation content."
            
            # Generate AI summary
            system_prompt = """You are a documentation expert. Summarize the provided documentation content to help a developer understand the topic. Be concise but comprehensive. Include code examples if available."""
            
            prompt = f"""Summarize this documentation about "{query}":

"""
            
            for piece in content_pieces:
                prompt += f"""
Source: {piece['title']} ({piece['url']})
Content: {piece['content']}

"""
            
            prompt += """
Provide a clear, practical summary that helps a developer understand and use this information. Include any code examples or important details."""
            
            summary = await self.ollama_client.generate_response(
                prompt,
                system_prompt=system_prompt
            )
            
            # Add source links
            sources = "\n\n📚 Sources:\n"
            for result in search_results:
                sources += f"• {result['title']}: {result['url']}\n"
            
            return summary + sources
            
        except Exception as e:
            console.print(f"[red]❌ Error generating documentation summary: {e}[/red]")
            return f"Error searching documentation: {e}"
    
    async def find_code_examples(self, query: str, language: str = None) -> List[Dict[str, Any]]:
        """Find code examples for a specific topic."""
        console.print(f"[blue]🔍 Finding code examples for: {query}[/blue]")
        
        try:
            # Search for code examples
            code_query = f"{query} code example {language or ''}"
            results = await self.search_documentation(code_query, language, limit=5)
            
            # Filter for results likely to contain code
            code_results = []
            for result in results:
                snippet = result.get('snippet', '').lower()
                url = result.get('url', '').lower()
                
                # Look for indicators of code content
                if any(indicator in snippet or indicator in url for indicator in [
                    'example', 'tutorial', 'guide', 'code', 'github', 'gist'
                ]):
                    code_results.append(result)
            
            return code_results
            
        except Exception as e:
            console.print(f"[red]❌ Error finding code examples: {e}[/red]")
            return []
    
    async def show_search_results(self, results: List[Dict[str, Any]]) -> None:
        """Display search results in a beautiful format."""
        if not results:
            console.print("[yellow]No results found[/yellow]")
            return
        
        table = Table(title="🔍 Documentation Search Results")
        table.add_column("Title", style="cyan", width=30)
        table.add_column("Site", style="green", width=20)
        table.add_column("Snippet", style="white", width=50)
        
        for result in results:
            title = result.get('title', 'Unknown')[:30]
            site = result.get('site', 'Unknown')
            snippet = result.get('snippet', '')[:50] + "..." if len(result.get('snippet', '')) > 50 else result.get('snippet', '')
            
            table.add_row(title, site, snippet)
        
        console.print(table)
        
        # Show URLs
        console.print("\n[bold green]🔗 Links:[/bold green]")
        for i, result in enumerate(results, 1):
            console.print(f"{i}. {result.get('url', 'No URL')}")
    
    def get_language_from_context(self, context: str) -> Optional[str]:
        """Detect programming language from context."""
        context_lower = context.lower()
        
        # Language indicators
        language_indicators = {
            'python': ['python', '.py', 'pip', 'django', 'flask', 'fastapi', 'pandas'],
            'javascript': ['javascript', 'js', '.js', 'node', 'npm', 'react', 'vue'],
            'typescript': ['typescript', 'ts', '.ts', 'angular'],
            'go': ['golang', 'go', '.go', 'goroutine'],
            'rust': ['rust', '.rs', 'cargo', 'rustc'],
            'java': ['java', '.java', 'maven', 'gradle', 'spring'],
            'cpp': ['c++', 'cpp', '.cpp', '.hpp', 'cmake'],
            'csharp': ['c#', 'csharp', '.cs', 'dotnet', '.net'],
            'php': ['php', '.php', 'laravel', 'symfony', 'composer'],
            'ruby': ['ruby', '.rb', 'rails', 'gem']
        }
        
        for language, indicators in language_indicators.items():
            if any(indicator in context_lower for indicator in indicators):
                return language
        
        return None


# Utility function for easy access
async def search_documentation(query: str, language: str = None, ollama_client: OllamaClient = None, config: Config = None) -> str:
    """Quick function to search documentation and get AI summary."""
    if not ollama_client or not config:
        return "Web search not available - missing configuration"
    
    async with WebSearchAssistant(ollama_client, config) as search_assistant:
        return await search_assistant.search_and_summarize(query, language)

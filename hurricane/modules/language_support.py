"""
Multi-language support module for Hurricane AI Agent.
Provides language-specific code analysis, best practices, and intelligence.
"""

import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class CodeElement:
    """Represents a code element (function, class, variable, etc.)."""
    name: str
    type: str  # function, class, variable, interface, etc.
    line_start: int
    line_end: int
    language: str
    signature: str = ""
    docstring: str = ""
    parameters: List[str] = None
    return_type: str = ""
    visibility: str = "public"  # public, private, protected
    is_async: bool = False
    decorators: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.decorators is None:
            self.decorators = []


class LanguageAnalyzer:
    """Base class for language-specific code analysis."""
    
    def __init__(self, language: str):
        self.language = language
        self.file_extensions = []
        self.comment_patterns = []
        self.string_patterns = []
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a code file and extract information."""
        try:
            content = file_path.read_text(encoding='utf-8')
            return self.analyze_code(content)
        except Exception as e:
            return {"error": str(e), "elements": []}
    
    def analyze_code(self, content: str) -> Dict[str, Any]:
        """Analyze code content and extract elements."""
        return {
            "language": self.language,
            "elements": [],
            "imports": [],
            "line_count": len(content.split('\n')),
            "complexity": self.calculate_complexity(content)
        }
    
    def calculate_complexity(self, content: str) -> int:
        """Calculate basic code complexity."""
        # Simple complexity based on control structures
        complexity_keywords = ['if', 'else', 'elif', 'for', 'while', 'try', 'except', 'switch', 'case']
        complexity = 1  # Base complexity
        
        for keyword in complexity_keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', content))
        
        return complexity
    
    def get_best_practices(self) -> List[str]:
        """Get language-specific best practices."""
        return []
    
    def get_common_patterns(self) -> Dict[str, str]:
        """Get common code patterns for this language."""
        return {}


class PythonAnalyzer(LanguageAnalyzer):
    """Python-specific code analyzer."""
    
    def __init__(self):
        super().__init__("python")
        self.file_extensions = [".py", ".pyw", ".pyi"]
        self.comment_patterns = [r"#.*$"]
        self.string_patterns = [r'""".*?"""', r"'''.*?'''", r'".*?"', r"'.*?'"]
    
    def analyze_code(self, content: str) -> Dict[str, Any]:
        """Analyze Python code using AST."""
        try:
            tree = ast.parse(content)
            elements = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    elements.append(self._analyze_function(node, content))
                elif isinstance(node, ast.AsyncFunctionDef):
                    elements.append(self._analyze_async_function(node, content))
                elif isinstance(node, ast.ClassDef):
                    elements.append(self._analyze_class(node, content))
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.extend(self._analyze_import(node))
            
            return {
                "language": self.language,
                "elements": elements,
                "imports": imports,
                "line_count": len(content.split('\n')),
                "complexity": self.calculate_complexity(content)
            }
            
        except SyntaxError as e:
            return {
                "language": self.language,
                "elements": [],
                "imports": [],
                "line_count": len(content.split('\n')),
                "complexity": 0,
                "syntax_error": str(e)
            }
    
    def _analyze_function(self, node: ast.FunctionDef, content: str) -> CodeElement:
        """Analyze a Python function."""
        lines = content.split('\n')
        
        # Get function signature
        signature = f"def {node.name}("
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        signature += ", ".join(args) + ")"
        
        # Get return type
        return_type = ""
        if node.returns:
            return_type = ast.unparse(node.returns)
            signature += f" -> {return_type}"
        
        # Get docstring
        docstring = ""
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
        
        # Get decorators
        decorators = [ast.unparse(dec) for dec in node.decorator_list]
        
        return CodeElement(
            name=node.name,
            type="function",
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            language=self.language,
            signature=signature,
            docstring=docstring,
            parameters=[arg.arg for arg in node.args.args],
            return_type=return_type,
            decorators=decorators
        )
    
    def _analyze_async_function(self, node: ast.AsyncFunctionDef, content: str) -> CodeElement:
        """Analyze a Python async function."""
        element = self._analyze_function(node, content)
        element.is_async = True
        element.signature = element.signature.replace("def ", "async def ")
        return element
    
    def _analyze_class(self, node: ast.ClassDef, content: str) -> CodeElement:
        """Analyze a Python class."""
        # Get base classes
        bases = [ast.unparse(base) for base in node.bases]
        signature = f"class {node.name}"
        if bases:
            signature += f"({', '.join(bases)})"
        
        # Get docstring
        docstring = ""
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
        
        # Get decorators
        decorators = [ast.unparse(dec) for dec in node.decorator_list]
        
        return CodeElement(
            name=node.name,
            type="class",
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            language=self.language,
            signature=signature,
            docstring=docstring,
            decorators=decorators
        )
    
    def _analyze_import(self, node) -> List[str]:
        """Analyze import statements."""
        imports = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports
    
    def get_best_practices(self) -> List[str]:
        """Get Python best practices."""
        return [
            "Follow PEP 8 style guide",
            "Use type hints for function parameters and return values",
            "Write descriptive docstrings for functions and classes",
            "Use list comprehensions when appropriate",
            "Handle exceptions properly with try/except blocks",
            "Use context managers (with statements) for resource management",
            "Prefer f-strings for string formatting",
            "Use meaningful variable and function names",
            "Keep functions small and focused on a single task",
            "Use virtual environments for dependency management"
        ]


class JavaScriptAnalyzer(LanguageAnalyzer):
    """JavaScript/TypeScript code analyzer."""
    
    def __init__(self, is_typescript: bool = False):
        super().__init__("typescript" if is_typescript else "javascript")
        self.is_typescript = is_typescript
        self.file_extensions = [".ts", ".tsx"] if is_typescript else [".js", ".jsx"]
        self.comment_patterns = [r"//.*$", r"/\*.*?\*/"]
        self.string_patterns = [r'".*?"', r"'.*?'", r"`.*?`"]
    
    def analyze_code(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code using regex patterns."""
        elements = []
        imports = []
        
        # Find functions
        function_patterns = [
            r"function\s+(\w+)\s*\([^)]*\)\s*{",
            r"const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*{",
            r"(\w+)\s*:\s*function\s*\([^)]*\)\s*{",
            r"async\s+function\s+(\w+)\s*\([^)]*\)\s*{",
            r"const\s+(\w+)\s*=\s*async\s*\([^)]*\)\s*=>\s*{"
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in function_patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    is_async = "async" in line
                    
                    elements.append(CodeElement(
                        name=func_name,
                        type="function",
                        line_start=i,
                        line_end=i,  # Simplified - would need proper parsing for end
                        language=self.language,
                        signature=line.strip(),
                        is_async=is_async
                    ))
        
        # Find classes
        class_pattern = r"class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{"
        for i, line in enumerate(lines, 1):
            match = re.search(class_pattern, line)
            if match:
                class_name = match.group(1)
                extends = match.group(2) if match.group(2) else ""
                
                signature = f"class {class_name}"
                if extends:
                    signature += f" extends {extends}"
                
                elements.append(CodeElement(
                    name=class_name,
                    type="class",
                    line_start=i,
                    line_end=i,
                    language=self.language,
                    signature=signature
                ))
        
        # Find imports
        import_patterns = [
            r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]",
            r"import\s+['\"]([^'\"]+)['\"]",
            r"const\s+.*?\s+=\s+require\(['\"]([^'\"]+)['\"]\)"
        ]
        
        for line in lines:
            for pattern in import_patterns:
                matches = re.findall(pattern, line)
                imports.extend(matches)
        
        return {
            "language": self.language,
            "elements": elements,
            "imports": imports,
            "line_count": len(lines),
            "complexity": self.calculate_complexity(content)
        }
    
    def get_best_practices(self) -> List[str]:
        """Get JavaScript/TypeScript best practices."""
        practices = [
            "Use const and let instead of var",
            "Use arrow functions for short functions",
            "Use template literals for string interpolation",
            "Handle promises with async/await",
            "Use destructuring for object and array assignments",
            "Use strict equality (===) instead of loose equality (==)",
            "Use meaningful variable and function names",
            "Handle errors properly with try/catch blocks",
            "Use ESLint for code quality",
            "Use modern ES6+ features"
        ]
        
        if self.is_typescript:
            practices.extend([
                "Use type annotations for function parameters and return values",
                "Define interfaces for object shapes",
                "Use enums for constants",
                "Enable strict mode in TypeScript configuration",
                "Use generic types for reusable components"
            ])
        
        return practices


class GoAnalyzer(LanguageAnalyzer):
    """Go code analyzer."""
    
    def __init__(self):
        super().__init__("go")
        self.file_extensions = [".go"]
        self.comment_patterns = [r"//.*$", r"/\*.*?\*/"]
        self.string_patterns = [r'".*?"', r"`.*?`"]
    
    def analyze_code(self, content: str) -> Dict[str, Any]:
        """Analyze Go code using regex patterns."""
        elements = []
        imports = []
        
        lines = content.split('\n')
        
        # Find functions
        func_pattern = r"func\s+(?:\([^)]*\)\s+)?(\w+)\s*\([^)]*\)(?:\s*\([^)]*\))?\s*{"
        for i, line in enumerate(lines, 1):
            match = re.search(func_pattern, line)
            if match:
                func_name = match.group(1)
                
                elements.append(CodeElement(
                    name=func_name,
                    type="function",
                    line_start=i,
                    line_end=i,
                    language=self.language,
                    signature=line.strip()
                ))
        
        # Find structs
        struct_pattern = r"type\s+(\w+)\s+struct\s*{"
        for i, line in enumerate(lines, 1):
            match = re.search(struct_pattern, line)
            if match:
                struct_name = match.group(1)
                
                elements.append(CodeElement(
                    name=struct_name,
                    type="struct",
                    line_start=i,
                    line_end=i,
                    language=self.language,
                    signature=line.strip()
                ))
        
        # Find interfaces
        interface_pattern = r"type\s+(\w+)\s+interface\s*{"
        for i, line in enumerate(lines, 1):
            match = re.search(interface_pattern, line)
            if match:
                interface_name = match.group(1)
                
                elements.append(CodeElement(
                    name=interface_name,
                    type="interface",
                    line_start=i,
                    line_end=i,
                    language=self.language,
                    signature=line.strip()
                ))
        
        # Find imports
        import_pattern = r'import\s+(?:\(\s*)?["\']([^"\']+)["\']'
        for line in lines:
            matches = re.findall(import_pattern, line)
            imports.extend(matches)
        
        return {
            "language": self.language,
            "elements": elements,
            "imports": imports,
            "line_count": len(lines),
            "complexity": self.calculate_complexity(content)
        }
    
    def get_best_practices(self) -> List[str]:
        """Get Go best practices."""
        return [
            "Use gofmt to format code consistently",
            "Follow Go naming conventions (camelCase, PascalCase)",
            "Use go vet to catch common mistakes",
            "Handle errors explicitly, don't ignore them",
            "Use interfaces to define behavior",
            "Keep functions small and focused",
            "Use go modules for dependency management",
            "Write table-driven tests",
            "Use context for cancellation and timeouts",
            "Prefer composition over inheritance"
        ]


class RustAnalyzer(LanguageAnalyzer):
    """Rust code analyzer."""
    
    def __init__(self):
        super().__init__("rust")
        self.file_extensions = [".rs"]
        self.comment_patterns = [r"//.*$", r"/\*.*?\*/"]
        self.string_patterns = [r'".*?"', r"r#.*?#"]
    
    def analyze_code(self, content: str) -> Dict[str, Any]:
        """Analyze Rust code using regex patterns."""
        elements = []
        imports = []
        
        lines = content.split('\n')
        
        # Find functions
        func_pattern = r"(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\([^)]*\)(?:\s*->\s*[^{]+)?\s*{"
        for i, line in enumerate(lines, 1):
            match = re.search(func_pattern, line)
            if match:
                func_name = match.group(1)
                is_async = "async" in line
                is_public = "pub" in line
                
                elements.append(CodeElement(
                    name=func_name,
                    type="function",
                    line_start=i,
                    line_end=i,
                    language=self.language,
                    signature=line.strip(),
                    is_async=is_async,
                    visibility="public" if is_public else "private"
                ))
        
        # Find structs
        struct_pattern = r"(?:pub\s+)?struct\s+(\w+)(?:<[^>]*>)?\s*{"
        for i, line in enumerate(lines, 1):
            match = re.search(struct_pattern, line)
            if match:
                struct_name = match.group(1)
                is_public = "pub" in line
                
                elements.append(CodeElement(
                    name=struct_name,
                    type="struct",
                    line_start=i,
                    line_end=i,
                    language=self.language,
                    signature=line.strip(),
                    visibility="public" if is_public else "private"
                ))
        
        # Find enums
        enum_pattern = r"(?:pub\s+)?enum\s+(\w+)(?:<[^>]*>)?\s*{"
        for i, line in enumerate(lines, 1):
            match = re.search(enum_pattern, line)
            if match:
                enum_name = match.group(1)
                is_public = "pub" in line
                
                elements.append(CodeElement(
                    name=enum_name,
                    type="enum",
                    line_start=i,
                    line_end=i,
                    language=self.language,
                    signature=line.strip(),
                    visibility="public" if is_public else "private"
                ))
        
        # Find traits
        trait_pattern = r"(?:pub\s+)?trait\s+(\w+)(?:<[^>]*>)?\s*{"
        for i, line in enumerate(lines, 1):
            match = re.search(trait_pattern, line)
            if match:
                trait_name = match.group(1)
                is_public = "pub" in line
                
                elements.append(CodeElement(
                    name=trait_name,
                    type="trait",
                    line_start=i,
                    line_end=i,
                    language=self.language,
                    signature=line.strip(),
                    visibility="public" if is_public else "private"
                ))
        
        # Find use statements (imports)
        use_pattern = r"use\s+([^;]+);"
        for line in lines:
            match = re.search(use_pattern, line)
            if match:
                imports.append(match.group(1).strip())
        
        return {
            "language": self.language,
            "elements": elements,
            "imports": imports,
            "line_count": len(lines),
            "complexity": self.calculate_complexity(content)
        }
    
    def get_best_practices(self) -> List[str]:
        """Get Rust best practices."""
        return [
            "Use cargo fmt to format code consistently",
            "Use cargo clippy for linting and suggestions",
            "Handle errors with Result<T, E> type",
            "Use ownership and borrowing effectively",
            "Prefer iterators over manual loops",
            "Use pattern matching with match expressions",
            "Write comprehensive tests with #[test]",
            "Use cargo for dependency management",
            "Follow Rust naming conventions",
            "Use lifetimes when necessary for memory safety"
        ]


class MultiLanguageSupport:
    """Multi-language support manager."""
    
    def __init__(self):
        self.analyzers = {
            "python": PythonAnalyzer(),
            "javascript": JavaScriptAnalyzer(is_typescript=False),
            "typescript": JavaScriptAnalyzer(is_typescript=True),
            "go": GoAnalyzer(),
            "rust": RustAnalyzer()
        }
        
        # File extension to language mapping
        self.extension_map = {}
        for lang, analyzer in self.analyzers.items():
            for ext in analyzer.file_extensions:
                self.extension_map[ext] = lang
    
    def detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        suffix = file_path.suffix.lower()
        return self.extension_map.get(suffix)
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a code file with the appropriate language analyzer."""
        language = self.detect_language(file_path)
        
        if not language or language not in self.analyzers:
            return {
                "language": "unknown",
                "elements": [],
                "imports": [],
                "line_count": 0,
                "complexity": 0,
                "error": f"Unsupported language for file: {file_path}"
            }
        
        analyzer = self.analyzers[language]
        result = analyzer.analyze_file(file_path)
        result["file_path"] = str(file_path)
        
        return result
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return list(self.analyzers.keys())
    
    def get_language_info(self, language: str) -> Dict[str, Any]:
        """Get information about a specific language."""
        if language not in self.analyzers:
            return {"error": f"Unsupported language: {language}"}
        
        analyzer = self.analyzers[language]
        return {
            "language": language,
            "file_extensions": analyzer.file_extensions,
            "best_practices": analyzer.get_best_practices(),
            "comment_patterns": analyzer.comment_patterns
        }
    
    def show_language_support(self) -> None:
        """Display supported languages and their features."""
        table = Table(title="🌐 Multi-Language Support")
        table.add_column("Language", style="cyan")
        table.add_column("Extensions", style="green")
        table.add_column("Features", style="white")
        
        for lang, analyzer in self.analyzers.items():
            extensions = ", ".join(analyzer.file_extensions)
            features = "Functions, Classes, Imports, Best Practices"
            
            if lang == "python":
                features += ", AST Analysis, Type Hints"
            elif lang in ["javascript", "typescript"]:
                features += ", Async/Await, ES6+"
            elif lang == "go":
                features += ", Structs, Interfaces, Goroutines"
            elif lang == "rust":
                features += ", Traits, Ownership, Memory Safety"
            
            table.add_row(lang.title(), extensions, features)
        
        console.print(table)
    
    def get_language_statistics(self, project_files: List[Path]) -> Dict[str, Any]:
        """Get statistics about languages used in a project."""
        language_stats = {}
        total_files = 0
        total_lines = 0
        
        for file_path in project_files:
            if file_path.is_file():
                language = self.detect_language(file_path)
                if language:
                    analysis = self.analyze_file(file_path)
                    
                    if language not in language_stats:
                        language_stats[language] = {
                            "files": 0,
                            "lines": 0,
                            "functions": 0,
                            "classes": 0,
                            "complexity": 0
                        }
                    
                    language_stats[language]["files"] += 1
                    language_stats[language]["lines"] += analysis.get("line_count", 0)
                    language_stats[language]["complexity"] += analysis.get("complexity", 0)
                    
                    for element in analysis.get("elements", []):
                        if element.type == "function":
                            language_stats[language]["functions"] += 1
                        elif element.type in ["class", "struct", "interface", "trait"]:
                            language_stats[language]["classes"] += 1
                    
                    total_files += 1
                    total_lines += analysis.get("line_count", 0)
        
        return {
            "languages": language_stats,
            "total_files": total_files,
            "total_lines": total_lines,
            "primary_language": max(language_stats.keys(), key=lambda k: language_stats[k]["lines"]) if language_stats else None
        }

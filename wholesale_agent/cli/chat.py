"""
Interactive chat interface for the wholesale AI agent.
"""
import os
import sys
import readline
import atexit
from typing import Optional, List
from datetime import datetime
import json

from ..core import WholesaleAgent
from ..utils.config import Config
from ..utils.logger import setup_logger


class ChatInterface:
    """Interactive command-line chat interface."""
    
    def __init__(self, config: Optional[Config] = None, enable_rag: bool = False):
        self.config = config or Config()
        self.logger = setup_logger('chat', self.config.log_level)
        self.agent = WholesaleAgent(enable_rag=enable_rag)
        
        # Chat history
        self.history = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup readline for better CLI experience
        self._setup_readline()
        
        # Colors and formatting
        self.colors = {
            'agent': '\033[94m',    # Blue
            'user': '\033[92m',     # Green
            'system': '\033[93m',   # Yellow
            'error': '\033[91m',    # Red
            'reset': '\033[0m',     # Reset
            'bold': '\033[1m',      # Bold
            'dim': '\033[2m'        # Dim
        }
        
        # Command handlers
        self.commands = {
            '/help': self._show_help,
            '/clear': self._clear_screen,
            '/history': self._show_history,
            '/save': self._save_session,
            '/load': self._load_session,
            '/status': self._show_status,
            '/config': self._show_config,
            '/exit': self._exit,
            '/quit': self._exit
        }
    
    def _setup_readline(self):
        """Setup readline for command history and completion."""
        # History file
        history_file = os.path.expanduser('~/.wholesale_agent_history')
        
        # Load history if it exists
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass
        
        # Save history on exit
        atexit.register(readline.write_history_file, history_file)
        
        # Set up tab completion
        readline.set_completer(self._completer)
        readline.parse_and_bind('tab: complete')
        
        # Set history length
        readline.set_history_length(1000)
    
    def _completer(self, text: str, state: int) -> Optional[str]:
        """Tab completion for commands and common queries."""
        options = []
        
        # Command completion
        if text.startswith('/'):
            options = [cmd for cmd in self.commands.keys() if cmd.startswith(text)]
        else:
            # Query completion - common wholesale queries
            common_queries = [
                "How much stock do we have?",
                "Show me low stock products",
                "Find products in Electronics category",
                "What is our total inventory value?",
                "Show me recent inventory movements",
                "List all suppliers",
                "Show out of stock products",
                "What are our top selling categories?",
                "Find products from specific supplier",
                "Show pricing for product"
            ]
            options = [query for query in common_queries if query.lower().startswith(text.lower())]
        
        if state < len(options):
            return options[state]
        return None
    
    def start(self):
        """Start the interactive chat session."""
        self._print_welcome()
        
        while True:
            try:
                user_input = self._get_user_input()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if user_input in self.commands:
                        result = self.commands[user_input]()
                        if result == 'exit':
                            break
                    else:
                        self._print_error(f"Unknown command: {user_input}")
                        self._print_info("Type /help for available commands")
                    continue
                
                # Process regular queries
                self._handle_query(user_input)
                
            except KeyboardInterrupt:
                self._print_info("\nUse /exit or /quit to exit gracefully")
            except EOFError:
                self._print_info("\nGoodbye!")
                break
            except Exception as e:
                self._print_error(f"An error occurred: {str(e)}")
                self.logger.error(f"Chat error: {str(e)}", exc_info=True)
    
    def _print_welcome(self):
        """Print welcome message."""
        print(f"{self.colors['bold']}{self.colors['system']}")
        print("=" * 60)
        print("🤖 WHOLESALE AI AGENT")
        print("=" * 60)
        print(f"{self.colors['reset']}")
        print(f"{self.colors['dim']}Your AI assistant for wholesale business operations{self.colors['reset']}")
        print()
        print("💡 Examples:")
        print("  • How much stock of USB cables do we have?")
        print("  • Show me low stock products")
        print("  • What's our total inventory value?")
        print("  • Find products in Electronics category")
        print()
        print(f"{self.colors['dim']}Type /help for commands or start asking questions!{self.colors['reset']}")
        print("─" * 60)
    
    def _get_user_input(self) -> str:
        """Get user input with prompt."""
        prompt = f"{self.colors['user']}You: {self.colors['reset']}"
        return input(prompt).strip()
    
    def _handle_query(self, query: str):
        """Handle user query."""
        # Add to history
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'user',
            'content': query
        })
        
        # Show thinking indicator
        print(f"{self.colors['dim']}🤔 Processing...{self.colors['reset']}", end='', flush=True)
        
        try:
            # Get response from agent
            response = self.agent.process_query(query)
            
            # Clear thinking indicator
            print(f"\r{' ' * 20}\r", end='')
            
            # Display response
            self._print_agent_response(response)
            
            # Add response to history
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'agent',
                'content': response
            })
            
        except Exception as e:
            print(f"\r{' ' * 20}\r", end='')
            self._print_error(f"Error processing query: {str(e)}")
            self.logger.error(f"Query processing error: {str(e)}", exc_info=True)
    
    def _print_agent_response(self, response: str):
        """Print agent response with formatting."""
        print(f"{self.colors['agent']}🤖 Agent:{self.colors['reset']}")
        print(f"{self._format_response(response)}")
        print()
    
    def _format_response(self, response: str) -> str:
        """Format agent response for better readability."""
        # Add some basic formatting
        lines = response.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
                
            # Highlight bullet points
            if line.startswith('•'):
                formatted_lines.append(f"  {self.colors['dim']}{line}{self.colors['reset']}")
            # Highlight warnings
            elif '⚠️' in line or 'warning' in line.lower():
                formatted_lines.append(f"{self.colors['system']}{line}{self.colors['reset']}")
            # Highlight headings (lines ending with :)
            elif line.endswith(':'):
                formatted_lines.append(f"{self.colors['bold']}{line}{self.colors['reset']}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _print_info(self, message: str):
        """Print info message."""
        print(f"{self.colors['system']}ℹ️  {message}{self.colors['reset']}")
    
    def _print_error(self, message: str):
        """Print error message."""
        print(f"{self.colors['error']}❌ {message}{self.colors['reset']}")
    
    def _show_help(self):
        """Show help information."""
        print(f"{self.colors['bold']}📋 AVAILABLE COMMANDS:{self.colors['reset']}")
        print()
        help_text = [
            ("/help", "Show this help message"),
            ("/clear", "Clear the screen"),
            ("/history", "Show conversation history"),
            ("/save", "Save current session"),
            ("/load", "Load previous session"),
            ("/status", "Show system status"),
            ("/config", "Show configuration"),
            ("/exit, /quit", "Exit the chat")
        ]
        
        for cmd, desc in help_text:
            print(f"  {self.colors['user']}{cmd:<12}{self.colors['reset']} - {desc}")
        
        print()
        print(f"{self.colors['bold']}💡 EXAMPLE QUERIES:{self.colors['reset']}")
        examples = [
            "How much stock of wireless headphones do we have?",
            "Show me products running low on stock",
            "What is our total inventory value?",
            "Find all products in the Electronics category",
            "Which products are out of stock?",
            "Show me recent inventory movements",
            "List all active suppliers"
        ]
        
        for example in examples:
            print(f"  {self.colors['dim']}• {example}{self.colors['reset']}")
        print()
    
    def _clear_screen(self):
        """Clear the screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        self._print_welcome()
    
    def _show_history(self):
        """Show conversation history."""
        if not self.history:
            self._print_info("No conversation history")
            return
        
        print(f"{self.colors['bold']}📝 CONVERSATION HISTORY:{self.colors['reset']}")
        print()
        
        for i, entry in enumerate(self.history[-10:], 1):  # Show last 10 entries
            timestamp = entry['timestamp'][:19].replace('T', ' ')
            content = entry['content'][:100] + "..." if len(entry['content']) > 100 else entry['content']
            
            if entry['type'] == 'user':
                print(f"{i:2}. [{timestamp}] {self.colors['user']}You:{self.colors['reset']} {content}")
            else:
                print(f"    [{timestamp}] {self.colors['agent']}Agent:{self.colors['reset']} {content}")
        print()
    
    def _save_session(self):
        """Save current session to file."""
        if not self.history:
            self._print_info("No session data to save")
            return
        
        sessions_dir = os.path.expanduser('~/.wholesale_agent_sessions')
        os.makedirs(sessions_dir, exist_ok=True)
        
        filename = f"session_{self.session_id}.json"
        filepath = os.path.join(sessions_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    'session_id': self.session_id,
                    'created_at': datetime.now().isoformat(),
                    'history': self.history
                }, f, indent=2)
            
            self._print_info(f"Session saved to {filepath}")
        except Exception as e:
            self._print_error(f"Failed to save session: {str(e)}")
    
    def _load_session(self):
        """Load previous session."""
        sessions_dir = os.path.expanduser('~/.wholesale_agent_sessions')
        
        if not os.path.exists(sessions_dir):
            self._print_info("No saved sessions found")
            return
        
        # List available sessions
        sessions = [f for f in os.listdir(sessions_dir) if f.endswith('.json')]
        
        if not sessions:
            self._print_info("No saved sessions found")
            return
        
        print("Available sessions:")
        for i, session in enumerate(sessions[-5:], 1):  # Show last 5 sessions
            print(f"  {i}. {session}")
        
        try:
            choice = input("Enter session number (or press Enter to cancel): ").strip()
            if not choice:
                return
            
            session_file = sessions[int(choice) - 1]
            filepath = os.path.join(sessions_dir, session_file)
            
            with open(filepath, 'r') as f:
                session_data = json.load(f)
            
            self.history = session_data.get('history', [])
            self._print_info(f"Loaded session: {session_data.get('session_id', 'Unknown')}")
            
        except (ValueError, IndexError, FileNotFoundError) as e:
            self._print_error(f"Failed to load session: {str(e)}")
    
    def _show_status(self):
        """Show system status."""
        print(f"{self.colors['bold']}📊 SYSTEM STATUS:{self.colors['reset']}")
        print()
        
        # Database connectivity
        try:
            from ..models import db_manager
            with db_manager.get_session() as session:
                session.execute("SELECT 1")
            db_status = "🟢 Connected"
        except Exception as e:
            db_status = f"🔴 Error: {str(e)}"
        
        # LLM availability
        try:
            llm_available = self.agent.llm_client.is_available()
            llm_status = "🟢 Available" if llm_available else "🟡 Limited (fallback mode)"
        except Exception:
            llm_status = "🔴 Unavailable"
        
        status_items = [
            ("Database", db_status),
            ("AI Model", llm_status),
            ("Session ID", self.session_id),
            ("History Entries", str(len(self.history))),
            ("Log Level", self.config.log_level)
        ]
        
        for label, value in status_items:
            print(f"  {label:<15}: {value}")
        print()
    
    def _show_config(self):
        """Show current configuration."""
        print(f"{self.colors['bold']}⚙️  CONFIGURATION:{self.colors['reset']}")
        print()
        
        config_items = [
            ("LLM Provider", getattr(self.config, 'llm_provider', 'Not set')),
            ("LLM Model", getattr(self.config, 'llm_model', 'Not set')),
            ("Database URL", getattr(self.config, 'database_url', 'Not set')[:50] + "..."),
            ("Debug Mode", str(getattr(self.config, 'debug', False))),
            ("Log Level", self.config.log_level)
        ]
        
        for label, value in config_items:
            print(f"  {label:<15}: {value}")
        print()
    
    def _exit(self):
        """Exit the chat interface."""
        print(f"{self.colors['system']}👋 Thank you for using Wholesale AI Agent!{self.colors['reset']}")
        print(f"{self.colors['dim']}Session ID: {self.session_id}{self.colors['reset']}")
        return 'exit'
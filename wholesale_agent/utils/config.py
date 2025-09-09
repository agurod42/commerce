"""
Configuration management for wholesale agent.
Handles environment variables, config files, and production settings.
"""
import os
import json
from typing import Optional, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///wholesale_agent.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    log_dir: str = "logs"
    structured: bool = False
    console_output: bool = True
    file_rotation_mb: int = 10
    backup_count: int = 5


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: Optional[str] = None
    allowed_hosts: list = None
    rate_limit_per_minute: int = 60
    session_timeout_minutes: int = 60
    
    def __post_init__(self):
        if self.allowed_hosts is None:
            self.allowed_hosts = ["localhost", "127.0.0.1"]


@dataclass
class PerformanceConfig:
    """Performance and monitoring configuration."""
    enable_metrics: bool = True
    query_timeout_seconds: int = 30
    max_concurrent_queries: int = 10
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300


class Config:
    """Main configuration class for wholesale agent."""
    
    def __init__(self, config_file: Optional[str] = None, debug: bool = False):
        self.debug = debug
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
        # Initialize configuration sections
        self.database = DatabaseConfig()
        self.llm = LLMConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        self.performance = PerformanceConfig()
        
        # Load configuration from various sources
        self._load_from_environment()
        
        if config_file:
            self._load_from_file(config_file)
        else:
            self._load_from_default_files()
        
        # Apply debug overrides
        if debug:
            self._apply_debug_settings()
        
        # Validate configuration
        self._validate_config()
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # Database configuration
        if os.getenv('DATABASE_URL'):
            self.database.url = os.getenv('DATABASE_URL')
        self.database.echo = os.getenv('DB_ECHO', 'false').lower() == 'true'
        
        # LLM configuration
        self.llm.provider = os.getenv('LLM_PROVIDER', self.llm.provider)
        self.llm.model = os.getenv('LLM_MODEL', self.llm.model)
        self.llm.api_key = os.getenv('LLM_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.llm.base_url = os.getenv('LLM_BASE_URL')
        
        if os.getenv('LLM_MAX_TOKENS'):
            self.llm.max_tokens = int(os.getenv('LLM_MAX_TOKENS'))
        if os.getenv('LLM_TEMPERATURE'):
            self.llm.temperature = float(os.getenv('LLM_TEMPERATURE'))
        if os.getenv('LLM_TIMEOUT'):
            self.llm.timeout = int(os.getenv('LLM_TIMEOUT'))
        
        # Logging configuration
        self.logging.level = os.getenv('LOG_LEVEL', self.logging.level)
        self.logging.log_dir = os.getenv('LOG_DIR', self.logging.log_dir)
        self.logging.structured = os.getenv('LOG_STRUCTURED', 'false').lower() == 'true'
        
        # Security configuration
        self.security.secret_key = os.getenv('SECRET_KEY')
        if os.getenv('ALLOWED_HOSTS'):
            self.security.allowed_hosts = os.getenv('ALLOWED_HOSTS').split(',')
        if os.getenv('RATE_LIMIT_PER_MINUTE'):
            self.security.rate_limit_per_minute = int(os.getenv('RATE_LIMIT_PER_MINUTE'))
        
        # Performance configuration
        self.performance.enable_metrics = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
        if os.getenv('QUERY_TIMEOUT'):
            self.performance.query_timeout_seconds = int(os.getenv('QUERY_TIMEOUT'))
        if os.getenv('MAX_CONCURRENT_QUERIES'):
            self.performance.max_concurrent_queries = int(os.getenv('MAX_CONCURRENT_QUERIES'))
        
        self.performance.cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        if os.getenv('CACHE_TTL'):
            self.performance.cache_ttl_seconds = int(os.getenv('CACHE_TTL'))
    
    def _load_from_file(self, config_file: str):
        """Load configuration from a JSON file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        self._apply_config_data(config_data)
    
    def _load_from_default_files(self):
        """Load configuration from default configuration files."""
        # Look for configuration files in order of precedence
        config_files = [
            'config.local.json',  # Local overrides (not in version control)
            f'config.{self.environment}.json',  # Environment-specific
            'config.json'  # Default configuration
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    self._apply_config_data(config_data)
                    break
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Could not load config file {config_file}: {e}")
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data from dictionary."""
        if 'database' in config_data:
            self._update_dataclass(self.database, config_data['database'])
        
        if 'llm' in config_data:
            self._update_dataclass(self.llm, config_data['llm'])
        
        if 'logging' in config_data:
            self._update_dataclass(self.logging, config_data['logging'])
        
        if 'security' in config_data:
            self._update_dataclass(self.security, config_data['security'])
        
        if 'performance' in config_data:
            self._update_dataclass(self.performance, config_data['performance'])
    
    def _update_dataclass(self, target_obj: object, data: Dict[str, Any]):
        """Update a dataclass instance with data from dictionary."""
        for key, value in data.items():
            if hasattr(target_obj, key):
                setattr(target_obj, key, value)
    
    def _apply_debug_settings(self):
        """Apply debug-specific configuration overrides."""
        self.logging.level = "DEBUG"
        self.logging.console_output = True
        self.database.echo = True
        self.performance.enable_metrics = True
    
    def _validate_config(self):
        """Validate configuration settings."""
        # Validate required settings for production
        if self.environment == 'production':
            if not self.security.secret_key:
                raise ValueError("SECRET_KEY is required for production environment")
            
            if self.llm.provider == 'openai' and not self.llm.api_key:
                print("Warning: OpenAI API key not configured. LLM functionality will be limited.")
            
            # Ensure secure defaults for production
            if self.database.url.startswith('sqlite:'):
                print("Warning: SQLite database is not recommended for production")
            
            self.logging.structured = True  # Force structured logging in production
        
        # Validate numeric settings
        if self.llm.max_tokens <= 0:
            raise ValueError("LLM max_tokens must be positive")
        
        if self.llm.temperature < 0 or self.llm.temperature > 2:
            raise ValueError("LLM temperature must be between 0 and 2")
        
        if self.performance.query_timeout_seconds <= 0:
            raise ValueError("Query timeout must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'environment': self.environment,
            'debug': self.debug,
            'database': asdict(self.database),
            'llm': {
                **asdict(self.llm),
                'api_key': '***' if self.llm.api_key else None  # Mask API key
            },
            'logging': asdict(self.logging),
            'security': {
                **asdict(self.security),
                'secret_key': '***' if self.security.secret_key else None  # Mask secret
            },
            'performance': asdict(self.performance)
        }
    
    def save_to_file(self, config_file: str):
        """Save current configuration to file."""
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @property
    def log_level(self) -> str:
        """Get current log level."""
        return self.logging.level
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == 'development'
    
    def get_database_url(self) -> str:
        """Get database URL with any necessary transformations."""
        return self.database.url
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration as dictionary."""
        return asdict(self.llm)


def load_config(config_file: Optional[str] = None, debug: bool = False) -> Config:
    """Load configuration with optional file override."""
    return Config(config_file=config_file, debug=debug)


def create_default_config_file(output_path: str = "config.json"):
    """Create a default configuration file."""
    default_config = Config()
    default_config.save_to_file(output_path)
    print(f"Default configuration file created: {output_path}")


# Environment-specific configuration helpers
def is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv('ENVIRONMENT', 'development') == 'production'


def is_development() -> bool:
    """Check if running in development environment."""
    return os.getenv('ENVIRONMENT', 'development') == 'development'


def get_env_var(name: str, default: Any = None, required: bool = False) -> Any:
    """Get environment variable with validation."""
    value = os.getenv(name, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{name}' is not set")
    
    return value
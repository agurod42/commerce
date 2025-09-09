"""
Tests for configuration management.
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from wholesale_agent.utils.config import Config, DatabaseConfig, LLMConfig, load_config


@pytest.mark.unit
class TestConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.environment == 'development'
        assert config.debug is False
        assert config.database.url == "sqlite:///wholesale_agent.db"
        assert config.llm.provider == "openai"
        assert config.logging.level == "INFO"
    
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DATABASE_URL': 'postgresql://test:test@localhost/testdb',
            'LLM_PROVIDER': 'anthropic',
            'LLM_MODEL': 'claude-3-sonnet',
            'LLM_API_KEY': 'test-api-key',
            'LOG_LEVEL': 'DEBUG',
            'LOG_STRUCTURED': 'true',
            'SECRET_KEY': 'test-secret-key'
        }):
            config = Config()
            
            assert config.environment == 'production'
            assert config.database.url == 'postgresql://test:test@localhost/testdb'
            assert config.llm.provider == 'anthropic'
            assert config.llm.model == 'claude-3-sonnet'
            assert config.llm.api_key == 'test-api-key'
            assert config.logging.level == 'DEBUG'
            assert config.logging.structured is True
            assert config.security.secret_key == 'test-secret-key'
    
    def test_config_file_loading(self):
        """Test loading configuration from JSON file."""
        config_data = {
            'database': {
                'url': 'postgresql://file:test@localhost/filedb',
                'echo': True
            },
            'llm': {
                'provider': 'local',
                'model': 'llama2',
                'base_url': 'http://localhost:11434'
            },
            'logging': {
                'level': 'WARNING',
                'structured': True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = Config(config_file=config_file)
            
            assert config.database.url == 'postgresql://file:test@localhost/filedb'
            assert config.database.echo is True
            assert config.llm.provider == 'local'
            assert config.llm.model == 'llama2'
            assert config.llm.base_url == 'http://localhost:11434'
            assert config.logging.level == 'WARNING'
            assert config.logging.structured is True
        finally:
            os.unlink(config_file)
    
    def test_debug_settings_override(self):
        """Test debug settings override."""
        config = Config(debug=True)
        
        assert config.debug is True
        assert config.logging.level == "DEBUG"
        assert config.logging.console_output is True
        assert config.database.echo is True
        assert config.performance.enable_metrics is True
    
    def test_production_validation(self):
        """Test production environment validation."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            # Should raise ValueError for missing secret key
            with pytest.raises(ValueError) as exc_info:
                Config()
            
            assert "SECRET_KEY is required" in str(exc_info.value)
    
    def test_production_with_valid_config(self):
        """Test production environment with valid configuration."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'SECRET_KEY': 'production-secret-key',
            'LLM_API_KEY': 'production-api-key'
        }):
            config = Config()
            
            assert config.is_production is True
            assert config.is_development is False
            assert config.logging.structured is True  # Forced in production
    
    def test_config_validation_errors(self):
        """Test configuration validation errors."""
        # Test invalid LLM settings
        with patch.dict(os.environ, {
            'LLM_MAX_TOKENS': '-1',
            'LLM_TEMPERATURE': '3.0'
        }):
            with pytest.raises(ValueError) as exc_info:
                Config()
            
            assert "max_tokens must be positive" in str(exc_info.value)
    
    def test_config_to_dict(self):
        """Test converting configuration to dictionary."""
        with patch.dict(os.environ, {
            'LLM_API_KEY': 'test-api-key',
            'SECRET_KEY': 'test-secret'
        }):
            config = Config()
            config_dict = config.to_dict()
            
            assert 'environment' in config_dict
            assert 'database' in config_dict
            assert 'llm' in config_dict
            
            # API keys should be masked
            assert config_dict['llm']['api_key'] == '***'
            assert config_dict['security']['secret_key'] == '***'
    
    def test_config_save_and_load(self):
        """Test saving and loading configuration."""
        original_config = Config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            # Save configuration
            original_config.save_to_file(config_file)
            
            # Verify file was created and contains expected data
            assert Path(config_file).exists()
            
            with open(config_file) as f:
                saved_data = json.load(f)
            
            assert 'environment' in saved_data
            assert 'database' in saved_data
            assert 'llm' in saved_data
            
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)
    
    def test_missing_config_file(self):
        """Test handling of missing configuration file."""
        with pytest.raises(FileNotFoundError):
            Config(config_file='nonexistent_config.json')
    
    def test_invalid_config_file(self):
        """Test handling of invalid JSON configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            config_file = f.name
        
        try:
            # Should not raise an exception, but should use defaults
            config = Config(config_file=config_file)
            assert config.database.url == "sqlite:///wholesale_agent.db"  # Default value
        finally:
            os.unlink(config_file)
    
    def test_properties(self):
        """Test configuration properties."""
        config = Config()
        
        assert config.log_level == config.logging.level
        assert config.is_development is True  # Default environment
        assert config.is_production is False
        assert config.get_database_url() == config.database.url
        assert isinstance(config.get_llm_config(), dict)


@pytest.mark.unit
class TestDataclassConfigs:
    """Test individual configuration dataclasses."""
    
    def test_database_config(self):
        """Test DatabaseConfig dataclass."""
        db_config = DatabaseConfig(
            url="postgresql://user:pass@localhost/db",
            echo=True,
            pool_size=10
        )
        
        assert db_config.url == "postgresql://user:pass@localhost/db"
        assert db_config.echo is True
        assert db_config.pool_size == 10
        assert db_config.max_overflow == 10  # Default value
    
    def test_llm_config(self):
        """Test LLMConfig dataclass."""
        llm_config = LLMConfig(
            provider="anthropic",
            model="claude-3-sonnet",
            api_key="test-key",
            temperature=0.5
        )
        
        assert llm_config.provider == "anthropic"
        assert llm_config.model == "claude-3-sonnet"
        assert llm_config.api_key == "test-key"
        assert llm_config.temperature == 0.5
        assert llm_config.max_tokens == 1000  # Default value
    
    def test_security_config_post_init(self):
        """Test SecurityConfig post_init behavior."""
        from wholesale_agent.utils.config import SecurityConfig
        
        # Test with None allowed_hosts
        security_config = SecurityConfig(allowed_hosts=None)
        assert security_config.allowed_hosts == ["localhost", "127.0.0.1"]
        
        # Test with custom allowed_hosts
        custom_hosts = ["example.com", "api.example.com"]
        security_config = SecurityConfig(allowed_hosts=custom_hosts)
        assert security_config.allowed_hosts == custom_hosts


@pytest.mark.unit
class TestConfigHelpers:
    """Test configuration helper functions."""
    
    def test_load_config(self):
        """Test load_config helper function."""
        config = load_config()
        assert isinstance(config, Config)
        
        # Test with debug flag
        debug_config = load_config(debug=True)
        assert debug_config.debug is True
    
    def test_environment_helpers(self):
        """Test environment detection helpers."""
        from wholesale_agent.utils.config import is_production, is_development
        
        # Test default environment
        assert is_development() is True
        assert is_production() is False
        
        # Test with environment variable
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            assert is_production() is True
            assert is_development() is False
    
    def test_get_env_var(self):
        """Test get_env_var helper function."""
        from wholesale_agent.utils.config import get_env_var
        
        # Test with existing environment variable
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            assert get_env_var('TEST_VAR') == 'test_value'
        
        # Test with default value
        assert get_env_var('NONEXISTENT_VAR', 'default') == 'default'
        
        # Test with required flag
        with pytest.raises(ValueError) as exc_info:
            get_env_var('NONEXISTENT_REQUIRED_VAR', required=True)
        
        assert "Required environment variable" in str(exc_info.value)
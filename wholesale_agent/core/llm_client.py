"""
LLM client for AI agent functionality.
Supports multiple LLM providers with fallback options.
"""
import os
import logging
from typing import Optional, Dict, Any
import json
import requests
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    provider: str = "openai"  # openai, anthropic, local
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7


class LLMClient:
    """Client for interacting with Large Language Models.
    
    Configuration is automatically loaded from environment variables.
    No external configuration needed - just set the appropriate environment variables.
    """
    
    def __init__(self):
        """Initialize LLM client with configuration from environment variables."""
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
        self._validate_config()
    
    def _load_config(self) -> LLMConfig:
        """Load configuration from environment variables."""
        # Load .env file if available
        if DOTENV_AVAILABLE:
            load_dotenv()
        
        # Get API key from LLM_API_KEY environment variable
        api_key = os.getenv("LLM_API_KEY")
        
        return LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            api_key=api_key,
            model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            base_url=os.getenv("LLM_BASE_URL"),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7"))
        )
    
    def _validate_config(self):
        """Validate LLM configuration."""
        if self.config.provider == "openai" and not self.config.api_key:
            self.logger.warning("LLM API key not found. LLM functionality will be limited.")
        elif self.config.provider == "anthropic" and not self.config.api_key:
            self.logger.warning("LLM API key not found. LLM functionality will be limited.")
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using configured LLM."""
        try:
            if self.config.provider == "openai":
                return self._generate_openai_response(prompt, system_prompt)
            elif self.config.provider == "anthropic":
                return self._generate_anthropic_response(prompt, system_prompt)
            elif self.config.provider == "local":
                return self._generate_local_response(prompt, system_prompt)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
        
        except Exception as e:
            self.logger.error(f"Error generating LLM response: {str(e)}")
            raise
    
    def _generate_openai_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using OpenAI API."""
        if not self.config.api_key:
            raise ValueError("LLM API key not configured")
        
        url = self.config.base_url or "https://api.openai.com/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _generate_anthropic_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Anthropic Claude API."""
        if not self.config.api_key:
            raise ValueError("LLM API key not configured")
        
        url = self.config.base_url or "https://api.anthropic.com/v1/messages"
        
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        messages = [{"role": "user", "content": prompt}]
        
        data = {
            "model": self.config.model or "claude-3-sonnet-20240229",
            "max_tokens": self.config.max_tokens,
            "messages": messages
        }
        
        if system_prompt:
            data["system"] = system_prompt
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["content"][0]["text"]
    
    def _generate_local_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using local LLM (e.g., Ollama)."""
        url = self.config.base_url or "http://localhost:11434/api/generate"
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        data = {
            "model": self.config.model or "llama2",
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature
            }
        }
        
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    
    def is_available(self) -> bool:
        """Check if LLM service is available."""
        try:
            test_response = self.generate_response("Hello", "You are a test assistant.")
            return bool(test_response.strip())
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "available": self.is_available()
        }
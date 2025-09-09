#!/usr/bin/env python3
"""
Setup configuration for Wholesale AI Agent.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [
            line.strip() for line in f.readlines()
            if line.strip() and not line.startswith('#') and not line.startswith('-r')
        ]

setup(
    name="wholesale-agent",
    version="1.0.0",
    description="AI-native wholesale business operations agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # Author information
    author="Commerce Systems",
    author_email="engineering@commercesystems.ai",
    url="https://github.com/commercesystems/wholesale-agent",
    
    # Package information
    packages=find_packages(exclude=["tests*", "docs*"]),
    python_requires=">=3.8",
    install_requires=requirements,
    
    # Entry points for CLI
    entry_points={
        "console_scripts": [
            "wholesale-agent=wholesale_agent.cli.main:main",
            "wholesale-setup=scripts.generate_mock_data:main",
        ],
    },
    
    # Package data
    include_package_data=True,
    package_data={
        "wholesale_agent": [
            "*.txt",
            "*.json",
            "*.yaml",
            "*.yml",
        ],
    },
    
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    
    # Keywords
    keywords=[
        "ai", "agent", "wholesale", "inventory", "business", "automation",
        "llm", "chatbot", "commerce", "operations"
    ],
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/commercesystems/wholesale-agent/issues",
        "Source": "https://github.com/commercesystems/wholesale-agent",
        "Documentation": "https://docs.commercesystems.ai/wholesale-agent",
    },
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "postgres": [
            "psycopg2-binary>=2.9.0",
        ],
        "mysql": [
            "pymysql>=1.0.0",
        ],
        "redis": [
            "redis>=4.5.0",
        ],
        "monitoring": [
            "prometheus-client>=0.16.0",
            "structlog>=23.0.0",
        ],
        "rag": [
            "torch>=1.11.0",
            "sentence-transformers>=2.2.0", 
            "faiss-cpu>=1.7.0",
        ],
        "all": [
            "psycopg2-binary>=2.9.0",
            "pymysql>=1.0.0",
            "redis>=4.5.0",
            "prometheus-client>=0.16.0",
            "structlog>=23.0.0",
        ],
    },
    
    # Zip safe
    zip_safe=False,
)
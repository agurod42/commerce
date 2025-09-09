# Wholesale AI Agent

An AI-native tool for wholesale business operations that helps automate inventory management, business analytics, and operational workflows through a conversational interface.

## 🚀 Features

- **Intelligent Inventory Management**: Ask questions like "How much stock of wireless headphones do we have?" and get instant answers
- **Business Analytics**: Get insights on sales trends, top products, and inventory performance
- **Command-Line Chat Interface**: Natural language interaction through a terminal-based chat interface  
- **Inventory Management**: Add/remove stock, create products, update prices via natural language
- **Multi-LLM Support**: Works with OpenAI GPT, Anthropic Claude, and local models
- **Production-Ready**: Proper logging, error handling, configuration management, and monitoring
- **Extensible**: Clean architecture for adding new functionality

## 🏗️ Architecture

```
wholesale_agent/
├── cli/                    # Command-line interface
├── core/                   # AI agent and query processing
├── models/                 # Database models and ORM
├── utils/                  # Configuration, logging, migrations
├── tests/                  # Comprehensive test suite
├── scripts/                # Setup and utility scripts
└── migrations/             # Database migrations
```

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd wholesale-agent
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Optional: Install RAG dependencies (large download ~1GB)
pip install -r requirements-rag.txt
# OR using make:
# make install-rag
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=sqlite:///wholesale_agent.db

# LLM Configuration (choose one)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here

# Or use Anthropic Claude
# LLM_PROVIDER=anthropic
# LLM_API_KEY=your_anthropic_api_key_here

# Or use local model (e.g., Ollama)
# LLM_PROVIDER=local
# LLM_BASE_URL=http://localhost:11434/api/generate
# LLM_MODEL=llama2

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# Production settings (for deployment)
ENVIRONMENT=development
SECRET_KEY=your_secret_key_for_production
```

### 5. Initialize Database and Generate Mock Data

```bash
python -m wholesale_agent.cli.main --setup
```

### 6. Start the Agent

```bash
python -m wholesale_agent.cli.main
```

## 📖 Usage Examples

Once the agent is running, you can ask questions like:

```
You: How much stock of wireless headphones do we have?
🤖 Agent: I found 2 matching products:
• Wireless Bluetooth Headphones (SKU: ELE-1234-001) - Stock: 100 units (IN_STOCK)
• Premium Wireless Headphones (SKU: ELE-1235-002) - Stock: 15 units (LOW_STOCK)

You: Show me products running low on stock
🤖 Agent: ⚠️ 12 products are running low on stock:
• USB-C Cable - 5/20 units
• Cotton T-Shirt - 8/15 units
• Phone Case - 3/10 units
...

You: What's our total inventory value?
🤖 Agent: 📊 Business Overview:
• Total Products: 250
• Total Inventory Value: $125,750.00

🏷️ Top Categories:
• Electronics: 85 products ($45,200.00)
• Clothing: 65 products ($32,100.00)
• Home & Garden: 45 products ($28,150.00)

You: Add 50 units of wireless headphones
🤖 Agent: ✅ Successfully added 50 units to Wireless Bluetooth Headphones
Stock: 100 → 150 units

You: Remove 10 USB cables due to damage
🤖 Agent: ✅ Successfully removed 10 units from USB-C Cable
Stock: 45 → 35 units (marked as DAMAGED)
```

## 🔧 CLI Commands

```bash
# Interactive chat mode (default)
python -m wholesale_agent.cli.main

# Initialize database and generate mock data
python -m wholesale_agent.cli.main --setup

# Run single query
python -m wholesale_agent.cli.main --query "How much stock do we have?"

# Run database migrations
python -m wholesale_agent.cli.main --migrate

# Check system configuration
python -m wholesale_agent.cli.main --config-check

# Generate mock data only
python -m wholesale_agent.cli.main --generate-data

# Enable debug mode
python -m wholesale_agent.cli.main --debug

# Direct inventory management
python scripts/manage_inventory.py add "USB Cable" 50
python scripts/manage_inventory.py remove "Headphones" 10 --reason DAMAGED
python scripts/manage_inventory.py create NEW-001 "New Product" "Electronics" "TechCorp" 10.00 15.00 25.00
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=wholesale_agent --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

## 📊 Development

### Using Make (Recommended)

```bash
# Show available commands
make help

# Set up development environment
make dev-setup

# Install development dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Run all quality checks
make quality

# Build package
make build
```

### Database Management

```bash
# Initialize database
make setup-db

# Run migrations
make migrate

# Reset database (WARNING: Deletes all data)
make db-reset

# Generate new mock data
make generate-data
```

## 🚀 Production Deployment

For production setup, scaling, monitoring, and operations, see the [Deployment Guide](DEPLOYMENT.md).

## 🔧 Configuration

### Configuration Files

Create configuration files in JSON format:

```json
{
  "database": {
    "url": "sqlite:///wholesale_agent.db",
    "echo": false,
    "pool_size": 5
  },
  "llm": {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "max_tokens": 1000,
    "temperature": 0.7
  },
  "logging": {
    "level": "INFO",
    "structured": false,
    "log_dir": "logs"
  },
  "security": {
    "secret_key": "your-secret-key",
    "allowed_hosts": ["localhost"],
    "rate_limit_per_minute": 60
  },
  "performance": {
    "query_timeout_seconds": 30,
    "max_concurrent_queries": 10,
    "cache_enabled": true
  }
}
```

Load custom configuration:

```bash
python -m wholesale_agent.cli.main --config /path/to/config.json
```

### Environment Variables

All configuration can be overridden with environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `development` |
| `DATABASE_URL` | Database connection string | `sqlite:///wholesale_agent.db` |
| `LLM_PROVIDER` | LLM provider (openai/anthropic/local) | `openai` |
| `LLM_API_KEY` | API key for LLM provider | None |
| `LLM_MODEL` | Model name | `gpt-3.5-turbo` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SECRET_KEY` | Secret key for security | None (required for production) |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run quality checks: `make quality`
5. Run tests: `make test`
6. Commit your changes: `git commit -am 'Add new feature'`
7. Push to the branch: `git push origin feature/your-feature`
8. Submit a pull request

### Code Style

- Use Black for code formatting: `make format`
- Follow PEP 8 guidelines
- Add type hints for all functions
- Write comprehensive tests for new features
- Update documentation for user-facing changes

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Q: "No module named 'wholesale_agent'" error**
A: Make sure you're in the project directory and have activated your virtual environment:
```bash
source venv/bin/activate
pip install -e .
```

**Q: Database connection errors**
A: Check your DATABASE_URL environment variable and ensure the database is accessible:
```bash
python -m wholesale_agent.cli.main --config-check
```

**Q: LLM not responding**
A: Verify your API key and provider configuration:
```bash
export LLM_API_KEY=your_api_key_here
python -m wholesale_agent.cli.main --config-check
```

**Q: Permission errors on Linux/Mac**
A: Make sure scripts are executable:
```bash
chmod +x scripts/generate_mock_data.py
chmod +x wholesale_agent/cli/main.py
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
python -m wholesale_agent.cli.main --debug
```

### Getting Help

- Check the logs: `make logs`
- Run configuration check: `make config-check`
- Review test output: `make test`
- Open an issue on GitHub with:
  - Error messages
  - System information (`python --version`, OS)
  - Configuration (sanitize sensitive data)

## 🔗 Links

- [Documentation](docs/)
- [API Reference](docs/api/)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)